
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

import datetime
import logging
import unittest

import rw_peas
import rwlogger

from gi.repository import RwsdnalYang
import gi
gi.require_version('RwTypes', '1.0')
gi.require_version('RwSdnal', '1.0')
from gi.repository import RwcalYang
from gi.repository import IetfNetworkYang
from gi.repository.RwTypes import RwStatus


logger = logging.getLogger('mock')

def get_sdn_account():
    """
    Creates an object for class RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    """
    account                 = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    account.account_type    = "mock"
    account.mock.username   = "rift"
    account.mock.plugin_name = "rwsdn_mock"
    return account

def get_sdn_plugin():
    """
    Loads rw.sdn plugin via libpeas
    """
    plugin = rw_peas.PeasPlugin('rwsdn_mock', 'RwSdn-1.0')
    engine, info, extension = plugin()

    # Get the RwLogger context
    rwloggerctx = rwlogger.RwLog.Ctx.new("SDN-Log")

    sdn = plugin.get_interface("Topology")
    try:
        rc = sdn.init(rwloggerctx)
        assert rc == RwStatus.SUCCESS
    except:
        logger.error("ERROR:SDN plugin instantiation failed. Aborting tests")
    else:
        logger.info("Mock SDN plugin successfully instantiated")
    return sdn



class SdnMockTest(unittest.TestCase):
    def setUp(self):
        """
          Initialize test plugins
        """
        self._acct = get_sdn_account()
        logger.info("Mock-SDN-Test: setUp")
        self.sdn   = get_sdn_plugin()
        logger.info("Mock-SDN-Test: setUpEND")

    def tearDown(self):
        logger.info("Mock-SDN-Test: Done with tests")

    def test_get_network_list(self):
        """
           First test case
        """
        rc, nwtop = self.sdn.get_network_list(self._acct)
        self.assertEqual(rc, RwStatus.SUCCESS) 
        logger.debug("SDN-Mock-Test: Retrieved network attributes ")
        for nw in nwtop.network:
           logger.debug("...Network id %s", nw.network_id)
           logger.debug("...Network name %s", nw.l2_network_attributes.name)
           print(nw)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()




