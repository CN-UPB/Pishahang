
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


logger = logging.getLogger('sdnopenstack')

openstack_info = {
    'username'           : 'pluto',
    'password'           : 'mypasswd',
    'auth_url'           : 'http://10.66.4.17:5000/v2.0/',
    'project_name'       : 'demo',
    'user_domain_name'   : 'default',
    'project_domain_name': 'default'
}


def get_sdn_account():
    """
    Creates an object for class RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    """
    account                 = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList()
    account.name                     = "grunt17"
    account.account_type             = "openstack"
    account.openstack.plugin_name = "rwsdn_openstack"
    account.openstack.key            = openstack_info['username']
    account.openstack.secret         = openstack_info['password']
    account.openstack.auth_url       = openstack_info['auth_url']
    account.openstack.tenant         = openstack_info['project_name']
    account.openstack.user_domain    = openstack_info['user_domain_name']
    account.openstack.project_domain = openstack_info['project_domain_name']

    return account

def get_sdn_plugin():
    """
    Loads rw.sdn plugin via libpeas
    """
    plugin = rw_peas.PeasPlugin('rwsdn_openstack', 'RwSdn-1.0')
    engine, info, extension = plugin()

    # Get the RwLogger context
    rwloggerctx = rwlogger.RwLog.Ctx.new("SDN-Log")

    sdn = plugin.get_interface("Topology")
    try:
        rc = sdn.init(rwloggerctx)
        assert rc == RwStatus.SUCCESS
    except:
        logger.error("ERROR:SDN openstack plugin instantiation failed. Aborting tests")
    else:
        logger.info("SDN openstack plugin successfully instantiated")
    return sdn



class SdnOpenstackTest(unittest.TestCase):
    def setUp(self):
        """
          Initialize test plugins
        """
        self._acct = get_sdn_account()
        logger.info("SDN-Openstack-Test: setUp")
        self.sdn   = get_sdn_plugin()
        logger.info("SDN-Openstack-Test: setUpEND")

    def tearDown(self):
        logger.info("SDN-Openstack-Test: Done with tests")

    def test_validate_sdn_creds(self):
        """
           First test case
        """
        logger.debug("SDN-Openstack-Test: Starting validate creds ")
        rc, status = self.sdn.validate_sdn_creds(self._acct)
        logger.debug("SDN-Openstack-Test: SDN return code %s resp %s", rc, status)
        self.assertEqual(rc, RwStatus.SUCCESS)
        logger.info("SDN-Openstack-Test: Passed validate creds")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()




