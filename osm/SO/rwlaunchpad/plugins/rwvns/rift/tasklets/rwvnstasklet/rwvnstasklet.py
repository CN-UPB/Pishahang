
#
#   Copyright 2016-2017 RIFT.IO Inc
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

import asyncio
import sys

import gi
gi.require_version('RwVnsYang', '1.0')
gi.require_version('RwDts', '1.0')
from gi.repository import (
    RwVnsYang,
    RwDts as rwdts,
    RwTypes,
)

import rift.tasklets
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
)
import rift.mano.sdn

from rift.vlmgr import (
    VlrDtsHandler,
    VldDtsHandler,
    VirtualLinkRecord,
    VirtualLinkEventListener
)

from rift.topmgr import (
    NwtopStaticDtsHandler,
    NwtopDiscoveryDtsHandler,
    NwtopDataStore,
)


class VlRecordError(Exception):
    """ Vlr Record creation Error """
    pass


class VlRecordNotFound(Exception):
    """ Vlr Record not found"""
    pass


class SDNAccountHandlers(object):
    def __init__(self, dts, log, log_hdl, acctstore, loop, project):
        self._log = log
        self._log_hdl = log_hdl
        self._dts = dts
        self._loop = loop
        self._acctstore = acctstore
        self._project = project
  
        self._log.debug("Creating SDN account config handler")
        self.sdn_cfg_handler = rift.mano.sdn.SDNAccountConfigSubscriber(
              self._dts, self._log, project, self._log_hdl,
              rift.mano.sdn.SDNAccountConfigCallbacks(
                  on_add_apply=self.on_sdn_account_added,
                  on_delete_apply=self.on_sdn_account_deleted,
              ),
              self._acctstore

        )
  
        self._log.debug("Creating SDN account opdata handler")
        self.sdn_operdata_handler = rift.mano.sdn.SDNAccountDtsOperdataHandler(
              self._dts, self._log, self._loop, project,
        )
  
    def on_sdn_account_deleted(self, account_name):
        self._log.debug("SDN account deleted")
        self.sdn_operdata_handler.delete_sdn_account(account_name)
  
    def on_sdn_account_added(self, account):
        self._log.debug("SDN account added")
        self.sdn_operdata_handler.add_sdn_account(account)
  
    @asyncio.coroutine
    def register(self):
        self.sdn_cfg_handler.register()
        yield from self.sdn_operdata_handler.register()

    def deregister(self):
        self.sdn_cfg_handler.deregister()
        self.sdn_operdata_handler.deregister()


