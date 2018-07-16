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
# Author(s): Varun Prasad
# Creation Date: 09/25/2016
#

import asyncio
import gi
import uuid

from gi.repository import (RwDts as rwdts)
import rift.mano.dts as mano_dts
import rift.tasklets
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from ..protocol import StagingStoreProtocol

class StagingStorePublisher(mano_dts.DtsHandler, StagingStoreProtocol):

    def __init__(self, project):
        super().__init__(project.log, project.dts, project.loop, project)
        self.delegate = None

    def xpath(self, area_id=None):
        return self.project.add_project("D,/rw-staging-mgmt:staging-areas/rw-staging-mgmt:staging-area" +
                                        ("[area-id={}]".format(quoted_key(area_id)) if area_id else ""))

    @asyncio.coroutine
    def register(self):
        # we need a dummy callback for recovery to work
        @asyncio.coroutine
        def on_event(dts, g_reg, xact, xact_event, scratch_data):
            if xact_event == rwdts.MemberEvent.INSTALL:
                if self.delegate:
                    self.delegate.on_recovery(self.reg.elements)

            return rwdts.MemberRspCode.ACTION_OK

        hdl = rift.tasklets.DTS.RegistrationHandler()
        handlers = rift.tasklets.Group.Handler(on_event=on_event)
        with self.dts.group_create(handler=handlers) as group:
            self.reg = group.register(xpath=self.xpath(),
                                        handler=hdl,
                                        flags=(rwdts.Flag.PUBLISHER |
                                               rwdts.Flag.NO_PREP_READ |
                                               rwdts.Flag.CACHE |
                                               rwdts.Flag.DATASTORE),)

        assert self.reg is not None

    def deregister(self):
        self._log.debug("Project {}: de-register staging store handler".
                        format(self._project.name))
        if self.reg:
            self.reg.deregister()

    def on_staging_area_create(self, store):
        self.reg.update_element(self.xpath(store.area_id), store)

    def on_staging_area_delete(self, store):
        self.reg.update_element(self.xpath(store.area_id), store)

    def stop(self):
        self.deregister()

    def deregister(self):
        """ de-register with dts """
        if self.reg is not None:
            self.reg.deregister()
            self.reg = None
