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

@file rwmonparam.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 01-Jul-2016

"""

import asyncio

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')

from gi.repository import (
        RwDts as rwdts,
        RwLaunchpadYang,
        NsrYang,
        ProtobufC)
import rift.mano.cloud
import rift.mano.dts as subscriber
import rift.tasklets
import concurrent.futures
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
    )
from . import vnfr_core
from . import nsr_core


class MonParamProject(ManoProject):

    def __init__(self, name, tasklet, **kw):
        super(MonParamProject, self).__init__(tasklet.log, name)
        self.update(tasklet)

        self.vnfr_subscriber = None

        self.vnfr_monitors = {}
        self.nsr_monitors = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Needs to be moved to store once the DTS bug is resolved
        # Gather all VNFRs
        self.vnfrs = {}

        self.vnfr_subscriber = subscriber.VnfrCatalogSubscriber.from_project(
                self,
                callback=self.handle_vnfr)
        self.nsr_subsriber = subscriber.NsrCatalogSubscriber.from_project(
                self,
                callback=self.handle_nsr)

        self._nsd_subscriber = subscriber.NsdCatalogSubscriber.from_project(self)
        self._vnfd_subscriber = subscriber.VnfdCatalogSubscriber.from_project(self)

        self.log.debug("Created DTS Api GI Object: %s", self.dts)

    @asyncio.coroutine
    def register (self):
        self.log.debug("creating vnfr subscriber")
        yield from self._nsd_subscriber.register()
        yield from self._vnfd_subscriber.register()
        yield from self.vnfr_subscriber.register()
        yield from self.nsr_subsriber.register()


    def deregister(self):
        self.log.debug("De-register vnfr project {}".format(self.name))
        self._nsd_subscriber.deregister()
        self._vnfd_subscriber.deregister()
        self.vnfr_subscriber.deregister()
        self.nsr_subsriber.deregister()

    def _unwrap(self, values, id_name):
        try:
            return values[0]
        except KeyError:
            self.log.exception("Unable to find the object with the given "
                "ID {}".format(id_name))

    def get_vnfd(self, vnfd_id):
        values = [vnfd for vnfd in list(self._vnfd_subscriber.reg.get_xact_elements()) if vnfd.id == vnfd_id]
        return self._unwrap(values, vnfd_id)

    def get_nsd(self, nsd_id):
        values = [nsd for nsd in list(self._nsd_subscriber.reg.get_xact_elements()) if nsd.id == nsd_id]
        return self._unwrap(values, nsd_id)


    def handle_vnfr(self, vnfr, action):
        """Starts a monitoring parameter job for every VNFR that reaches
        running state

        Args:
            vnfr (GiOBject): VNFR Gi object message from DTS
            delete_mode (bool, optional): if set, stops and removes the monitor.
        """

        def vnfr_create():
            # if vnfr.operational_status == "running" and vnfr.id not in self.vnfr_monitors:
            vnfr_status = (vnfr.operational_status == "running" and
                           vnfr.config_status in ["configured", "config_not_needed"])

            if vnfr_status and vnfr.id not in self.vnfr_monitors:

                vnf_mon = vnfr_core.VnfMonitorDtsHandler.from_vnf_data(
                        self,
                        vnfr,
                        self.get_vnfd(vnfr.vnfd.id))

                self.vnfr_monitors[vnfr.id] = vnf_mon
                self.vnfrs[vnfr.id] = vnfr

                @asyncio.coroutine
                def task():
                    yield from vnf_mon.register()
                    if vnfr.nsr_id_ref in self.nsr_monitors:
                        vnf_mon.update_nsr_mon(self.nsr_monitors[vnfr.nsr_id_ref])
                    vnf_mon.start()
                    #self.update_nsrs(vnfr, action)

                self.loop.create_task(task())


        def vnfr_delete():
            if vnfr.id in self.vnfr_monitors:
                self.log.debug("VNFR %s deleted: Stopping vnfr monitoring", vnfr.id)
                vnf_mon = self.vnfr_monitors.pop(vnfr.id)
                vnf_mon.stop()
                self.vnfrs.pop(vnfr.id)
                #self.update_nsrs(vnfr, action)

        if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
            vnfr_create()
        elif action == rwdts.QueryAction.DELETE:
            vnfr_delete()

    def update_nsrs(self, vnfr, action):
        if vnfr.nsr_id_ref not in self.nsr_monitors:
            return

        monitor = self.nsr_monitors[vnfr.nsr_id_ref]

        if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
            @asyncio.coroutine
            def update_vnfr():
                yield from monitor.update([vnfr])

            self.loop.create_task(update_vnfr())
        elif action == rwdts.QueryAction.DELETE:
            @asyncio.coroutine
            def delete_vnfr():
                try:
                    yield from monitor.delete([vnfr])
                except Exception as e:
                    self.log.exception(str(e))

            self.loop.create_task(delete_vnfr())



    def handle_nsr(self, nsr, action):
        """Callback for NSR opdata changes. Creates a publisher for every
        NS that moves to config state.

        Args:
            nsr (RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr): Ns Opdata
            action (rwdts.QueryAction): Action type of the change.
        """

        def nsr_create():
            # TODO clean up the if-else mess, exception

            success_state = (nsr.operational_status == "running" and
                    nsr.config_status == "configured")

            if not success_state:
                return

            if nsr.ns_instance_config_ref in self.nsr_monitors:
                return

            constituent_vnfrs = []

            for vnfr_id in nsr.constituent_vnfr_ref:
                if (vnfr_id.vnfr_id in self.vnfrs):
                    vnfr_obj = self.vnfrs[vnfr_id.vnfr_id]
                    constituent_vnfrs.append(vnfr_obj)
                else:
                    pass

            nsr_mon = nsr_core.NsrMonitorDtsHandler(
                self.log,
                self.dts,
                self.loop,
                self,
                nsr,
                constituent_vnfrs
            )
            for vnfr_id in nsr.constituent_vnfr_ref:
                if vnfr_id.vnfr_id in self.vnfr_monitors:
                     self.vnfr_monitors[vnfr_id.vnfr_id].update_nsr_mon(nsr_mon)

            self.nsr_monitors[nsr.ns_instance_config_ref] = nsr_mon


            @asyncio.coroutine
            def task():
                try:
                    yield from nsr_mon.register()
                    yield from nsr_mon.start()
                except Exception as e:
                    self.log.exception(e)

            self.loop.create_task(task())

        def nsr_delete():
            if nsr.ns_instance_config_ref in self.nsr_monitors:
                nsr_mon = self.nsr_monitors.pop(nsr.ns_instance_config_ref)
                nsr_mon.stop()

        if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
            nsr_create()
        elif action == rwdts.QueryAction.DELETE:
            nsr_delete()


class MonitoringParameterTasklet(rift.tasklets.Tasklet):
    """The main task of this Tasklet is to listen for VNFR changes and once the
    VNFR hits the running state, triggers the monitor.
    """
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            self.rwlog.set_category("rw-monitor-log")
        except Exception as e:
            self.log.exception(e)

        self._project_handler = None
        self.projects = {}

    def start(self):
        super().start()

        self.log.info("Starting MonitoringParameterTasklet")
        self.log.debug("Registering with dts")

        self.dts = rift.tasklets.DTS(
                self.tasklet_info,
                NsrYang.get_schema(),
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
        self.log.debug("creating project handler")
        self.project_handler = ProjectHandler(self, MonParamProject)
        self.project_handler.register()

    @asyncio.coroutine
    def run(self):
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
