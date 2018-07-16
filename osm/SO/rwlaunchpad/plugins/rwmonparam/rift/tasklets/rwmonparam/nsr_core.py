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

@file nsr_core.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 09-Jul-2016

"""
import asyncio
import collections
import functools
import gi
import uuid

import rift.tasklets

from gi.repository import (RwDts as rwdts, NsrYang)
import rift.mano.dts as mano_dts
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from . import aggregator as aggregator


class MissingValueField(Exception):
    pass


class VnfrMonitoringParamSubscriber(mano_dts.AbstractOpdataSubscriber):
    """Registers for VNFR monitoring parameter changes.

    Attributes:
        monp_id (str): Monitoring Param ID
        vnfr_id (str): VNFR ID
    """
    def __init__(self, log, dts, loop, project, vnfr_id, monp_id, callback=None):
        super().__init__(log, dts, loop, project, callback)
        self.vnfr_id = vnfr_id
        self.monp_id = monp_id

    def get_xpath(self):
        return self.project.add_project(("D,/vnfr:vnfr-catalog" +
               "/vnfr:vnfr[vnfr:id={}]".format(quoted_key(self.vnfr_id)) +
               "/vnfr:monitoring-param" +
               "[vnfr:id={}]".format(quoted_key(self.monp_id))))


class NsrMonitoringParam():
    """Class that handles NS Mon-param data.
    """
    MonParamMsg = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_MonitoringParam
    MISSING = None
    DEFAULT_AGGREGATION_TYPE = "AVERAGE"

    @classmethod
    def create_nsr_mon_params(cls, nsd, constituent_vnfrs, mon_param_project):
        """Convenience class that constructs NSMonitoringParam objects

        Args:
            nsd (RwNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd): Nsd object
            constituent_vnfrs (list): List of constituent vnfr objects of NSR
            mon_param_project (MonParamProject): Store object instance

        Returns:
            list NsrMonitoringParam object.

        Also handles legacy NSD descriptor which has no mon-param defines. In
        such cases the mon-params are created from VNFD's mon-param config.
        """
        mon_params = []
        for mon_param_msg in nsd.monitoring_param:
            mon_params.append(NsrMonitoringParam(
                    mon_param_msg,
                    constituent_vnfrs,
                    mon_param_name=mon_param_msg.name
                    ))

        # Legacy Handling.
        # This indicates that the NSD had no mon-param config.
        if not nsd.monitoring_param:
            for vnfr in constituent_vnfrs:
                vnfd = mon_param_project.get_vnfd(vnfr.vnfd.id)
                for monp in vnfd.monitoring_param:
                    mon_params.append(NsrMonitoringParam(
                        monp,
                        [vnfr],
                        is_legacy=True,
                        mon_param_name=monp.name))

        return mon_params

    def __init__(self, monp_config, constituent_vnfrs, is_legacy=False, mon_param_name=None):
        """
        Args:
            monp_config (GiObject): Config data to create the NSR mon-param msg
            constituent_vnfrs (list): List of VNFRs that may contain the mon-param
            is_legacy (bool, optional): If set then the mon-param are created from
                vnfd's config and not NSD's config.
        """
        self._nsd_mon_param_msg = monp_config
        self._constituent_vnfr_map = {vnfr.id:vnfr for vnfr in constituent_vnfrs}

        # An internal store to hold the data
        # Key => (vnfr_id, monp_id)
        # value => (value_type, value)
        self.vnfr_monparams = {}

        # create_nsr_mon_params() is already validating for 'is_legacy' by checking if
        # nsd is having 'monitoring_param'. So removing 'self.aggregation_type is None' check for is_legacy.
        self.is_legacy = is_legacy
        self.mon_param_name = mon_param_name

        if not is_legacy:
            self._msg = self._convert_nsd_msg()
        else:
            # TODO remove arg for consistency
            self._msg = self._convert_vnfd_msg(monp_config)

    def add_vnfr(self, vnfr):
        # If already added ignore
        if vnfr.id in self._constituent_vnfr_map:
            return

        # Update the map
        self._constituent_vnfr_map[vnfr.id] = vnfr

        if not self.is_legacy:
            self._msg = self._convert_nsd_msg()

    def delete_vnfr(self, vnfr):
        # Update the map
        if vnfr.id in self._constituent_vnfr_map:
            del self._constituent_vnfr_map[vnfr.id]

            # Delete the value stores.
            for vnfr_id, monp_id in list(self.vnfr_monparams.keys()):
                if vnfr_id == vnfr.id:
                    del self.vnfr_monparams[(vnfr_id, monp_id)]

        if not self.is_legacy:
            self._msg = self._convert_nsd_msg()

    @property
    def nsd_mon_param_msg(self):
        return self._nsd_mon_param_msg

    @property
    def nsr_mon_param_msg(self):
        """Gi object msg"""
        return self._msg

    @property
    def vnfr_ids(self):
        """Store Keys"""
        return list(self.vnfr_monparams.keys())

    @property
    def vnfr_values(self):
        """Store values"""
        return list(self.vnfr_monparams.values())

    @property
    def is_ready(self):
        """Flag which indicates if all of the constituent vnfr values are
        available to perform the aggregation"""
        return (self.MISSING not in self.vnfr_values)

    @property
    def aggregation_type(self):
        """Aggregation type"""
        return self.nsr_mon_param_msg.aggregation_type

    # @property
    # def is_legacy(self):
    #     return (self.aggregation_type is None)

    @classmethod
    def extract_value(cls, monp):
        """Class method to extract the value type and value from the 
        mon-param gi message
        
        Args:
            monp (GiObject): Mon param msg
        
        Returns:
            Tuple: (value type, value)
        
        Raises:
            MissingValueField: Raised if no valid field are available.
        """
        if monp.has_field("value_integer"):
            return ("value_integer", monp.value_integer)
        elif monp.has_field("value_decimal"):
            return ("value_decimal", monp.value_decimal)
        elif monp.has_field("value_string"):
            return ("value_string", monp.value_string)

        return None


    def _extract_ui_elements(self, monp):
        ui_fields = ["group_tag", "description", "widget_type", "units", "value_type"]
        ui_data = [getattr(monp, ui_field) for ui_field in ui_fields]

        return dict(zip(ui_fields, ui_data))


    def _convert_nsd_msg(self):
        """Create/update msg. This is also called when a new VNFR is added."""

        # For a single VNFD there might be multiple vnfrs
        vnfd_to_vnfr = collections.defaultdict(list)
        for vnfr_id, vnfr in self._constituent_vnfr_map.items():
            vnfd_to_vnfr[vnfr.vnfd.id].append(vnfr_id)

        # First, convert the monp param ref from vnfd to vnfr terms.
        vnfr_mon_param_ref = []
        for vnfd_mon in self.nsd_mon_param_msg.vnfd_monitoring_param:
            vnfr_ids = vnfd_to_vnfr[vnfd_mon.vnfd_id_ref]
            monp_id = vnfd_mon.vnfd_monitoring_param_ref

            for vnfr_id in vnfr_ids:
                key = (vnfr_id, monp_id)
                if key not in self.vnfr_monparams:
                    self.vnfr_monparams[key] = self.MISSING

                vnfr_mon_param_ref.append({
                    'vnfr_id_ref': vnfr_id,
                    'vnfr_mon_param_ref': monp_id
                    })

        monp_fields = {
                # For now both the NSD and NSR's monp ID are same.
                'id': self.nsd_mon_param_msg.id,
                'name': self.nsd_mon_param_msg.name,
                'nsd_mon_param_ref': self.nsd_mon_param_msg.id,
                'vnfr_mon_param_ref': vnfr_mon_param_ref,
                'aggregation_type': self.nsd_mon_param_msg.aggregation_type
            }

        ui_fields = self._extract_ui_elements(self.nsd_mon_param_msg)
        monp_fields.update(ui_fields)
        monp = self.MonParamMsg.from_dict(monp_fields)

        return monp

    def _convert_vnfd_msg(self, vnfd_monp):

        vnfr = list(self._constituent_vnfr_map.values())[0]
        self.vnfr_monparams[(vnfr.id, vnfd_monp.id)] = self.MISSING

        monp_data = {
                'id': str(uuid.uuid1()),
                'name': vnfd_monp.name,
                'vnfr_mon_param_ref': [{
                    'vnfr_id_ref': vnfr.id,
                    'vnfr_mon_param_ref': vnfd_monp.id
                    }]
                }

        ui_fields = self._extract_ui_elements(vnfd_monp)
        monp_data.update(ui_fields)
        monp = self.MonParamMsg.from_dict(monp_data)

        return monp

    def update_vnfr_value(self, key, value):
        """Update the internal store

        Args:
            key (Tuple): (vnfr_id, monp_id)
            value (Tuple): (value_type, value)
        """
        self.vnfr_monparams[key] = value
        

    def update_ns_value(self, value_field, value):
        """Updates the NS mon-param data with the aggregated value.

        Args:
            value_field (str): Value field in NSR
            value : Aggregated value
        """
        setattr(self.nsr_mon_param_msg, value_field, value)


class NsrMonitoringParamPoller(mano_dts.DtsHandler):
    """Handler responsible for publishing NS level monitoring
    parameters.

    Design:
        1. Created subscribers for each vnfr's monitoring parameter
        2. Accumulates the VNFR's value into the NsrMonitoringParam's internal
            store.
        3. Once all values are available, aggregate the value and triggers
            callback notification to the subscribers.
    """
    @classmethod
    def from_handler(cls, handler, monp, callback):
        """Convenience class to build NsrMonitoringParamPoller object.
        """
        return cls(handler.log, handler.dts, handler.loop, handler.project,
                   monp, callback)

    def __init__(self, log, dts, loop, project, monp, callback=None):
        """
        Args:
            monp (NsrMonitoringParam): Param object
            callback (None, optional): Callback to be triggered after value has
                been aggregated.
        """
        super().__init__(log, dts, loop, project)

        self.monp = monp
        self.subscribers = {}
        self.callback = callback
        self._agg = None

    def make_aggregator(self, field_types):
        if not self._agg:
            self._agg = aggregator.make_aggregator(field_types)
        return self._agg


    def update_value(self, monp, action, vnfr_id):
        """Callback that gets triggered when VNFR's mon param changes.

        Args:
            monp (Gi Object): Gi object msg
            action (rwdts.QueryAction)): Action type
            vnfr_id (str): Vnfr ID
        """
        key = (vnfr_id, monp.id)
        value = NsrMonitoringParam.extract_value(monp)
        if not value:
            return

        # Accumulate the value
        self.monp.update_vnfr_value(key, value)

        # If all values are not available, then don't start
        # the aggregation process.
        if not self.monp.is_ready:
            return

        if self.monp.is_legacy:
            # If no monp are specified then copy over the vnfr's monp data
            value_field, value = value
        else:
            field_types, values = zip(*self.monp.vnfr_values)

            value_field, value = self.make_aggregator(field_types).aggregate(
                    self.monp.aggregation_type,
                    values)

        self.monp.update_ns_value(value_field, value)
        if self.callback:
            self.callback(self.monp.nsr_mon_param_msg)

    @asyncio.coroutine
    def create_pollers(self, create=False, register=False):
        if (create):
            for vnfr_id, monp_id in self.monp.vnfr_ids:
                key = (vnfr_id, monp_id)
                callback = functools.partial(self.update_value, vnfr_id=vnfr_id)
                
                # if the poller is already created, ignore
                if key in self.subscribers:
                    continue
                
                self.subscribers[key] = VnfrMonitoringParamSubscriber(
                    self.loop,
                    self.dts,
                    self.loop,
                    self.project,
                    vnfr_id,
                    monp_id,
                    callback=callback)
                
                if register:
                    yield from self.subscribers[key].register()
        
    @asyncio.coroutine
    def update(self, vnfr):
        self.monp.add_vnfr(vnfr)
        yield from self.create_pollers(create=False, register=True)

    @asyncio.coroutine
    def delete(self, vnfr):
        self.monp.delete_vnfr(vnfr)
        for vnfr_id, monp_id in list(self.subscribers.keys()):
            if vnfr_id != vnfr.id:
                continue

            key = (vnfr_id, monp_id)
            sub = self.subscribers.pop(key)
            sub.deregister()


    @asyncio.coroutine
    def register(self):
        yield from self.create_pollers()

    @asyncio.coroutine
    def start(self):
        for sub in self.subscribers.values():
            yield from sub.register()

    def stop(self):
        for sub in self.subscribers.values():
            sub.deregister()
    
    def retrieve_data(self):
        return self.monp.nsr_mon_param_msg

class NsrMonitorDtsHandler(mano_dts.DtsHandler):
    """ NSR monitoring class """

    def __init__(self, log, dts, loop, project, nsr, constituent_vnfrs):
        """
        Args:
            nsr (RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr): NSR object
            constituent_vnfrs (list): list of VNFRs in NSR
        """
        super().__init__(log, dts, loop, project)

        self.nsr = nsr
        self.constituent_vnfrs = constituent_vnfrs
        self.dts_updates = dict()
        self.dts_update_task = None
        self.mon_params_pollers = []
        
    def nsr_xpath(self):
        return self.project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr" +
                "[nsr:ns-instance-config-ref={}]".format(quoted_key(self.nsr.ns_instance_config_ref)))
    
    def xpath(self, param_id=None):
        return self.project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr" +
            "[nsr:ns-instance-config-ref={}]".format(quoted_key(self.nsr.ns_instance_config_ref)) +
            "/nsr:monitoring-param" +
            ("[nsr:id={}]".format(quoted_key(param_id)) if param_id else ""))
        
    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def on_prepare(xact_info, query_action, ks_path, msg):
            nsrmsg =None
            xpath=None
            if (self.reg_ready):
                if (query_action ==  rwdts.QueryAction.READ):
                    if (len(self.mon_params_pollers)):
                        nsr_dict = {"ns_instance_config_ref": self.nsr.ns_instance_config_ref}
                        nsrmsg = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr. \
                                 from_dict(nsr_dict)
                        xpath = self.nsr_xpath()

                        for poller in self.mon_params_pollers:
                            mp_dict = \
                                      NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_MonitoringParam. \
                                      from_dict(poller.retrieve_data().as_dict())
                            nsrmsg.monitoring_param.append(mp_dict)

            try:
                xact_info.respond_xpath(rsp_code=rwdts.XactRspCode.ACK,
                                        xpath=self.nsr_xpath(),
                                        msg=nsrmsg)
            except rift.tasklets.dts.ResponseError:
                pass

        @asyncio.coroutine
        def on_ready(regh, status):
            self.reg_ready = 1

        handler = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare, on_ready=on_ready)
        self.reg_ready = 0

        self.reg = yield from self.dts.register(xpath=self.xpath(),
                                                flags=rwdts.Flag.PUBLISHER,
                                                handler=handler)

        assert self.reg is not None

    @asyncio.coroutine
    def nsr_monparam_update(self):
        #check if the earlier xact is done or there is an xact
        try:
            if (len(self.dts_updates) == 0):
                self.dts_update_task = None
                return
            nsr_dict = {"ns_instance_config_ref": self.nsr.ns_instance_config_ref}
            nsrmsg = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr.from_dict(nsr_dict)

            for k,v in self.dts_updates.items():
                mp_dict = NsrYang. \
                          YangData_RwProject_Project_NsInstanceOpdata_Nsr_MonitoringParam. \
                          from_dict(v.as_dict())
                nsrmsg.monitoring_param.append(mp_dict)
            self.dts_updates.clear()

            yield from self.dts.query_update(self.nsr_xpath(), rwdts.XactFlag.ADVISE,
                                             nsrmsg)

            self.dts_update_task = None
            if (len(self.dts_updates) == 0):
                #schedule a DTS task to update the NSR again
                self.add_dtsupdate_task()

        except Exception as e:
            self.log.exception("Exception updating NSR mon-param: %s", str(e))

    def add_dtsupdate_task(self):
        if (self.dts_update_task is None):
            self.dts_update_task = asyncio.ensure_future(self.nsr_monparam_update(), loop=self.loop)
        
    def callback(self, nsr_mon_param_msg):
        """Callback that triggers update.
        """
        self.dts_updates[nsr_mon_param_msg.id] = nsr_mon_param_msg
        #schedule a DTS task to update the NSR if one does not exist
        self.add_dtsupdate_task()
    
    @asyncio.coroutine
    def start(self):
        nsd = self.project.get_nsd(self.nsr.nsd_ref)

        mon_params = NsrMonitoringParam.create_nsr_mon_params(
                nsd,
                self.constituent_vnfrs,
                self.project)

        for monp in mon_params:
            poller = NsrMonitoringParamPoller.from_handler(
                    self,
                    monp,
                    callback=self.callback)

            self.mon_params_pollers.append(poller)
            yield from poller.register()
            yield from poller.start()

    @asyncio.coroutine
    def update(self, additional_vnfrs):
        for vnfr in additional_vnfrs:
            for poller in self.mon_params_pollers:
                yield from poller.update(vnfr)

    @asyncio.coroutine
    def delete(self, deleted_vnfrs):
        for vnfr in deleted_vnfrs:
            for poller in self.mon_params_pollers:
                yield from poller.delete(vnfr)

    def stop(self):
        self.deregister()
        for poller in self.mon_params_pollers:
            poller.stop()


    def deregister(self):
        """ de-register with dts """
        if self.reg is not None:
            self.reg.deregister()
            self.reg = None

    def apply_vnfr_mon(self, msg, vnfr_id):
        """ Change in vnfr mon to ne applied"""
        for poller in self.mon_params_pollers:
            if (poller.monp.mon_param_name == msg.name):
                poller.update_value(msg, rwdts.QueryAction.UPDATE, vnfr_id)
