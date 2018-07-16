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
import collections
import gi
import pytest
import random
import uuid

import rift.auto.mano
import rift.auto.descriptor
gi.require_version('RwUserYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwConmanYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('RwlogMgmtYang', '1.0')
from gi.repository import (
    RwUserYang,
    RwProjectYang,
    RwConmanYang,
    RwProjectVnfdYang,
    RwProjectNsdYang,
    RwNsrYang,
    RwVnfrYang,
    RwVlrYang,
    RwRbacPlatformYang,
    RwlogMgmtYang,
    RwRedundancyYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

SESSION_CONNECT_TIMEOUT=5

@pytest.fixture(scope='session')
def user_test_roles():
    """Returns tuples of roles which enable an user to delete/create a new user"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-rbac-platform:platform-admin')
    read_roles = tuple()
    return write_roles, read_roles


@pytest.fixture(scope='session')
def project_test_roles():
    """Returns tuples of roles which enable an user to create, read, delete a project"""
    write_roles = ('rw-rbac-platform:super-admin', )
    read_roles = ('rw-project:project-oper', 'rw-project:project-admin')
    return write_roles, read_roles


@pytest.fixture(scope='session')
def onboarding_test_roles():
    """Fixture that returns a tuple of roles which enable an user to onboard/modify/delete a VNF/NS package"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-project-mano:catalog-admin', 'rw-project:project-admin')
    read_roles = ('rw-project-mano:catalog-oper', 'rw-project-mano:lcm-admin')
    return write_roles, read_roles


@pytest.fixture(scope='session')
def account_test_roles():
    """Fixture that returns a tuple of roles which enable an user to CRUD a VIM, Sdn account"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-project-mano:account-admin', 'rw-project:project-admin')
    read_roles = ('rw-project-mano:account-oper', 'rw-project-mano:lcm-admin')
    return write_roles, read_roles


@pytest.fixture(scope='session')
def ns_instantiate_test_roles():
    """Fixture that returns a tuple of roles which enable an user to instantiate/terminate a NS
    Read roles: who all can access vnfr-catalog, vnfr-console, ns-instance-opdata etc"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-project-mano:lcm-admin', 'rw-project:project-admin')
    read_roles = ('rw-project-mano:lcm-oper', )
    return write_roles, read_roles


@pytest.fixture(scope='session')
def syslog_server_test_roles():
    """Fixture that returns a tuple of roles which enable an user set the syslog server_address"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-rbac-platform:platform-admin', 'rw-rbac-platform:platform-oper')
    read_roles = tuple()
    return write_roles, read_roles


@pytest.fixture(scope='session')
def redundancy_config_test_roles():
    """Fixture that returns a tuple of roles which enable an user set the syslog server_address"""
    write_roles = ('rw-rbac-platform:super-admin', 'rw-rbac-platform:platform-admin')
    read_roles =  ('rw-rbac-platform:platform-oper', )
    return write_roles, read_roles


@pytest.fixture(scope='session')
def project_acessible():
    """Fixture that returns name of the project to which all new users will be associated"""
    return random.choice(['project1', 'default'])


# @pytest.fixture(scope='session')
# def project_not_accessible():
#   """Retruns name of the project whose users are not supposed to access the resources under project 'project_acessible'"""
#   return 'project2'


@pytest.fixture(scope='session')
def users_test_data(rw_user_proxy, rbac_platform_proxy, rw_project_proxy, all_roles, user_test_roles, project_test_roles,
    onboarding_test_roles, account_test_roles, ns_instantiate_test_roles, user_domain, project_acessible, rw_conman_proxy,
    syslog_server_test_roles, all_roles_combinations, rw_rbac_int_proxy, tbac, redundancy_config_test_roles):
    """Creates new users required for a test and assign appropriate roles to them"""
    if pytest.config.getoption("--user-creation-test"):
        test_roles = user_test_roles
    elif pytest.config.getoption("--project-creation-test"):
        test_roles = project_test_roles
    elif pytest.config.getoption("--onboarding-test"):
        test_roles = onboarding_test_roles
    elif pytest.config.getoption("--account-test"):
        test_roles = account_test_roles
    elif pytest.config.getoption("--nsr-test"):
        test_roles = ns_instantiate_test_roles
    elif pytest.config.getoption("--syslog-server-test"):
        test_roles = syslog_server_test_roles
    elif pytest.config.getoption("--redundancy-role-test"):
        test_roles = redundancy_config_test_roles

    # Create a project to which these users will be part of
    if project_acessible != 'default':
        rift.auto.mano.create_project(rw_conman_proxy, project_acessible)

    def create_user_assign_role(user_name, password, role_set):
        rift.auto.mano.create_user(rw_user_proxy, user_name, password, user_domain)
        project_roles_list, platform_roles_list = [], []
        for role in role_set:
            if 'platform' in role:
                platform_roles_list.append(role)
            else:
                project_roles_list.append(role)
        if platform_roles_list:
            rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, platform_roles_list, user_name, user_domain, rw_rbac_int_proxy)
        if project_roles_list:
            rift.auto.mano.assign_project_role_to_user(rw_project_proxy, project_roles_list, user_name,
                                                       project_acessible, user_domain, rw_rbac_int_proxy)

    write_roles, read_roles = test_roles
    fail_roles = [role for role in all_roles if role not in write_roles]

    if False: #If its desired to run checks for all combinations, tbd on what option this will be enabled
        write_roles_tmp, read_roles_tmp, fail_roles_tmp = [], [], []
        for role_combination in all_roles_combinations:
            if bool(set(role_combination).intersection(write_roles)):
                write_roles_tmp.append(role_combination)
                continue
            if bool(set(role_combination).intersection(read_roles)):
                read_roles_tmp.append(role_combination)
                continue
            if bool(set(role_combination).isdisjoint(write_roles)):
                fail_roles_tmp.append(role_combination)
        write_roles, read_roles, fail_roles = write_roles_tmp, read_roles_tmp, fail_roles_tmp

    # Create the users with roles mapped
    write_users, read_users, fail_users = dict(), dict(), dict()
    for idx, role_set in enumerate(write_roles, 1):
        if type(role_set) is str:
            role_set = [role_set]
        user_name = 'write-{}'.format(idx)
        if tbac:
            password=user_name
        else:
            password = rift.auto.mano.generate_password()
        create_user_assign_role(user_name, password, role_set)
        write_users[user_name] = (role_set, password)

    for idx, role_set in enumerate(read_roles, 1):
        if type(role_set) is str:
            role_set = [role_set]
        user_name = 'read-{}'.format(idx)
        if tbac:
            password=user_name
        else:
            password = rift.auto.mano.generate_password()
        create_user_assign_role(user_name, password, role_set)
        read_users[user_name] = (role_set, password)

    for idx, role_set in enumerate(fail_roles, 1):
        if type(role_set) is str:
            role_set = [role_set]
        user_name = 'fail-{}'.format(idx)
        if tbac:
            password=user_name
        else:
            password = rift.auto.mano.generate_password()
        create_user_assign_role(user_name, password, role_set)
        fail_users[user_name] = (role_set, password)
    return write_users, read_users, fail_users


@pytest.mark.setup('test_rbac_roles_setup')
@pytest.mark.incremental
class TestRbacVerification(object):
    @pytest.mark.skipif(not pytest.config.getoption("--project-creation-test"), reason="need --project-creation-test option to run")
    def test_project_create_delete_authorization(self, logger, users_test_data, session_class, confd_host, rw_conman_proxy,
                                                        project_keyed_xpath, project_acessible):
        """Verifies only users with certain roles can create/delete a project"""

        write_users, read_users, fail_users = users_test_data

        # Check users in write_users dict able to create/delete a project
        logger.debug('Verifying users which are authorised to create/delete a project')
        for user in write_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, write_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, write_users[user][1])
            pxy = user_session.proxy(RwProjectYang)

            project_name = 'project-{}'.format(user)
            logger.debug('Trying to create project {}'.format(project_name))
            rift.auto.mano.create_project(pxy, project_name)

            logger.debug('Trying to delete project {}'.format(project_name))
            rift.auto.mano.delete_project(pxy, project_name)

            rift.auto.mano.close_session(user_session)

        # Check users in read_users dict able to read a project
        logger.debug('Verifying users which are authorised to read a project')
        for user in read_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, read_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, read_users[user][1])
            pxy = user_session.proxy(RwProjectYang)

            logger.debug('User {} trying to read project {}'.format(user, project_acessible))
            project_ = pxy.get_config(project_keyed_xpath.format(project_name=quoted_key(project_acessible))+'/project-state', list_obj=True)
            assert project_

            rift.auto.mano.close_session(user_session)

        # Check users in fail_users dict shouldn't be allowed to create a project or delete a project

        # 'project-admin' user not able to create a project, but can delete a project, hence do the create/delete
        # operation for this user at the end
        fail_users_reordered = collections.OrderedDict()
        for user, role_passwd_tuple in fail_users.items():
            if any('project-admin' in role for role in role_passwd_tuple[0]):
                project_admin_key, project_admin_val = user, role_passwd_tuple
                continue
            fail_users_reordered[user] = role_passwd_tuple
        fail_users_reordered[project_admin_key] = project_admin_val

        logger.debug('Verifying users which are not supposed to create/delete a project')
        for user in fail_users_reordered:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users_reordered[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users_reordered[user][1])
            pxy = user_session.proxy(RwProjectYang)

            project_name = 'project-{}'.format(user)

            with pytest.raises(Exception, message='User {} not authorised to create project {}'.format(
                                                        user, project_name)) as excinfo:
                logger.debug('User {} trying to create project {}'.format(user, project_name))
                rift.auto.mano.create_project(pxy, project_name)

            logger.debug('User {} trying to delete project {}'.format(user, project_acessible))
            if any('project-admin' in role for role in fail_users_reordered[user][0]):
                rift.auto.mano.delete_project(pxy, project_acessible)
                continue
            with pytest.raises(Exception, message='User {} not authorised to delete project {}'.format(
                                                        user, project_acessible)) as excinfo:
                rift.auto.mano.delete_project(pxy, project_acessible)

            rift.auto.mano.close_session(user_session)

    def delete_user_from_project(
            self, project_proxy, target_user, target_project, user_domain):
        project_xpath = (
            "/project[name={project}]/project-config/user" +
            "[user-name={user}][user-domain={domain}]"
        )
        # Check if the user exists for the project
        ret_val = project_proxy.get_config(
            project_xpath.format(
                project=quoted_key(target_project),
                user=quoted_key(target_user),
                domain=quoted_key(user_domain)))
        
        assert ret_val
        # Delete the target_user from the target_project
        project_proxy.delete_config(
            project_xpath.format(
                project=quoted_key(target_project),
                user=quoted_key(target_user),
                domain=quoted_key(user_domain))
        )
        # Verify that he is deleted
        ret_val = project_proxy.get_config(
            project_xpath.format(
                project=quoted_key(target_project),
                user=quoted_key(target_user),
                domain=quoted_key(user_domain))
        )
        assert ret_val is None

    @pytest.mark.skipif(
        not pytest.config.getoption("--project-creation-test"),
        reason="need --project-creation-test option to run")
    def test_project_admin_users_role_authorization(
            self, logger, user_roles, rw_user_proxy, session_class,
            user_domain, confd_host, rw_conman_proxy, project_keyed_xpath,
            rw_project_proxy, rw_rbac_int_proxy, tbac):
        """Verify project admin & oper role operations on a single project."""
        logger.debug(
            "Create a project & 8 users each with its own project/mano role")
        rift.auto.mano.create_project(rw_conman_proxy, 'project-vzw')
        project_user_data = {}
        for idx, role in enumerate(user_roles, 1):
            user_name = 'project_vzw_user-{}'.format(idx)
            if not tbac:
                password = rift.auto.mano.generate_password()
            else:
                password = user_name
            rift.auto.mano.create_user(
                rw_user_proxy, user_name, password, user_domain)
            rift.auto.mano.assign_project_role_to_user(
                rw_project_proxy, role, user_name, 'project-vzw',
                user_domain, rw_rbac_int_proxy)
            project_user_data[user_name] = {"role": role, "password": password}
            if "project-admin" in role:
                project_admin_user = user_name

        logger.debug("Project admin deleting roles from users.")
        project_admin_session = rift.auto.mano.get_session(
            session_class, confd_host, project_admin_user,
            project_user_data[project_admin_user]["password"])
        project_admin_proxy = project_admin_session.proxy(RwProjectYang)
        for user in project_user_data:
            role = project_user_data[user]["role"]
            if project_admin_user == user:
                continue
            rift.auto.mano.revoke_project_role_from_user(
                project_admin_proxy, role, user, 'project-vzw', user_domain)
        rift.auto.mano.close_session(project_admin_session)

        logger.debug("Verify project admin can assign another role to users")
        project_admin_session = rift.auto.mano.get_session(
            session_class, confd_host, project_admin_user,
            project_user_data[project_admin_user]["password"])
        project_admin_proxy = project_admin_session.proxy(RwProjectYang)
        for user in project_user_data:
            role = 'rw-project:project-oper'
            if project_admin_user == user:
                continue
            rift.auto.mano.assign_project_role_to_user(
                project_admin_proxy, role, user, 'project-vzw',
                user_domain, rw_rbac_int_proxy)
            rift.auto.mano.close_session(project_admin_session)

        # Verify the user able to read project
        for user in project_user_data:
            user_session = rift.auto.mano.get_session(
                session_class, confd_host, user,
                project_user_data[user]["password"])
            user_project_pxy = user_session.proxy(RwProjectYang)
            logger.debug("verifying user able to read project")
            xpath = "/project[name={project}]/project-config"
            ret_val = user_project_pxy.get_config(
                xpath.format(project=quoted_key('project-vzw')))
            assert ret_val
            rift.auto.mano.close_session(user_session)

        logger.debug("Verify if project admin can replace roles for users")
        project_admin_session = rift.auto.mano.get_session(
            session_class, confd_host, project_admin_user,
            project_user_data[project_admin_user]["password"])
        project_admin_proxy = project_admin_session.proxy(RwProjectYang)
        for user in project_user_data:
            if project_admin_user != user:
                xpath = (
                    "/project[name={project}]/project-config/user" +
                    "[user-name={user}][user-domain={domain}]")
                new_role = (
                    RwProjectYang.
                    YangData_RwProject_Project_ProjectConfig_User_Role.
                    from_dict({
                        'role': 'rw-project-mano:account-admin'})
                )
                project_admin_proxy.replace_config(
                    xpath.format(
                        project=quoted_key('project-vzw'),
                        user=quoted_key(user),
                        domain=quoted_key(user_domain)), new_role)
                ret_val = project_admin_proxy.get_config(
                    xpath.format(
                        project=quoted_key('project-vzw'),
                        user=quoted_key(user),
                        domain=quoted_key(user_domain),
                        role=quoted_key('rw-project-mano:lcm-oper')))
                assert ret_val
            rift.auto.mano.close_session(project_admin_session)

        logger.debug("Verify if users able to change its own user details")
        for user in project_user_data:
            if tbac:
                break
            password = project_user_data[user]["password"]
            user_session = rift.auto.mano.get_session(
                session_class, confd_host, user, password)
            user_proxy = user_session.proxy(RwUserYang)
            rift.auto.mano.update_password(
                user_proxy, user, user, user_domain, rw_rbac_int_proxy)
            project_user_data[user]["new_password"] = user
            rift.auto.mano.close_session(user_session)

            logger.debug(
                "{} trying to connect ".format(user) +
                "with its old password {}".format(password)
            )

            message = ('{} not supposed to '.format(user) +
                       'log-in with old passwd {}'.format(password))
            with pytest.raises(Exception, message=message):
                rift.auto.mano.get_session(
                    session_class, confd_host, user,
                    password, timeout=SESSION_CONNECT_TIMEOUT)

            # Verify the user should be able to log-in with new password
            logger.debug(
                "User {} trying to log-in with its updated password {}".format(
                    user, project_user_data[user]["new_password"]))

            usession_updated_passwd = rift.auto.mano.get_session(
                session_class, confd_host, user,
                project_user_data[user]["new_password"])

        # project admin able to delete users from the project database
        if tbac:
            password = project_user_data[project_admin_user]["password"]
        else:
            password = project_user_data[project_admin_user]["new_password"]
        project_admin_session = rift.auto.mano.get_session(
            session_class, confd_host, project_admin_user, password)
        project_admin_proxy = project_admin_session.proxy(RwProjectYang)

        for user in project_user_data:
            if user == project_admin_user:
                continue
            logger.debug('deleting user {} from project project-vzw'.format(user))
            self.delete_user_from_project(
                project_admin_proxy, user, 'project-vzw', user_domain)
            rift.auto.mano.close_session(project_admin_session)

    @pytest.mark.skipif(
        not pytest.config.getoption("--project-creation-test"),
        reason="need --project-creation-test option to run")
    def test_multi_project_multi_users_role_authorization(
            self, logger, user_roles, rw_user_proxy, session_class,
            user_domain, confd_host, rw_conman_proxy, project_keyed_xpath,
            rw_project_proxy, rw_rbac_int_proxy, tbac, rbac_user_passwd):
        """Verify that users with roles doesn't have unauthorized access."""
        """
        Case 01. rbac_user2 has different roles in project1 and project2.
        Case 02. rbac_user4 has project-admin in project3 and project4.
        Case 03. rbac_user9 has project-oper in project5 and project6.
        """

        # The sample user data
        role1 = 'rw-project:project-admin'
        role2 = 'rw-project:project-oper'
        project_user_data = {
            "project1": {
                "rbac_user1": role1,
                "rbac_user2": role2,
            },
            "project2": {
                "rbac_user2": role1,
                "rbac_user3": role2,
            },
            "project3": {
                "rbac_user4": role1,
                "rbac_user5": role2,

            },
            "project4": {
                "rbac_user4": role1,
                "rbac_user6": role2,
            },
            "project5": {
                "rbac_user7": role1,
                "rbac_user9": role2,
            },
            "project6": {
                "rbac_user8": role1,
                "rbac_user9": role2,
            }
        }
        # Create projects
        for idx in range(1, 7):
            rift.auto.mano.create_project(
                rw_conman_proxy, 'project{}'.format(idx))
        # Create users
        for idx in range(1, 10):
            rift.auto.mano.create_user(
                rw_user_proxy, 'rbac_user{}'.format(idx),
                rbac_user_passwd, user_domain)
        # Assign roles to users according to the project_user_data
        for idx in range(1, 7):
            project = 'project{}'.format(idx)
            for user_name, role in project_user_data[project].items():
                rift.auto.mano.assign_project_role_to_user(
                    rw_project_proxy, role, user_name, project,
                    user_domain, rw_rbac_int_proxy)

        def project_access(
                user_name, target_project, session_class,
                confd_host, logger):
            """Verify if user has access to target project."""
            password = rbac_user_passwd
            if tbac:
                password = user_name
            user_session = rift.auto.mano.get_session(
                session_class, confd_host, user_name, password)
            logger.debug("{} trying to access {}".format(
                user_name, target_project) +
                "/project-state"
            )
            pxy = user_session.proxy(RwProjectYang)
            # Verify is user has access to /project
            project_xpath = '/project[name={}]/project-state'.format(
                quoted_key(target_project)
            )
            response = pxy.get_config(project_xpath, list_obj=True)
            assert response
            # Verify is user has access to /project/project-config/user
            project_user_xpath = (
                "/project[name={project}]/project-config/" +
                "user[user-name={user}][user-domain={domain}]"
            )
            target_user = list(project_user_data[target_project].keys())[0]
            pxy = user_session.proxy(RwProjectYang)
            response = pxy.get_config(
                project_user_xpath.format(
                    project=quoted_key(target_project),
                    user=quoted_key(target_user),
                    domain=quoted_key(user_domain)
                )
            )
            assert response
            rift.auto.mano.close_session(user_session)

        # Case 01. rbac_user2 has different roles in project1 and project2.

        logger.debug('Veryfy rbac_user1 of project1 has no access to project2')
        with pytest.raises(
                Exception,
                message="rbac_user1 accessed project2 which its not part of."):
            project_access(
                'rbac_user1', 'project2', session_class, confd_host, logger)

        logger.debug('Verify rbac_user2 has access to project1 and project2')
        project_access(
            'rbac_user2', 'project1', session_class, confd_host, logger)
        project_access(
            'rbac_user2', 'project2', session_class, confd_host, logger)

        # Case 02. rbac_user4 has project-admin in project3 and project4.

        logger.debug('Verify rbac_user4 has access to project 3 & project4')
        project_access(
            'rbac_user4', 'project4', session_class, confd_host, logger)
        project_access(
            'rbac_user4', 'project3', session_class, confd_host, logger)

        logger.debug('Two users in project3 exchanges roles & check access')
        rift.auto.mano.revoke_project_role_from_user(
            rw_project_proxy, role1, 'rbac_user4',
            'project3', user_domain)
        rift.auto.mano.revoke_project_role_from_user(
            rw_project_proxy, role2, 'rbac_user5',
            'project3', user_domain)
        rift.auto.mano.assign_project_role_to_user(
            rw_project_proxy, role2, 'rbac_user4',
            'project3', user_domain, rw_rbac_int_proxy)
        rift.auto.mano.assign_project_role_to_user(
            rw_project_proxy, role1, 'rbac_user5',
            'project3', user_domain, rw_rbac_int_proxy)

        logger.debug('rbac_user5 trying its access on project3 and project4')
        project_access(
            'rbac_user5', 'project3', session_class,
            confd_host, logger
        )
        with pytest.raises(
                Exception,
                message="rbac_user5 accessed project4 which its not part of."):
            project_access(
                'rbac_user5', 'project4', session_class,
                confd_host, logger
            )

        # 'rbac_user5'(admin role) revoking the role from rbac-user4
        password = rbac_user_passwd
        if tbac:
            password = 'rbac_user5'
        rbac_user2_session = rift.auto.mano.get_session(
            session_class, confd_host, 'rbac_user5', password)
        rbac_user2_prjt_pxy = rbac_user2_session.proxy(RwProjectYang)
        self.delete_user_from_project(
            rbac_user2_prjt_pxy, 'rbac_user4', 'project3', user_domain)

        # Create new user 'del-user'
        rift.auto.mano.create_user(
            rw_user_proxy, 'del-user', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_project_role_to_user(
            rw_project_proxy, role2, 'del-user', 'project3',
            user_domain, rw_rbac_int_proxy)
        # Delete 'del-user' with 'rbac_user5'(admin role)
        self.delete_user_from_project(
            rbac_user2_prjt_pxy, 'del-user', 'project3', user_domain)

        logger.debug(
            'rbac_user4 try to access project3 which its not a part of anymore'
        )
        with pytest.raises(
                Exception,
                message="rbac_user4 accessed project3 which its not part of."):
            project_access(
                'rbac_user4', 'project3', session_class,
                confd_host, logger)

        logger.debug('rbac_user4 try to access project4 which its a part of.')
        project_access(
            'rbac_user4', 'project4', session_class,
            confd_host, logger)

        # Case 03. rbac_user9 has project-oper in project5 and project6.

        logger.debug('rbac_user9 try to access project5 & project6')
        project_access(
            'rbac_user9', 'project5', session_class,
            confd_host, logger)
        project_access(
            'rbac_user9', 'project6', session_class,
            confd_host, logger)

        logger.debug(
            'rbac_user8 try to access to project5 which its not part of.'
        )
        with pytest.raises(
                Exception,
                message="rbac_user8 accessed project5 which its not part of."):
            project_access(
                'rbac_user8', 'project5', session_class,
                confd_host, logger)

        logger.debug(
            'rbac_user7 try to access to project6 which its not part of.'
        )
        with pytest.raises(
                Exception,
                message="rbac_user7 accessed project6 which its not part of."):
            project_access(
                'rbac_user7', 'project6', session_class,
                confd_host, logger)


    @pytest.mark.skipif(not pytest.config.getoption("--user-creation-test"), reason="need --user-creation-test option to run")
    def test_user_create_delete_authorization(self, logger, users_test_data, session_class, confd_host, rw_user_proxy,
                        rbac_user_passwd, user_domain, tbac, rw_rbac_int_proxy):
        """Verifies only users with certain roles can create/delete users and set the password of an user"""
        write_users, read_users, fail_users = users_test_data

        # Create a dummy user with admin/admin
        dummy_user_name = 'dummy-user'
        rift.auto.mano.create_user(rw_user_proxy, dummy_user_name, rbac_user_passwd, user_domain)

        # Check users in write_users dict able to create/delete an user and able to set password for others
        logger.debug('Verifying users which are authorised to create/delete an user')
        for user in write_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, write_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, write_users[user][1])
            pxy = user_session.proxy(RwUserYang)

            user_name = 'new-user-{}'.format(user)
            logger.debug('Trying to create user {}'.format(user_name))
            rift.auto.mano.create_user(pxy, user_name, rbac_user_passwd, user_domain)

            logger.debug('Trying to delete user {}'.format(user_name))
            rift.auto.mano.delete_user(pxy, user_name, user_domain)

            if not tbac:    # password update is not allowed for external users in tbac
                new_passwd = rift.auto.mano.generate_password()
                # Check users in write_users dict able to set password for other user (dummy-user)
                logger.debug('User {} trying to update password for user {}'.format(user, dummy_user_name))
                rift.auto.mano.update_password(pxy, dummy_user_name, new_passwd, user_domain, rw_rbac_int_proxy)

                # Verify dummy_user_name able to log-in with its new password
                logger.debug('User {} trying to log-in with its updated password {}'.format(dummy_user_name, new_passwd))
                dummy_user_session_updated_passwd = rift.auto.mano.get_session(session_class, confd_host, dummy_user_name,
                                                                new_passwd)

                # Verify the user not able to log-in with old password
                with pytest.raises(Exception, message='User {} not supposed to log-in with its old password {}'.format(
                                                                dummy_user_name, rbac_user_passwd)) as excinfo:
                    logger.debug('User {} trying to connect with its old password {}'.format(user, rbac_user_passwd))
                    rift.auto.mano.get_session(session_class, confd_host, dummy_user_name, rbac_user_passwd,
                                        timeout=SESSION_CONNECT_TIMEOUT)

                rift.auto.mano.close_session(dummy_user_session_updated_passwd)
            rift.auto.mano.close_session(user_session)

        # Check users in read_users dict able to read user list (path: /user-config)
        logger.debug('Verifying users which are authorised to read user list')
        for user in read_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, read_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, read_users[user][1])
            pxy = user_session.proxy(RwUserYang)
            logger.debug('User {} trying to access /user-config xpath'.format(user))
            user_config = pxy.get_config('/user-config')
            assert [user.user_name for user in user_config.user]

            rift.auto.mano.close_session(user_session)

        # Check users in fail_users dict not able to create/delete an user
        logger.debug('Verifying users which are not supposed to create/delete an user')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            pxy = user_session.proxy(RwUserYang)

            user_name = 'new-user-{}'.format(user)

            with pytest.raises(Exception, message='User {} not authorised to create user {}'.format(
                                                    user, user_name)) as excinfo:
                logger.debug('User {} trying to create an user {}'.format(user, user_name))
                rift.auto.mano.create_user(pxy, user_name, rbac_user_passwd, user_domain)

            with pytest.raises(Exception, message='User {} not authorised to delete user {}'.format(
                                                    user, dummy_user_name)) as excinfo:
                logger.debug('User {} trying to delete user {}'.format(user, dummy_user_name))
                rift.auto.mano.delete_user(pxy, dummy_user_name, user_domain)

            rift.auto.mano.close_session(user_session)

        if not tbac:    # password update is not allowed for external users in tbac
            # Check all users able to set their own password
            logger.debug('Verifying an user able to set its own password')
            for user, role_passwd_tuple in dict(write_users, **dict(read_users, **fail_users)).items():
                logger.debug('Verifying user:(role,password) {}:{}'.format(user, role_passwd_tuple))
                user_session = rift.auto.mano.get_session(session_class, confd_host, user, role_passwd_tuple[1])
                pxy = user_session.proxy(RwUserYang)

                new_passwd = rift.auto.mano.generate_password()
                logger.debug('User {} trying to update its password to {}'.format(user, new_passwd))
                rift.auto.mano.update_password(pxy, user, new_passwd, user_domain, rw_rbac_int_proxy)

                # Verify the user should be able to log-in with new password
                logger.debug('User {} trying to log-in with its updated password {}'.format(user, new_passwd))
                user_session_updated_passwd = rift.auto.mano.get_session(session_class, confd_host, user, new_passwd)

                # Verify the user not able to log-in with old password
                with pytest.raises(Exception, message='User {} not supposed to log-in with its old password {}'.format(
                                                                        user, role_passwd_tuple[1])) as excinfo:
                    logger.debug('User {} trying to connect with its old password {}'.format(user, role_passwd_tuple[1]))
                    rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd, timeout=SESSION_CONNECT_TIMEOUT)

                rift.auto.mano.close_session(user_session)
                rift.auto.mano.close_session(user_session_updated_passwd)


    @pytest.mark.skipif(not pytest.config.getoption("--account-test"), reason="need --account-test option to run")
    def test_account_create_delete_authorization(self, users_test_data, mgmt_session, logger, cloud_module, fmt_cloud_xpath,
                            fmt_prefixed_cloud_xpath, project_acessible, cloud_account, session_class, confd_host):
        """Verifies only users with certain roles can create/read/delete cloud, sdn accounts"""
        write_users, read_users, fail_users = users_test_data
        xpath_no_pfx = fmt_cloud_xpath.format(project=quoted_key(project_acessible), account_name=quoted_key(cloud_account.name))
        xpath = fmt_prefixed_cloud_xpath.format(project=quoted_key(project_acessible), account_name=quoted_key(cloud_account.name))

        # Check users in write_users dict able to create/delete cloud accounts
        logger.debug('Verifying users which are authorised to create/delete cloud accounts')
        for user in write_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, write_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, write_users[user][1])
            cloud_pxy = user_session.proxy(cloud_module)

            logger.debug('Trying to create a cloud account')
            cloud_pxy.replace_config(xpath, cloud_account)
            response =  cloud_pxy.get(xpath_no_pfx)
            assert response.name == cloud_account.name
            assert response.account_type == cloud_account.account_type

            logger.debug('Trying to delete the cloud account')
            cloud_pxy.delete_config(xpath)
            assert cloud_pxy.get(xpath_no_pfx) is None

            rift.auto.mano.close_session(user_session)

        # admin user creating a cloud account which read_users will be trying to read
        logger.debug('admin user creating cloud account {}'.format(cloud_account.name))
        admin_cloud_proxy = mgmt_session.proxy(cloud_module)
        admin_cloud_proxy.replace_config(xpath, cloud_account)
        assert admin_cloud_proxy.get(xpath_no_pfx).name == cloud_account.name

        # Check users in read_users dict able to read cloud accounts
        logger.debug('Verifying users which are authorised to read cloud accounts')
        for user in read_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, read_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, read_users[user][1])
            cloud_pxy = user_session.proxy(cloud_module)

            response =  cloud_pxy.get(xpath_no_pfx)
            assert response.name == cloud_account.name
            assert response.account_type == cloud_account.account_type

            rift.auto.mano.close_session(user_session)

        # Check users in fail_users dict not able to delete/read cloud accounts
        logger.debug('Verifying users which are not authorised to read/delete cloud accounts')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            cloud_pxy = user_session.proxy(cloud_module)

            with pytest.raises(Exception, message='User {} not authorised to delete cloud account {}'.format(
                                                user, cloud_account.name)) as excinfo:
                logger.debug('User {} trying to delete cloud account {}'.format(user, cloud_account.name))
                cloud_pxy.delete_config(xpath)

            # logger.debug('User {} trying to access cloud account {}'.format(user, cloud_account.name))
            # assert cloud_pxy.get(xpath_no_pfx) is None
            rift.auto.mano.close_session(user_session)

        # admin user deleting the cloud account
        logger.debug('admin user deleting cloud account {}'.format(cloud_account.name))
        admin_cloud_proxy.delete_config(xpath)
        assert admin_cloud_proxy.get(xpath_no_pfx) is None

        # Check users in fail_users dict not able to create cloud accounts
        logger.debug('Verifying users which are not authorised to create cloud accounts')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            cloud_pxy = user_session.proxy(cloud_module)

            with pytest.raises(Exception, message='User {} not authorised to create cloud account {}'.format(
                                                user, cloud_account.name)) as excinfo:
                logger.debug('User {} trying to create a cloud account {}'.format(user, cloud_account.name))
                cloud_pxy.replace_config(xpath, cloud_account)

            rift.auto.mano.close_session(user_session)

    @staticmethod
    def delete_descriptors(project, vnfd_proxy, nsd_proxy, vnfd_xpath, nsd_xpath, fmt_vnfd_id_xpath, fmt_nsd_id_xpath):
        nsds = nsd_proxy.get('{}/nsd'.format(nsd_xpath), list_obj=True)
        for nsd in nsds.nsd:
            xpath = fmt_nsd_id_xpath.format(project=quoted_key(project), nsd_id=quoted_key(nsd.id))
            nsd_proxy.delete_config(xpath)
        nsds = nsd_proxy.get('{}/nsd'.format(nsd_xpath), list_obj=True)
        assert nsds is None or len(nsds.nsd) == 0

        vnfds = vnfd_proxy.get('{}/vnfd'.format(vnfd_xpath), list_obj=True)
        for vnfd_record in vnfds.vnfd:
            xpath = fmt_vnfd_id_xpath.format(project=quoted_key(project), vnfd_id=quoted_key(vnfd_record.id))
            vnfd_proxy.delete_config(xpath)

        vnfds = vnfd_proxy.get('{}/vnfd'.format(vnfd_xpath), list_obj=True)
        assert vnfds is None or len(vnfds.vnfd) == 0

    @pytest.mark.skipif(not pytest.config.getoption("--onboarding-test"), reason="need --onboarding-test option to run")
    def test_onboarding_authorization(self, users_test_data, logger, descriptors, session_class, confd_host,
            fmt_vnfd_catalog_xpath, fmt_nsd_catalog_xpath, fmt_nsd_id_xpath, fmt_vnfd_id_xpath, project_acessible, mgmt_session):
        """Verifies only users with certain roles can onboard/update/delete a package"""

        descriptor_vnfds, descriptor_nsd = descriptors[:-1], descriptors[-1]
        write_users, read_users, fail_users = users_test_data
        logger.debug('The descriptrs being used: {}'.format(descriptors))
        nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(project_acessible))
        vnfd_xpath = fmt_vnfd_catalog_xpath.format(project=quoted_key(project_acessible))

        def onboard(user_session, project):
            for descriptor in descriptors:
                rift.auto.descriptor.onboard(user_session, descriptor, project=project)

        def verify_descriptors(vnfd_pxy, nsd_pxy, vnfd_count, nsd_count):
            catalog = vnfd_pxy.get_config(vnfd_xpath)
            actual_vnfds = catalog.vnfd
            assert len(actual_vnfds) == vnfd_count, 'There should be {} vnfds'.format(vnfd_count)
            catalog = nsd_pxy.get_config(nsd_xpath)
            actual_nsds = catalog.nsd
            assert len(actual_nsds) == nsd_count, 'There should be {} nsd'.format(nsd_count)

        # Check users in write_users dict able to onboard/delete descriptors
        logger.debug('Verifying users which are authorised to onboard/delete descriptors')
        for user in write_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, write_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, write_users[user][1])
            vnfd_pxy = user_session.proxy(RwProjectVnfdYang)
            nsd_pxy = user_session.proxy(RwProjectNsdYang)
            logger.debug('Trying to onboard ping-pong descriptors')
            onboard(user_session, project_acessible)
            logger.debug('Verifying if the descriptors are uploaded')
            verify_descriptors(vnfd_pxy, nsd_pxy, len(descriptor_vnfds), 1)

            logger.debug('Trying to delete descriptors')
            TestRbacVerification.delete_descriptors(project_acessible, vnfd_pxy, nsd_pxy, vnfd_xpath, nsd_xpath,
                                                    fmt_vnfd_id_xpath, fmt_nsd_id_xpath)

            rift.auto.mano.close_session(user_session)

        # onboard the descriptors using mgmt_session which read_users will try to read
        logger.debug('admin user uploading the descriptors which read_users will try to read')
        onboard(mgmt_session, project_acessible)
        admin_vnfd_pxy = mgmt_session.proxy(RwProjectVnfdYang)
        admin_nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
        logger.debug('Verifying if the descriptors are uploaded')
        verify_descriptors(admin_vnfd_pxy, admin_nsd_pxy, len(descriptor_vnfds), 1)

        # Check users in read_users dict able to read already onboarded descriptors
        logger.debug('Verifying users which are authorised to read descriptors')
        for user in read_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, read_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, read_users[user][1])
            vnfd_pxy = user_session.proxy(RwProjectVnfdYang)
            nsd_pxy = user_session.proxy(RwProjectNsdYang)

            logger.debug('Trying to read ping-pong descriptors')
            verify_descriptors(vnfd_pxy, nsd_pxy, len(descriptor_vnfds), 1)

            rift.auto.mano.close_session(user_session)

        # Check users in fail_users dict not able to onboard/delete descriptors
        logger.debug('Verifying users which are not supposed to delete descriptors')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            vnfd_pxy = user_session.proxy(RwProjectVnfdYang)
            nsd_pxy = user_session.proxy(RwProjectNsdYang)

            with pytest.raises(Exception, message='User {} not authorised to delete descriptors'.format(user)) as excinfo:
                logger.debug('User {} trying to delete descriptors'.format(user))
                TestRbacVerification.delete_descriptors(project_acessible, vnfd_pxy, nsd_pxy, vnfd_xpath, nsd_xpath,
                                                        fmt_vnfd_id_xpath, fmt_nsd_id_xpath)

            rift.auto.mano.close_session(user_session)

        logger.debug('Deleting the descriptors as fail_users trying to upload the descriptors')
        TestRbacVerification.delete_descriptors(project_acessible, admin_vnfd_pxy, admin_nsd_pxy, vnfd_xpath, nsd_xpath,
                                                fmt_vnfd_id_xpath, fmt_nsd_id_xpath)

        logger.debug('Verifying users which are not supposed to create descriptors')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            vnfd_pxy = user_session.proxy(RwProjectVnfdYang)
            nsd_pxy = user_session.proxy(RwProjectNsdYang)

            with pytest.raises(Exception, message='User {} not authorised to onboard descriptors'.format(user)) as excinfo:
                logger.debug('User {} trying to onboard ping-pong descriptors'.format(user))
                onboard(user_session)

            rift.auto.mano.close_session(user_session)

    @pytest.mark.skipif(not pytest.config.getoption("--nsr-test"),
                        reason="need --nsr-test option to run")
    def test_nsr_authorization(self, users_test_data, logger, cloud_account,
                               cloud_module, descriptors, session_class,
                               confd_host, fmt_cloud_xpath,
                               fmt_prefixed_cloud_xpath, mgmt_session, fmt_nsd_id_xpath, fmt_vnfd_id_xpath,
                               project_acessible, fmt_nsd_catalog_xpath, fmt_vnfd_catalog_xpath):
        """Verifies only users with certain roles can
        create/read/delete nsr/vlr/vnfr
        """

        descriptor_vnfds, descriptor_nsd = descriptors[:-1], descriptors[-1]
        write_users, read_users, fail_users = users_test_data

        # Cloud account creation
        logger.debug('Creating a cloud account which will be used for NS instantiation')
        cloud_pxy = mgmt_session.proxy(cloud_module)
        cloud_pxy.replace_config(fmt_prefixed_cloud_xpath.format(project=quoted_key(project_acessible),
                                                                 account_name=quoted_key(cloud_account.name)),
                                 cloud_account)
        response = cloud_pxy.get(
            fmt_cloud_xpath.format(project=quoted_key(project_acessible), account_name=quoted_key(cloud_account.name)))
        assert response.name == cloud_account.name

        cloud_pxy.wait_for(fmt_cloud_xpath.format(project=quoted_key(project_acessible), account_name=quoted_key(
            cloud_account.name)) + '/connection-status/status', 'success', timeout=30, fail_on=['failure'])

        # Upload the descriptors
        nsd_xpath = fmt_nsd_catalog_xpath.format(project=quoted_key(project_acessible))
        vnfd_xpath = fmt_vnfd_catalog_xpath.format(project=quoted_key(project_acessible))
        logger.debug('Uploading descriptors {} which will be used for NS instantiation'.format(descriptors))
        for descriptor in descriptors:
            rift.auto.descriptor.onboard(mgmt_session, descriptor, project=project_acessible)
        admin_nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
        nsd_catalog = admin_nsd_pxy.get_config(nsd_xpath)
        assert nsd_catalog
        nsd = nsd_catalog.nsd[0]
        nsr = rift.auto.descriptor.create_nsr(cloud_account.name, nsd.name, nsd)

        # Check users in write_users dict able to instantiate/delete a NS
        logger.debug('Verifying users which are authorised to instantiate/delete a NS')
        for user in write_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, write_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, write_users[user][1])
            rwnsr_pxy = user_session.proxy(RwNsrYang)
            rwvnfr_pxy = user_session.proxy(RwVnfrYang)
            rwvlr_pxy = user_session.proxy(RwVlrYang)

            logger.info("Trying to instantiate the Network Service")
            rift.auto.descriptor.instantiate_nsr(nsr, rwnsr_pxy, logger,
                                                 project=project_acessible)

            logger.info("Trying to terminate the Network Service")
            rift.auto.descriptor.terminate_nsr(rwvnfr_pxy, rwnsr_pxy,
                                               rwvlr_pxy, logger,
                                               project_acessible)

        # Instantiate a NS which the read_users, fail_users will try to
        # read/delete.
        admin_rwnsr_pxy = mgmt_session.proxy(RwNsrYang)
        admin_rwvnfr_pxy = mgmt_session.proxy(RwVnfrYang)
        admin_rwvlr_pxy = mgmt_session.proxy(RwVlrYang)
        logger.debug('admin user instantiating NS which the read_users, fail_users will try to read/delete.')
        rift.auto.descriptor.instantiate_nsr(nsr, admin_rwnsr_pxy, logger, project=project_acessible)

        # Check users in read_users, write_users dict able to read vnfr-console, vnfr-catalog, ns-instance-opdata
        p_xpath = '/project[name={}]'.format(quoted_key(project_acessible))
        read_xpaths = ['/ns-instance-opdata', '/vnfr-catalog', '/vnfr-console']
        logger.debug('Verifying users which are authorised to read vnfr-catalog, ns-instance-opdata, vnfr-console etc')
        for user, role_passwd_tuple in dict(write_users, **read_users).items():
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, role_passwd_tuple))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, role_passwd_tuple[1])
            rwnsr_pxy = user_session.proxy(RwNsrYang)
            rwvnfr_pxy = user_session.proxy(RwVnfrYang)
            for xpath in read_xpaths:
                logger.debug('Trying to read xpath: {}'.format(p_xpath+xpath))
                proxy_ = rwvnfr_pxy if 'vnfr' in xpath else rwnsr_pxy
                assert proxy_.get(p_xpath+xpath)

            rift.auto.mano.close_session(user_session)

        # Check users in fail_users dict not able to terminate a NS
        logger.debug('Verifying users which are NOT authorised to terminate a NS')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            rwnsr_pxy = user_session.proxy(RwNsrYang)
            rwvnfr_pxy = user_session.proxy(RwVnfrYang)

            with pytest.raises(Exception, message='User {} not authorised to terminate NS'.format(user)) as excinfo:
                logger.debug('User {} trying to delete NS'.format(user))
                rift.auto.descriptor.terminate_nsr(rwvnfr_pxy, rwnsr_pxy,
                                                   logger, admin_rwvlr_pxy,
                                                   project=project_acessible)
            rift.auto.mano.close_session(user_session)

        # Terminate the NS instantiated by admin user
        logger.debug('admin user terminating the NS')
        rift.auto.descriptor.terminate_nsr(admin_rwvnfr_pxy,
                                           admin_rwnsr_pxy,
                                           admin_rwvlr_pxy, logger,
                                           project=project_acessible)

        # Check users in fail_users dict not able to instantiate a NS
        nsr.id = str(uuid.uuid4())
        logger.debug('Verifying users which are NOT authorised to instantiate a NS')
        for user in fail_users:
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, fail_users[user]))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, fail_users[user][1])
            rwnsr_pxy = user_session.proxy(RwNsrYang)
            rwvnfr_pxy = user_session.proxy(RwVnfrYang)

            with pytest.raises(Exception, message='User {} not authorised to instantiate NS'.format(user)) as excinfo:
                logger.debug('User {} trying to instantiate NS'.format(user))
                rift.auto.descriptor.instantiate_nsr(nsr, rwnsr_pxy, logger, project=project_acessible)
            rift.auto.mano.close_session(user_session)

        # delete cloud accounts and descriptors; else deleting project in teardown fails
        cloud_pxy.delete_config(fmt_prefixed_cloud_xpath.format(project=quoted_key(project_acessible), 
                        account_name=quoted_key(cloud_account.name)))
        admin_vnfd_pxy = mgmt_session.proxy(RwProjectVnfdYang)
        TestRbacVerification.delete_descriptors(project_acessible, admin_vnfd_pxy, admin_nsd_pxy, vnfd_xpath, nsd_xpath,
                                                fmt_vnfd_id_xpath, fmt_nsd_id_xpath)

    @pytest.mark.skipif(not pytest.config.getoption("--syslog-server-test"), reason="need --syslog-server-test option to run")
    def test_set_syslog_server_authorization(self, mgmt_session, users_test_data, session_class, confd_host, logger):
        """Verifies only users with certain roles can set syslog server"""
        write_users, read_users, fail_users = users_test_data
        admin_log_mgmt_pxy = mgmt_session.proxy(RwlogMgmtYang)

        def update_syslog_server_address(user_log_mgmt_pxy):
            ip = '127.0.0.{}'.format(random.randint(0,255))
            sink_obj = RwlogMgmtYang.Logging_Sink.from_dict({'server_address': ip})

            syslog_name = admin_log_mgmt_pxy.get_config('/logging').sink[0].name
            logger.debug('updating the syslog {} server_address to {}'.format(syslog_name, ip))
            user_log_mgmt_pxy.merge_config('/logging/sink[name={sink_name}]'.format(sink_name=quoted_key(syslog_name)), sink_obj)
            assert [sink.server_address for sink in admin_log_mgmt_pxy.get_config('/logging').sink if sink.name == syslog_name][0] == ip

        for user, role_passwd_tuple in dict(write_users, **dict(read_users, **fail_users)).items():
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, role_passwd_tuple))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, role_passwd_tuple[1])
            user_log_mgmt_pxy = user_session.proxy(RwlogMgmtYang)

            if user in write_users:
                logger.debug('User {} should be able to update the syslog server address'.format(user))
                update_syslog_server_address(user_log_mgmt_pxy)

            if user in fail_users:
                with pytest.raises(Exception, message='User {} not authorised to set syslog server address'.format(user)) as excinfo:
                    logger.debug('User {} trying to update the syslog server address. It should fail'.format(user))
                    update_syslog_server_address(user_log_mgmt_pxy)

            if user in read_users:
                logger.debug('User {} trying to read the syslog server address'.format(user))
                logging_obj = user_log_mgmt_pxy.get_config('/logging')
                assert logging_obj.sink[0]
                assert logging_obj.sink[0].server_address

    @pytest.mark.skipif(not pytest.config.getoption("--redundancy-role-test"), reason="need --redundancy-role-test option to run")
    def test_redundancy_config_authorization(self, mgmt_session, users_test_data, session_class, confd_host, logger, redundancy_config_test_roles):
        """Verifies only users with certain roles can set redundancy-config or read redundancy-state"""
        write_users, read_users, fail_users = users_test_data
        admin_redundancy_pxy = mgmt_session.proxy(RwRedundancyYang)
        site_nm_pfx = 'ha_site_'

        def create_redundancy_site(user_redundancy_pxy, site_nm):
            site_id = '127.0.0.1'
            site_obj = RwRedundancyYang.YangData_RwRedundancy_RedundancyConfig_Site.from_dict({'site_name': site_nm, 'site_id': site_id})

            logger.debug('Creating redundancy site {}'.format(site_nm))
            user_redundancy_pxy.create_config('/rw-redundancy:redundancy-config/rw-redundancy:site', site_obj)
            assert [site.site_name for site in admin_redundancy_pxy.get_config('/redundancy-config/site', list_obj=True).site if site.site_name == site_nm]

        def delete_redundancy_site(user_redundancy_pxy, site_nm):
            logger.debug('Deleting redundancy site {}'.format(site_nm))
            user_redundancy_pxy.delete_config('/rw-redundancy:redundancy-config/rw-redundancy:site[rw-redundancy:site-name={}]'.format(quoted_key(site_nm)))
            assert not [site.site_name for site in admin_redundancy_pxy.get_config('/redundancy-config/site', list_obj=True).site if site.site_name == site_nm]

        # Create a redundancy site which fail user will try to delete/ read user will try to read
        create_redundancy_site(admin_redundancy_pxy, 'test_site')

        for user, role_passwd_tuple in dict(write_users, **dict(read_users, **fail_users)).items():
            logger.debug('Verifying user:(role,password) {}:{}'.format(user, role_passwd_tuple))
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, role_passwd_tuple[1])
            user_redundancy_pxy = user_session.proxy(RwRedundancyYang)
            
            if user in write_users:
                site_nm = '{}_{}'.format(site_nm_pfx, user)
                logger.debug('User {} should be able to create a new redundancy site {}'.format(user, site_nm))
                create_redundancy_site(user_redundancy_pxy, site_nm)

                logger.debug('User {} should be able to delete a redundancy site {}'.format(user, site_nm))
                delete_redundancy_site(user_redundancy_pxy, site_nm)
                
                assert user_redundancy_pxy.get('/redundancy-state')

            if user in fail_users:
                site_nm = '{}_{}'.format(site_nm_pfx, user)
                with pytest.raises(Exception, message='User {} not authorised to create redundancy site'.format(user)) as excinfo:
                    logger.debug('User {} trying to create redundancy site {}. It should fail'.format(user, site_nm))
                    create_redundancy_site(user_redundancy_pxy, site_nm)

                with pytest.raises(Exception, message='User {} not authorised to delete redundancy site'.format(user)) as excinfo:
                    logger.debug('User {} trying to delete redundancy site {}. It should fail'.format(user, site_nm))
                    delete_redundancy_site(user_redundancy_pxy, 'test_site')

            if user in read_users:
                logger.debug('User {} trying to read redundancy-config'.format(user))
                assert user_redundancy_pxy.get('/redundancy-state')
                assert user_redundancy_pxy.get('/redundancy-config')


