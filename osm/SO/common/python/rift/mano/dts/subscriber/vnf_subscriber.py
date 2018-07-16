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

@file vnfr_subscriber.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 09-Jul-2016

"""

import gi
gi.require_version('RwDts', '1.0')
from gi.repository import RwDts as rwdts

from . import core


class VnfrCatalogSubscriber(core.AbstractOpdataSubscriber):
    """Vnfr Listener """

    def key_name(self):
        return "id"

    def get_reg_flags(self):
        return rwdts.Flag.SUBSCRIBER|rwdts.Flag.DELTA_READY

    def get_xpath(self):
        return self.project.add_project("D,/vnfr:vnfr-catalog/vnfr:vnfr")


class VnfdCatalogSubscriber(core.AbstractConfigSubscriber):
    """VNFD Listener"""

    def key_name(self):
        return "id"

    def get_xpath(self):
        return self.project.add_project("C,/project-vnfd:vnfd-catalog/project-vnfd:vnfd")
