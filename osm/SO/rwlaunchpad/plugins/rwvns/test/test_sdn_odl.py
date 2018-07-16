
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

import logging
import unittest

import rw_peas
import rwlogger

import gi
gi.require_version('RwTypes', '1.0')
from gi.repository import RwsdnalYang
from gi.repository.RwTypes import RwStatus


logger = logging.getLogger('sdnodl')

odl_info = {
    'username'      : 'admin',
    'password'      : 'admin',
    'url'           : 'http://10.66.4.27:8181',
}


def get_sdn_account():
    """
    Creates an object for class RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    """
    account                 = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    account.name            = "grunt27"
    account.account_type    = "odl"
    account.odl.plugin_name = "rwsdn_odl"
    account.odl.username    = odl_info['username']
    account.odl.password    = odl_info['password']
    account.odl.url       = odl_info['url']

    return account

def get_sdn_plugin():
    """
    Loads rw.sdn plugin via libpeas
    """
    plugin = rw_peas.PeasPlugin('rwsdn_odl', 'RwSdn-1.0')
    engine, info, extension = plugin()

    # Get the RwLogger context
    rwloggerctx = rwlogger.RwLog.Ctx.new("SDN-Log")

    sdn = plugin.get_interface("Topology")
    try:
        rc = sdn.init(rwloggerctx)
        assert rc == RwStatus.SUCCESS
    except:
        logger.error("ERROR:SDN ODL plugin instantiation failed. Aborting tests")
    else:
        logger.info("SDN ODL plugin successfully instantiated")
    return sdn



class SdnOdlTest(unittest.TestCase):
    def setUp(self):
        """
          Initialize test plugins
        """
        self._acct = get_sdn_account()
        logger.info("SDN-Odl-Test: setUp")
        self.sdn   = get_sdn_plugin()
        logger.info("SDN-Odl-Test: setUpEND")

    def tearDown(self):
        logger.info("SDN-Odl-Test: Done with tests")

    def test_validate_sdn_creds(self):
        """
           First test case
        """
        logger.debug("SDN-Odl-Test: Starting validate creds ")
        rc, status = self.sdn.validate_sdn_creds(self._acct)
        logger.debug("SDN-Odl-Test: SDN return code %s resp %s", rc, status)
        self.assertEqual(rc, RwStatus.SUCCESS)
        logger.info("SDN-Odl-Test: Passed validate creds")

    def test_get_network_list(self):
        """
           Get-network-list test case
        """
        logger.debug("SDN-Odl-Test: Getting network list ")
        rc, status = self.sdn.get_network_list(self._acct)
        logger.debug("SDN-Odl-Test: SDN return code %s resp %s", rc, status)
        self.assertEqual(rc, RwStatus.SUCCESS)
        logger.info("SDN-Odl-Test: Passed get network list")



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()