class VnsManager(object):
    """ The Virtual Network Service Manager """
    def __init__(self, dts, log, log_hdl, loop, project):
        self._dts = dts
        self._log = log
        self._log_hdl = log_hdl
        self._loop = loop
        self._project = project
        self._acctstore = {}
        self._vlr_handler = VlrDtsHandler(dts, log, loop, self)
        self._vld_handler = VldDtsHandler(dts, log, loop, self)
        self._sdn_handlers = SDNAccountHandlers(dts, log, log_hdl, self._acctstore, loop, self._project)
        self._nwtopdata_store = NwtopDataStore(log)
        self._nwtopdiscovery_handler = NwtopDiscoveryDtsHandler(dts, log, loop, project,
                                                                self._acctstore, self._nwtopdata_store)
        self._nwtopstatic_handler = NwtopStaticDtsHandler(dts, log, loop, project,
                                                          self._acctstore, self._nwtopdata_store)
        self._vl_event_listener = VirtualLinkEventListener(dts, log, loop, self)
        self._vlrs = {}

    @asyncio.coroutine
    def register_vlr_handler(self):
        """ Register vlr DTS handler """
        self._log.debug("Registering  DTS VLR handler")
        yield from self._vlr_handler.register()

    @asyncio.coroutine
    def register_vld_handler(self):
        """ Register vlr DTS handler """
        self._log.debug("Registering  DTS VLD handler")
        yield from self._vld_handler.register()

    @asyncio.coroutine
    def register_sdn_handlers(self):
        """ Register SDN DTS handlers """
        self._log.debug("Registering  SDN Account handlers")
        yield from self._sdn_handlers.register()

    @asyncio.coroutine
    def register_nwtopstatic_handler(self):
        """ Register static NW topology DTS handler """
        self._log.debug("Registering  static DTS NW topology handler")
        yield from self._nwtopstatic_handler.register()

    @asyncio.coroutine
    def register_nwtopdiscovery_handler(self):
        """ Register discovery-based NW topology DTS handler """
        self._log.debug("Registering  discovery-based DTS NW topology handler")
        yield from self._nwtopdiscovery_handler.register()

    @asyncio.coroutine
    def register_vl_event_listener(self):
        """ Register Virtual Link related events DTS handler """
        self._log.debug("Registering  Virtual Link Event listener")
        yield from self._vl_event_listener.register()

    @asyncio.coroutine
    def register(self):
        """ Register all static DTS handlers"""
        yield from self.register_sdn_handlers()
        yield from self.register_vlr_handler()
        yield from self.register_vld_handler()
        yield from self.register_nwtopstatic_handler()
        yield from self.register_nwtopdiscovery_handler()
        yield from self.register_vl_event_listener()

    def deregister(self):
        self._vl_event_listener.deregister()
        self._nwtopdiscovery_handler.deregister()
        self._nwtopstatic_handler.deregister()
        self._vld_handler.deregister()
        self._vlr_handler.deregister()
        self._sdn_handlers.deregister()

    def create_vlr(self, msg):
        """ Create VLR """
        if msg.id in self._vlrs:
            err = "Vlr id %s already exists" % msg.id
            self._log.error(err)
            # raise VlRecordError(err)
            return self._vlrs[msg.id]

        self._log.info("Creating VirtualLinkRecord %s", msg.id)
        self._vlrs[msg.id] = VirtualLinkRecord(self._dts,
                                               self._log,
                                               self._loop,
                                               self,
                                               msg,
                                               )
        return self._vlrs[msg.id]

    def get_vlr(self, vlr_id):
        """  Get VLR by vlr id """
        return self._vlrs[vlr_id]

    @asyncio.coroutine
    def delete_vlr(self, vlr_id, xact):
        """ Delete VLR with the passed id"""
        if vlr_id not in self._vlrs:
            err = "Delete Failed - Vlr id %s not found" % vlr_id
            self._log.error(err)
            raise VlRecordNotFound(err)

        self._log.info("Deleting virtual link id %s", vlr_id)
        yield from self._vlrs[vlr_id].terminate(xact)
        del self._vlrs[vlr_id]
        self._log.info("Deleted virtual link id %s", vlr_id)

    def find_vlR_by_vld_id(self, vld_id):
        """ Find a VLR matching the VLD Id """
        for vlr in self._vlrs.values():
            if vlr.vld_id == vld_id:
                return vlr
        return None

    @asyncio.coroutine
    def run(self):
        """ Run this VNSM instance """
        self._log.debug("Run VNSManager - registering static DTS handlers")
        yield from self.register()

    def vld_in_use(self, vld_id):
        """ Is this VLD in use """
        return False

    @asyncio.coroutine
    def publish_vlr(self, xact, xpath, msg):
        """ Publish a VLR """
        path = self._project.add_project(xpath)
        self._log.debug("Publish vlr called with path %s, msg %s",
                        path, msg)
        yield from self._vlr_handler.update(xact, path, msg)

    @asyncio.coroutine
    def unpublish_vlr(self, xact, xpath):
        """ Publish a VLR """
        path = self._project.add_project(xpath)
        self._log.debug("Unpublish vlr called with path %s", path)
        yield from self._vlr_handler.delete(xact, path)

    def create_virual_link_event(self, event_id, event_msg):
        """ Update Virtual Link Event """
        self._log.debug("Creating Virtual Link Event id [%s], msg [%s]",
                       event_id, event_msg)

    @asyncio.coroutine
    def update_virual_link_event(self, event_id, event_msg):
        """ Update Virtual Link Event """
        self._log.debug("Updating Virtual Link Event id [%s], msg [%s]",
                        event_id, event_msg)
        # event id and vlr_id are the same.
        # Use event id to look up the VLR and update and publish state change
        vlr = None

        if event_id in self._vlrs:
            vlr = self._vlrs[event_id]

        if vlr is None:
            self._log.error("Received VLR Event notifcation for unknown VLR - event-id:%s",
                            event_id)
            return

        if event_msg.resource_info.resource_state == 'active':
            with self._dts.transaction(flags=0) as xact:
                yield from vlr.ready(event_msg, xact)
        elif event_msg.resource_info.resource_state == 'failed':
            with self._dts.transaction(flags=0) as xact:
                if event_msg.resource_info.resource_errors:
                    vlr._state_failed_reason = str(event_msg.resource_info.resource_errors)
                yield from vlr.failed(event_msg, xact)
        else:
            self._log.warning("Receieved unknown resource state %s for event id %s vlr:%s",
                              event_msg.resource_info.resource_state, event_id, vlr.name)

    def delete_virual_link_event(self, event_id):
        """ Delete Virtual Link Event """
        self._log.debug("Deleting Virtual Link Event id [%s]",
                        event_id)


