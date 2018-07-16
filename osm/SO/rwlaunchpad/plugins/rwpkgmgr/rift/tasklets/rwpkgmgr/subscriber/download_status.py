#
#   Copyright 2016-2017 RIFT.IO Inc
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

import gi
import os

import rift.mano.dts as mano_dts
import rift.package.store as store
from rift.package.convert import (
    RwVnfdSerializer,
    RwNsdSerializer,
)

from gi.repository import (
    RwYang,
    RwDts
)

class DownloadStatusSubscriber(mano_dts.AbstractOpdataSubscriber):
    def __init__(self, log, dts, loop, project, callback):
        super().__init__(log, dts, loop, project, callback)

    def get_xpath(self):
        return self._project.add_project(
            "D,/rw-pkg-mgmt:download-jobs/rw-pkg-mgmt:job")


class VnfdStatusSubscriber(mano_dts.VnfdCatalogSubscriber):
    DOWNLOAD_DIR = store.VnfdPackageFilesystemStore.DEFAULT_ROOT_DIR
    DESC_TYPE = 'vnfd'
    SERIALIZER = RwVnfdSerializer()

    def __init__(self, log, dts, loop, project):
        super().__init__(log, dts, loop, project, callback=self.on_change)

    def on_change(self, msg, action):
        log_msg = "1. Vnfd called w/ msg attributes: {} id {} name {} action: {}". \
                  format(repr(msg), msg.id, msg.name, repr(action))
        self.log.debug(log_msg)
        if action == RwDts.QueryAction.UPDATE or action == RwDts.QueryAction.CREATE:
            actionCreate(self, msg, self.project.name)
        else:
            self.log.debug("VnfdStatusSubscriber: No action for {}".format(repr(action)))
            pass


class NsdStatusSubscriber(mano_dts.NsdCatalogSubscriber):
    DOWNLOAD_DIR = store.NsdPackageFilesystemStore.DEFAULT_ROOT_DIR
    DESC_TYPE = 'nsd'
    SERIALIZER = RwNsdSerializer()

    def __init__(self, log, dts, loop, project):
        super().__init__(log, dts, loop, project, callback=self.on_change)

    def on_change(self, msg, action):
        log_msg = "1. Nsd called w/ msg attributes: {} id {} name {} action: {}". \
                  format(repr(msg), msg.id, msg.name, repr(action))
        self.log.debug(log_msg)
        if action == RwDts.QueryAction.UPDATE or action == RwDts.QueryAction.CREATE:
            actionCreate(self, msg, self.project.name)
        else:
            self.log.debug("NsdStatusSubscriber: No action for {}".format(repr(action)))
            pass


def actionCreate(descriptor, msg, project_name=None):
    ''' Create folder structure if it doesn't exist: id/vnf name OR id/nsd name
    Serialize the Vnfd/Nsd object to yaml and store yaml file in the created folder.
    '''

    download_dir = os.path.join(
            descriptor.DOWNLOAD_DIR,
            project_name if project_name else "",  
            msg.id)

    # If a download dir is present with contents, then we know it has been created in the
    # upload path.
    if os.path.exists(download_dir) and os.listdir(download_dir):
        descriptor.log.debug("Skpping folder creation, {} already present".format(download_dir))
        return
    else:
        # Folder structure is based on top-level package-id directory
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            descriptor.log.debug("Created directory {}".format(download_dir))
        yaml_path = "{base}/{name}_{type}.yaml". \
                    format(base=download_dir, name=msg.name[0:50], type=descriptor.DESC_TYPE)
        with open(yaml_path,"w") as fh:
                fh.write(descriptor.SERIALIZER.to_yaml_string(msg))
