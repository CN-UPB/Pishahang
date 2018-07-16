#!/usr/bin/env python3
"""
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
"""

import pytest
import gi

import rift.auto.mano
import rift.auto.descriptor

gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
gi.require_version('RwCloudYang', '1.0')
gi.require_version('RwSdnYang', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwImageMgmtYang', '1.0')
gi.require_version('RwStagingMgmtYang', '1.0')
gi.require_version('RwPkgMgmtYang', '1.0')

from gi.repository import (
    RwProjectNsdYang,
    RwProjectVnfdYang,
    RwCloudYang,
    RwSdnYang,
    RwLaunchpadYang,
    RwVnfrYang,
    RwNsrYang,
    RwImageMgmtYang,
    RwStagingMgmtYang,
    RwPkgMgmtYang,
)

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


@pytest.fixture(scope='module')
def mano_xpaths():
    """All xpaths which need to be accessed by users with various roles"""

    xpaths_dict = {
        'catalog' : ('/vnfd-catalog', '/nsd-catalog'),
        'accounts' : ('/cloud', '/sdn'),
        'records' : ('/vnfr-catalog', '/vnfr-console', '/ns-instance-config', '/ns-instance-opdata'),
        'pkg-mgmt' : ('/staging-areas', '/upload-jobs', '/copy-jobs', '/download-jobs'), 
        'config-agent': ('/config-agent',),
        'ro' : ('/resource-orchestrator',),
        'datacenter' : ('/datacenters',),
    }
    return xpaths_dict


@pytest.fixture(scope='module')
def mano_roles_xpaths_mapping():
    """Mano roles and its accessible xpaths mapping"""
    mano_roles_xpaths_mapping_dict = {
        'rw-project:project-admin': ('catalog', 'accounts', 'records', 'pkg-mgmt', 'config-agent', 'ro', 'datacenter'), 
        'rw-project:project-oper' : ('catalog', 'accounts', 'records', 'pkg-mgmt', 'config-agent', 'ro', 'datacenter'),  
        'rw-project-mano:catalog-oper' : ('catalog', 'pkg-mgmt'), 
        'rw-project-mano:catalog-admin' : ('catalog', 'pkg-mgmt'),  
        'rw-project-mano:lcm-admin' : ('catalog', 'accounts', 'records', 'config-agent', 'datacenter'), 
        'rw-project-mano:lcm-oper' : ('records',), 
        'rw-project-mano:account-admin' : ('accounts', 'config-agent', 'ro', 'datacenter'), 
        'rw-project-mano:account-oper' : ('accounts', 'config-agent', 'ro', 'datacenter'), 
    }
    return mano_roles_xpaths_mapping_dict


@pytest.fixture(scope='module')
def xpath_module_mapping():
    """Mano Xpaths and its module mapping. Value also carries config or opdata type along with yang-module"""
    xpath_module_mapping_dict = {
        ('/vnfd-catalog',): (RwProjectVnfdYang, 'get_config'), 
        ('/nsd-catalog',): (RwProjectNsdYang, 'get_config'),
        ('/cloud',): (RwCloudYang, 'get_config'),
        ('/sdn',): (RwSdnYang, 'get_config'),
        ('/vnfr-catalog', '/vnfr-console'): (RwVnfrYang, 'get'),
        ('/ns-instance-config', '/ns-instance-opdata'): (RwNsrYang, 'get'), 
        ('/upload-jobs', '/download-jobs'): (RwImageMgmtYang, 'get'),
        ('/copy-jobs', ): (RwPkgMgmtYang, 'get'),
        ('/staging-areas',): (RwStagingMgmtYang, 'get'),
        ('/resource-orchestrator', '/datacenters'): (RwLaunchpadYang, None),
        ('/config-agent',): None,
    }
    return xpath_module_mapping_dict

@pytest.mark.setup('mano_xpath_access')
@pytest.mark.depends('nsr')
@pytest.mark.incremental
class TestRbacManoXpathAccess(object):
    def test_copy_nsd_catalog_item(self, mgmt_session):
        """Copy a NSD catalog item, so that /copy-jobs xpath can be tested."""
        nsd_path = '/rw-project:project[rw-project:name="default"]/nsd-catalog'
        nsd = mgmt_session.proxy(RwProjectNsdYang).get_config(nsd_path)
        nsd_pkg_id = nsd.nsd[0].id
        rpc_input = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageCopy.from_dict(
            {'package_type': 'NSD', 'package_id': nsd_pkg_id, 'package_name': 'test_nsd_copy',
             'project_name': 'default'})
        mgmt_session.proxy(RwPkgMgmtYang).rpc(rpc_input)

    def test_rbac_mano_xpaths_access(self, mano_xpaths, logger, mano_roles_xpaths_mapping, xpath_module_mapping, session_class,
        project_keyed_xpath, user_domain, rbac_platform_proxy, rw_project_proxy, rbac_user_passwd, confd_host, rw_user_proxy, rw_rbac_int_proxy):
        """Verify Mano roles/Permission mapping works (Verifies only read access for all Xpaths)."""
        project_name = 'default'

        # Skipping download-jobs as it is not yet implemented from MANO side.
        # Others are skipped becuase they need Juju, Openmano configurations etc.
        skip_xpaths = ('/download-jobs', '/config-agent', '/resource-orchestrator', '/datacenters', '/upload-jobs')
        
        for index, (role, xpath_keys_tuple) in enumerate(mano_roles_xpaths_mapping.items()):
            # Create an user and assign a role 
            user_name = 'user-{}'.format(index)
            rift.auto.mano.create_user(rw_user_proxy, user_name, rbac_user_passwd, user_domain)
            logger.debug('Creating an user {} with role {}'.format(user_name, role))
            if 'platform' in role:
                rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, role, user_name, user_domain, rw_rbac_int_proxy)
            else:
                rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, user_name, project_name, user_domain, rw_rbac_int_proxy)
                
            # Get user session
            user_session = rift.auto.mano.get_session(session_class, confd_host, user_name, rbac_user_passwd)

            # go through each of its xpaths keys and try to access
            for xpath_key in xpath_keys_tuple:
                for xpath in mano_xpaths[xpath_key]:
                    if xpath in skip_xpaths:
                        continue
                    logger.debug('User {} with role {} trying to access xpath {}'.format(user_name, role, xpath))
                    yang_module, get_type = [yang_module for xpath_tuple, yang_module in xpath_module_mapping.items() 
                                                                                            if xpath in xpath_tuple][0]
                    user_pxy = user_session.proxy(yang_module)
                    get_data_func = getattr(user_pxy, get_type)
                    assert get_data_func(project_keyed_xpath.format(project_name=quoted_key(project_name))+xpath) 

            # go through remaining xpaths keys which this user-role not part of and try to access; it should fail
            access_denied_xpath_keys_tuple = set(mano_xpaths.keys()).difference(xpath_keys_tuple)
            for xpath_key in access_denied_xpath_keys_tuple:
                for xpath in mano_xpaths[xpath_key]:
                    if xpath in skip_xpaths:
                        continue
                    logger.debug('User {} with role {} trying to access xpath {}. It should get None'.format(user_name, role, xpath))
                    yang_module, get_type = [yang_module for xpath_tuple, yang_module in xpath_module_mapping.items() 
                                                                                            if xpath in xpath_tuple][0]
                    user_pxy = user_session.proxy(yang_module)
                    get_data_func = getattr(user_pxy, get_type)
                    assert get_data_func(project_keyed_xpath.format(project_name=quoted_key(project_name))+xpath) is None
