#
#   Copyright 2016 RIFT.IO Inc
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
# Author(s): Varun Prasad
# Creation Date: 09/25/2016
#

import asyncio
import os

import rift.package.store as store
import rift.package.package
import rift.package.icon as icon
import rift.package.checksums as checksums

from .base import AbstractPackageManagerProxy
from rift.tasklets.rwlaunchpad import image

class UnknownPackageType(Exception):
    pass


class FileSystemProxy(AbstractPackageManagerProxy):
    """Proxy for Filesystem based store.
    """
    PACKAGE_TYPE_MAP = {"vnfd": store.VnfdPackageFilesystemStore,
                        "nsd": store.NsdPackageFilesystemStore}

    # Refer: https://confluence.riftio.com/display/ATG/Launchpad+package+formats
    SCHEMA = {
        "nsd": ["icons", "ns_config", "scripts", "vnf_config"],
        "vnfd": ["charms", "cloud_init", "icons", "images", "scripts", "readme", "test", "doc"]
    }

    SCHEMA_TO_PERMS = {'scripts': 0o777}

    def __init__(self, loop, log, dts):
        self.loop = loop
        self.log = log
        self.dts = dts
        self.store_cache = {}
        self.uploader = image.ImageUploader(self.log, self.loop, self.dts)

    def _get_store(self, package_type, project_name = None):
        store_cls = self.PACKAGE_TYPE_MAP[package_type]
        self.store_cache[package_type] = store_cls(self.log, project=project_name)
        store = self.store_cache[package_type]

        return store

    @asyncio.coroutine
    def endpoint(self, package_type, package_id, project_name=None):
        package_type = package_type.lower()
        if package_type not in self.PACKAGE_TYPE_MAP:
            raise UnknownPackageType()
        
        store = self._get_store(package_type, project_name)

        package = store._get_package_dir(package_id)
        rel_path = os.path.relpath(package, start=os.path.dirname(store.root_dir))

        url = "https://127.0.0.1:8008/mano/api/package/{}/{}".format(package_type, rel_path)
        
        return url

    @asyncio.coroutine
    def schema(self, package_type):
        package_type = package_type.lower()
        if package_type not in self.PACKAGE_TYPE_MAP:
            raise UnknownPackageType()

        return self.SCHEMA[package_type]

    def package_file_add(self, new_file, package_type, package_id, package_path, package_file_type, project_name):
        # Get the schema from thr package path
        # the first part will always be the vnfd/nsd name
        mode = 0o664

        # for files other than README, create the package path from the asset type, e.g. icons/icon1.png
        # for README files, strip off any leading '/' 
        file_name = package_path
        package_path = package_file_type + "/" + package_path \
            if package_file_type != "readme" else package_path.strip('/')
        
        components = package_path.split("/")
        if len(components) > 2:
            schema = components[1]
            mode = self.SCHEMA_TO_PERMS.get(schema, mode)

        # Fetch the package object
        package_type = package_type.lower()
        store = self._get_store(package_type, project_name)
        package = store.get_package(package_id)

        # Construct abs path of the destination obj
        path = store._get_package_dir(package_id)
        dest_file = os.path.join(path, package.prefix, package_path)

        # Insert (by copy) the file in the package location. For icons, 
        # insert also in UI location for UI to pickup
        try:
            self.log.debug("Inserting file {} in the destination {} - {} ".format(dest_file, package_path, dest_file))
            package.insert_file(new_file, dest_file, package_path, mode=mode)

            if package_file_type == 'icons': 
                icon_extract = icon.PackageIconExtractor(self.log) 
                icon_extract.extract_icons(package)

            if package_file_type == 'images':                                
                image_hdl = package.open(package_path)
                image_checksum = checksums.checksum(image_hdl)
                
                try:
                    self.uploader.upload_image(file_name, image_checksum, image_hdl, {})
                    self.uploader.upload_image_to_cloud_accounts(file_name, image_checksum, project_name)
                finally:
                    _ = image_hdl.close()
        except rift.package.package.PackageAppendError as e:
            self.log.exception(e)
            return False

        self.log.debug("File insertion complete at {}".format(dest_file))
        return True

    def package_file_delete(self, package_type, package_id, package_path, package_file_type, project_name):
        package_type = package_type.lower()
        store = self._get_store(package_type, project_name)
        package = store.get_package(package_id)

        # for files other than README, create the relative package path from the asset type
        package_path_rel = package_file_type + "/" + package_path \
            if package_file_type != "readme" else package_path

        # package_path has to be relative, so strip off the starting slash if
        # provided incorrectly.
        if package_path_rel[0] == "/":
            package_path_rel = package_path_rel[1:]

        # Construct abs path of the destination obj
        path = store._get_package_dir(package_id)
        dest_file = os.path.join(path, package.prefix, package_path_rel)

        try:
            package.delete_file(dest_file, package_path_rel)

            if package_file_type == 'icons': 
                ui_icon_path = os.path.join(
                        icon.PackageIconExtractor.DEFAULT_INSTALL_DIR, 
                        package_type, 
                        package_id)
                if os.path.exists(ui_icon_path): 
                    icon_file = os.path.join(ui_icon_path, package_path)
                    self.log.debug("Deleting UI icon file path {}".format(icon_file))
                    os.remove(icon_file)

        except rift.package.package.PackageAppendError as e:
            self.log.exception(e)
            return False

        return True

