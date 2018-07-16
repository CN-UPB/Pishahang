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
    RwProjectVnfdYang,
    RwCloudYang
)


@pytest.mark.setup('active_configuration')
@pytest.mark.incremental
class TestActiveLpConfiguration(object):
    """Setting up the configuration."""

    def collect_active_lp_data(
            self, active_lp_node_obj, active_confd_host,
            standby_confd_host, logger):
        """Collect active lp data."""
        mano.verify_hagr_endpoints(active_confd_host, standby_confd_host)
        active_lp_node_obj.collect_data()

    def wait_for_standby_to_comeup(
            self, standby_mgmt_session, active_confd_host, standby_confd_host):
        """Wait for the standby to come up.

        Wait for endpoint 'ha/geographic/active' to return 200
        """
        mano.wait_for_standby_to_become_active(standby_mgmt_session)
        # mano.verify_hagr_endpoints(
        #    active_host=standby_confd_host, standby_host=active_confd_host)

    def collect_standby_lp_data(
            self, standby_lp_node_obj, standby_mgmt_session, cloud_account,
            fmt_cloud_xpath, projects, fmt_nsd_catalog_xpath):
        """Collect standby lp data."""
        time.sleep(180)
        rw_new_active_cloud_pxy = standby_mgmt_session.proxy(RwCloudYang)
        nsd_pxy = standby_mgmt_session.proxy(RwProjectNsdYang)
        rwnsr_proxy = standby_mgmt_session.proxy(RwNsrYang)

        for project_name in projects:
            rw_new_active_cloud_pxy.wait_for(
                fmt_cloud_xpath.format(
                    project=quoted_key(project_name),
                    account_name=quoted_key(cloud_account.name)) +
                '/connection-status/status', 'success',
                timeout=60, fail_on=['failure'])

            # nsd_catalog = nsd_pxy.get_config(
            #    fmt_nsd_catalog_xpath.format(project=quoted_key(project_name)))
            # assert nsd_catalog

            if pytest.config.getoption("--nsr-test"):
                nsr_opdata = rwnsr_proxy.get(
                    '/rw-project:project[rw-project:name={project}]' +
                    '/ns-instance-opdata'.format(
                        project=quoted_key(project_name))
                )

                assert nsr_opdata
                nsrs = nsr_opdata.nsr

                for nsr in nsrs:
                    xpath = (
                        '/rw-project:project[rw-project:name={project}]' +
                        '/ns-instance-opdata/nsr[ns-instance-config-ref=' +
                        '{config_ref}]/config-status'.format(
                            project=quoted_key(project_name),
                            config_ref=quoted_key(nsr.ns_instance_config_ref))
                    )

                    rwnsr_proxy.wait_for(
                        xpath, "configured", fail_on=['failed'], timeout=400)

        standby_lp_node_obj.collect_data()

    def attempt_indirect_failover(
            self, revertive_pref_host, active_confd_host, standby_confd_host,
            active_site_name, standby_site_name, logger):
        """Try indirect failover."""
        time.sleep(5)
        logger.debug(
            'Attempting first failover. Host {} will be new active'.format(
                standby_confd_host))

        mano.indirect_failover(
            revertive_pref_host, new_active_ip=standby_confd_host,
            new_active_site=standby_site_name,
            new_standby_ip=active_confd_host,
            new_standby_site=active_site_name)

    def match_active_standby(self, active_lp_node_obj, standby_lp_node_obj):
        """Compare active standby."""
        active_lp_node_obj.compare(standby_lp_node_obj)

    def test_create_project_users_cloud_acc(
            self, rbac_user_passwd, user_domain, rw_active_user_proxy, logger,
            rw_active_project_proxy, rw_active_rbac_int_proxy, cloud_account,
            rw_active_conman_proxy, rw_active_cloud_pxy, user_roles,
            fmt_prefixed_cloud_xpath, fmt_cloud_xpath, descriptors,
            active_mgmt_session, fmt_nsd_catalog_xpath, active_lp_node_obj,
            standby_lp_node_obj, active_confd_host, standby_confd_host,
            revertive_pref_host, active_site_name, standby_site_name,
            standby_mgmt_session):
        """Create 3 of users, projects, cloud accounts, decriptors & nsrs."""
        def failover_and_match():
            """Try an indirect failover.

            Match active and standby data
            """
            self.collect_active_lp_data(
                active_lp_node_obj, active_confd_host,
                standby_confd_host, logger)
            self.attempt_indirect_failover(
                revertive_pref_host, active_confd_host, standby_confd_host,
                active_site_name, standby_site_name, logger)
            self.wait_for_standby_to_comeup(
                standby_mgmt_session, active_confd_host, standby_confd_host)
            self.collect_standby_lp_data(
                standby_lp_node_obj, standby_mgmt_session, cloud_account,
                fmt_cloud_xpath, projects, fmt_nsd_catalog_xpath)
            self.match_active_standby(active_lp_node_obj, standby_lp_node_obj)

        def delete_data_set(idx):

            rift.auto.descriptor.terminate_nsr(
                rwvnfr_pxy, rwnsr_pxy, rwvlr_pxy, logger,
                project=projects[idx])

            rift.auto.descriptor.delete_descriptors(
                active_mgmt_session, project_name)

            rw_active_cloud_pxy.delete_config(
                fmt_prefixed_cloud_xpath.format(
                    project=quoted_key(projects[idx]),
                    account_name=quoted_key(cloud_account.name)
                )
            )
            response = rw_active_cloud_pxy.get(
                fmt_cloud_xpath.format(
                    project=quoted_key(projects[idx]),
                    account_name=quoted_key(cloud_account.name)
                )
            )
            assert response is None

            mano.delete_project(rw_active_conman_proxy, projects[idx])
            projects.pop()
            mano.delete_user(rw_active_user_proxy, users[idx], user_domain)
            users.pop()

        # Create test users
        user_name_pfx = 'user_ha_'
        users = []
        for idx in range(1, 4):
            users.append(user_name_pfx + str(idx))

            mano.create_user(
                rw_active_user_proxy, user_name_pfx + str(idx),
                rbac_user_passwd, user_domain)

        # Create projects and assign roles to users
        prj_name_pfx = 'prj_ha_'
        projects = []
        for idx in range(1, 4):
            project_name = prj_name_pfx + str(idx)
            projects.append(project_name)
            mano.create_project(
                rw_active_conman_proxy, project_name)

        for idx in range(0, 3):
            project_name = projects[idx]
            role = random.choice(user_roles)
            user = users[idx]
            logger.debug(
                'Assinging role {} to user {} in project {}'.format(
                    role, user, project_name))

            mano.assign_project_role_to_user(
                rw_active_project_proxy, role, user, project_name,
                user_domain, rw_active_rbac_int_proxy)

            logger.debug(
                'Creating cloud account {} for project {}'.format(
                    cloud_account.name, project_name))

            xpath = fmt_prefixed_cloud_xpath.format(
                project=quoted_key(project_name),
                account_name=quoted_key(cloud_account.name))

            rw_active_cloud_pxy.replace_config(xpath, cloud_account)

            xpath_no_pfx = fmt_cloud_xpath.format(
                project=quoted_key(project_name),
                account_name=quoted_key(cloud_account.name))

            response = rw_active_cloud_pxy.get(xpath_no_pfx)
            assert response.name == cloud_account.name
            assert response.account_type == cloud_account.account_type

            rw_active_cloud_pxy.wait_for(
                fmt_cloud_xpath.format(
                    project=quoted_key(project_name),
                    account_name=quoted_key(cloud_account.name)) +
                '/connection-status/status', 'success', timeout=30,
                fail_on=['failure'])

            # Uploads the descriptors
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(
                    active_mgmt_session, descriptor, project=project_name)

            # Verify whether the descriptors uploaded successfully
            logger.debug(
                'Onboarding descriptors for project {}'.format(project_name))

            nsd_pxy = active_mgmt_session.proxy(RwProjectNsdYang)
            rwnsr_pxy = active_mgmt_session.proxy(RwNsrYang)
            rwvnfr_pxy = active_mgmt_session.proxy(RwVnfrYang)
            rwvlr_pxy = active_mgmt_session.proxy(RwVlrYang)

            nsd_xpath = fmt_nsd_catalog_xpath.format(
                project=quoted_key(project_name))
            nsd_catalog = nsd_pxy.get_config(nsd_xpath)
            assert nsd_catalog

            nsd_xpath = fmt_nsd_catalog_xpath.format(
                project=quoted_key(project_name))
            nsd_catalog = nsd_pxy.get_config(nsd_xpath)
            assert nsd_catalog
            nsd = nsd_catalog.nsd[0]
            nsr = rift.auto.descriptor.create_nsr(
                cloud_account.name, nsd.name, nsd)

            logger.debug(
                'Instantiating NS for project {}'.format(project_name))
            rift.auto.descriptor.instantiate_nsr(
                nsr, rwnsr_pxy, logger, project=project_name)

        delete_data_set(2)
        failover_and_match()
        delete_data_set(1)
        failover_and_match()


