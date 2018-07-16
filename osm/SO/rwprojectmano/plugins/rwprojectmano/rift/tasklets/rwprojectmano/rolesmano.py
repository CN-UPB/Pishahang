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
Project Manager tasklet is responsible for managing the Projects
configurations required for Role Based Access Control feature.
"""

import asyncio
import gi

gi.require_version('RwDts', '1.0')
gi.require_version('RwRbacInternalYang', '1.0')
gi.require_version('RwProjectManoYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    ProtobufC,
    RwTypes,
    RwRbacInternalYang,
    RwProjectManoYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.tasklets
from rift.tasklets.rwidmgr.rbac import (
    StateMachine,
    User,
    UserState,
    RoleKeys,
    RoleKeysUsers,
    encode_role_instance_key,
)
from rift.mano.utils.project import (
    NS_PROJECT,
    get_add_delete_update_cfgs,
)


from .projectmano import MANO_PROJECT_ROLES


class ProjectConfigSubscriber(object):
    """Config subscriber for rw-user config"""

    def __init__(self, project):
        self.project_name = project.name
        self._log = project.log
        self._dts = project.dts

        self.users = {}
        self.pub = ProjectMgrManoRoleConfigPublisher(project)
        self.proj_roles = [role['mano-role'] for role in MANO_PROJECT_ROLES]

    def get_xpath(self):
        return "C,/{}[name={}]/project-config/user".format(NS_PROJECT, quoted_key(self.project_name))

    def get_reg_flags(self):
        return (rwdts.Flag.SUBSCRIBER  | 
                rwdts.Flag.DELTA_READY | 
                rwdts.Flag.CACHE       |
                rwdts.Flag.DATASTORE)

    def role_inst(self, role, keys=None):
        if not keys:
            keys = encode_role_instance_key(self.project_name)

        r = RoleKeys()
        r.role = role.role
        r.keys = keys
        return r

    def delete_user(self, cfg):
        user = User().pb(cfg)
        self._log.info("Delete user {} for project {}".
                        format(user.key, self.project_name))
        if user.key in self.users:
            roles = self.users[user.key]
            for role_key in list(roles):
                self.delete_role(user, role_key)
            self.users.pop(user.key)

    def update_user(self, cfg):
        user = User().pb(cfg)
        self._log.debug("Update user {} for project {} cfg {}".
                        format(user.key, self.project_name, cfg))
        cfg_roles = {}
        for cfg_role in cfg.mano_role:
            r = self.role_inst(cfg_role)
            cfg_roles[r.key] = r

        if not user.key in self.users:
            self.users[user.key] = set()
        else:
            #Check if any roles are deleted for the user
            for role_key in list(self.users[user.key]):
                    if role_key not in cfg_roles:
                        self.delete_role(user, role_key)

        for role_key in cfg_roles.keys():
            if role_key not in self.users[user.key]:
                self.update_role(user, cfg_roles[role_key])

    def delete_role(self, user, role_key):
        self._log.info("Delete role {} for user {}".
                        format(role_key, user.key))
        user_key = user.key

        try:
            roles = self.users[user_key]
        except KeyError:
            roles = set()
            self.users[user.key] = roles

        if role_key in roles:
            roles.remove(role_key)
            self.pub.delete_role(role_key, user_key)

    def update_role(self, user, role):
        self._log.debug("Update role {} for user {}".
                        format(role.role, user.key))

        user_key = user.key

        try:
            roles = self.users[user.key]
        except KeyError:
            roles = set()
            self.users[user_key] = roles

        role_key = role.key

        if not role_key in roles:
            roles.add(role_key)
            self.pub.add_update_role(role_key, user_key)

    def delete_project(self):
        # Clean up rw-rbac-intenal
        self._log.error("Project {} delete".format(self.project_name))
        for user_key, roles in self.users.items():
            for role_key in roles:
                self._log.error("delete role {} for user {}".format(role_key, user_key))
                self.pub.delete_role(user_key, role_key)

    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, scratch):
            self._log.debug("Got user apply config (xact: %s) (action: %s)",
                            xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.info("Project {} user being restored: {}.".
                                       format(self.project_name, cfg.as_dict()))
                        self.update_user(cfg)
                else:
                    # When RIFT first comes up, an INSTALL is called with the current config
                    # Since confd doesn't actally persist data this never has any data so
                    # skip this for now.
                    self._log.debug("No xact handle.  Skipping apply config")

                return

            # TODO: There is user-name and user-domain as keys. Need to fix
            # this
            add_cfgs, delete_cfgs, update_cfgs = get_add_delete_update_cfgs(
                    dts_member_reg=self._reg,
                    xact=xact,
                    key_name="user_name",
                    )

            self._log.debug("Added: {}, Deleted: {}, Modified: {}".
                            format(add_cfgs, delete_cfgs, update_cfgs))
            # Handle Deletes
            for cfg in delete_cfgs:
                self.delete_user(cfg)

            # Handle Adds
            for cfg in add_cfgs:
                self.update_user(cfg)

            # Handle Updates
            for cfg in update_cfgs:
                self.update_user(cfg)

            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for Project """

            action = xact_info.query_action

            self._log.debug("Project %s on_prepare config received (action: %s): %s",
                            self.project_name, xact_info.query_action, msg)

            user = User().pb(msg)
            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                if user.key in self.users:
                    self._log.debug("User {} update request".
                                    format(user.key))

                else:
                    self._log.debug("User {}: on_prepare add request".
                                    format(user.key))

                for role in msg.mano_role:
                    if role.role not in self.proj_roles:
                        errmsg = "Invalid MANO role {} for user {}". \
                                 format(role.role, user.key)
                        self._log.error(errmsg)
                        xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                                   self.get_xpath(),
                                                   errmsg)
                        xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                        return

            elif action == rwdts.QueryAction.DELETE:
                # Check if the user got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    if user.key in self.users:
                        self._log.debug("User {} being deleted".format(user.key))
                    else:
                        self._log.warning("Delete on unknown user: {}".
                                          format(user.key))

                try:
                    xact_info.respond_xpath(rwdts.XactRspCode.ACK)
                except rift.tasklets.dts.ResponseError as e:
                    xpath = ks_path.to_xpath(RwProjectManoYang.get_schema())
                    self._log.debug("Exception sending response for {}: {}".
                                    format(xpath, e))
                return

            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self.get_xpath()
        self._log.debug("Registering for project config using xpath: %s",
                        xpath,
                        )

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                    xpath=xpath,
                    flags=self.get_reg_flags(),
                    on_prepare=on_prepare,
                    )

        yield from self.pub.register()
        self.pub.create_project_roles()

    def deregister(self):
        self._log.debug("De-registering DTS handler for project {}".
                        format(self.project_name))

        if self._reg:
            self._reg.deregister()
            self._reg = None

        self.pub.delete_project_roles()
        self.pub.deregister()

