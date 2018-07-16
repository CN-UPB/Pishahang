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
def test_projects():
    projects = ['default']
    for idx in range(1, 4):
        projects.append('project_ha_'+str(idx))
    return projects


@pytest.mark.setup('active_configuration')
@pytest.mark.incremental
class TestActiveLpConfiguration(object):
    """sets up the configuration as per RIFT-17854"""
    def test_create_project_users(self, rbac_user_passwd, user_domain, rw_active_user_proxy, logger,
            rw_active_project_proxy, rw_active_rbac_int_proxy, rw_active_conman_proxy, test_projects, user_roles):
        # Create test users
        user_name_pfx = 'user_ha_'
        users = []
        for idx in range(1, 9):
            users.append(user_name_pfx+str(idx))
            mano.create_user(rw_active_user_proxy, user_name_pfx+str(idx), rbac_user_passwd, user_domain)

        # Create projects and assign roles to users in the newly created project
        for project_name in test_projects:
            if project_name == 'default':
                continue
            logger.debug('Creating project {}'.format(project_name))
            mano.create_project(rw_active_conman_proxy, project_name)

        for project_name in test_projects:
            for _ in range(2):
                role = random.choice(user_roles)
                user = users.pop()
                logger.debug('Assinging role {} to user {} in project {}'.format(role, user, project_name))
                mano.assign_project_role_to_user(rw_active_project_proxy, role, user, project_name, user_domain,
                                                rw_active_rbac_int_proxy)

    def test_create_cloud_accounts(self, cloud_account, fmt_prefixed_cloud_xpath, fmt_cloud_xpath, rw_active_cloud_pxy, 
                                test_projects, logger):
        for project_name in test_projects:
            logger.debug('Creating cloud account {} for project {}'.format(cloud_account.name, project_name))
            xpath = fmt_prefixed_cloud_xpath.format(project=quoted_key(project_name),
                                                    account_name=quoted_key(cloud_account.name))
            rw_active_cloud_pxy.replace_config(xpath, cloud_account)
            xpath_no_pfx = fmt_cloud_xpath.format(project=quoted_key(project_name),
                                                  account_name=quoted_key(cloud_account.name))
            response =  rw_active_cloud_pxy.get(xpath_no_pfx)
            assert response.name == cloud_account.name
            assert response.account_type == cloud_account.account_type

            rw_active_cloud_pxy.wait_for(fmt_cloud_xpath.format(project=quoted_key(project_name), account_name=quoted_key(
            cloud_account.name)) + '/connection-status/status', 'success', timeout=30, fail_on=['failure'])

    def test_onboard_descriptors(self, descriptors, test_projects, active_mgmt_session, fmt_nsd_catalog_xpath, logger):
        # Uploads the descriptors
        for project_name in test_projects:
            for descriptor in descriptors:
                logger.debug('Onboarding descriptor {} for project {}'.format(descriptor, project_name))
                rift.auto.descriptor.onboard(active_mgmt_session, descriptor, project=project_name)

        # Verify whether the descriptors uploaded successfully
        nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
        for project_name in test_projects:
            nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(project_name))
            nsd_catalog = nsd_pxy.get_config(nsd_xpath)
            assert nsd_catalog
    
    @pytest.mark.skipif(not pytest.config.getoption("--nsr-test"), reason="need --nsr-test option to run")
    def test_instantiate_nsr(self, fmt_nsd_catalog_xpath, cloud_account, active_mgmt_session, logger, test_projects):
        nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
        rwnsr_pxy = active_mgmt_session.proxy(RwNsrYang)

        for project_name in test_projects:
            nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(project_name))
            nsd_catalog = nsd_pxy.get_config(nsd_xpath)
            assert nsd_catalog
            nsd = nsd_catalog.nsd[0]
            nsr = rift.auto.descriptor.create_nsr(cloud_account.name, nsd.name, nsd)

            logger.debug('Instantiating NS for project {}'.format(project_name))
            rift.auto.descriptor.instantiate_nsr(nsr, rwnsr_pxy, logger, project=project_name)