class VnsProject(ManoProject):

    def __init__(self, name, tasklet, **kw):
        super(VnsProject, self).__init__(tasklet.log, name)
        self.update(tasklet)

        self._vlr_handler = None
        self._vnsm = None
        # A mapping of instantiated vlr_id's to VirtualLinkRecord objects
        self._vlrs = {}

    @asyncio.coroutine
    def register (self):
        try:
            self._vnsm = VnsManager(dts=self._dts,
                                    log=self.log,
                                    log_hdl=self.log_hdl,
                                    loop=self.loop,
                                    project=self)
            yield from self._vnsm.run()
        except Exception as e:
            self.log.exception("VNS Task failed to run", e)

    def deregister(self):
        self._log.debug("De-register project {}".format(self.name))
        self._vnsm.deregister()


class VnsTasklet(rift.tasklets.Tasklet):
    """ The VNS tasklet class """
    def __init__(self, *args, **kwargs):
        super(VnsTasklet, self).__init__(*args, **kwargs)
        self.rwlog.set_category("rw-mano-log")
        self.rwlog.set_subcategory("vns")

        self._dts = None
        self._project_handler = None
        self.projects = {}

    @property
    def dts(self):
        return self._dts

    def start(self):
        super(VnsTasklet, self).start()
        self.log.info("Starting VnsTasklet")

        self.log.debug("Registering with dts")
        try:
            self._dts = rift.tasklets.DTS(self.tasklet_info,
                                          RwVnsYang.get_schema(),
                                          self.loop,
                                          self.on_dts_state_change)
        except Exception:
            self.log.exception("Caught Exception in VNS start:", e)

        self.log.debug("Created DTS Api GI Object: %s", self._dts)

    def on_instance_started(self):
        """ The task instance started callback"""
        self.log.debug("Got instance started callback")

    def stop(self):
      try:
         self._dts.deinit()
      except Exception:
         print("Caught Exception in VNS stop:", sys.exc_info()[0])
         raise

    @asyncio.coroutine
    def init(self):
        """ task init callback"""
        self.log.debug("creating project handler")
        self.project_handler = ProjectHandler(self, VnsProject)
        self.project_handler.register()

    @asyncio.coroutine
    def run(self):
        """ tasklet run callback """
        pass

    @asyncio.coroutine
    def on_dts_state_change(self, state):
        """Take action according to current dts state to transition
        application into the corresponding application state

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
            self._dts.handle.set_state(next_state)
