
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

import logging
import unittest

import rw_peas
import rwlogger

import gi
gi.require_version('RwTypes', '1.0')
from gi.repository import RwsdnalYang
from gi.repository.RwTypes import RwStatus


logger = logging.getLogger('sdnsim')

def get_sdn_account():
    """
    Creates an object for class RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    """
    account                 = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    account.account_type    = "sdnsim"
    account.sdnsim.username   = "rift"
    account.sdnsim.plugin_name = "rwsdn_sim"
    return account

def get_sdn_plugin():
    """
    Loads rw.sdn plugin via libpeas
    """
    plugin = rw_peas.PeasPlugin('rwsdn_sim', 'RwSdn-1.0')
    engine, info, extension = plugin()

    # Get the RwLogger context
    rwloggerctx = rwlogger.RwLog.Ctx.new("SDN-Log")

    sdn = plugin.get_interface("Topology")
    try:
        rc = sdn.init(rwloggerctx)
        assert rc == RwStatus.SUCCESS
    except:
        logger.error("ERROR:SDN sim plugin instantiation failed. Aborting tests")
    else:
        logger.info("SDN sim plugin successfully instantiated")
    return sdn



class SdnSimTest(unittest.TestCase):
    def setUp(self):
        """
          Initialize test plugins
        """
        self._acct = get_sdn_account()
        logger.info("SDN-Sim-Test: setUp")
        self.sdn   = get_sdn_plugin()
        logger.info("SDN-Sim-Test: setUpEND")

    def tearDown(self):
        logger.info("SDN-Sim-Test: Done with tests")

    def test_get_network_list(self):
        """
           First test case
        """
        rc, nwtop = self.sdn.get_network_list(self._acct)
        self.assertEqual(rc, RwStatus.SUCCESS) 
        logger.debug("SDN-Sim-Test: Retrieved network attributes ")
        for nw in nwtop.network:
           logger.debug("...Network id %s", nw.network_id)
           logger.debug("...Network name %s", nw.l2_network_attributes.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()