@pytest.mark.depends('active_configuration')
@pytest.mark.setup('first-failover')
@pytest.mark.incremental
class TestHaFirstFailover(object):
    def test_collect_active_lp_data(self, active_lp_node_obj, active_confd_host, standby_confd_host, logger):
        mano.verify_hagr_endpoints(active_confd_host, standby_confd_host)
        active_lp_node_obj.collect_data()

    def test_attempt_indirect_failover(self, revertive_pref_host, active_confd_host, standby_confd_host, 
                                        active_site_name, standby_site_name, logger):
        # Wait for redundancy poll interval though collecting data on active LP takes more than 5 secs
        time.sleep(5)
        logger.debug('Attempting first failover. Host {} will be new active'.format(standby_confd_host))
        mano.indirect_failover(revertive_pref_host, new_active_ip=standby_confd_host, new_active_site=standby_site_name, 
            new_standby_ip=active_confd_host, new_standby_site=active_site_name)

    def test_wait_for_standby_to_comeup(self, standby_mgmt_session, active_confd_host, standby_confd_host):
        """Wait for the standby to come up; Wait for endpoint 'ha/geographic/active' to return 200"""
        mano.wait_for_standby_to_become_active(standby_mgmt_session)
        # mano.verify_hagr_endpoints(active_host=standby_confd_host, standby_host=active_confd_host)

    def test_collect_standby_lp_data(self, standby_lp_node_obj, standby_mgmt_session, cloud_account,
                                         fmt_cloud_xpath, test_projects, fmt_nsd_catalog_xpath):
        time.sleep(180)
        rw_new_active_cloud_pxy = standby_mgmt_session.proxy(RwCloudYang)
        nsd_pxy = standby_mgmt_session.proxy(RwProjectNsdYang)
        rwnsr_proxy = standby_mgmt_session.proxy(RwNsrYang)

        for project_name in test_projects:
            rw_new_active_cloud_pxy.wait_for(
                fmt_cloud_xpath.format(project=quoted_key(project_name), account_name=quoted_key(
                    cloud_account.name)) + '/connection-status/status', 'success', timeout=60, fail_on=['failure'])

            # nsd_catalog = nsd_pxy.get_config(fmt_nsd_catalog_xpath.format(project=quoted_key(project_name)))
            # assert nsd_catalog

            if pytest.config.getoption("--nsr-test"):
                nsr_opdata = rwnsr_proxy.get(
                    '/rw-project:project[rw-project:name={project}]/ns-instance-opdata'.format(
                        project=quoted_key(project_name)))
                assert nsr_opdata
                nsrs = nsr_opdata.nsr

                for nsr in nsrs:
                    xpath = "/rw-project:project[rw-project:name={project}]/ns-instance-opdata/nsr[ns-instance-config-ref={config_ref}]/config-status".format(
                        project=quoted_key(project_name), config_ref=quoted_key(nsr.ns_instance_config_ref))
                    rwnsr_proxy.wait_for(xpath, "configured", fail_on=['failed'], timeout=400)

        standby_lp_node_obj.collect_data()

    def test_match_active_standby(self, active_lp_node_obj, standby_lp_node_obj):
        active_lp_node_obj.compare(standby_lp_node_obj)


