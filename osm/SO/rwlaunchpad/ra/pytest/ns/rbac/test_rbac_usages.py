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
import time
import random
import rift.auto.mano
import rift.auto.descriptor

gi.require_version('RwConmanYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('RwRbacInternalYang', '1.0')
gi.require_version('RwRbacPlatformYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwUserYang', '1.0')
gi.require_version('RwOpenidcProviderYang', '1.0')
from gi.repository import (
    RwConmanYang,
    RwProjectVnfdYang,
    RwProjectNsdYang,
    RwNsrYang,
    RwVnfrYang,
    RwVlrYang,
    RwRbacInternalYang,
    RwRbacPlatformYang,
    RwProjectYang,
    RwUserYang,
    RwOpenidcProviderYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

@pytest.fixture(scope='session')
def complex_scaling_factor():
    return 10

@pytest.mark.incremental
class TestRbacSetup(object):
    def test_onboarded_vnfds_project_independent(self, descriptors, logger, rbac_platform_proxy, rw_conman_proxy, rw_user_proxy,
        rw_project_proxy, rbac_user_passwd, user_domain, fmt_vnfd_catalog_xpath, session_class, confd_host, fmt_vnfd_id_xpath, rw_rbac_int_proxy):
        """Same VNFDs on boarded in two different projects. VNFD changes in one project shouldn't affect another."""
        map_project_user_roles = {
                                    'user1': ('project_test_onboarded_vnfds_project_independent_1', 'rw-project-mano:catalog-admin'),
                                    'user2': ('project_test_onboarded_vnfds_project_independent_2', 'rw-project:project-admin'),
                                    }
        user_to_modify_vnfds, user_not_supposed_to_see_vnfd_changes = 'user1', 'user2'

        modified_vnfd_name = 'test_rbac_vnfd'
        user_sessions = {}
        logger.debug('descriptors being used: {}'.format(descriptors))

        for user, project_role_tuple in map_project_user_roles.items():
            project_name, role = project_role_tuple
            logger.debug('Creating user {} with {}'.format(user, project_role_tuple))

            rift.auto.mano.create_project(rw_conman_proxy, project_name)
            rift.auto.mano.create_user(rw_user_proxy, user, rbac_user_passwd, user_domain)
            if 'platform' in role:
                rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, role, user, user_domain, rw_rbac_int_proxy)
            else:
                rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, user,
                                project_name, user_domain, rw_rbac_int_proxy)

            logger.debug('User {} onboarding the packages'.format(user))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
            user_sessions[user] = user_session
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(user_session, descriptor, project=project_name)

        vnfd_pxy = user_sessions[user_to_modify_vnfds].proxy(RwProjectVnfdYang)
        vnfd_xpath = '{}/vnfd'.format(fmt_vnfd_catalog_xpath.format(project=quoted_key(map_project_user_roles[user_to_modify_vnfds][0])))
        for vnfd in vnfd_pxy.get(vnfd_xpath, list_obj=True).vnfd:
            logger.debug('Changing the vnfd name from {} to {} for user {}'.format(vnfd.name, modified_vnfd_name, user_to_modify_vnfds))
            vnfd.name = modified_vnfd_name
            vnfd_pxy.replace_config(fmt_vnfd_id_xpath.format(
                project=quoted_key(map_project_user_roles[user_to_modify_vnfds][0]), vnfd_id=quoted_key(vnfd.id)), vnfd)

        for vnfd in vnfd_pxy.get(vnfd_xpath, list_obj=True).vnfd:
            assert vnfd.name == modified_vnfd_name

        vnfd_pxy = user_sessions[user_not_supposed_to_see_vnfd_changes].proxy(RwProjectVnfdYang)
        vnfd_xpath = '{}/vnfd'.format(fmt_vnfd_catalog_xpath.format(project=quoted_key(map_project_user_roles[user_not_supposed_to_see_vnfd_changes][0])))
        for vnfd in vnfd_pxy.get(vnfd_xpath, list_obj=True).vnfd:
            logger.debug('Verifying the vnfd name {} for user {} did not change to {}'.format(
                vnfd.name, user_not_supposed_to_see_vnfd_changes, modified_vnfd_name))
            assert vnfd.name != modified_vnfd_name

    def test_multi_projects_multi_vnf(
            self, rw_project_proxy, rw_conman_proxy, cloud_account,
            cloud_module, descriptors, session_class,
            confd_host, user_domain, mgmt_session, fmt_nsd_catalog_xpath,
            logger, rw_rbac_int_proxy):
        """Creates multiple projects, cloud accounts and then
        instantiates them. Then it lets the instantiated NS's run for a minute
        after which gets terminated. Use the SCALE_FACTOR to adjust the number
        of instantiations."""

        def instantiate_nsr_not_wait(nsr, rwnsr_proxy, project='default'):
            ns_instance_opdata_xpath = '/project[name={}]/ns-instance-opdata'.format(quoted_key(project))
            rwnsr_proxy.create_config('/rw-project:project[rw-project:name={}]/nsr:ns-instance-config/nsr:nsr'.format(quoted_key(project)), nsr)
            nsr_opdata = rwnsr_proxy.get('{}/nsr[ns-instance-config-ref={}]'.format(ns_instance_opdata_xpath, quoted_key(nsr.id)))
            assert nsr_opdata is not None

            nsr_opdata = rwnsr_proxy.get(ns_instance_opdata_xpath)
            nsr_ = [nsr_ for nsr_ in nsr_opdata.nsr if nsr_.ns_instance_config_ref==nsr.id][0]

        #Creating multiple projects according to the scale factor
        SCALE_FACTOR = 5
        PROJECT_LIST = {}
        for idx in range(1,SCALE_FACTOR+1):
            rift.auto.mano.create_project(rw_conman_proxy, 'cloud_project_{}'.format(idx))
            PROJECT_LIST['cloud_project_{}'.format(idx)] = None
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, 'rw-project:project-admin', 'admin', 'cloud_project_{}'
                                                                        .format(idx), 'system', rw_rbac_int_proxy)
        #Creating cloud accounts, uploading descriptors, instantiating NS
        for project_name in PROJECT_LIST:
            rift.auto.mano.create_cloud_account(mgmt_session, cloud_account, project_name)
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(mgmt_session, descriptor, project=project_name)
            admin_nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
            nsd_catalog = admin_nsd_pxy.get_config(fmt_nsd_catalog_xpath.format(project=quoted_key(project_name)))
            assert nsd_catalog
            nsd = nsd_catalog.nsd[0]
            nsr = rift.auto.descriptor.create_nsr(cloud_account.name, nsd.name, nsd)
            PROJECT_LIST[project_name] = nsr

        for project_name, NSR in PROJECT_LIST.items():
            admin_rwnsr_pxy = mgmt_session.proxy(RwNsrYang)
            admin_rwvnfr_pxy = mgmt_session.proxy(RwVnfrYang)
            admin_rwvlr_pxy = mgmt_session.proxy(RwVlrYang)
            instantiate_nsr_not_wait(NSR, admin_rwnsr_pxy,
                                     project=project_name)

        # Waiting for NS's to get started and configured.
        for project_name in PROJECT_LIST:
            admin_rwnsr_pxy = mgmt_session.proxy(RwNsrYang)
            nsr_opdata = admin_rwnsr_pxy.get('/rw-project:project[rw-project:name={}]/ns-instance-opdata'.format(quoted_key(project_name)))
            nsrs = nsr_opdata.nsr

            for nsr in nsrs:
                xpath = "/rw-project:project[rw-project:name={}]/ns-instance-opdata/nsr[ns-instance-config-ref={}]/operational-status".format(
                    quoted_key(project_name), quoted_key(nsr.ns_instance_config_ref))
                admin_rwnsr_pxy.wait_for(xpath, "running", fail_on=['failed'], timeout=400)

            for nsr in nsrs:
                xpath = "/rw-project:project[rw-project:name={}]/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status".format(
                    quoted_key(project_name), quoted_key(nsr.ns_instance_config_ref))
                admin_rwnsr_pxy.wait_for(xpath, "configured", fail_on=['failed'], timeout=400)

        # Letting the started NS's run for a minute after which is terminated
        start_time = time.time()
        while (time.time() - start_time) < 60:
            time.sleep(2)
        for project_name in PROJECT_LIST:
            rift.auto.descriptor.terminate_nsr(
                admin_rwvnfr_pxy, admin_rwnsr_pxy, admin_rwvlr_pxy, logger,
                project=project_name)

    def test_descriptor_nsr_persistence_check(
            self, rw_conman_proxy, rw_user_proxy, rw_project_proxy,
            cloud_account, cloud_module, mgmt_session, descriptors, logger,
            user_domain, session_class, confd_host, rbac_user_passwd,
            fmt_nsd_catalog_xpath, rw_rbac_int_proxy):
        """Creates a project and cloud account for it. Uploads descriptors.
        Logs in as project-admin and checks if the uploaded descriptors
        are still there, after which he logs out.
        Then instantiates nsr. Again logs in as project admin and checks
        if the instantiated nsr is still there."""
        # Creating a project, assigning project admin and creating
        # a cloud account for the project
        for idx in range(1,6):
            rift.auto.mano.create_project(rw_conman_proxy, 'xcloud_project_{}'.format(idx))
            rift.auto.mano.create_user(rw_user_proxy, 'project_admin_{}'.format(idx), rbac_user_passwd, user_domain)
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, 'rw-project:project-admin', 'project_admin_{}'
                                            .format(idx), 'xcloud_project_{}'.format(idx), user_domain, rw_rbac_int_proxy)
            rift.auto.mano.create_cloud_account(mgmt_session, cloud_account, 'xcloud_project_{}'.format(idx))
            #Uploading descriptors and verifying its existence from another user(project admin)
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(mgmt_session, descriptor, project='xcloud_project_{}'.format(idx))
            user_session = rift.auto.mano.get_session(session_class, confd_host, 'project_admin_{}'.format(idx), rbac_user_passwd)
            project_admin_nsd_pxy = user_session.proxy(RwProjectNsdYang)
            nsd_catalog = project_admin_nsd_pxy.get_config(fmt_nsd_catalog_xpath.format(project=quoted_key('xcloud_project_{}'.format(idx))))
            assert nsd_catalog, "Descriptor Not found on try no: {}".format(idx)
            nsd = nsd_catalog.nsd[0]
            nsr = rift.auto.descriptor.create_nsr(cloud_account.name, nsd.name, nsd)
            rift.auto.mano.close_session(user_session)
            #Instantiating the nsr and verifying its existence from another user(project admin), after which it gets terminated
            admin_rwnsr_pxy = mgmt_session.proxy(RwNsrYang)
            admin_rwvnfr_pxy = mgmt_session.proxy(RwVnfrYang)
            admin_rwvlr_pxy = mgmt_session.proxy(RwVlrYang)

            rift.auto.descriptor.instantiate_nsr(nsr, admin_rwnsr_pxy, logger, project='xcloud_project_{}'.format(idx))
            user_session = rift.auto.mano.get_session(session_class, confd_host, 'project_admin_{}'.format(idx), rbac_user_passwd)
            pxy = user_session.proxy(RwNsrYang)
            nsr_opdata = pxy.get('/rw-project:project[rw-project:name={}]/ns-instance-opdata'.format(quoted_key('xcloud_project_{}'.format(idx))))
            nsrs = nsr_opdata.nsr
            for nsr in nsrs:
                xpath = "/rw-project:project[rw-project:name={}]/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status".format(
                                quoted_key('xcloud_project_{}'.format(idx)), quoted_key(nsr.ns_instance_config_ref))
                pxy.wait_for(xpath, "configured", fail_on=['failed'], timeout=60)
            rift.auto.mano.close_session(user_session)
            rift.auto.descriptor.terminate_nsr(
                admin_rwvnfr_pxy, admin_rwnsr_pxy, admin_rwvlr_pxy, logger,
                project='xcloud_project_{}'.format(idx))

    def delete_records(self, nsd_proxy, vnfd_proxy, project_name='default'):
        """Delete the NSD & VNFD records."""
        nsds = nsd_proxy.get(
            "/rw-project:project[rw-project:name={}]/nsd-catalog/nsd".format(
                quoted_key(project_name)),
            list_obj=True)
        for nsd in nsds.nsd:
            xpath = (
                "/rw-project:project[rw-project:name={}]".format(
                    quoted_key(project_name)) +
                "/nsd-catalog/nsd[id={}]".format(quoted_key(nsd.id))
            )
            nsd_proxy.delete_config(xpath)

        nsds = nsd_proxy.get(
            "/rw-project:project[rw-project:name={}]/nsd-catalog/nsd".format(
                quoted_key(project_name)),
            list_obj=True)
        assert nsds is None or len(nsds.nsd) == 0

        vnfds = vnfd_proxy.get(
            "/rw-project:project[rw-project:name={}]/vnfd-catalog/vnfd".format(
                quoted_key(project_name)),
            list_obj=True)
        for vnfd_record in vnfds.vnfd:
            xpath = (
                "/rw-project:project[rw-project:name={}]/".format(
                    quoted_key(project_name)) +
                "vnfd-catalog/vnfd[id={}]".format(quoted_key(vnfd_record.id))
            )
            vnfd_proxy.delete_config(xpath)

        vnfds = vnfd_proxy.get(
            "/rw-project:project[rw-project:name={}]/vnfd-catalog/vnfd".format(
                quoted_key(project_name)),
            list_obj=True)
        assert vnfds is None or len(vnfds.vnfd) == 0

    def test_delete_project_and_vim_accounts(
            self, rw_conman_proxy, rw_user_proxy, logger,
            rbac_user_passwd, user_domain, rw_project_proxy, rw_rbac_int_proxy,
            mgmt_session, cloud_module, cloud_account, descriptors,
            fmt_nsd_catalog_xpath, session_class, confd_host):
        """Testing vim accounts."""
        # Create a project and three cloud accounts for it.
        rift.auto.mano.create_project(rw_conman_proxy, 'vim_project')
        rift.auto.mano.assign_project_role_to_user(
            rw_project_proxy, 'rw-project:project-admin', 'admin',
            'vim_project', 'system', rw_rbac_int_proxy)
        for idx in range(1, 4):
            rift.auto.mano.create_cloud_account(
                mgmt_session, cloud_account,
                'vim_project', 'cloud_account_{}'.format(idx))
        # Uploading descriptors
        for descriptor in descriptors:
            rift.auto.descriptor.onboard(
                mgmt_session, descriptor, project='vim_project')
        nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
        nsd_catalog = nsd_pxy.get_config(fmt_nsd_catalog_xpath.format(
            project=quoted_key('vim_project')))
        assert nsd_catalog
        nsd = nsd_catalog.nsd[0]
        nsr = rift.auto.descriptor.create_nsr(
            'cloud_account_1', nsd.name, nsd)
        # Instantiating the nsr
        rwnsr_pxy = mgmt_session.proxy(RwNsrYang)
        rift.auto.descriptor.instantiate_nsr(
            nsr, rwnsr_pxy, logger, project='vim_project')
        # Trying to delete the project before taking the instance down
        with pytest.raises(
                Exception,
                message="Project deletion should've failed"):
            rift.auto.mano.delete_project(rw_conman_proxy, 'vim_project')
        # Trying to delete the vim account before taking the instance down
        with pytest.raises(
                Exception,
                message="Vim account deletion should've failed"):
            rift.auto.mano.delete_cloud_account(
                mgmt_session, 'cloud_account_1', 'vim_project')
        # Terminating the nsr
        rwvnfr_pxy = mgmt_session.proxy(RwVnfrYang)
        rwvlr_pxy = mgmt_session.proxy(RwVlrYang)
        rift.auto.descriptor.terminate_nsr(
            rwvnfr_pxy, rwnsr_pxy, rwvlr_pxy, logger, project='vim_project')
        # Delete all cloud accounts for the project
        for idx in range(1, 4):
            rift.auto.mano.delete_cloud_account(
                mgmt_session, 'cloud_account_{}'.format(idx), 'vim_project')
        # Delete the uploaded descriptors
        vnfd_proxy = mgmt_session.proxy(RwProjectVnfdYang)
        self.delete_records(nsd_pxy, vnfd_proxy, 'vim_project')
        # Delete the project
        rift.auto.mano.delete_project(rw_conman_proxy, 'vim_project')
        # Check in rw-rbac-internal if project is removed
        rwinternal_xpath = '/rw-rbac-internal/role'
        response = (
            rw_rbac_int_proxy.get(
                rwinternal_xpath, list_obj=True)
        ).as_dict()['role']
        keys = [role['keys'] for role in response if 'keys' in role]
        for key in keys:
            assert 'vim_project' not in key, "Improper project deletion"

    @pytest.mark.skipif(
        not pytest.config.getoption("--complex-scaling"),
        reason="need --complex-scaling option to run")
    def test_complex_scaling(
            self, rw_conman_proxy, rw_user_proxy, rbac_user_passwd,
            user_domain, rw_project_proxy, rw_rbac_int_proxy, logger,
            rbac_platform_proxy, user_roles, platform_roles, mgmt_session,
            cloud_module, cloud_account, rw_ro_account_proxy,
            tbac, fmt_nsd_catalog_xpath, descriptors, complex_scaling_factor):
        """Complex scaling - Default values.

        No. of projects - 25 (Two users & two cloud accounts per project)
        No. of users - 50 (Two roles per user)
        No. of cloud accounts - 50
        No. of RO accounts - 25 (50 if you are considering the default 'rift').
        """
        # This test can be controlled using complex_scaling_factor fixture
        logger.debug('Creating projects')
        for idx in range(1, complex_scaling_factor + 1):
            rift.auto.mano.create_project(
                rw_conman_proxy, 'scaling_project_{}'.format(idx)
            )
        logger.debug('Create users, cloud accounts double the no. of projects')
        for idx in range(1, (2 * complex_scaling_factor) + 1):
            project_index = int((idx + 1) / 2)
            rift.auto.mano.create_user(
                rw_user_proxy, 'scaling_user_{}'.format(idx),
                rbac_user_passwd, user_domain)
            # Each user has a project role & platform role
            pr_role = random.choice(user_roles)
            pl_role = random.choice(platform_roles)
            rift.auto.mano.assign_project_role_to_user(
                rw_project_proxy, pr_role, 'scaling_user_{}'.format(idx),
                'scaling_project_{}'.format(project_index), user_domain,
                rw_rbac_int_proxy)
            rift.auto.mano.assign_platform_role_to_user(
                rbac_platform_proxy, pl_role,
                'scaling_user_{}'.format(idx), user_domain, rw_rbac_int_proxy)
            # Creating two cloud accounts for each project
            rift.auto.mano.create_cloud_account(
                mgmt_session, cloud_account,
                'scaling_project_{}'.format(project_index),
                'cloud_account_{}'.format(idx)
            )
        logger.debug('Creating RO accounts')
        for idx in range(1, complex_scaling_factor + 1):
            rift.auto.mano.create_ro_account(
                rw_ro_account_proxy, 'ro_account_{}'.format(idx),
                'scaling_project_{}'.format(idx)
            )
            # Uploading descriptors
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(
                    mgmt_session, descriptor,
                    project='scaling_project_{}'.format(idx)
                )
            nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
            nsd_catalog = nsd_pxy.get_config(
                fmt_nsd_catalog_xpath.format(
                    project=quoted_key('scaling_project_{}'.format(idx))
                )
            )
            assert nsd_catalog

    @pytest.mark.skipif(
        not pytest.config.getoption("--complex-scaling"),
        reason="need --complex-scaling option to run")
    def test_complex_scaling_verification(
            self, complex_scaling_factor, rw_project_proxy, rw_ro_account_proxy,
            mgmt_session, fmt_nsd_catalog_xpath, cloud_module, logger):
        """Reboot verification script for test_complex_scaling."""
        for idx in range(1, complex_scaling_factor + 1):
            # Verifying projects
            logger.debug('Verification: projects, ro accounts started')
            project_name = 'scaling_project_{}'.format(idx)
            project_cm_config_xpath = '/project[name={project_name}]/project-state'
            project_ = rw_project_proxy.get_config(
                project_cm_config_xpath.format(
                    project_name=quoted_key(project_name)
                ),
                list_obj=True
            )
            assert project_
            # Verifying RO Accounts
            ro_account_name = 'ro_account_{}'.format(idx)
            ro_obj = rw_ro_account_proxy.get_config(
                '/project[name={}]/ro-account/account[name={}]'.format(
                    quoted_key(project_name), quoted_key(ro_account_name))
            )
            assert ro_obj.name == ro_account_name
            assert ro_obj.ro_account_type == 'openmano'
            logger.debug('Verification: descriptors, cloud accounts started')
            # Verifying Descriptors
            nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
            nsd_catalog = nsd_pxy.get_config(
                fmt_nsd_catalog_xpath.format(
                    project=quoted_key(project_name)
                )
            )
            assert nsd_catalog
        for idx in range(1, (2 * complex_scaling_factor) + 1):
            # Verifying cloud accounts
            project_index = int((idx + 1) / 2)
            project_name = 'scaling_project_{}'.format(project_index)
            cloud_acc_name = 'cloud_account_{}'.format(idx)
            fmt_cloud_xpath = (
                '/project[name={project}]/cloud/account[name={account_name}]'
            )
            cloud_pxy = mgmt_session.proxy(cloud_module)
            response = cloud_pxy.get(fmt_cloud_xpath.format(
                project=quoted_key(project_name),
                account_name=quoted_key(cloud_acc_name))
            )
            assert response.name == cloud_acc_name


    def test_change_visibility_same_session(self, session_class, rw_conman_proxy, confd_host, logger,
            user_domain, project_keyed_xpath, rw_project_proxy, rw_rbac_int_proxy, rw_user_proxy):
        """admin make changes which is seen by the operator already logged in for the same project.

        oper is logged in. admin assigns oper to a new project X. oper should be able to see the new project X being \
        in the same session without re-logging-in.
        """
        user = 'oper2' if user_domain != 'default' else 'oper'
        oper_user, oper_passwd = [user]*2
        
        if user_domain != 'default':
            rift.auto.mano.create_user(rw_user_proxy, oper_user, oper_passwd, user_domain)
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, 'rw-project:project-oper', oper_user,
                                                       'default', user_domain, rw_rbac_int_proxy)
        oper_session = rift.auto.mano.get_session(session_class, confd_host, oper_user, oper_passwd)
        oper_conman_pxy = oper_session.proxy(RwProjectYang)

        default_project_cm_config_xpath = project_keyed_xpath.format(project_name=quoted_key('default'))+'/project-state'
        assert oper_conman_pxy.get_config(default_project_cm_config_xpath, list_obj=True)

        # admin assigns oper 'project-admin' role under a new project
        new_project = 'project_test_change_visibility_same_session_1'
        rift.auto.mano.create_project(rw_project_proxy, new_project)
        rift.auto.mano.assign_project_role_to_user(rw_project_proxy, 'rw-project:project-admin', oper_user, new_project,
                                                   user_domain, rw_rbac_int_proxy)

        # Check oper user should be able to access the new project
        new_project_cm_config_xpath = project_keyed_xpath.format(project_name=quoted_key(new_project))+'/project-state'
        assert oper_conman_pxy.get_config(new_project_cm_config_xpath, list_obj=True)

    def test_super_admin(
            self, rw_user_proxy, rbac_platform_proxy, rw_project_proxy,
            session_class, confd_host, rbac_user_passwd, user_domain,
            rw_rbac_int_proxy):
        """Variou tests on the super-admin role."""
        # Creating two super admins and then deleting the first one.
        rift.auto.mano.create_user(
            rw_user_proxy, 'super_admin', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(
            rbac_platform_proxy, 'rw-rbac-platform:super-admin',
            'super_admin', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.create_user(
            rw_user_proxy, 'super_admin_2', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(
            rbac_platform_proxy, 'rw-rbac-platform:super-admin',
            'super_admin_2', user_domain, rw_rbac_int_proxy)

        user_session = rift.auto.mano.get_session(
            session_class, confd_host, 'super_admin_2', rbac_user_passwd)
        pxy = user_session.proxy(RwRbacPlatformYang)
        role_keyed_path = (
            "/rbac-platform-config/" +
            "user[user-name={user}][user-domain={domain}]"
        )
        pxy.delete_config(role_keyed_path.format(
            user=quoted_key('super_admin'), domain=quoted_key(user_domain))
        )
        pxy = user_session.proxy(RwUserYang)
        rift.auto.mano.delete_user(pxy, 'super_admin', user_domain)
        rift.auto.mano.close_session(user_session)

    @pytest.mark.skipif(not pytest.config.getoption("--tbac"), reason="need --tbac option to run")
    def test_token_expiry_timeout(self, mgmt_session, rw_user_proxy, rw_conman_proxy, rbac_user_passwd, user_domain,
        confd_host, logger, rw_project_proxy, rw_rbac_int_proxy, session_class):
        """Set 30 seconds as token-expiry-timeout; then verifies an user session is automatically expired after 30 secs"""
        test_user, role = 'user-1', 'rw-project:project-oper'
        test_proj = 'project_test_token_expiry_timeout'
        token_expiry_timeout = 30

        logger.debug('Creating user {} under project {} and assigning it {}'.format(test_user, test_proj, role))
        rift.auto.mano.create_project(rw_conman_proxy, test_proj)
        rift.auto.mano.create_user(rw_user_proxy, test_user, rbac_user_passwd, user_domain)
        rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, test_user, test_proj, user_domain, rw_rbac_int_proxy)

        # admin user setting token_expiry_timeout
        openidc_provider_xpath = '/rw-openidc-provider:openidc-provider-config'
        openidc_provider = RwOpenidcProviderYang.YangData_RwOpenidcProvider_OpenidcProviderConfig.from_dict(
                                                                {'token_expiry_timeout': 30})
        pxy = mgmt_session.proxy(RwOpenidcProviderYang)
        logger.debug('Settig token_expiry_timeout to {} secs'.format(token_expiry_timeout))
        pxy.replace_config(openidc_provider_xpath, openidc_provider)

        # Verifying if token_expiry_timeout is set in openidc-provider-config
        openidc_provider = pxy.get_config(openidc_provider_xpath)
        assert openidc_provider
        assert openidc_provider.token_expiry_timeout == token_expiry_timeout

        def project_access(user_session):
            user_conman_pxy = user_session.proxy(RwProjectYang)
            assert user_conman_pxy.get_config('/project[name={}]/project-state'.format(quoted_key(test_proj)), list_obj=True)

        # Log-in as test_user and validate operations under that user getting 'Unauthorized' after time-out
        user_session = rift.auto.mano.get_session(session_class, confd_host, test_user, rbac_user_passwd)
        project_access(user_session)

        logger.debug('Sleeping for {} secs'.format(token_expiry_timeout))
        time.sleep(token_expiry_timeout+5)

        with pytest.raises(Exception, message='logged-in user able to access default project even after token expired'):
            logger.debug('User {} trying to access default project. It should fail')
            project_access(user_session)

        # log-in as same user and perform the same operation. It should pass now.
        user_session = rift.auto.mano.get_session(session_class, confd_host, test_user, rbac_user_passwd)
        project_access(user_session)
