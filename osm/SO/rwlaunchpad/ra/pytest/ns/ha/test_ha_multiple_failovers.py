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

import gi
import pytest
import random
import time

import rift.auto.mano as mano
import rift.auto.descriptor
from gi.repository.RwKeyspec import quoted_key

from gi.repository import (
    RwProjectNsdYang,
    RwNsrYang,
    RwVnfrYang,
    RwVlrYang,
    RwCloudYang,
    RwConmanYang,
)

@pytest.fixture(scope='module')
def test_project():
    return 'project_ha'

@pytest.mark.setup('active-configuration')
@pytest.mark.incremental
class TestMutipleFailoverActiveSetup(object):
    def test_create_project_users(self, rbac_user_passwd, user_domain, rw_active_user_proxy, logger,
            rw_active_project_proxy, rw_active_rbac_int_proxy, rw_active_conman_proxy, test_project, user_roles):
        # Create test users
        user_name_pfx = 'user_ha_'
        users = []
        for idx in range(1, 9):
            users.append(user_name_pfx+str(idx))
            mano.create_user(rw_active_user_proxy, user_name_pfx+str(idx), rbac_user_passwd, user_domain)

        # Create a test project and assign roles to users in the newly created project
        logger.debug('Creating project {}'.format(test_project))
        mano.create_project(rw_active_conman_proxy, test_project)

        for _ in range(8):
            role = random.choice(user_roles)
            user = users.pop()
            logger.debug('Assinging role {} to user {} in project {}'.format(role, user, test_project))
            mano.assign_project_role_to_user(rw_active_project_proxy, role, user, test_project, user_domain,
                                            rw_active_rbac_int_proxy)

    def test_create_cloud_account(self, cloud_account, fmt_prefixed_cloud_xpath, fmt_cloud_xpath, rw_active_cloud_pxy, 
                                test_project, logger):
        logger.debug('Creating cloud account {} for project {}'.format(cloud_account.name, test_project))
        xpath = fmt_prefixed_cloud_xpath.format(project=quoted_key(test_project),
                                                account_name=quoted_key(cloud_account.name))
        rw_active_cloud_pxy.replace_config(xpath, cloud_account)
        xpath_no_pfx = fmt_cloud_xpath.format(project=quoted_key(test_project),
                                              account_name=quoted_key(cloud_account.name))
        response =  rw_active_cloud_pxy.get(xpath_no_pfx)
        assert response.name == cloud_account.name
        assert response.account_type == cloud_account.account_type

        rw_active_cloud_pxy.wait_for(fmt_cloud_xpath.format(project=quoted_key(test_project), account_name=quoted_key(
        cloud_account.name)) + '/connection-status/status', 'success', timeout=30, fail_on=['failure'])

    def test_onboard_descriptors(self, descriptors, test_project, active_mgmt_session, fmt_nsd_catalog_xpath, logger):
        # Uploads the descriptors
        pingpong_descriptors = descriptors['pingpong']
        for descriptor in pingpong_descriptors:
            logger.debug('Onboarding descriptor {} for project {}'.format(descriptor, test_project))
            rift.auto.descriptor.onboard(active_mgmt_session, descriptor, project=test_project)

        # Verify whether the descriptors uploaded successfully
        nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
        nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(test_project))
        nsd_catalog = nsd_pxy.get_config(nsd_xpath)
        assert nsd_catalog
    
    def test_instantiate_nsr(self, fmt_nsd_catalog_xpath, cloud_account, active_mgmt_session, logger, test_project):
        nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
        rwnsr_pxy = active_mgmt_session.proxy(RwNsrYang)

        nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(test_project))
        nsd_catalog = nsd_pxy.get_config(nsd_xpath)
        assert nsd_catalog
        nsd = nsd_catalog.nsd[0]
        nsr = rift.auto.descriptor.create_nsr(cloud_account.name, nsd.name, nsd)

        logger.debug('Instantiating NS for project {}'.format(test_project))
        rift.auto.descriptor.instantiate_nsr(nsr, rwnsr_pxy, logger, project=test_project)


