# 
#   Copyright 2017 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Author(s): Nandan Sinha
#

import enum
import gi
import json
import os
import shutil 
import uuid

gi.require_version('RwVnfdYang', '1.0')
gi.require_version('RwNsdYang', '1.0')
from gi.repository import (
    RwYang, 
    NsdYang,
    VnfdYang,
    RwVnfdYang,
    RwNsdYang,
    RwPkgMgmtYang
)

import rift.package.icon as icon 
import rift.tasklets.rwlaunchpad.onboard as onboard 

class PackageCopyError(Exception): 
    pass

class CopyStatus(enum.Enum):
    UNINITIATED = 0
    STARTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5

TaskStatus = RwPkgMgmtYang.TaskStatus

class CopyMeta:
    STATUS_MAP = {
        CopyStatus.STARTED: TaskStatus.QUEUED.value_nick.upper(),
        CopyStatus.UNINITIATED: TaskStatus.QUEUED.value_nick.upper(),
        CopyStatus.IN_PROGRESS: TaskStatus.IN_PROGRESS.value_nick.upper(),
        CopyStatus.COMPLETED: TaskStatus.COMPLETED.value_nick.upper(),
        CopyStatus.FAILED: TaskStatus.FAILED.value_nick.upper(),
        CopyStatus.CANCELLED: TaskStatus.CANCELLED.value_nick.upper()
        }

    def __init__(self, transaction_id):
        self.transaction_id = transaction_id
        self.state = CopyStatus.UNINITIATED

    def set_state(self, state):
        self.state = state

    def as_dict(self): 
        return self.__dict__

    def to_yang(self):
        job = RwPkgMgmtYang.YangData_RwProject_Project_CopyJobs_Job.from_dict({
            "transaction_id": self.transaction_id, 
            "status": CopyMeta.STATUS_MAP[self.state]
            })
        return job

class CopyManifest: 
    """ Utility class to hold manifest information."""
    def __init__(self, project, log): 
        self.tasklet_info = project.tasklet.tasklet_info
        self.manifest = self.tasklet_info.get_pb_manifest() 
        self.use_ssl = self.manifest.bootstrap_phase.rwsecurity.use_ssl
        self.ssl_cert, self.ssl_key = None, None 
        if self.use_ssl: 
            self.ssl_cert = self.manifest.bootstrap_phase.rwsecurity.cert
            self.ssl_key = self.manifest.bootstrap_phase.rwsecurity.key
        self.onboarder = None
        self.log = log

    def ssl_manifest(self):
        return (self.use_ssl, self.ssl_cert, self.ssl_key)

    def get_onboarder(self, host="127.0.0.1", port="8008"): 
        if not self.onboarder: 
            self.onboarder = onboard.DescriptorOnboarder(self.log, 
                host, port, *self.ssl_manifest())
        return self.onboarder
            
        
