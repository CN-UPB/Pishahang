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

from rift.auto.session import NetconfSession, RestconfSession
import rift.auto.mano

gi.require_version('RwUserYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwRbacPlatformYang', '1.0')
gi.require_version('RwRbacInternalYang', '1.0')
from gi.repository import (
    RwUserYang,
    RwProjectYang,
    RwRbacPlatformYang,
    RwRbacInternalYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

@pytest.fixture(scope='session')
def rbac_test_data():
    """Fixture which returns rbac test data: users, roles, projects being used in the test.
    users: tuple of user names
    projects: tuple of project names
    map_platform_roles: mapping of a user to multiple platform roles
    map_project_roles: mapping of a user to multiple projects (project, list of roles in that project)"""
    users = ('admin3', 'user1', 'user2', )

    projects = ('project1', 'project2', )

    map_platform_roles = {
                            'admin3': ['rw-rbac-platform:platform-admin'],
                            }

    map_project_roles = {
                            'user1': [
                                        ('project1', ['rw-project:project-admin']),
                                        ('project2', ['rw-project:project-oper']),
                                     ], 

                            'user2': [
                                        ('project1', ['rw-project:project-admin']),
                                     ], 

                            'admin3': [],
                            }

    return {'users': users, 'projects': projects, 'roles': (map_platform_roles, map_project_roles)}


@pytest.mark.setup('rbac_setup')
@pytest.mark.incremental
class TestRbacSetup(object):
    def test_create_users(self, rbac_test_data, rw_user_proxy, user_domain, rbac_user_passwd, logger):
        """Creates all users as per rbac test-data  and verify if they are successfully created."""
        users_test_data =  rbac_test_data['users']

        # Create all users mentioned in users_test_data
        for user in users_test_data:
            rift.auto.mano.create_user(rw_user_proxy, user, rbac_user_passwd, user_domain)

        # Verify users are created
        user_config = rw_user_proxy.get_config('/user-config')
        assert user_config

        user_config_test_data = [user.user_name for user in user_config.user if user.user_name in users_test_data]
        logger.debug('Users: {} have been successfully created'.format(user_config_test_data))

        assert len(user_config_test_data) == len(users_test_data)

    def test_create_projects(self, logger, rw_conman_proxy, rbac_test_data):
        """Creates all projects as per rbac test-data and verify them."""
        projects_test_data = rbac_test_data['projects']

        # Create all projects mentioned in projects_test_data and verify if they are created
        for project in projects_test_data:
            logger.debug('Creating project {}'.format(project))
            rift.auto.mano.create_project(rw_conman_proxy, project)

    def test_assign_platform_roles_to_users(self, rbac_platform_proxy, logger, rbac_test_data, user_domain, rw_rbac_int_proxy):
        """Assign platform roles to an user as per test data mapping and verify them."""
        platform_roles_test_data, _ = rbac_test_data['roles']

        # Loop through the user & platform-roles mapping and assign roles to the user
        for user, roles in platform_roles_test_data.items():
            for role in roles:
                rift.auto.mano.assign_platform_role_to_user(rbac_platform_proxy, role, user, user_domain, rw_rbac_int_proxy)

        # Verify if the roles are assigned as per test data mapping
        platform_config = rbac_platform_proxy.get_config('/rbac-platform-config')

        platform_config_test_data_match = 0
        logger.debug('Matching platform_roles_test_data with rbac-platform-config')
        for user in platform_config.user:
            if user.user_name in platform_roles_test_data:
                logger.debug('Matched user: {}'.format(user.as_dict()))
                platform_config_test_data_match += 1

                test_data_user_platform_roles = platform_roles_test_data[user.user_name]
                assert len(test_data_user_platform_roles) == len(user.role)
                assert len(test_data_user_platform_roles) == len([role for role in user.role if role.role in test_data_user_platform_roles])

        assert platform_config_test_data_match == len(platform_roles_test_data)

    def test_assign_users_to_projects_roles(self, rbac_test_data, rw_project_proxy, user_domain, rw_rbac_int_proxy):
        """Assign projects and roles to an user as per test data mapping."""
        _, project_roles_test_data = rbac_test_data['roles']

        # Loop through the user & (project, role) mapping and asign the project, role to the user
        for user, project_role_tuple in project_roles_test_data.items():
            for project, role_list in project_role_tuple:
                for role in role_list:
                    rift.auto.mano.assign_project_role_to_user(rw_project_proxy, role, user, project, user_domain, rw_rbac_int_proxy)


@pytest.mark.depends('rbac_setup')
@pytest.mark.incremental
class TestRbacVerification(object):
    def test_match_rbac_internal(self, mgmt_session, logger, rbac_test_data):
        """Verifies the test data with rw-rbac-internal"""
        rbac_intl_proxy = mgmt_session.proxy(RwRbacInternalYang)
        rbac_intl = rbac_intl_proxy.get('/rw-rbac-internal')

        # Verify users in show rw-rbac-internal
        users_test_data =  rbac_test_data['users']
        assert len(rbac_intl.user) == len(users_test_data) + 2   # 'admin', 'oper' are two default users
        users_match = 0
        for user in rbac_intl.user:
            if user.user_name in users_test_data:
                logger.info('User matched: {}'.format(user.as_dict()))
                users_match += 1
        assert users_match == len(users_test_data)

        # Verify roles (only project roles mapping, not the platform roles mapping)
        # Each role in rw-rbac-internal is associated with a project through the field 'keys'. All mapping from users to project 
        # is part of project roles mapping.
        _, project_roles_test_data = rbac_test_data['roles']
        for user, project_role_tuple in project_roles_test_data.items():
            for project, role_list in project_role_tuple:
                for role in role_list:
                    logger.debug("Matching user: '{}' and its role '{}' in project '{}'".format(user, role, project))
                    
                    # Verify there exists a role entry in rw-rbac-internal which matches 'role', 'project'
                    rbac_intl_role = [role_ for role_ in rbac_intl.role if (role_.role==role and role_.keys==project)]

                    # Each role is identified through its key 'project'. So there can be only one such role which matches 
                    # the above 'role.role==role and role.keys=project'
                    assert len(rbac_intl_role) == 1
                    logger.info('Matched role in rw-rbac-internal: {}'.format(rbac_intl_role[0].as_dict()))

                    # Verify the user list in this rw-rbac-internal role carries 'user'
                    assert len([user_ for user_ in rbac_intl_role[0].user if user_.user_name==user]) == 1

    def test_role_access(self, logger, session_class, confd_host, rbac_test_data, rbac_user_passwd, project_keyed_xpath):
        """Verifies the roles assigned to users for a project. Login as each user and verify the user can only access 
        the projects linked to it."""
        _, project_roles_test_data = rbac_test_data['roles']
        projects_test_data = rbac_test_data['projects']

        for user, project_role_tuple in project_roles_test_data.items():
            logger.debug('Verifying user: {}'.format(user))
            projects_not_accessible = list(projects_test_data)

            # Establish a session with this current user
            user_session = rift.auto.mano.get_session(session_class, confd_host, user, rbac_user_passwd)
            print ("Connected using username {} password {}".format(user, rbac_user_passwd))

            rw_project_proxy_ = user_session.proxy(RwProjectYang)
            
            if project_role_tuple:  # Skip the for loop for users who are not associated with any project e.g admin3
                for project, role_list in project_role_tuple:
                    projects_not_accessible.remove(project)
                    project_config = rw_project_proxy_.get_config(project_keyed_xpath.format(project_name=quoted_key(project))+'/project-config')
                    user_ = [user_ for user_ in project_config.user if user_.user_name==user]
                    logger.debug('User: {}'.format(user_[0].as_dict()))
                    assert len(user_) == 1

                    # Match the roles for this user
                    assert set(role_list) == set([role_.role for role_ in user_[0].role])

            # It can't access any other project.
            for project in projects_not_accessible:
                assert rw_project_proxy_.get_config(project_keyed_xpath.format(project_name=quoted_key(project))+'/project-config') is None # It should 
                # return None as the project is not mapped to this user.

    def test_admin_user(self, logger, rw_project_proxy, project_keyed_xpath, rbac_test_data):
        """Verify admin can see all projects as part of test-data as well as the default project"""
        projects_test_data = rbac_test_data['projects']
        projects_test_data = projects_test_data + ('default', )

        # Verify admin user can see all projects including default
        # If it is post-reboot verification, then check default project should not be listed
        for project in projects_test_data:
            project_ = rw_project_proxy.get_config(project_keyed_xpath.format(project_name=quoted_key(project))+'/project-state', list_obj=True)
            if project=='default' and pytest.config.getoption('--default-project-deleted'):
                assert project_ is None
                continue
            assert project_     # If the project doesn't exist, it returns None


@pytest.mark.depends('rbac_setup')
@pytest.mark.teardown('rbac_setup')
@pytest.mark.incremental
class TestRbacTeardown(object):
    def test_delete_default_project(self, logger, rw_conman_proxy):
        """Only deletes the default project"""
        logger.debug('Deleting the default project')
        rift.auto.mano.delete_project(rw_conman_proxy, 'default')
    
    def test_delete_projects(self, logger, rbac_test_data, rw_conman_proxy):
        """Deletes the projects which are part of rbac test-data and verify their deletion"""
        projects_test_data = rbac_test_data['projects']

        # Delete the projects
        for project in projects_test_data:
            logger.debug('Deleting project {}'.format(project))
            rift.auto.mano.delete_project(rw_conman_proxy, project)

    def test_delete_users(self, logger, rw_user_proxy, rbac_platform_proxy, platform_config_keyed_xpath, 
                                    user_keyed_xpath, rbac_test_data, user_domain):
        """Deletes the users which are part of rbac test-data and verify their deletion"""
        users_test_data = rbac_test_data['users']
        map_platform_roles, _ = rbac_test_data['roles']

        # Deletes the users
        # If an user is associated with a platform role, at first it needs be removed from rbac-platform-config
        # before deleting it from user-config
        for user in users_test_data:
            if user in map_platform_roles:
                rbac_platform_proxy.delete_config(platform_config_keyed_xpath.format(user=quoted_key(user), domain=quoted_key(user_domain)))
            rw_user_proxy.delete_config(user_keyed_xpath.format(user=quoted_key(user), domain=quoted_key(user_domain)))

        # Verify if the users are deleted
        user_config = rw_user_proxy.get_config('/user-config')
        default_users = [user.user_name for user in user_config.user]

        logger.debug('Default users list: {}'.format(default_users))
        expected_empty_user_list = [user for user in users_test_data if user in default_users]
        assert not expected_empty_user_list
