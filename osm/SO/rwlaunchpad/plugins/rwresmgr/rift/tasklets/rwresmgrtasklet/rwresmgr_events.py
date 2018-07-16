
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
import gi
import sys

gi.require_version('RwDts', '1.0')
gi.require_version('RwYang', '1.0')
gi.require_version('RwResourceMgrYang', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('RwcalYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    RwYang,
    RwResourceMgrYang,
    RwLaunchpadYang,
    RwcalYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from gi.repository.RwTypes import RwStatus
import rift.tasklets

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async


class ResourceMgrEvent(object):
    VDU_REQUEST_XPATH = "D,/rw-resource-mgr:resource-mgmt/vdu-event/vdu-event-data"
    VLINK_REQUEST_XPATH = "D,/rw-resource-mgr:resource-mgmt/vlink-event/vlink-event-data"

    def __init__(self, dts, log, loop, parent):
        self._log = log
        self._dts = dts
        self._loop = loop
        self._parent = parent
        self._project = parent._project
        self._vdu_reg = None
        self._link_reg = None

        self._vdu_reg_event = asyncio.Event(loop=self._loop)
        self._link_reg_event = asyncio.Event(loop=self._loop)

    @asyncio.coroutine
    def wait_ready(self, timeout=5):
        self._log.debug("Waiting for all request registrations to become ready.")
        yield from asyncio.wait([self._link_reg_event.wait(), self._vdu_reg_event.wait()],
                                timeout=timeout, loop=self._loop)

    def _add_config_flag(self, xpath, config=False):
        if xpath[0] == '/':
            if config:
                return 'C,' + xpath
            else:
                return 'D,' + xpath

        return xpath

    def create_record_dts(self, regh, xact, xpath, msg):
        """
        Create a record in DTS with path and message
        """
        path = self._add_config_flag(self._project.add_project(xpath))
        self._log.debug("Creating Resource Record xact = %s, %s:%s",
                        xact, path, msg)
        regh.create_element(path, msg)

    def delete_record_dts(self, regh, xact, xpath):
        """
        Delete a VNFR record in DTS with path and message
        """
        path = self._add_config_flag(self._project.add_project(xpath))
        self._log.debug("Deleting Resource Record xact = %s, %s",
                        xact, path)
        regh.delete_element(path)


    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def onlink_event(dts, g_reg, xact, xact_event, scratch_data):
            @asyncio.coroutine
            def instantiate_realloc_vn(link):
                """Re-populate the virtual link information after restart

                Arguments:
                    vlink 

                """
                # wait for 3 seconds
                yield from asyncio.sleep(3, loop=self._loop)
                
                try:
                    response_info = yield from self._parent.reallocate_virtual_network(
                          link.event_id,
                          link.cloud_account,
                          link.request_info, link.resource_info,
                        )
                except Exception as e:
                  self._log.error("Encoutered exception in reallocate_virtual_network")
                  self._log.exception(e)


            if (xact_event == rwdts.MemberEvent.INSTALL):
              link_cfg = self._link_reg.elements
              self._log.debug("onlink_event INSTALL event: {}".format(link_cfg))

              for link in link_cfg:
                self._loop.create_task(instantiate_realloc_vn(link))

              self._log.debug("onlink_event INSTALL event complete")

            return rwdts.MemberRspCode.ACTION_OK

        @asyncio.coroutine
        def onvdu_event(dts, g_reg, xact, xact_event, scratch_data):
            @asyncio.coroutine
            def instantiate_realloc_vdu(vdu):
                """Re-populate the VDU information after restart

                Arguments:
                    vdu 

                """
                # wait for 3 seconds
                yield from asyncio.sleep(3, loop=self._loop)

                try:
                    response_info = yield from self._parent.allocate_virtual_compute(
                        vdu.event_id,
                        vdu.cloud_account,
                        vdu.request_info
                       )
                except Exception as e:
                    self._log.error("Encoutered exception in allocate_virtual_network")
                    self._log.exception(e)
                    raise e

                response_xpath = "/rw-resource-mgr:resource-mgmt/rw-resource-mgr:vdu-event/rw-resource-mgr:vdu-event-data[rw-resource-mgr:event-id={}]/resource-info".format(
                    quoted_key(vdu.event_id.strip()))

                cloud_account = self._parent.get_cloud_account_detail(cloud_account)
                asyncio.ensure_future(monitor_vdu_state(response_xpath, vdu.event_id, cloud_account.vdu_instance_timeout), loop=self._loop)

            if (xact_event == rwdts.MemberEvent.INSTALL):
                vdu_cfg = self._vdu_reg.elements
                self._log.debug("onvdu_event INSTALL event: {}".format(vdu_cfg))

                for vdu in vdu_cfg:
                    self._loop.create_task(instantiate_realloc_vdu(vdu))

                self._log.debug("onvdu_event INSTALL event complete")

            return rwdts.MemberRspCode.ACTION_OK

        @asyncio.coroutine
        def allocate_vlink_task(ks_path, event_id, cloud_account, request_info):
            response_xpath = ks_path.to_xpath(RwResourceMgrYang.get_schema()) + "/resource-info"
            schema = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData().schema()
            pathentry = schema.keyspec_to_entry(ks_path)
            try:
                response_info = yield from self._parent.allocate_virtual_network(pathentry.key00.event_id,
                                                                                 cloud_account,
                                                                                 request_info)
            except Exception as e:
                self._log.error("Encountered exception: %s while creating virtual network", str(e))
                self._log.exception(e)
                response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData_ResourceInfo()
                response_info.resource_state = 'failed'
                response_info.resource_errors = str(e)
                yield from self._dts.query_update(response_xpath,
                                                  rwdts.XactFlag.ADVISE,
                                                  response_info)
            else:
                yield from self._dts.query_update(response_xpath,
                                                  rwdts.XactFlag.ADVISE,
                                                  response_info)


        @asyncio.coroutine
        def on_link_request_prepare(xact_info, action, ks_path, request_msg):
            self._log.debug(
                "Received virtual-link on_prepare callback (xact_info: %s, action: %s): %s",
                            xact_info, action, request_msg)

            response_info = None
            response_xpath = ks_path.to_xpath(RwResourceMgrYang.get_schema()) + "/resource-info"

            schema = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData().schema()
            pathentry = schema.keyspec_to_entry(ks_path)

            if action == rwdts.QueryAction.CREATE:
                try:
                    response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData_ResourceInfo()
                    response_info.resource_state = 'pending'
                    request_msg.resource_info = response_info
                    self.create_record_dts(self._link_reg,
                                           None,
                                           ks_path.to_xpath(RwResourceMgrYang.get_schema()),
                                           request_msg)

                    asyncio.ensure_future(allocate_vlink_task(ks_path,
                                                              pathentry.key00.event_id,
                                                              request_msg.cloud_account,
                                                              request_msg.request_info),
                                                              loop = self._loop)
                except Exception as e:
                    self._log.error(
                        "Encountered exception: %s while creating virtual network", str(e))
                    self._log.exception(e)
                    response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VlinkEvent_VlinkEventData_ResourceInfo()
                    response_info.resource_state = 'failed'
                    response_info.resource_errors = str(e)
                    yield from self._dts.query_update(response_xpath,
                                                      rwdts.XactFlag.ADVISE,
                                                      response_info)
            elif action == rwdts.QueryAction.DELETE:
                yield from self._parent.release_virtual_network(pathentry.key00.event_id)
                self.delete_record_dts(self._link_reg, None, 
                    ks_path.to_xpath(RwResourceMgrYang.get_schema()))

            elif action == rwdts.QueryAction.READ:
                # TODO: Check why we are getting null event id request
                if pathentry.key00.event_id:
                    response_info = yield from self._parent.read_virtual_network_info(pathentry.key00.event_id)
                else:
                    xact_info.respond_xpath(rwdts.XactRspCode.NA)
                    return
            else:
                raise ValueError(
                    "Only read/create/delete actions available. Received action: %s" %(action))

            self._log.info("Responding with VirtualLinkInfo at xpath %s: %s.",
                           response_xpath, response_info)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK, response_xpath, response_info)



        def monitor_vdu_state(response_xpath, event_id, vdu_timeout):
            self._log.info("Initiating VDU state monitoring for xpath: %s ", response_xpath)
            sleep_time = 2
            loop_cnt = int(vdu_timeout/sleep_time)

            for i in range(loop_cnt):
                self._log.debug(
                    "VDU state monitoring for xpath: %s. Sleeping for 2 second", response_xpath)
                yield from asyncio.sleep(2, loop = self._loop)

                try:
                    response_info = yield from self._parent.read_virtual_compute_info(event_id)
                except Exception as e:
                    self._log.info(
                        "VDU state monitoring: Received exception %s in VDU state monitoring for %s. Aborting monitoring", str(e),response_xpath)

                    response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData_ResourceInfo()
                    response_info.resource_state = 'failed'
                    response_info.resource_errors = str(e)
                    yield from self._dts.query_update(response_xpath,
                                                      rwdts.XactFlag.ADVISE,
                                                      response_info)
                else:
                    if response_info.resource_state == 'active' or response_info.resource_state == 'failed':
                        self._log.info("VDU state monitoring: VDU reached terminal state. " +
                                       "Publishing VDU info: %s at path: %s",
                                       response_info, response_xpath)
                        yield from self._dts.query_update(response_xpath,
                                                          rwdts.XactFlag.ADVISE,
                                                          response_info)
                        return
            else:
                ### End of loop. This is only possible if VDU did not reach active state
                err_msg = ("VDU state monitoring: VDU at xpath :{} did not reached active " +
                           "state in {} seconds. Aborting monitoring".
                           format(response_xpath, time_to_wait))
                self._log.info(err_msg)
                response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData_ResourceInfo()
                response_info.resource_state = 'failed'
                response_info.resource_errors = err_msg
                yield from self._dts.query_update(response_xpath,
                                                  rwdts.XactFlag.ADVISE,
                                                  response_info)
            return

        def allocate_vdu_task(ks_path, event_id, cloud_account, request_msg):
            response_xpath = ks_path.to_xpath(RwResourceMgrYang.get_schema()) + "/resource-info"
            response_xpath = self._add_config_flag(response_xpath)
            schema = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData().schema()
            pathentry = schema.keyspec_to_entry(ks_path)
            try:
                response_info = yield from self._parent.allocate_virtual_compute(event_id,
                                                                                 cloud_account,
                                                                                 request_msg,)
            except Exception as e:
                self._log.error("Encountered exception : %s while creating virtual compute", str(e))
                response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData_ResourceInfo()
                response_info.resource_state = 'failed'
                response_info.resource_errors = str(e)
                yield from self._dts.query_update(response_xpath,
                                                  rwdts.XactFlag.ADVISE,
                                                  response_info)
            else:
                cloud_account = self._parent.get_cloud_account_detail(cloud_account)
                #RIFT-17719 - Set the resource state to active if no floating ip pool specified and is waiting for public ip.
                if response_info.resource_state == 'pending' and cloud_account.has_field('openstack') \
                     and not (cloud_account.openstack.has_field('floating_ip_pool')) :
                    if (request_msg.has_field('allocate_public_address')) and (request_msg.allocate_public_address == True):
                        if not response_info.has_field('public_ip'):
                            response_info.resource_state = 'active'

                if response_info.resource_state == 'failed' or response_info.resource_state == 'active' :
                    self._log.debug("Virtual compute create task completed. Publishing VDU info: %s at path: %s",
                                    response_info, response_xpath)
                    yield from self._dts.query_update(response_xpath,
                                                      rwdts.XactFlag.ADVISE,
                                                      response_info)
                else:
                    asyncio.ensure_future(monitor_vdu_state(response_xpath, pathentry.key00.event_id, cloud_account.vdu_instance_timeout),
                                          loop = self._loop)

        @asyncio.coroutine
        def on_vdu_request_prepare(xact_info, action, ks_path, request_msg):
            self._log.debug("Received vdu on_prepare callback (xact_info: %s, action: %s): %s",
                            xact_info, action, request_msg)
            response_xpath = ks_path.to_xpath(RwResourceMgrYang.get_schema()) + "/resource-info"
            response_xpath = self._add_config_flag(response_xpath)
            schema = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData().schema()
            pathentry = schema.keyspec_to_entry(ks_path)

            if action == rwdts.QueryAction.CREATE:
                response_info = RwResourceMgrYang.YangData_RwProject_Project_ResourceMgmt_VduEvent_VduEventData_ResourceInfo()
                response_info.resource_state = 'pending'
                request_msg.resource_info = response_info
                self.create_record_dts(self._vdu_reg,
                                       None,
                                       ks_path.to_xpath(RwResourceMgrYang.get_schema()),
                                       request_msg)
                asyncio.ensure_future(allocate_vdu_task(ks_path,
                                                        pathentry.key00.event_id,
                                                        request_msg.cloud_account,
                                                        request_msg.request_info),
                                      loop = self._loop)
            elif action == rwdts.QueryAction.DELETE:
                response_info = None
                yield from self._parent.release_virtual_compute(pathentry.key00.event_id)
                self.delete_record_dts(self._vdu_reg, None, ks_path.to_xpath(RwResourceMgrYang.get_schema()))
            elif action == rwdts.QueryAction.READ:
                # TODO: Check why we are getting null event id request
                if pathentry.key00.event_id:
                    response_info = yield from self._parent.read_virtual_compute_info(pathentry.key00.event_id)
                else:
                    xact_info.respond_xpath(rwdts.XactRspCode.NA)
                    return
            else:
                raise ValueError("Only create/delete actions available. Received action: %s" %(action))

            self._log.debug("Responding with VDUInfo at xpath %s: %s",
                            response_xpath, response_info)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK, response_xpath, response_info)


        @asyncio.coroutine
        def on_request_ready(registration, status):
            self._log.debug("Got request ready event (registration: %s) (status: %s)",
                            registration, status)

            if registration == self._link_reg:
                self._link_reg_event.set()
            elif registration == self._vdu_reg:
                self._vdu_reg_event.set()
            else:
                self._log.error("Unknown registration ready event: %s", registration)

        link_handlers = rift.tasklets.Group.Handler(on_event=onlink_event,)
        with self._dts.group_create(handler=link_handlers) as link_group:
            xpath = self._project.add_project(ResourceMgrEvent.VLINK_REQUEST_XPATH)
            self._log.debug("Registering for Link Resource Request using xpath: {}".
                            format(xpath))

            self._link_reg = link_group.register(xpath=xpath,
                                                 handler=rift.tasklets.DTS.RegistrationHandler(on_ready=on_request_ready,
                                                                                               on_prepare=on_link_request_prepare),
                                                 flags=rwdts.Flag.PUBLISHER | rwdts.Flag.DATASTORE,)
            
        vdu_handlers = rift.tasklets.Group.Handler(on_event=onvdu_event, )
        with self._dts.group_create(handler=vdu_handlers) as vdu_group:
                
            xpath = self._project.add_project(ResourceMgrEvent.VDU_REQUEST_XPATH)
            self._log.debug("Registering for VDU Resource Request using xpath: {}".
                            format(xpath))

            self._vdu_reg = vdu_group.register(xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(on_ready=on_request_ready,
                                                              on_prepare=on_vdu_request_prepare),
                                               flags=rwdts.Flag.PUBLISHER | rwdts.Flag.DATASTORE,)


    def deregister(self):
        self._log.debug("De-register for project {}".format(self._project.name))

        if self._vdu_reg:
            self._vdu_reg.deregister()
            self._vdu_reg = None

        if self._link_reg:
            self._link_reg.deregister()
            self._link_reg = None