@pytest.mark.depends('first-failover')
@pytest.mark.setup('active-teardown')
@pytest.mark.incremental
class TestHaTeardown(object):
    """It terminates the NS & deletes descriptors, cloud accounts, projects"""
    @pytest.mark.skipif(not pytest.config.getoption("--nsr-test"), reason="need --nsr-test option to run")
    def test_terminate_nsr(self, test_projects, standby_mgmt_session, logger):
        rwnsr_pxy = standby_mgmt_session.proxy(RwNsrYang)
        rwvnfr_pxy = standby_mgmt_session.proxy(RwVnfrYang)
        rwvlr_pxy = standby_mgmt_session.proxy(RwVlrYang)

        for project_name in test_projects:
            logger.debug("Trying to terminate NSR in project {}".format(project_name))
            rift.auto.descriptor.terminate_nsr(rwvnfr_pxy, rwnsr_pxy, rwvlr_pxy, logger, project_name)

    def test_delete_descriptors(self, standby_mgmt_session, test_projects, logger):
        for project_name in test_projects:
            logger.info("Trying to delete the descriptors in project {}".format(project_name))
            rift.auto.descriptor.delete_descriptors(standby_mgmt_session, project_name)

    def test_delete_cloud_accounts(self, standby_mgmt_session, logger, test_projects, cloud_account):
        for project_name in test_projects:
            logger.info("Trying to delete the cloud-account in project {}".format(project_name))
            rift.auto.mano.delete_cloud_account(standby_mgmt_session, cloud_account.name, project_name)

    def test_delete_projects(self, standby_mgmt_session, test_projects, logger):
        rw_conman_proxy = standby_mgmt_session.proxy(RwConmanYang)
        for project_name in test_projects:
            if project_name == 'default':
                continue
            logger.debug('Deleting project {}'.format(project_name))
            rift.auto.mano.delete_project(rw_conman_proxy, project_name)


@pytest.mark.depends('active-teardown')
@pytest.mark.incremental
class TestHaFailoverToOriginalActive(object):
    """Does a failover to original active and verifies the config"""
    def test_collect_current_active_lp_data(self, standby_lp_node_obj, logger):
        time.sleep(30)
        logger.debug('Collecting data for host {}'.format(standby_lp_node_obj.host))
        standby_lp_node_obj.collect_data()

    def test_attempt_indirect_failover(self, revertive_pref_host, active_confd_host, standby_confd_host, 
                                        active_site_name, standby_site_name, logger):
        # Wait for redundancy poll interval.
        time.sleep(5)
        logger.debug('Attempting second failover. Host {} will be new active'.format(active_confd_host))
        mano.indirect_failover(revertive_pref_host, new_active_ip=active_confd_host, new_active_site=active_site_name, 
            new_standby_ip=standby_confd_host, new_standby_site=standby_site_name)

    def test_wait_for_standby_to_comeup(self, active_mgmt_session, active_confd_host, standby_confd_host):
        """Wait for the standby to come up; Wait for endpoint 'ha/geographic/active' to return 200"""
        mano.wait_for_standby_to_become_active(active_mgmt_session)
        # mano.verify_hagr_endpoints(active_host=standby_confd_host, standby_host=active_confd_host)

    def test_collect_original_active_lp_data(self, active_lp_node_obj, logger):
        active_lp_node_obj.session = None
        logger.debug('Collecting data for host {}'.format(active_lp_node_obj.host))
        active_lp_node_obj.collect_data()

    def test_match_active_standby(self, active_lp_node_obj, standby_lp_node_obj):
        standby_lp_node_obj.compare(active_lp_node_obj)

    def test_delete_default_project(self, rw_active_conman_proxy):
        rift.auto.mano.delete_project(rw_active_conman_proxy, 'default')

    def test_users_presence_in_active(self, rw_active_user_proxy, user_keyed_xpath, user_domain):
        """Users were not deleted as part of Teardown; Check those users should be present and delete them"""
        user_config = rw_active_user_proxy.get_config('/user-config')
        current_users_list = [user.user_name for user in user_config.user]

        user_name_pfx = 'user_ha_'
        original_test_users_list = [user_name_pfx+str(idx) for idx in range(1,9)]

        assert set(original_test_users_list).issubset(current_users_list)

        # Delete the users
        for idx in range(1,9):
            rw_active_user_proxy.delete_config(
                user_keyed_xpath.format(user=quoted_key(user_name_pfx + str(idx)), domain=quoted_key(user_domain)))

    def test_projects_deleted(self, test_projects, project_keyed_xpath, rw_active_conman_proxy):
        """There should only be the default project; all other test projects are already deleted as part of Teardown"""
        for project_name in test_projects:
            project_ = rw_active_conman_proxy.get_config(
                project_keyed_xpath.format(project_name=quoted_key(project_name)) + '/name')
            assert project_ is None