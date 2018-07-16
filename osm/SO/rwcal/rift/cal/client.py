"""
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

@file client.py
@author Varun Prasad(varun.prasad@riftio.com)
@date 2016-06-14
"""

import os

import gi
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwCal', '1.0')
gi.require_version('RwLog', '1.0')

from gi.repository import RwcalYang

import rift.cal.utils as cal_utils


class CloudsimClient(cal_utils.CloudSimCalMixin):
    """Cloudsim client that handles interactions with the server.
    """
    def __init__(self, log):
        super().__init__()
        self.log = log

    @property
    def images(self):
        _, images = self.cal.get_image_list(self.account)
        return images.imageinfo_list or []

    @property
    def vlinks(self):
        _, vlinks = self.cal.get_virtual_link_list(self.account)
        return vlinks.virtual_link_info_list or []

    @property
    def vdus(self):
        _, vdus = self.cal.get_vdu_list(self.account)
        return vdus.vdu_info_list or []

    def upload_image(self, location, name=None):
        """Onboard image to cloudsim server."""

        image = RwcalYang.YangData_RwProject_Project_VimResources_ImageinfoList()
        image.name = name or os.path.basename(location)
        image.location = location
        image.disk_format = "qcow2"
        rc, image.id = self.cal.create_image(self.account, image)

        self.log.info("Image created: {}".format(image.as_dict()))

        return image
