"""
#
#   Copyright 2016 RIFT.IO Inc
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

@file rwstagingmgr.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 28-Sep-2016

"""

import asyncio

import tornado
import tornado.httpserver
import tornado.httputil
import tornado.platform.asyncio
import tornadostreamform.multipart_streamer as multipart_streamer

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwStagingMgmtYang', '1.0')
gi.require_version('rwlib', '1.0')

from gi.repository import (
        RwDts as rwdts,
        RwStagingMgmtYang)
import rift.tasklets
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
)
import gi.repository.rwlib as rwlib

from . import rpc
from . import store
from .server import StagingApplication
from .publisher import StagingStorePublisher


class StagingManagerProject(ManoProject):

    def __init__(self, name, tasklet, **kw):
        super(StagingManagerProject, self).__init__(tasklet.log, name)
        self.update(tasklet)

        self.publisher = StagingStorePublisher(self)
        # For recovery
        self.publisher.delegate = tasklet.store

    @asyncio.coroutine
    def register (self):
        yield from self.publisher.register()

    def deregister(self):
        self.publisher.deregister()


class StagingManagerTasklet(rift.tasklets.Tasklet):
    """Tasklet to handle all staging related operations
    """
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            self._project_handler = None
            self.projects = {}

        except Exception as e:
            self.log.exception("Staging Manager tasklet init: {}".
                               format(e))

    def start(self):
        super().start()

        self.log.debug("Registering with dts")

        self.dts = rift.tasklets.DTS(
                self.tasklet_info,
                RwStagingMgmtYang.get_schema(),
                self.loop,
                self.on_dts_state_change
                )

    def stop(self):
        try:
            self.dts.deinit()
        except Exception as e:
            self.log.exception(e)

    @asyncio.coroutine
    def init(self):
        self.store = store.StagingFileStore(self)

        io_loop = rift.tasklets.tornado.TaskletAsyncIOLoop(asyncio_loop=self.loop)
        self.app = StagingApplication(self.store, self.loop)

        manifest = self.tasklet_info.get_pb_manifest()
        ssl_cert = manifest.bootstrap_phase.rwsecurity.cert
        ssl_key = manifest.bootstrap_phase.rwsecurity.key
        ssl_options = {"certfile": ssl_cert, "keyfile": ssl_key}

        if manifest.bootstrap_phase.rwsecurity.use_ssl:
            self.server = tornado.httpserver.HTTPServer(
                self.app,
                max_body_size=self.app.MAX_BODY_SIZE,
                io_loop=io_loop,
                ssl_options=ssl_options)
        else:
            self.server = tornado.httpserver.HTTPServer(
                self.app,
                max_body_size=self.app.MAX_BODY_SIZE,
                io_loop=io_loop,
            )

        self.create_stg_rpc = rpc.StagingAreaCreateRpcHandler(
                self.log,
                self.dts,
                self.loop,
                self.store)
        yield from self.create_stg_rpc.register()

        self.log.debug("creating project handler")
        self.project_handler = ProjectHandler(self, StagingManagerProject)
        self.project_handler.register()

    @asyncio.coroutine
    def run(self):
        address = rwlib.getenv("RWVM_INTERNAL_IPADDR")
        if (address is None):
            address=""
        self.server.listen(self.app.PORT, address=address)
        self.server.listen(self.app.PORT, address="127.0.0.1")

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