@pytest.mark.depends('test_rbac_roles_setup')
@pytest.mark.teardown('test_rbac_roles_setup')
@pytest.mark.incremental
class TestRbacTeardown(object):
    def test_delete_project(self, rw_project_proxy, logger, project_keyed_xpath, project_acessible):
        """Deletes projects used for the test"""
        if rw_project_proxy.get_config(project_keyed_xpath.format(project_name=quoted_key(project_acessible))+'/project-state', list_obj=True):
            logger.debug('Deleting project {}'.format(project_acessible))
            rift.auto.mano.delete_project(rw_project_proxy, project_acessible)

    def test_delete_users(self, users_test_data, logger, rw_user_proxy, rbac_platform_proxy, platform_config_keyed_xpath,
                                    user_keyed_xpath, user_domain, rw_conman_proxy, project_acessible):
        """Deletes the users which are part of rbac test-data and verify their deletion"""
        write_users, read_users, fail_users = users_test_data

        for user, role_passwd_tuple in dict(write_users, **dict(read_users, **fail_users)).items():
            logger.debug('Deleting user:(role,password) {}:{}'.format(user, role_passwd_tuple))
            if any('platform' in role for role in role_passwd_tuple[0]):
                rbac_platform_proxy.delete_config(platform_config_keyed_xpath.format(user=quoted_key(user), domain=quoted_key(user_domain)))
            rw_user_proxy.delete_config(user_keyed_xpath.format(user=quoted_key(user), domain=quoted_key(user_domain)))

            # Verify if the user is deleted
            user_config = rw_user_proxy.get_config('/user-config')
            current_users_list = [user.user_name for user in user_config.user]

            assert user not in current_users_list

        # Verify only two users should be present now: oper & admin
        user_config = rw_user_proxy.get_config('/user-config')
        current_users_list = [user.user_name for user in user_config.user]

        logger.debug('Current users list after deleting all test users: {}'.format(current_users_list))
        expected_empty_user_list = [user for user in users_test_data if user in current_users_list]
        assert not expected_empty_user_list
