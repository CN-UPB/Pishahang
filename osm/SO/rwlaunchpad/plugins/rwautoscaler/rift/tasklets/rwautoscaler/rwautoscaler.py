"""
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

@file rwautoscaler.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 01-Jul-2016

"""
import asyncio
import collections

from . import engine
from . import subscribers as monp_subscriber

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('NsrYang', '1.0')

from gi.repository import (
        RwDts as rwdts,
        NsrYang,
        RwLaunchpadYang,
        ProtobufC)
import rift.mano.cloud
import rift.mano.dts as subscriber
import rift.tasklets
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
    )

class AutoScalerProject(ManoProject, engine.ScalingPolicy.Delegate):

    def __init__(self, name, tasklet, **kw):
        super(AutoScalerProject, self).__init__(tasklet.log, name)
        self.update(tasklet)

        self.store = None
        self.monparam_store = None
        self.nsr_sub = None
        self.nsr_monp_subscribers = {}
        self.instance_id_store = collections.defaultdict(list)

        self.store = subscriber.SubscriberStore.from_project(self)
        self.nsr_sub = subscriber.NsrCatalogSubscriber(self.log, self.dts, self.loop,
                                                       self, self.handle_nsr)

    def deregister(self):
        self.log.debug("De-register project {}".format(self.name))
        self.nsr_sub.deregister()
        self.store.deregister()


    @asyncio.coroutine
    def register (self):
        self.log.debug("creating vnfr subscriber")
        yield from self.store.register()
        yield from self.nsr_sub.register()

    def scale_in(self, scaling_group_name, nsr_id, instance_id):
        """Delegate callback

        Args:
            scaling_group_name (str): Scaling group name to be scaled in
            nsr_id (str): NSR id
            instance_id (str): Instance id of the scaling group

        """
        self.log.info("Sending a scaling-in request for {} in NSR: {}".format(
                scaling_group_name,
                nsr_id))

        @asyncio.coroutine
        def _scale_in():

            # Purposely ignore passed instance_id
            instance_id_ = self.instance_id_store[(scaling_group_name, nsr_id)].pop()
            # Trigger an rpc
            rpc_ip = NsrYang.YangInput_Nsr_ExecScaleIn.from_dict({
                'project_name': self.name,
                'nsr_id_ref': nsr_id,
                'instance_id': instance_id_,
                'scaling_group_name_ref': scaling_group_name})

            rpc_out = yield from self.dts.query_rpc(
                        "/nsr:exec-scale-in",
                        0,
                        rpc_ip)

        # Check for existing scaled-out VNFs if any.
        if len(self.instance_id_store):
            self.loop.create_task(_scale_in())

    def scale_out(self, scaling_group_name, nsr_id):
        """Delegate callback for scale out requests

        Args:
            scaling_group_name (str): Scaling group name
            nsr_id (str): NSR ID
        """
        self.log.info("Sending a scaling-out request for {} in NSR: {}".format(
                scaling_group_name,
                nsr_id))

        @asyncio.coroutine
        def _scale_out():
            # Trigger an rpc
            rpc_ip = NsrYang.YangInput_Nsr_ExecScaleOut.from_dict({
                'project_name': self.name,
                'nsr_id_ref': nsr_id ,
                'scaling_group_name_ref': scaling_group_name})

            itr = yield from self.dts.query_rpc("/nsr:exec-scale-out", 0, rpc_ip)

            key = (scaling_group_name, nsr_id)
            for res in itr:
                result = yield from res
                rpc_out = result.result
                self.instance_id_store[key].append(rpc_out.instance_id)

                self.log.info("Created new scaling group {} with instance id {}".format(
                        scaling_group_name,
                        rpc_out.instance_id))

        self.loop.create_task(_scale_out())


    def handle_nsr(self, nsr, action):
        """Callback for NSR opdata changes. Creates a publisher for every
        NS that moves to config state.

        Args:
            nsr (RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr): Ns Opdata
            action (rwdts.QueryAction): Action type of the change.
        """
        def nsr_create():
            if nsr.config_status == "configured" and nsr.ns_instance_config_ref not in self.nsr_monp_subscribers:
                nsr_id = nsr.ns_instance_config_ref
                self.nsr_monp_subscribers[nsr_id] = []
                nsd = self.store.get_nsd(nsr.nsd_ref)
                self.log.debug ("Creating a scaling policy monitor for NSR: {}".format(
                    nsr_id))

                @asyncio.coroutine
                def task():
                    for scaling_group in nsd.scaling_group_descriptor:
                        for policy_cfg in scaling_group.scaling_policy:
                            policy = engine.ScalingPolicy(
                                self.log, self.dts, self.loop, self,
                                nsr.ns_instance_config_ref,
                                nsr.nsd_ref,
                                scaling_group.name,
                                policy_cfg,
                                self.store,
                                delegate=self)
                            self.nsr_monp_subscribers[nsr_id].append(policy)
                            yield from policy.register()
                    self.log.debug ("Started a scaling policy monitor for NSR: {}".format(
                        nsr_id))


                self.loop.create_task(task())


        def nsr_delete():
            if nsr.ns_instance_config_ref in self.nsr_monp_subscribers:
                policies = self.nsr_monp_subscribers[nsr.ns_instance_config_ref]
                for policy in policies:
                    policy.deregister()
                del self.nsr_monp_subscribers[nsr.ns_instance_config_ref]
                self.log.debug ("Deleted the scaling policy monitor for NSD: {}".format(
                    nsr.ns_instance_config_ref))


        if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
            nsr_create()
        elif action == rwdts.QueryAction.DELETE:
            nsr_delete()


class AutoScalerTasklet(rift.tasklets.Tasklet):
    """The main task of this Tasklet is to listen for NSR changes and once the
    NSR is configured, ScalingPolicy is created.
    """
    def __init__(self, *args, **kwargs):

        try:
            super().__init__(*args, **kwargs)
            self.rwlog.set_category("rw-mano-log")

            self._project_handler = None
            self.projects = {}

        except Exception as e:
            self.log.exception(e)

    def start(self):
        super().start()

        self.log.debug("Registering with dts")

        self.dts = rift.tasklets.DTS(
                self.tasklet_info,
                RwLaunchpadYang.get_schema(),
                self.loop,
                self.on_dts_state_change
                )

        self.log.debug("Created DTS Api GI Object: %s", self.dts)

    def stop(self):
        try:
            self.dts.deinit()
        except Exception as e:
            self.log.exception(e)

    @asyncio.coroutine
    def init(self):
        self.log.debug("creating project handler")
        self.project_handler = ProjectHandler(self, AutoScalerProject)
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