class PackageFileCopier:
    DESCRIPTOR_MAP = {
            "vnfd": (RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd, 'vnfd rw-vnfd'), 
            "nsd" : (RwNsdYang.YangData_Nsd_NsdCatalog_Nsd, 'nsd rw-nsd') 
            }

    @classmethod
    def from_rpc_input(cls, rpc_input, project, proxy, log=None): 
        return cls(
                rpc_input.package_id,
                rpc_input.package_type, 
                rpc_input.package_name,
                rpc_input.project_name,
                project = project,
                proxy = proxy,
                log=log)

    def __init__(self, 
            pkg_id, 
            pkg_type, 
            pkg_name, 
            proj_name,
            project,
            proxy, 
            log):
        self.src_package_id = pkg_id
        self.package_type = pkg_type.lower()
        self.dest_package_name = pkg_name
        self.project_name = proj_name
        self.manifest = CopyManifest(project, log)
        self.dest_package_id = str(uuid.uuid4())
        self.transaction_id = str(uuid.uuid4())
        self.proxy = proxy
        self.log = log
        self.meta = CopyMeta(self.transaction_id)
        self.src_package = None
        self.dest_desc_msg = None

    @property
    def onboarder(self): 
        """ Onboarder object to invoke REST endpoint calls."""
        return self.manifest.get_onboarder()

    @property
    def progress(self): 
        """ Current status of operations."""
        return self.meta.to_yang()

    @property
    def descriptor_msg(self): 
        """ Descriptor message of the generated copied descriptor."""
        return self.dest_desc_msg 

    # Start of delegate calls
    def call_delegate(self, event):
        if not self.delegate:
            return
        
        getattr(self.delegate, event)(self) 

    def _copy_tree(self):
        """
        Locate directory tree of the source descriptor folder. 
        Copy directory tree to destination descriptor folder.  

        """
        self.copy_progress()

        store = self.proxy._get_store(self.package_type, \
                self.project_name if self.project_name else None)
        src_path = store._get_package_dir(self.src_package_id)
        self.src_package = store.get_package(self.src_package_id) 

        self.dest_copy_path = os.path.join(
                store.root_dir, 
                self.dest_package_id) 
        self.log.debug("Copying contents from {src} to {dest}".
                format(src=src_path, dest=self.dest_copy_path))

        shutil.copytree(src_path, self.dest_copy_path)
        # If there are icon files, also need to copy them in UI location
        if os.path.exists(os.path.join(src_path, "icons")): 
            src_icon_path = os.path.join(
                    icon.PackageIconExtractor.DEFAULT_INSTALL_DIR, 
                    self.package_type, 
                    self.src_package_id)
            dest_icon_path = os.path.join(
                    os.path.dirname(src_icon_path), 
                    self.dest_package_id)
            
            self.log.debug("Copying UI icon location from {} to {}".format(src_icon_path, 
                dest_icon_path))
            shutil.copytree(src_icon_path, dest_icon_path)

    def _create_descriptor_file(self):
        """ Update descriptor file for the newly copied descriptor catalog.
        Get descriptor contents from REST endpoint, change some identifiers
        and create a new descriptor yaml file from it.
        """
        # API call for the updated descriptor contents
        src_desc_contents = self.onboarder.get_updated_descriptor(self.src_package.descriptor_msg, self.project_name)

        # To generate the pb object, extract subtree in dict from "project-nsd:nsd" and root it 
        # under "nsd:nsd-catalog" (or vnfd)  
        root_element = "{0}:{0}-catalog".format(self.package_type)
        extract_sub_element = "project-{0}:{0}".format(self.package_type, self.package_type)
        src_desc_contents[extract_sub_element].update(
                id =self.dest_package_id, 
                name = self.dest_package_name,
                short_name = self.dest_package_name
                )
        D = {}
        D[root_element] = {self.package_type : src_desc_contents[extract_sub_element]}

        # Build the proto-buf gi object from generated JSON
        json_desc_msg = json.dumps(D)
        self.log.debug("*** JSON contents: {}".format(json_desc_msg))
        desc_cls, modules = PackageFileCopier.DESCRIPTOR_MAP[self.package_type]

        model = RwYang.Model.create_libyang()
        for module in modules.split():
            model.load_module(module) 

        self.dest_desc_msg = desc_cls.from_json(model, json_desc_msg, strict=False)

        # Write to yaml desc file 
        dest_desc_path = os.path.join(self.dest_copy_path, 
                "{pkg_name}_{pkg_type}.yaml".format(pkg_name=self.dest_package_name, pkg_type=self.package_type))
        with open(dest_desc_path, "w") as fh:
            fh.write(self.dest_desc_msg.to_yaml(model))

        # Remove copied .yaml, if present 
        src_desc_file = self.src_package.descriptor_file
        copied_desc_file = os.path.join(self.dest_copy_path, os.path.basename(src_desc_file))
        if os.path.exists(copied_desc_file):
            self.log.debug("Deleting copied yaml from old source %s" % (copied_desc_file))
            os.remove(copied_desc_file)

    def copy(self):
        try:
            if self.package_type not in PackageFileCopier.DESCRIPTOR_MAP: 
                raise PackageCopyError("Package type {} not currently supported for copy operations".format(self.package_type))

            self._copy_tree()
            self._create_descriptor_file()
            self.copy_succeeded()

        except Exception as e: 
            self.log.exception(str(e))
            self.copy_failed()

        self.copy_finished()

    def copy_failed(self):
        self.meta.set_state(CopyStatus.FAILED)
        self.call_delegate("on_download_failed")

    def copy_progress(self): 
        self.meta.set_state(CopyStatus.IN_PROGRESS)
        self.call_delegate("on_download_progress")

    def copy_succeeded(self):
        self.meta.set_state(CopyStatus.COMPLETED)
        self.call_delegate("on_download_succeeded")

    def copy_finished(self): 
        self.call_delegate("on_download_finished") 

