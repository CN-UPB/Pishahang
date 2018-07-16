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
gi.require_version('RwProjectManoYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    ProtobufC,
    RwTypes,
    RwProjectManoYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.tasklets
from rift.mano.utils.project import (
    NS_PROJECT,
    get_add_delete_update_cfgs,
    ProjectConfigCallbacks,
)


MANO_PROJECT_ROLES = [
    { 'mano-role':"rw-project-mano:catalog-oper",
      'description':("The catalog-oper Role has read permission to nsd-catalog "
                     "and vnfd-catalog under specific Projects, "
                     "as identified by /rw-project:project/rw-project:name.  The "
                     "catatlog-oper Role may also have execute permission to specific "
                     "non-mutating RPCs.  This Role is intended for read-only access to "
                     "catalogs under a specific project.") },

    { 'mano-role':"rw-project-mano:catalog-admin",
      'description':("The catalog-admin Role has full CRUDX permissions to vnfd and nsd "
                     "catalogs under specific Projects, as identified by "
                     "/rw-project:project/rw-project:name.") },

    { 'mano-role':"rw-project-mano:lcm-oper",
      'description':("The lcm-oper Role has read permission to the VL, VNF and NS "
                     "records within a Project.  The lcm-oper Role may also have "
                     "execute permission to specific non-mutating RPCs.") },

    { 'mano-role':"rw-project-mano:lcm-admin",
      'description':("The lcm-admin Role has full CRUDX permissions to the VL, VNF "
                     "and NS records within a Project.  The lcm-admin Role does "
                     "not provide general CRUDX permissions to the Project as a whole, "
                     "nor to the RIFT.ware platform in general.") },

    { 'mano-role':"rw-project-mano:account-admin",
      'description':("The account-admin Role has full CRUDX permissions to the VIM, SDN, VCA "
                     "and RO accounts within a Project.  The account-admin Role does "
                     "not provide general CRUDX permissions to the Project as a whole, "
                     "nor to the RIFT.ware platform in general.") },
    
    { 'mano-role':"rw-project-mano:account-oper",
      'description':("The account-oper Role has read permission to the VIM, SDN, VCA "
                     "and RO accounts within a Project.  The account-oper Role may also have "
                     "execute permission to specific non-mutating RPCs.") },
]


class ProjectDtsHandler(object):
    XPATH = "C,/{}".format(NS_PROJECT)

    def __init__(self, dts, log, callbacks):
        self._dts = dts
        self._log = log
        self._callbacks = callbacks

        self.reg = None
        self.projects = []

    @property
    def log(self):
        return self._log

    @property
    def dts(self):
        return self._dts

    def get_reg_flags(self):
        return (rwdts.Flag.SUBSCRIBER  | 
                rwdts.Flag.DELTA_READY | 
                rwdts.Flag.CACHE       | 
                rwdts.Flag.DATASTORE)

    def add_project(self, cfg):
        name = cfg.name
        self._log.info("Adding project: {}".format(name))

        if name not in self.projects:
            self._callbacks.on_add_apply(name, cfg)
            self.projects.append(name)
        else:
            self._log.error("Project already present: {}".
                           format(name))

    def delete_project(self, name):
        self._log.info("Deleting project: {}".format(name))
        if name in self.projects:
            self._callbacks.on_delete_apply(name)
            self.projects.remove(name)
        else:
            self._log.error("Unrecognized project: {}".
                           format(name))

    def update_project(self, cfg):
        """ Update an existing project

        Currently, we do not take any action on MANO for this,
        so no callbacks are defined

        Arguments:
            msg - The project config message
        """
        name = cfg.name
        self._log.info("Updating project: {}".format(name))
        if name in self.projects:
            pass
        else:
            self._log.error("Unrecognized project: {}".
                           format(name))

    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, scratch):
            self._log.debug("Got project apply config (xact: %s) (action: %s)", xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.info("Project {} being re-added after restart.".
                                       format(cfg.name))
                        self.add_project(cfg)
                else:
                    self._log.debug("No xact handle.  Skipping apply config")

                return

            add_cfgs, delete_cfgs, update_cfgs = get_add_delete_update_cfgs(
                    dts_member_reg=self._reg,
                    xact=xact,
                    key_name="name",
                    )

            # Handle Deletes
            for cfg in delete_cfgs:
                self.delete_project(cfg.name)

            # Handle Adds
            for cfg in add_cfgs:
                self.add_project(cfg)

            # Handle Updates
            for cfg in update_cfgs:
                self.update_project(cfg)

            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for Project """

            action = xact_info.query_action
            name = msg.name

            self._log.debug("Project %s on_prepare config received (action: %s): %s",
                            name, xact_info.query_action, msg)

            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                if name in self.projects:
                    self._log.debug("Project {} already exists. Ignore request".
                                    format(name))

                else:
                    self._log.debug("Project {}: Invoking on_prepare add request".
                                    format(name))
                    rc, err_msg = yield from self._callbacks.on_add_prepare(name, msg)
                    if rc is False:
                        xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                                   ProjectDtsHandler.XPATH,
                                                   err_msg)
                        xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                        return

            elif action == rwdts.QueryAction.DELETE:
                # Check if the entire project got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    if name in self.projects:
                        rc, delete_msg = yield from self._callbacks.on_delete_prepare(name)
                        if not rc:
                            self._log.error("Project {} should not be deleted. Reason : {}".
                                            format(name, delete_msg))

                            xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           ProjectDtsHandler.XPATH,
                                           delete_msg)
                            
                            xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                            return
                    else:
                        self._log.warning("Delete on unknown project: {}".
                                          format(name))

            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._log.debug("Registering for project config using xpath: %s",
                        ProjectDtsHandler.XPATH)

        acg_handler = rift.tasklets.AppConfGroup.Handler(
            on_apply=apply_config,
        )

        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                xpath=ProjectDtsHandler.XPATH,
                flags=self.get_reg_flags(),
                on_prepare=on_prepare,
            )


class ProjectHandler(object):
    def __init__(self, tasklet, project_class):
        self._tasklet = tasklet
        self._log = tasklet.log
        self._log_hdl = tasklet.log_hdl
        self._dts = tasklet.dts
        self._loop = tasklet.loop
        self._class = project_class

        self.mano_roles = [role['mano-role'] for role in MANO_PROJECT_ROLES]

        self._log.debug("Creating project config handler")
        self.project_cfg_handler = ProjectDtsHandler(
            self._dts, self._log,
            ProjectConfigCallbacks(
                on_add_apply=self.on_project_added,
                on_add_prepare=self.on_add_prepare,
                on_delete_apply=self.on_project_deleted,
                on_delete_prepare=self.on_delete_prepare,
            )
        )

    def _get_tasklet_name(self):
        return self._tasklet.tasklet_info.instance_name

    def _get_project(self, name):
        try:
            proj = self._tasklet.projects[name]
        except Exception as e:
            self._log.exception("Project {} ({})not found for tasklet {}: {}".
                                format(name, list(self._tasklet.projects.keys()),
                                       self._get_tasklet_name(), e))
            raise e

        return proj

    def on_project_deleted(self, name):
        self._log.debug("Project {} deleted".format(name))
        try:
            self._get_project(name).deregister()
        except Exception as e:
            self._log.exception("Project {} deregister for {} failed: {}".
                                format(name, self._get_tasklet_name(), e))

        try:
            proj = self._tasklet.projects.pop(name)
            del proj
        except Exception as e:
            self._log.exception("Project {} delete for {} failed: {}".
                                format(name, self._get_tasklet_name(), e))

    def on_project_added(self, name, cfg):
        if name not in self._tasklet.projects:
            try:
                self._tasklet.projects[name] = \
                                self._class(name, self._tasklet)
                self._loop.create_task(self._get_project(name).register())

            except Exception as e:
                self._log.exception("Project {} create for {} failed: {}".
                                    format(name, self._get_tasklet_name(), e))
                raise e

        self._log.debug("Project {} added to tasklet {}".
                        format(name, self._get_tasklet_name()))
        self._get_project(name)._apply = True

    @asyncio.coroutine
    def on_add_prepare(self, name, msg):
        self._log.debug("Project {} to be added to {}".
                        format(name, self._get_tasklet_name()))

        if name in self._tasklet.projects:
            err_msg = ("Project already exists: {}".
                       format(name))
            self._log.error(err_msg)
            return False, err_msg

        # Validate mano-roles, if present
        try:
            cfg = msg.project_config
            users = cfg.user
            for user in users:
                for role in user.mano_role:
                    if role.role not in self.mano_roles:
                        err_msg = ("Invalid role {} for user {} in project {}".
                               format(role.role, user.user_name, name))
                        self._log.error(err_msg)
                        return False, err_msg

        except AttributeError as e:
            # If the user or mano role is not present, ignore
            self._log.debug("Project {}: {}".format(name, e))

        return True, ""

    @asyncio.coroutine
    def on_delete_prepare(self, name):
        self._log.error("Project {} being deleted for tasklet {}".
                        format(name, self._get_tasklet_name()))
        rc, delete_msg = yield from self._get_project(name).delete_prepare()
        return (rc, delete_msg)

    def register(self):
        self.project_cfg_handler.register()


class ProjectStateRolePublisher(rift.tasklets.DtsConfigPublisher):

    def __init__(self, tasklet):
        super().__init__(tasklet)
        self.proj_state = RwProjectManoYang.YangData_RwProject_Project_ProjectState()
        self.projects = set()
        self.roles = MANO_PROJECT_ROLES

    def get_xpath(self):
        return "D,/rw-project:project/rw-project:project-state/rw-project-mano:mano-role"

    def get_reg_flags(self):
        return super().get_reg_flags() | rwdts.Flag.DATASTORE

    def role_xpath(self, project, role):
        return "/rw-project:project[rw-project:name={}]".format(quoted_key(project)) + \
            "/rw-project:project-state/rw-project-mano:mano-role" + \
            "[rw-project-mano:role={}]".format(quoted_key(role['mano-role']))

    def pb_role(self, role):
        pbRole = self.proj_state.create_mano_role()
        pbRole.role = role['mano-role']
        pbRole.description = role['description']
        return pbRole

    def publish_roles(self, project):
        if not project in self.projects:
            self.projects.add(project)
            for role in self.roles:
                xpath = self.role_xpath(project, role)
                pb_role = self.pb_role(role)
                self.log.debug("publishing xpath:{}".format(xpath))
                self._regh.update_element(xpath, pb_role)

    def unpublish_roles(self, project):
        if project in self.projects:
            self.projects.remove(project)
            for role in self.roles:
                xpath = self.role_xpath(project, role)
                self.log.debug("unpublishing xpath:{}".format(xpath))
                self._regh.delete_element(xpath)