@pytest.mark.depends('active-configuration')
@pytest.mark.setup('multiple-failovers')
@pytest.mark.incremental
class TestHaMultipleFailovers(object):
    def test_ha_multiple_failovers(self, revertive_pref_host, active_confd_host, standby_confd_host, standby_lp_node_obj, active_lp_node_obj, logger, 
                                        fmt_cloud_xpath, cloud_account, test_project, active_site_name, standby_site_name, standby_mgmt_session, active_mgmt_session, descriptors):
        count, failover_count = 1, 10
        current_actv_mgmt_session, current_stdby_mgmt_session = active_mgmt_session, standby_mgmt_session
        current_actv_lp_node_obj = active_lp_node_obj

        descriptor_list = descriptors['haproxy'][::-1] + descriptors['vdud_cfgfile'][::-1]
        
        original_active_as_standby_kwargs = {'revertive_pref_host': revertive_pref_host, 'new_active_ip': standby_confd_host, 'new_active_site': standby_site_name, 
            'new_standby_ip': active_confd_host, 'new_standby_site': active_site_name}
        original_active_as_active_kwargs = {'revertive_pref_host': revertive_pref_host, 'new_active_ip':active_confd_host, 'new_active_site': active_site_name, 
            'new_standby_ip': standby_confd_host, 'new_standby_site': standby_site_name}

        while count <= failover_count:
            kwargs = original_active_as_active_kwargs
            if count%2 == 1:
                kwargs = original_active_as_standby_kwargs

            # upload descriptor
            if count not in [5,6,7,8]:
                descriptor = descriptor_list.pop()
                rift.auto.descriptor.onboard(current_actv_mgmt_session, descriptor, project=test_project)

            # Collect config, op-data from current active before doing a failover
            current_actv_lp_node_obj.session = None
            current_actv_lp_node_obj.collect_data()

            time.sleep(5)
            logger.debug('Failover Iteration - {}. Current standby {} will be the new active'.format(count, current_stdby_mgmt_session.host))
            mano.indirect_failover(**kwargs)

            last_actv_lp_node_obj = current_actv_lp_node_obj
            current_actv_mgmt_session, current_stdby_mgmt_session = active_mgmt_session, standby_mgmt_session
            current_actv_lp_node_obj = active_lp_node_obj
            if count%2 == 1:
                current_actv_lp_node_obj = standby_lp_node_obj
                current_actv_mgmt_session, current_stdby_mgmt_session = standby_mgmt_session, active_mgmt_session

            logger.debug('Waiting for the new active {} to come up'.format(current_actv_mgmt_session.host))
            mano.wait_for_standby_to_become_active(current_actv_mgmt_session)

            # Wait for NSR to become active
            rw_new_active_cloud_pxy = current_actv_mgmt_session.proxy(RwCloudYang)
            rwnsr_proxy = current_actv_mgmt_session.proxy(RwNsrYang)

            rw_new_active_cloud_pxy.wait_for(
                fmt_cloud_xpath.format(project=quoted_key(test_project), account_name=quoted_key(
                    cloud_account.name)) + '/connection-status/status', 'success', timeout=60, fail_on=['failure'])

            nsr_opdata = rwnsr_proxy.get(
                    '/rw-project:project[rw-project:name={project}]/ns-instance-opdata'.format(
                        project=quoted_key(test_project)))
            assert nsr_opdata
            nsrs = nsr_opdata.nsr

            for nsr in nsrs:
                xpath = "/rw-project:project[rw-project:name={project}]/ns-instance-opdata/nsr[ns-instance-config-ref={config_ref}]/config-status".format(
                    project=quoted_key(test_project), config_ref=quoted_key(nsr.ns_instance_config_ref))
                rwnsr_proxy.wait_for(xpath, "configured", fail_on=['failed'], timeout=400)

            # Collect config, op-data from new active
            current_actv_lp_node_obj.session = None
            current_actv_lp_node_obj.collect_data()

            # Compare data between last active and current active
            current_actv_lp_node_obj.compare(last_actv_lp_node_obj)
            count += 1


@pytest.mark.depends('multiple-failovers')
@pytest.mark.incremental
class TestHaOperationPostMultipleFailovers(object):
    def test_instantiate_nsr(self, fmt_nsd_catalog_xpath, cloud_account, active_mgmt_session, logger, test_project):
        """Check if a new NS instantiation goes through after multiple HA failovers.
        It uses metadata cfgfile nsd for the instantiation.
        There alreasy exists ping pong NS instantiation"""
        nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
        rwnsr_pxy = active_mgmt_session.proxy(RwNsrYang)

        nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(test_project))
        nsd_catalog = nsd_pxy.get_config(nsd_xpath)
        assert nsd_catalog
        cfgfile_nsd = [nsd for nsd in nsd_catalog.nsd if 'cfgfile_nsd' in nsd.name][0]
        nsr = rift.auto.descriptor.create_nsr(cloud_account.name, cfgfile_nsd.name, cfgfile_nsd)

        logger.debug('Instantiating cfgfile NS for project {}'.format(test_project))
        rift.auto.descriptor.instantiate_nsr(nsr, rwnsr_pxy, logger, project=test_project)

    def test_nsr_terminate(self, active_mgmt_session, logger, test_project):
        """"""
        rwnsr_pxy = active_mgmt_session.proxy(RwNsrYang)
        rwvnfr_pxy = active_mgmt_session.proxy(RwVnfrYang)
        rwvlr_pxy = active_mgmt_session.proxy(RwVlrYang)

        logger.debug("Trying to terminate ping pong, cfgfile NSRs in project {}".format(test_project))
        rift.auto.descriptor.terminate_nsr(rwvnfr_pxy, rwnsr_pxy, rwvlr_pxy, logger, test_project)

    def test_delete_descriptors(self, active_mgmt_session, test_project, logger):
        logger.info("Trying to delete the descriptors in project {}".format(test_project))
        rift.auto.descriptor.delete_descriptors(active_mgmt_session, test_project)

    def test_delete_cloud_accounts(self, active_mgmt_session, logger, test_project, cloud_account):
        logger.info("Trying to delete the cloud-account in project {}".format(test_project))
        rift.auto.mano.delete_cloud_account(active_mgmt_session, cloud_account.name, test_project)

    def test_delete_projects(self, active_mgmt_session, test_project, logger):
        rw_conman_proxy = active_mgmt_session.proxy(RwConmanYang)
        logger.debug('Deleting project {}'.format(test_project))
        rift.auto.mano.delete_project(rw_conman_proxy, test_project)