class ProjectMgrManoRoleConfigPublisher(rift.tasklets.DtsConfigPublisher):

    def __init__(self, project):
        super().__init__(project._tasklet)
        self.project_name = project.name
        self.notify = project._tasklet.notify
        self.rbac_int = RwRbacInternalYang.YangData_RwRbacInternal_RwRbacInternal()
        self.roles = {}
        self.proj_roles = [role['mano-role'] for role in MANO_PROJECT_ROLES]
        self.proj_roles_published = False

    def get_xpath(self):
        return "D,/rw-rbac-internal:rw-rbac-internal/rw-rbac-internal:role"

    def get_reg_flags(self):
        return super().get_reg_flags() | rwdts.Flag.DATASTORE

    def role_xpath(self, role_key):
        return "D,/rw-rbac-internal:rw-rbac-internal/rw-rbac-internal:role" + \
            "[rw-rbac-internal:role={}]".format(quoted_key(role_key[0])) + \
            "[rw-rbac-internal:keys={}]".format(quoted_key(role_key[1]))

    def role_user_xpath(self, role_key, user_key):
        return self.role_xpath(role_key) + \
            "/rw-rbac-internal:user" + \
            "[rw-rbac-internal:user-name={}]".format(quoted_key(user_key[0])) + \
            "[rw-rbac-internal:user-domain={}]".format(quoted_key(user_key[1]))

    def pb_role(self, role, user):
        pbRole = self.rbac_int.create_role()
        pbRole.role = role.role
        pbRole.keys = role.keys
        pbRole.state_machine.state = role.state.name

        pbUser = pbRole.create_user()
        pbUser.user_name = user.user_name
        pbUser.user_domain = user.user_domain
        pbUser.state_machine.state = user.state.name

        pbRole.user.append(pbUser)

        return pbRole

    def pb_project_role(self, role):
        pbRole = self.rbac_int.create_role()
        pbRole.role = role.role
        pbRole.keys = role.keys
        pbRole.state_machine.state = role.state.name
        return pbRole

    def add_update_role(self, role_key, user_key):
        try:
            role = self.roles[role_key]
        except KeyError:
            role = RoleKeysUsers(role_key)
            self.roles[role_key] = role

        try:
            user = role.user(user_key)
        except KeyError:
            user = UserState(user_key)
            role.add_user(user)

        user.state = StateMachine.new

        xpath = self.role_xpath(role_key)
        self.log.debug("add/update role: {} user: {} ".format(role_key, user_key))

        pb_role = self.pb_role(role, user)
        self._regh.update_element(xpath, pb_role)

        event_desc = "Role '{}' with key '{}' assigned to user '{}' in domain '{}'". \
                     format(role.role, role.keys, user.user_name, user.user_domain)
        self.notify.send_event("role-assigned", event_desc)

    def delete_role(self, role_key, user_key):
        try:
            role = self.roles[role_key]
            user = role.user(user_key)
        except KeyError:
            self.log.error("delete_role: invalid role/user {}/{}".format(role_key, user_key))
            return

        user.state = StateMachine.delete
        xpath = self.role_xpath(role_key)
        self.log.debug("deleting role: {} user: {}".format(role_key, user_key))

        pb_role = self.pb_role(role, user)
        self._regh.update_element(xpath, pb_role)

        event_desc = "Role '{}' with key '{}' unassigned from user '{}' in domain '{}'". \
                     format(role.role, role.keys, user.user_name, user.user_domain)
        self.notify.send_event("role-unassigned", event_desc)

    def create_project_roles(self):
        for name in self.proj_roles:
            role = RoleKeys()
            role.role = name
            role.keys = encode_role_instance_key(self.project_name)
            self.create_project_role(role)

    def create_project_role(self, role):
        role_key = role.key
        try:
            role = self.roles[role_key]
            # already exist
            return
        except KeyError:
            role = RoleKeysUsers(role_key)
            self.roles[role_key] = role
            
        xpath = self.role_xpath(role.key)

        pb_role = self.pb_project_role(role)

        # print("create_project_role path:{} role:{}".format(xpath, pb_role))
        self._regh.update_element(xpath, pb_role)

    def delete_project_roles(self):
        for name in self.proj_roles:
            role = RoleKeys()
            role.role = name
            role.keys = encode_role_instance_key(self.project_name)
            self.delete_project_role(role)

    def delete_project_role(self, role):
        xpath = self.role_xpath(role.key)

        self._regh.delete_element(xpath)

    def do_prepare(self, xact_info, action, ks_path, msg):
        """Handle on_prepare.  To be overridden by Concreate Publisher Handler
        """
        role_key = tuple([msg.role, msg.keys])
        try:
            role = self.roles[role_key]
        except KeyError:
            xact_info.respond_xpath(rwdts.XactRspCode.NA)
            return

        self.log.debug("do_prepare (MANO-ROLES): action: {}, path: {}, msg: {}".format(action, ks_path, msg))
        xact_info.respond_xpath(rwdts.XactRspCode.ACK)
        xpath = self.role_xpath(role_key)

        if msg.state_machine.state == 'init_done':
            msg.state_machine.state = 'active'
            role.state = StateMachine.active
            self._regh.update_element(xpath, msg)
        elif msg.state_machine.state == 'delete_done':
            self._regh.delete_element(xpath)
            del self.roles[role_key]
            # deleted at role level, skip processing users under it
            return

        if msg.user:
            for pbUser in msg.user:
                user_key = tuple([pbUser.user_name, pbUser.user_domain])
                try:
                    user = role.user(user_key)
                except KeyError:
                    self._log.debug("**** User {} not found".format(user_key))
                    continue
                user_xpath = self.role_user_xpath(role_key, user_key)
                state = pbUser.state_machine.state
                if state == 'init_done':
                    pbUser.state_machine.state = 'active'
                    user.state = StateMachine.active
                    self._regh.update_element(xpath, msg)
                elif state == 'delete_done':
                    role.delete_user(user)
                    self._regh.delete_element(user_xpath)

    def deregister(self):
        if self.reg:
            self.delete_project_roles()
            super().deregister()
