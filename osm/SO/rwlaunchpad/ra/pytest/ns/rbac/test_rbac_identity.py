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
#This file contains the code for RIFT-16314, RIFT-16315, RIFT-16536,
#RIFT-16537, RIFT-16541, RIFT-16313, RIFT-16692, RIFT-16637, RIFT-16636.
"""
import gi
import pytest

import rift.auto.mano

gi.require_version('RwUserYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwRbacPlatformYang', '1.0')
gi.require_version('RwRbacInternalYang', '1.0')
gi.require_version('RwlogMgmtYang', '1.0')


from gi.repository import (
    RwUserYang,
    RwProjectYang,
    RwRbacPlatformYang,
    RwRbacInternalYang,
    RwlogMgmtYang,
    RwConmanYang
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


@pytest.mark.setup('rbac_setup')
@pytest.mark.incremental
class TestIdentity(object):
    """Test Identity."""

    platform_role_users = ['platform_user_admin', 'platform_user_oper', 'platform_user_super_admin']
    platform_users = ['platform_user_admin', 'platform_user_oper', 'platform_user_test', 'platform_user_super_admin']

    project_roles = (
        'rw-project-mano:catalog-oper', 'rw-project-mano:catalog-admin',
        'rw-project-mano:lcm-oper', 'rw-project-mano:lcm-admin',
        'rw-project-mano:account-oper', 'rw-project-mano:account-admin',
        'rw-project:project-admin', 'rw-project:project-oper'
    )
    platform_roles = (
        'rw-rbac-platform:platform-admin',
        'rw-rbac-platform:platform-oper',
        'rw-rbac-platform:super-admin'
    )

    RBAC_PROJECTS = ['default']
    RBAC_USERS = []

    TEST_PROJECTS = []
    TEST_USERS = []

    # This is required so as to track the
    # already deleted users when creation and deletion
    # are performed in ad-hoc way.
    # Checking this set allows us to ignore Proxy request
    # errors when deletion is performed twice.
    DELETED_PROJECTS_TRACKER = set()

    INVALID_CREDENTIALS = {
        'Jason' * 500: 'likeu' * 500
    }

    POSSIBLY_PROBLEMATIC_CREDENTIALS = {
        'Ja#son': ['lik#eu', 'syste#m'],
        'Ja&son': ['lik&eu', 'syste&m'],
        'J%ason': ['lik%eu', 'syste%m'],
        'Jåson': ['likeü', 'system'],
        '<Jason>': ['<likeu>', '<system>'],
        '/jason': ['/likeu', '/system;'],
        'jason;': ['likeu;', 'system;'],
        'j*son': ['like*u;', 'syste*m'],
        'j@so?': ['l!keu;', 'system!']
    }

    INAVLID_LOGIN_CREDENTIALS = {
        'wrong_username': 'mypasswd',
        'testuser': 0,
        0: 'mypasswd',
        0: 0,
        'wrong_username': 'wrong_password'
    }

    INVALID_PROJECT_KEYS = ['this_project_doesnt_exist', 'Test01']
    INVALID_PROJECT_CREATE_KEYS = ['testproject' * 500, ]
    #POSSIBLY_PROBLEMATIC_KEYS = ['/projectname', 'project name', 'projectname.', 'project,name', 'Projëçt', 'Pro;je:ct', 'Proj*ct', 'Pr@ject']
    POSSIBLY_PROBLEMATIC_KEYS = ['/projectname', 'project name', 'projectname.', 'project,name', 'Pro;je:ct', 'Proj*ct', 'Pr@ject']

    def test_platform_roles(self, rw_user_proxy, rbac_platform_proxy, rbac_user_passwd, user_domain, session_class, tbac, 
                                                                        confd_host, platform_roles, rw_rbac_int_proxy):
        # Setting users and roles up for upcoming checks
        rift.auto.mano.create_user(rw_user_proxy, 'platform_user_super_admin', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:super-admin',
                                                            'platform_user_super_admin', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.create_user(rw_user_proxy, 'platform_user_admin', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:platform-admin',
                                                            'platform_user_admin', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.create_user(rw_user_proxy, 'platform_user_oper', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:platform-oper',
                                                            'platform_user_oper', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.create_user(rw_user_proxy, 'platform_user_test', rbac_user_passwd, user_domain)

        """Various access tests for platform users"""

        # Testing if platform role users have access to /rbac-platform-config
        for user in self.platform_role_users:
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
            pxy = user_session.proxy(RwRbacPlatformYang)
            access_ = pxy.get_config("/rbac-platform-config/user[user-name='platform_user_admin'][user-domain={}]"
                                .format(quoted_key(user_domain)))
            assert access_ is not None
            rift.auto.mano.close_session(user_session)

        # Testing if platform role users have access to /rbac-platform-state
        for user in self.platform_role_users:
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
            pxy = user_session.proxy(RwRbacPlatformYang)
            access_ = pxy.get_config("/rbac-platform-state/user[user-name='platform_user_admin'][user-domain={}]"
                                .format(quoted_key(user_domain)))
            if user == 'platform_user_oper':
                    assert access_ is None
            else:
                """At the time of writing this code, /rbac-platform-state/user is unpopulated and so the access_ will be None no matter what.
                In the future when the path /rbac-platform-state/user is populated this test will break. When that happens, just change 
                the next line to 'access_ is not None'
                """
                assert access_ is None
            rift.auto.mano.close_session(user_session)

        """Changing roles and verifying it """

        # Case 01 Assign and then revoke that role. Assign a second role and see if that sticks and that the older role hasn't stayed on.
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:platform-oper', 
                                                            'platform_user_test', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.revoke_platform_role_from_user(rbac_platform_proxy, 'rw-rbac-platform:platform-oper', 
                                                            'platform_user_test', user_domain)
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:platform-admin', 
                                                            'platform_user_test', user_domain, rw_rbac_int_proxy)
        # If the older role didn't stick and the new role did stick (as it should), then the user should be able to change another users password
        user_session = rift.auto.mano.get_session(session_class, confd_host, 'platform_user_test', rbac_user_passwd)
        pxy = user_session.proxy(RwUserYang)
        rift.auto.mano.update_password(pxy, 'platform_user_oper', 'even_newer_password', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.close_session(user_session)

        # Case 02 Switching the roles back after Case 01
        rift.auto.mano.revoke_platform_role_from_user(rbac_platform_proxy, 'rw-rbac-platform:platform-admin',
                                                            'platform_user_test', user_domain)
        rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, 'rw-rbac-platform:platform-oper',
                                                            'platform_user_test', user_domain, rw_rbac_int_proxy)
        # If the older role didn't stick and the new role did stick (as it should), then the user shouldn't be able to change another users password
        user_session = rift.auto.mano.get_session(session_class, confd_host, 'platform_user_test', rbac_user_passwd)
        pxy = user_session.proxy(RwUserYang)
        with pytest.raises(Exception, message="User shouldn't be able to change another user's password") as excinfo:
            rift.auto.mano.update_password(pxy, 'platform_user_oper', 'new_password', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.close_session(user_session)

        if not tbac:
            """Disabling and enabling users and verifying it"""

            rift.auto.mano.create_user(rw_user_proxy, 'disabled_user', rbac_user_passwd, user_domain)
            rift.auto.mano.update_password(rw_user_proxy, 'platform_user_oper', rbac_user_passwd, user_domain, rw_rbac_int_proxy)
            # Checking if the disabled user can login
            rift.auto.mano.disable_user(rw_user_proxy, 'disabled_user', user_domain, rw_rbac_int_proxy)
            with pytest.raises(Exception, message="User shouldn't be able to login as he is disabled") as excinfo:
                user_session = rift.auto.mano.get_session(session_class, confd_host, 'disabled_user', rbac_user_passwd, timeout=5)
            # Checking if he can login after he has been enabled back on.
            rift.auto.mano.enable_user(rw_user_proxy, 'disabled_user', user_domain, rw_rbac_int_proxy)
            user_session = rift.auto.mano.get_session(session_class, confd_host, 'disabled_user', rbac_user_passwd)
            rift.auto.mano.close_session(user_session)
            # All platform roles trying to change the status of a user
            for user in self.platform_role_users:
                user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
                pxy = user_session.proxy(RwUserYang)
                if user == 'platform_user_oper':
                    with pytest.raises(Exception, message="Platform oper shouldn't be able to disable other users") as excinfo:
                        rift.auto.mano.disable_user(pxy, 'disabled_user', user_domain, rw_rbac_int_proxy)
                else:
                    rift.auto.mano.disable_user(pxy, 'disabled_user', user_domain, rw_rbac_int_proxy)
                    rift.auto.mano.enable_user(pxy, 'disabled_user', user_domain, rw_rbac_int_proxy)
                rift.auto.mano.close_session(user_session)

            # Testing if users can change their own passwords
            for user in self.platform_users:
                user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
                pxy = user_session.proxy(RwUserYang)
                rift.auto.mano.update_password(pxy, user, 'new_password', user_domain, rw_rbac_int_proxy)
                rift.auto.mano.close_session(user_session)

            # Testing if platform role users can change the password of another user
            for idx, user in enumerate(self.platform_role_users, 1):
                user_session = rift.auto.mano.get_session(session_class, confd_host, user, 'new_password')
                pxy = user_session.proxy(RwUserYang)
                if user == 'platform_user_oper':
                    with pytest.raises(Exception, message="User shouldn't be able to change another user's password") as excinfo:
                        rift.auto.mano.update_password(pxy, 'platform_user_test', 'even_newer_password_{}'.format(idx), user_domain, rw_rbac_int_proxy)
                else:
                    rift.auto.mano.update_password(pxy, 'platform_user_test', 'even_newer_password_{}'.format(idx), user_domain, rw_rbac_int_proxy)
                rift.auto.mano.close_session(user_session)

            # Testing if platform users have access to logging
            for user in self.platform_role_users:
                user_session = rift.auto.mano.get_session(session_class, confd_host, user, 'new_password')
                pxy = user_session.proxy(RwlogMgmtYang)
                access_ = pxy.get_config('/logging')
                assert access_ is not None
                rpc_input = RwlogMgmtYang.YangInput_RwlogMgmt_ShowLogs.from_dict({'all': 'None'})
                pxy.rpc(rpc_input)
                rpc_input_1 = RwlogMgmtYang.YangInput_RwlogMgmt_LogEvent.from_dict({'on': 'None'})
                pxy.rpc(rpc_input_1)
                rift.auto.mano.close_session(user_session)

    def rbac_internal_check(self, mgmt_session, xpath):

        rbac_intl_proxy = mgmt_session.proxy(RwRbacInternalYang)
        rbac_intl_proxy.wait_for(xpath, "active", timeout=5)

    def test_rbac_internal_verification(self, rw_user_proxy, rw_conman_proxy, rbac_user_passwd, user_domain, mgmt_session, 
                                                                rw_project_proxy, rbac_platform_proxy, rw_rbac_int_proxy):
        """Doing various tasks and verifying if rbac-internal is reflecting these changes properly"""

        # Creating projects and users for verifying the rbac-internal scenario
        for idx in range(1, 4):
            project_name = 'rbac_project_{}'.format(idx)
            rift.auto.mano.create_project(rw_conman_proxy, project_name)
            self.RBAC_PROJECTS.append(project_name)

            if project_name in self.DELETED_PROJECTS_TRACKER:
                self.DELETED_PROJECTS_TRACKER.remove(project_name)

        for idx in range(1, 5):
            rift.auto.mano.create_user(rw_user_proxy, 'rbac_user_{}'.format(idx), rbac_user_passwd, user_domain)
            self.RBAC_USERS.append('rbac_user_{}'.format(idx))

        # Rbac-Internal Verification
        project_order = [0, 1, 2, 3, 0]
        xpath = '/rw-rbac-internal/role[role={role}][keys={project}]/user[user-name={user}][user-domain={domain}]/state-machine/state'
        # Assigning four users to four projects with two project roles for each user and checking the rbac-internal
        for idx in range(0, 4):
            fdx = project_order[idx]
            ldx = project_order[idx + 1]
            role = self.project_roles[2 * idx]
            role1 = self.project_roles[(2 * idx) + 1]
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, self.RBAC_USERS[idx],
                                                    self.RBAC_PROJECTS[fdx], user_domain, rw_rbac_int_proxy)
            self.rbac_internal_check(mgmt_session, xpath.format(role=quoted_key(role), project=quoted_key(self.RBAC_PROJECTS[fdx]),
                                                    user=quoted_key(self.RBAC_USERS[idx]), domain=quoted_key(user_domain)))
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role1, self.RBAC_USERS[idx],
                                                    self.RBAC_PROJECTS[ldx], user_domain, rw_rbac_int_proxy)
            self.rbac_internal_check(mgmt_session, xpath.format(role=quoted_key(role1), project=quoted_key(self.RBAC_PROJECTS[ldx]),
                                                    user=quoted_key(self.RBAC_USERS[idx]), domain=quoted_key(user_domain)))
        # Deleting the four projects and then checking rw-rbac-internal
        for project_name in self.RBAC_PROJECTS:
            rift.auto.mano.delete_project(rw_conman_proxy, project_name)
            print ("Deleting project: {}".format(project_name))
            self.DELETED_PROJECTS_TRACKER.add(project_name)

        for idx in range(0, 4):
            fdx = project_order[idx]
            ldx = project_order[idx + 1]
            role = self.project_roles[2 * idx]
            role1 = self.project_roles[(2 * idx) + 1]

            with pytest.raises(Exception, message="This user {} (with this role {} and project {}) shouldn't be on rbac-internal."
                                        .format(self.RBAC_USERS[idx], role, self.RBAC_PROJECTS[fdx])) as excinfo:
                self.rbac_internal_check(mgmt_session, xpath.format(role=quoted_key(role), project=quoted_key(self.RBAC_PROJECTS[fdx]),
                                        user=quoted_key(self.RBAC_USERS[idx]), domain=quoted_key(user_domain)))
            with pytest.raises(Exception, message="This user {} (with this role {} and project {}) shouldn't be on rbac-internal."
                                        .format(self.RBAC_USERS[idx], role1, self.RBAC_PROJECTS[ldx])) as excinfo:
                self.rbac_internal_check(mgmt_session, xpath.format(role=quoted_key(role1), project=quoted_key(self.RBAC_PROJECTS[ldx]),
                                        user=quoted_key(self.RBAC_USERS[idx]), domain=quoted_key(user_domain)))

    def test_roles_revoke(self, rw_conman_proxy, rw_user_proxy, rbac_platform_proxy, rw_project_proxy, 
                                                                    rbac_user_passwd, user_domain, rw_rbac_int_proxy):
        """Assigning all the roles and then revoking them"""

        # Creating users and assigning each of them a role
        rift.auto.mano.create_project(rw_conman_proxy, 'test01')
        for incrementor, role in enumerate(self.project_roles + self.platform_roles, 1):
            user_name = 'test_user_{}'.format(incrementor)
            rift.auto.mano.create_user(rw_user_proxy, user_name, rbac_user_passwd, user_domain)

            if 'platform' in role:
                rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, role, user_name, user_domain, rw_rbac_int_proxy)
            else:

                rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, user_name, 'test01', user_domain, rw_rbac_int_proxy)

        # Removing the assigned roles from each user
        for incrementor, role in enumerate(self.project_roles + self.platform_roles, 1):
            user_name = 'test_user_{}'.format(incrementor)
            if 'platform' in role:
                rift.auto.mano.revoke_platform_role_from_user(rbac_platform_proxy, role, user_name, user_domain)
                rift.auto.mano.revoke_user_from_platform_config(rbac_platform_proxy, user_name, user_domain)
            else:
                rift.auto.mano.revoke_project_role_from_user(rw_project_proxy, role, user_name, 'test01', user_domain)

    def test_misbehaviours(
            self, rw_user_proxy, rbac_user_passwd, user_domain,
            session_class, confd_host, tbac, rw_rbac_int_proxy):
        """Verify if bad credentials can cause any problems."""
        rift.auto.mano.create_user(
            rw_user_proxy, 'testuser', rbac_user_passwd, user_domain)
        # Trying to login with an incorrect password multiple times
        counter = 1
        while(counter < 4):
            with pytest.raises(
                Exception,
                message="User was able to login with the wrong password"
            ):
                rift.auto.mano.get_session(
                    session_class, confd_host, 'testuser', 'wrong_password',
                    timeout=5)
            counter += 1

        # Trying to login with INAVLID_LOGIN_CREDENTIALS
        for uname, passwd in self.INAVLID_LOGIN_CREDENTIALS.items():
            with pytest.raises(
                Exception,
                message="User logged im with invalid login credentials"
            ):
                rift.auto.mano.get_session(
                    session_class, confd_host, uname, passwd, timeout=5)
        # Creating a user with POSSIBLY_PROBLEMATIC_CREDENTIALS
        if tbac:
            for uname, passwd in self.POSSIBLY_PROBLEMATIC_CREDENTIALS.items():
                rift.auto.mano.create_user(
                    rw_user_proxy, uname,
                    passwd[0],
                    passwd[1]
                )
        else:
            for uname, passwd in self.POSSIBLY_PROBLEMATIC_CREDENTIALS.items():
                rift.auto.mano.create_user(
                    rw_user_proxy, uname,
                    passwd[0],
                    user_domain
                )
        # Creating a user with INVALID_CREDENTIALS
        for username, password in self.INVALID_CREDENTIALS.items():
            with pytest.raises(
                Exception,
                message="User created with invalid credentials"
            ):
                rift.auto.mano.create_user(
                    rw_user_proxy, username, password, user_domain)
        # Delete the users created with POSSIBLY_PROBLEMATIC_CREDENTIALS
        if tbac:
            for uname, domain in self.POSSIBLY_PROBLEMATIC_CREDENTIALS.items():
                rift.auto.mano.delete_user(
                    rw_user_proxy, uname,
                    domain[1]
                )
        else:
            for uname, passwd in self.POSSIBLY_PROBLEMATIC_CREDENTIALS.items():
                rift.auto.mano.delete_user(
                    rw_user_proxy, uname, user_domain
                )

    def test_project_keys(
            self, rw_project_proxy, rbac_user_passwd, session_class,
            confd_host):
        """Trying to access/create various projects with bad project keys."""
        # Checking if INVALID_PROJECT_KEYS can be accessed.
        for project_name in self.INVALID_PROJECT_KEYS:
            project_cm_config_xpath = '/project[name={project_name}]/project-state'
            project_ = rw_project_proxy.get_config(
                project_cm_config_xpath.format(
                    project_name=quoted_key(project_name)
                ),
                list_obj=True
            )
            assert project_ is None
        # Trying to create projects with INVALID_PROJECT_CREATE_KEYS
        for project_name in self.INVALID_PROJECT_CREATE_KEYS:
            with pytest.raises(
                Exception,
                message="Project created with the INVALID_PROJECT_CREATE_KEYS"
            ):
                rift.auto.mano.create_project(rw_conman_proxy, project_name)
        # These POSSIBLY_PROBLEMATIC_KEYS should not cause any error in theory.
        for project_name in self.POSSIBLY_PROBLEMATIC_KEYS:
            rift.auto.mano.create_project(rw_project_proxy, project_name)
        # User trying to access a project he has no access to.
        user_session = rift.auto.mano.get_session(
            session_class, confd_host, 'test_user_11', rbac_user_passwd)
        pxy = user_session.proxy(RwConmanYang)
        project_ = pxy.get_config(
            project_cm_config_xpath.format(
                project_name=quoted_key('test01')
            )
        )
        assert project_ is None
        rift.auto.mano.close_session(user_session)

    def test_project_testing(self, rw_conman_proxy, rw_user_proxy, rw_project_proxy, rbac_user_passwd, user_domain, rw_rbac_int_proxy):
        """Multiple projects creation, deletion, re-addition with verification every step of the way"""

        # Creating projects and users for this test case
        for idx in range(1,5):
            project_name = 'testing_project_{}'.format(idx)
            rift.auto.mano.create_project(rw_conman_proxy, project_name)
            self.TEST_PROJECTS.append(project_name)
            if project_name in self.DELETED_PROJECTS_TRACKER:
                self.DELETED_PROJECTS_TRACKER.remove(project_name)

        for idx in range(1,9):
            rift.auto.mano.create_user(rw_user_proxy, 'testing_user_{}'.format(idx), rbac_user_passwd, user_domain)
            self.TEST_USERS.append('testing_user_{}'.format(idx))

        # Assigning project roles to users
        for idx in range(0,8):
            role = self.project_roles[idx]
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, self.TEST_USERS[idx], 
                                                    self.TEST_PROJECTS[idx//2], user_domain, rw_rbac_int_proxy)

        # Deleting all test projects
        for project_name in self.TEST_PROJECTS:
            rift.auto.mano.delete_project(rw_conman_proxy, project_name)
            self.DELETED_PROJECTS_TRACKER.add(project_name)

        # Recreating all the deleted projects
        for project_name in self.TEST_PROJECTS:
            rift.auto.mano.create_project(rw_conman_proxy, project_name)
            if project_name in self.DELETED_PROJECTS_TRACKER:
                self.DELETED_PROJECTS_TRACKER.remove(project_name)

        # Check if the recreated projects have the old users assigned to them still.
        for idx in range(0,8):
            role = self.project_roles[idx]
            role_keyed_path = "/project[name={project}]/project-config/user[user-name={user}][user-domain={domain}]/role[role={user_role}]"
            role_ = rw_project_proxy.get_config(role_keyed_path.format(project=quoted_key(self.TEST_PROJECTS[idx//2]),
                                                user=quoted_key(self.TEST_USERS[idx]), domain=quoted_key(user_domain), user_role=quoted_key(role)))
            assert role_ is None, "This user shouldn't exist in this project which was just created"

        # Reassigning the old users to their old roles.
        for idx in range(0,8):
            role = self.project_roles[idx]
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, self.TEST_USERS[idx],
                                                    self.TEST_PROJECTS[idx//2], user_domain, rw_rbac_int_proxy)


@pytest.mark.depends('rbac_setup')
@pytest.mark.teardown('rbac_setup')
@pytest.mark.incremental
class TestTeardown(object):
    """Class Teardown."""

    def test_delete_projects(self, rw_conman_proxy):
        invalid_projects = TestIdentity.POSSIBLY_PROBLEMATIC_KEYS + ['test01']
        valid_projects = TestIdentity.TEST_PROJECTS + TestIdentity.RBAC_PROJECTS
        all_projects = valid_projects + invalid_projects

        for project_name in all_projects:
            try:
                rift.auto.mano.delete_project(rw_conman_proxy, project_name)
            except rift.auto.session.ProxyRequestError as e:
                if project_name in TestIdentity.DELETED_PROJECTS_TRACKER:
                    print ("Project {} is already deleted".format(project_name))
                elif project_name not in invalid_projects:
                    print ("Failed to delete project: {}".format(project_name))
                    raise e

    def test_delete_users(self, rw_user_proxy, rbac_platform_proxy, user_domain):
        users_test_data = ['testuser']
        for incrementor, role in enumerate(TestIdentity.project_roles + TestIdentity.platform_roles, 1):
            users_test_data.append('test_user_{}'.format(incrementor))

        for user in TestIdentity.platform_users:
            users_test_data.append(user)

        # Deletes the users
        for user in users_test_data+TestIdentity.RBAC_USERS+TestIdentity.TEST_USERS:
            try:
                keyed_path = "/rbac-platform-config/user[user-name={user}][user-domain={domain}]"
                platform_cfg_ent = rbac_platform_proxy.get_config(keyed_path.format(user=quoted_key(user), domain=quoted_key(user_domain)))

                if platform_cfg_ent is not None:
                    # Delete from the platform-config first.
                    rift.auto.mano.revoke_user_from_platform_config(rbac_platform_proxy, user, user_domain)
                rift.auto.mano.delete_user(rw_user_proxy, user, user_domain)

            except rift.auto.session.ProxyRequestError as e:
                if user not in TestIdentity.INAVLID_LOGIN_CREDENTIALS:
                    print ("Deletion of user {} failed".format(user))
                    raise e
                else:
                    print ("Expected error deleting invalid user {}".format(user))
