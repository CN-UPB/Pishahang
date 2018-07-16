
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

import gi

import rift.mano.dts as mano_dts

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class NsrMonParamSubscriber(mano_dts.AbstractOpdataSubscriber):
    """Registers for NSR monitoring parameter changes.

    Attributes:
        monp_id (str): Monitoring Param ID
        nsr_id (str): NSR ID
    """
    def __init__(self, log, dts, loop, project, nsr_id, monp_id=None, callback=None):
        super().__init__(log, dts, loop, project, callback)
        self.nsr_id = nsr_id
        self.monp_id = monp_id

    def get_xpath(self):
        return self.project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr" +
            "[nsr:ns-instance-config-ref={}]".format(quoted_key(self.nsr_id)) +
            "/nsr:monitoring-param" +
            ("[nsr:id={}]".format(quoted_key(self.monp_id)) if self.monp_id else ""))


class NsrScalingGroupRecordSubscriber(mano_dts.AbstractOpdataSubscriber):
    def __init__(self, log, dts, loop, project, nsr_id, scaling_group, callback=None):
        super().__init__(log, dts, loop, project, callback)
        self.nsr_id = nsr_id
        self.scaling_group = scaling_group

    def get_xpath(self):
        return self.project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr" +
            "[nsr:ns-instance-config-ref={}]".format(quoted_key(self.nsr_id)) +
            "/nsr:scaling-group-record" +
            "[nsr:scaling-group-name-ref={}]/instance".format(quoted_key(self.scaling_group)))

