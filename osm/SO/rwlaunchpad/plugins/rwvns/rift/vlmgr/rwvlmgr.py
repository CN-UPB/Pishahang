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

import asyncio
import enum
import gi
import time
import uuid

gi.require_version('RwVlrYang', '1.0')
gi.require_version('RwDts', '1.0')
gi.require_version('RwResourceMgrYang', '1.0')
from gi.repository import (
    RwVlrYang,
    VldYang,
    RwDts as rwdts,
    RwResourceMgrYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key
import rift.tasklets


class NetworkResourceError(Exception):
    """ Network Resource Error """
    pass


class VlrRecordExistsError(Exception):
    """ VLR record already exists"""
    pass


class VlRecordError(Exception):
    """ VLR record error """
    pass


class VirtualLinkRecordState(enum.Enum):
    """ Virtual Link record state """
    INIT = 1
    INSTANTIATING = 2
    RESOURCE_ALLOC_PENDING = 3
    READY = 4
    TERMINATING = 5
    TERMINATED = 6
    FAILED = 10


class VirtualLinkRecord(object):
    """
        Virtual Link Record object
    """
    def __init__(self, dts, log, loop, vnsm, vlr_msg):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._vnsm = vnsm
        self._vlr_msg = vlr_msg
        self._vlr_id = self._vlr_msg.id

        self._project = vnsm._project
        self._network_id = None
        self._network_pool = None
        self._assigned_subnet = None
        self._virtual_cps = list()
        self._create_time = int(time.time())

        self._state = VirtualLinkRecordState.INIT
        self._state_failed_reason = None
        self._name = self._vlr_msg.name

    @property
    def vld_xpath(self):
        """ VLD xpath associated with this VLR record """
        return self._project.add_project("C,/vld:vld-catalog/vld:vld[id={}]".
                                         format(quoted_key(self.vld_id)))

    @property
    def vld_id(self):
        """ VLD id associated with this VLR record """
        return self._vlr_msg.vld_ref

    @property
    def vlr_id(self):
        """ VLR id associated with this VLR record """
        return self._vlr_id

    @property
    def xpath(self):
        """ path for this VLR """
        return self._project.add_project("D,/vlr:vlr-catalog"
               "/vlr:vlr[vlr:id={}]".format(quoted_key(self.vlr_id)))

    @property
    def name(self):
        """ Name of this VLR """
        return self._name

    @property
    def datacenter(self):
        """ RO Account to instantiate the virtual link on """
        return self._vlr_msg.datacenter

    @property
    def event_id(self):
        """ Event Identifier for this virtual link """
        return self._vlr_id

    @property
    def resmgr_path(self):
        """ path for resource-mgr"""
        return self._project.add_project("D,/rw-resource-mgr:resource-mgmt" +
                "/vlink-event/vlink-event-data[event-id={}]".format(quoted_key(self.event_id)))

    @property
    def operational_status(self):
        """ Operational status of this VLR"""
        op_stats_dict = {"INIT": "init",
                         "INSTANTIATING": "vl_alloc_pending",
                         "RESOURCE_ALLOC_PENDING": "vl_alloc_pending",
                         "READY": "running",
                         "FAILED": "failed",
                         "TERMINATING": "vl_terminate_pending",
                         "TERMINATED": "terminated"}

        return op_stats_dict[self._state.name]

    @property
    def msg(self):
        """ VLR message for this VLR """
        msg = RwVlrYang.YangData_RwProject_Project_VlrCatalog_Vlr()
        msg.copy_from(self._vlr_msg)

        if self._network_id is not None:
            msg.network_id = self._network_id

        if self._network_pool is not None:
            msg.network_pool = self._network_pool

        if self._assigned_subnet is not None:
            msg.assigned_subnet = self._assigned_subnet

        if self._virtual_cps:
            for cp in msg.virtual_connection_points:
                for vcp in self._virtual_cps:
                    if cp.name == vcp['name']:
                        cp.ip_address = vcp['ip_address']
                        cp.mac_address = vcp['mac_address']
                        cp.connection_point_id = vcp['connection_point_id']
                        break
        msg.operational_status = self.operational_status
        msg.operational_status_details = self._state_failed_reason
        msg.res_id = self.event_id
        return msg

    @property
    def resmgr_msg(self):
        """ VLR message for this VLR """
        msg = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData()
        msg.event_id = self.event_id
        msg.cloud_account = self.datacenter
        msg.request_info.name = self.name
        msg.request_info.vim_network_name = self._vlr_msg.vim_network_name
        msg.request_info.provider_network.from_dict(
                self._vlr_msg.provider_network.as_dict()
                )
        if self._vlr_msg.has_field('ip_profile_params'):
            msg.request_info.ip_profile_params.from_dict(self._vlr_msg.ip_profile_params.as_dict())

        for cp in self._vlr_msg.virtual_connection_points:
            vcp = msg.request_info.virtual_cps.add()
            vcp.from_dict({k:v for k,v in cp.as_dict().items()
                           if k in ['name','port_security_enabled','type_yang']})
            if (self._vlr_msg.has_field('ip_profile_params')) and (self._vlr_msg.ip_profile_params.has_field('security_group')):
                vcp.security_group = self._vlr_msg.ip_profile_params.security_group

        return msg

    @asyncio.coroutine
    def create_network(self, xact):
        """ Create network for this VL """
        self._log.debug("Creating network event-id: %s:%s", self.event_id, self._vlr_msg)
        network_rsp = yield from self.request_network(xact, "create")
        return network_rsp

    @asyncio.coroutine
    def delete_network(self, xact):
        """ Delete network for this VL """
        self._log.debug("Deleting network - event-id: %s", self.event_id)
        return (yield from self.request_network(xact, "delete"))

    @asyncio.coroutine
    def read_network(self, xact):
        """ Read network for this VL """
        self._log.debug("Reading network - event-id: %s", self.event_id)
        return (yield from self.request_network(xact, "read"))

    @asyncio.coroutine
    def request_network(self, xact, action):
        """Request creation/deletion network for this VL """

        block = xact.block_create()

        if action == "create":
            self._log.debug("Creating network path:%s, msg:%s",
                            self.resmgr_path, self.resmgr_msg)
            block.add_query_create(self.resmgr_path, self.resmgr_msg)
        elif action == "delete":
            self._log.debug("Deleting network path:%s", self.resmgr_path)
            block.add_query_delete(self.resmgr_path)
        elif action == "read":
            self._log.debug("Reading network path:%s", self.resmgr_path)
            block.add_query_read(self.resmgr_path)
        else:
            raise VlRecordError("Invalid action %s received" % action)

        res_iter = yield from block.execute(now=True)

        resp = None

        if action == "create" or action == "read":
            for i in res_iter:
                r = yield from i
                resp = r.result

            if resp is None:
                raise NetworkResourceError("Did not get a network resource response (resp: %s)", resp)

            if resp.has_field('resource_info') and resp.resource_info.resource_state == "failed":
                raise NetworkResourceError(resp.resource_info.resource_errors)

            if not resp.has_field('resource_info') :
                raise NetworkResourceError("Did not get a valid network resource response (resp: %s)", resp)

            self._log.debug("Got network request response: %s", resp)

        return resp

    @asyncio.coroutine
    def instantiate(self, xact, restart=0):
        """ Instantiate this VL """
        self._state = VirtualLinkRecordState.INSTANTIATING

        self._log.debug("Instantiating VLR path = [%s]", self.xpath)

        try:
            self._state = VirtualLinkRecordState.RESOURCE_ALLOC_PENDING

            network_rsp = None
            if restart == 0:
              network_resp = yield from self.create_network(xact)
            else:
              network_resp = yield from self.read_network(xact)
              if network_resp == None:
                  network_resp = yield from self.create_network(xact)

            if network_resp:
                self._state = self.vl_state_from_network_resp(network_resp)

            if self._state == VirtualLinkRecordState.READY:
                # Move this VL into ready state
                yield from self.ready(network_resp, xact)
            else:
                yield from self.publish(xact)
        except Exception as e:
            self._log.error("Instantiatiation of  VLR record failed: %s", str(e))
            self._state = VirtualLinkRecordState.FAILED
            self._state_failed_reason = str(e)
            yield from self.publish(xact)

    def vl_state_from_network_resp(self, network_resp):
        """ Determine VL state from network response """
        if network_resp.resource_info.resource_state == 'pending':
            return VirtualLinkRecordState.RESOURCE_ALLOC_PENDING
        elif network_resp.resource_info.resource_state == 'active':
            return VirtualLinkRecordState.READY
        elif network_resp.resource_info.resource_state == 'failed':
            return VirtualLinkRecordState.FAILED
        return VirtualLinkRecordState.RESOURCE_ALLOC_PENDING

    @asyncio.coroutine
    def ready(self, event_resp, xact):
        """ This virtual link is ready """
        # Note network_resp.virtual_link_id is CAL assigned network_id.
        self._log.debug("Virtual Link id %s name %s in ready state, event_rsp:%s",
                        self.vlr_id,
                        self.name,
                        event_resp)
        self._network_id = event_resp.resource_info.virtual_link_id
        self._network_pool = event_resp.resource_info.pool_name
        self._assigned_subnet = event_resp.resource_info.subnet
        self._virtual_cps = [ vcp.as_dict()
                              for vcp in event_resp.resource_info.virtual_connection_points ]

        yield from self.publish(xact)

        self._state = VirtualLinkRecordState.READY

        yield from self.publish(xact)

    @asyncio.coroutine
    def failed(self, event_resp, xact):
        """ This virtual link Failed """
        self._log.debug("Virtual Link id %s name %s failed to instantiate, event_rsp:%s",
                        self.vlr_id,
                        self.name,
                        event_resp)

        self._state = VirtualLinkRecordState.FAILED

        yield from self.publish(xact)

    @asyncio.coroutine
    def publish(self, xact):
        """ publish this VLR """
        vlr = self.msg
        self._log.debug("Publishing VLR path = [%s], record = [%s]",
                        self.xpath, self.msg)
        vlr.create_time = self._create_time
        yield from self._vnsm.publish_vlr(xact, self.xpath, self.msg)
        self._log.debug("Published VLR path = [%s], record = [%s]",
                        self.xpath, self.msg)

    @asyncio.coroutine
    def terminate(self, xact):
        """ Terminate this VL """
        if self._state not in [VirtualLinkRecordState.READY, VirtualLinkRecordState.FAILED]:
            self._log.error("Ignoring terminate for VL %s is in %s state",
                            self.vlr_id, self._state)
            return

        if self._state == VirtualLinkRecordState.READY:
            self._log.debug("Terminating VL with id %s", self.vlr_id)
            self._state = VirtualLinkRecordState.TERMINATING
            try:
                yield from self.delete_network(xact)
            except Exception:
                self._log.exception("Caught exception while deleting VL %s", self.vlr_id)
            self._log.debug("Terminated VL with id %s", self.vlr_id)

        yield from self.unpublish(xact)
        self._state = VirtualLinkRecordState.TERMINATED

    @asyncio.coroutine
    def unpublish(self, xact):
        """ Unpublish this VLR """
        self._log.debug("UnPublishing VLR id %s", self.vlr_id)
        yield from self._vnsm.unpublish_vlr(xact, self.xpath)
        self._log.debug("UnPublished VLR id %s", self.vlr_id)


class VlrDtsHandler(object):
    """ Handles DTS interactions for the VLR registration """
    XPATH = "D,/vlr:vlr-catalog/vlr:vlr"

    def __init__(self, dts, log, loop, vnsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._vnsm = vnsm

        self._regh = None
        self._project = vnsm._project

    @property
    def regh(self):
        """ The registration handle assocaited with this Handler"""
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for the VLR path """

        @asyncio.coroutine
        def on_event(dts, g_reg, xact, xact_event, scratch_data):
            @asyncio.coroutine
            def instantiate_realloc_vlr(vlr):
                """Re-populate the virtual link information after restart

                Arguments:
                    vlink

                """

                with self._dts.transaction(flags=0) as xact:
                  yield from vlr.instantiate(xact, 1)

            if (xact_event == rwdts.MemberEvent.INSTALL):
              curr_cfg = self.regh.elements
              for cfg in curr_cfg:
                vlr = self._vnsm.create_vlr(cfg)
                self._loop.create_task(instantiate_realloc_vlr(vlr))

            self._log.debug("Got on_event")
            return rwdts.MemberRspCode.ACTION_OK

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare for VLR registration"""
            self._log.debug(
                "Got vlr on_prepare callback (xact_info: %s, action: %s): %s",
                xact_info, action, msg
                )

            if action == rwdts.QueryAction.CREATE:
                vlr = self._vnsm.create_vlr(msg)
                with self._dts.transaction(flags=0) as xact:
                    yield from vlr.instantiate(xact)
                self._log.debug("Responding to VL create request path:%s, msg:%s",
                                vlr.xpath, vlr.msg)
                xact_info.respond_xpath(rwdts.XactRspCode.ACK, xpath=vlr.xpath, msg=vlr.msg)
                return
            elif action == rwdts.QueryAction.DELETE:
                # Delete an VLR record
                schema = RwVlrYang.YangData_RwProject_Project_VlrCatalog_Vlr.schema()
                path_entry = schema.keyspec_to_entry(ks_path)
                self._log.debug("Terminating VLR id %s", path_entry.key00.id)
                yield from self._vnsm.delete_vlr(path_entry.key00.id, xact_info.xact)
            else:
                err = "%s action on VirtualLinkRecord not supported" % action
                raise NotImplementedError(err)
            xact_info.respond_xpath(rwdts.XactRspCode.ACK)
            return

        xpath = self._project.add_project(VlrDtsHandler.XPATH)
        self._log.debug("Registering for VLR using xpath: {}".
                        format(xpath))

        reg_handle = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare,)
        handlers = rift.tasklets.Group.Handler(on_event=on_event,)
        with self._dts.group_create(handler=handlers) as group:
            self._regh = group.register(
                xpath=xpath,
                handler=reg_handle,
                flags=rwdts.Flag.PUBLISHER | rwdts.Flag.NO_PREP_READ| rwdts.Flag.DATASTORE,
                )

    def deregister(self):
        self._log.debug("De-register VLR handler for project {}".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None

    @asyncio.coroutine
    def create(self, xact, xpath, msg):
        """
        Create a VLR record in DTS with path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Creating VLR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.create_element(path, msg)
        self._log.debug("Created VLR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def update(self, xact, xpath, msg):
        """
        Update a VLR record in DTS with path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Updating VLR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.update_element(path, msg)
        self._log.debug("Updated VLR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def delete(self, xact, xpath):
        """
        Delete a VLR record in DTS with path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Deleting VLR xact = %s, %s", xact, path)
        self.regh.delete_element(path)
        self._log.debug("Deleted VLR xact = %s, %s", xact, path)


class VldDtsHandler(object):
    """ DTS handler for the VLD registration """
    XPATH = "C,/vld:vld-catalog/vld:vld"

    def __init__(self, dts, log, loop, vnsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._vnsm = vnsm

        self._regh = None

    @property
    def regh(self):
        """ The registration handle assocaited with this Handler"""
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register the VLD path """
        @asyncio.coroutine
        def on_prepare(xact_info, query_action, ks_path, msg):
            """ prepare callback on vld path """
            self._log.debug(
                "Got on prepare for VLD update (ks_path: %s) (action: %s)",
                ks_path.to_xpath(VldYang.get_schema()), msg)

            schema = VldYang.YangData_RwProject_Project_VldCatalog_Vld.schema()
            path_entry = schema.keyspec_to_entry(ks_path)
            # TODO: Check why on project delete this gets called
            if not path_entry:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
                return

            vld_id = path_entry.key00.id

            disabled_actions = [rwdts.QueryAction.DELETE, rwdts.QueryAction.UPDATE]
            if query_action not in disabled_actions:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
                return

            vlr = self._vnsm.find_vlr_by_vld_id(vld_id)
            if vlr is None:
                self._log.debug(
                    "Did not find an existing VLR record for vld %s. "
                    "Permitting %s vld action", vld_id, query_action)
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
                return

            raise VlrRecordExistsError(
                "Vlr record(s) exists."
                "Cannot perform %s action on VLD." % query_action)

        handler = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare)

        self._regh = yield from self._dts.register(
            self._vnsm._project.add_project(VldDtsHandler.XPATH),
            flags=rwdts.Flag.SUBSCRIBER,
            handler=handler
            )

    def deregister(self):
        self._log.debug("De-register VLD handler for project {}".
                        format(self._vnsm._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None

class VirtualLinkEventListener(object):
    """ DTS Listener to listen on Virtual Link related events """
    XPATH = "D,/rw-resource-mgr:resource-mgmt/vlink-event/vlink-event-data"
    def __init__(self, dts, log, loop, vnsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._vnsm = vnsm
        self._regh = None

    @property
    def regh(self):
        """ The registration handle assocaited with this Handler"""
        return self._regh

    def event_id_from_keyspec(self, ks):
        """ Get the event id from the keyspec """
        event_pe = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData.schema().keyspec_to_entry(ks)
        try:
            # Can get just path without event id when
            # deleting project
            event_id = event_pe.key00.event_id
        except AttributeError:
            return None
        return event_id

    @asyncio.coroutine
    def register(self):
        """ Register the Virtual Link Event path """
        @asyncio.coroutine
        def on_prepare(xact_info, query_action, ks_path, msg):
            """ prepare callback on Virtual Link Events  """
            try:
                self._log.debug(
                    "Got on prepare for Virtual Link Event id (ks_path: %s) (msg: %s)",
                    ks_path.to_xpath(RwResourceMgrYang.get_schema()), msg)
                event_id = self.event_id_from_keyspec(ks_path)
                if event_id:
                    if query_action == rwdts.QueryAction.CREATE or query_action == rwdts.QueryAction.UPDATE:
                        yield from self._vnsm.update_virual_link_event(event_id, msg)
                    elif query_action == rwdts.QueryAction.DELETE:
                        self._vnsm.delete_virual_link_event(event_id)
            except Exception as e:
                self._log.exception("Caught execption in Virtual Link Event handler", e)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        handler = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare)

        self._regh = yield from self._dts.register(
            self._vnsm._project.add_project(VirtualLinkEventListener.XPATH),
            flags=rwdts.Flag.SUBSCRIBER,
            handler=handler
        )

    def deregister(self):
      if self._regh:
        self._regh.deregister()
        self._regh = None
