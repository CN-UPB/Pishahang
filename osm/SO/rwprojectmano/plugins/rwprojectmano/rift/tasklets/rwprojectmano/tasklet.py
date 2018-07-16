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
Mano Project Manager tasklet is responsible for managing the Projects
configurations required for Role Based Access Control feature.
"""

import asyncio

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwLog', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwProjectManoYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    RwLog as rwlog,
    RwProjectYang,
    RwProjectManoYang,
)

import rift.tasklets

from rift.tasklets.rwidmgr.rbac import (
    RbacNotification,
)

from rift.mano.utils.project import (
    ManoProject,
    )

from .projectmano import (
    ProjectHandler,
    ProjectStateRolePublisher,
)

from .rolesmano import (
    ProjectMgrManoRoleConfigPublisher,
    ProjectConfigSubscriber,
)


class ProjectMgrManoProject(ManoProject):

    def __init__(self, name, tasklet):
        super(ProjectMgrManoProject, self).__init__(tasklet.log, name)
        self.update(tasklet)

        self.project_sub = ProjectConfigSubscriber(self)

    @asyncio.coroutine
    def register (self):
        self._log.info("Initializing the ProjectMgrMano for %s", self.name)
        yield from self.project_sub.register()
        self.tasklet.project_state_role_pub.publish_roles(self.name)

    def deregister(self):
        self._log.info("De-register project %s", self.name)
        self.tasklet.project_state_role_pub.unpublish_roles(self.name)
        self.project_sub.deregister()


class ProjectMgrManoTasklet(rift.tasklets.Tasklet):
    """Tasklet that manages the Project config
    """
    def __init__(self, *args, **kwargs):
        """Constructs a ProjectManager tasklet"""
        try:
            super().__init__(*args, **kwargs)
            self.rwlog.set_category("rw-mano-log")
            self.notify = RbacNotification(self)

            self.projects = {}

        except Exception as e:
            self.log.exception(e)


    def start(self):
        """Callback that gets invoked when a Tasklet is started"""
        super().start()
        self.log.info("Starting Mano Project Manager Tasklet")

        self.log.debug("Registering with dts")
        self.dts = rift.tasklets.DTS(
                self.tasklet_info,
                RwProjectManoYang.get_schema(),
                self.loop,
                self.on_dts_state_change
                )

        self.log.debug("Created DTS Api Object: %s", self.dts)

    def stop(self):
        """Callback that gets invoked when Tasklet is stopped"""
        try:
            self.dts.deinit()
        except Exception as e:
            self.log.exception(e)

    @asyncio.coroutine
    def init(self):
        """DTS Init state handler"""
        try:
            self.log.info("Registering for Project Config")
            self.project_handler = ProjectHandler(self, ProjectMgrManoProject)
            self.project_handler.register()

            self.project_state_role_pub = ProjectStateRolePublisher(self)
            yield from self.project_state_role_pub.register()

        except Exception as e:
            self.log.exception("Registering for project failed: {}".format(e))

    @asyncio.coroutine
    def run(self):
        """DTS run state handler"""
        pass

    @asyncio.coroutine
    def on_dts_state_change(self, state):
        """Handle DTS state change

        Take action according to current DTS state to transition application
        into the corresponding application state

        Arguments
            state - current dts state

        """
        switch = {
            rwdts.State.INIT: rwdts.State.REGN_COMPLETE,
            rwdts.State.CONFIG: rwdts.State.RUN,
        }

        handlers = {
            rwdts.State.INIT: self.init,
            rwdts.State.RUN: self.run,
        }

        # Transition application to next state
        handler = handlers.get(state, None)
        if handler is not None:
            yield from handler()

        # Transition dts to next state
        next_state = switch.get(state, None)
        if next_state is not None:
            self.dts.handle.set_state(next_state)

    def config_ready(self):
        """Subscription is complete and ready to start publishing."""
        self.log.debug("Configuration Ready")


# vim: ts=4 sw=4 et
