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

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import asyncio
import gi
import json
import ncclient
import ncclient.asyncio_manager
import os
import requests
import shutil
import sys
import tempfile
import time
import uuid
import yaml

from collections import defaultdict
from collections import deque
from enum import Enum
from urllib.parse import urlparse

# disable unsigned certificate warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

gi.require_version('RwYang', '1.0')
gi.require_version('NsdBaseYang', '1.0')
gi.require_version('ProjectNsdYang', '1.0')
gi.require_version('RwDts', '1.0')
gi.require_version('RwNsmYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('NsrYang', '1.0')
gi.require_version('RwTypes', '1.0')
gi.require_version('RwVlrYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('VnfrYang', '1.0')
gi.require_version('ProjectVnfdYang', '1.0')
from gi.repository import (
    RwYang,
    RwNsrYang,
    NsrYang,
    NsdBaseYang,
    ProjectNsdYang as NsdYang,
    RwVlrYang,
    VnfrYang,
    RwVnfrYang,
    RwNsmYang,
    RwsdnalYang,
    RwDts as rwdts,
    RwTypes,
    ProjectVnfdYang,
    ProtobufC,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from rift.mano.utils.ssh_keys import ManoSshKey
import rift.mano.ncclient
import rift.mano.config_data.config
import rift.mano.dts as mano_dts
import rift.tasklets
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
    get_add_delete_update_cfgs,
    DEFAULT_PROJECT,
    )

from . import rwnsm_conman as conman
from . import cloud
from . import publisher
from . import subscriber
from . import xpath
from . import config_value_pool
from . import rwvnffgmgr
from . import scale_group
from . import rwnsmplugin
from . import openmano_nsm
import functools
import collections

class NetworkServiceRecordState(Enum):
    """ Network Service Record State """
    INIT = 101
    VL_INIT_PHASE = 102
    VNF_INIT_PHASE = 103
    VNFFG_INIT_PHASE = 104
    RUNNING = 106
    SCALING_OUT = 107
    SCALING_IN = 108
    TERMINATE = 109
    TERMINATE_RCVD = 110
    VL_TERMINATE_PHASE = 111
    VNF_TERMINATE_PHASE = 112
    VNFFG_TERMINATE_PHASE = 113
    TERMINATED = 114
    FAILED = 115
    VL_INSTANTIATE = 116
    VL_TERMINATE = 117


class NetworkServiceRecordError(Exception):
    """ Network Service Record Error """
    pass


class NetworkServiceDescriptorError(Exception):
    """ Network Service Descriptor Error """
    pass


class VirtualNetworkFunctionRecordError(Exception):
    """ Virtual Network Function Record Error """
    pass


class NetworkServiceDescriptorNotFound(Exception):
    """ Cannot find Network Service Descriptor"""
    pass


class NetworkServiceDescriptorNotFound(Exception):
    """ Network Service Descriptor reference count exists """
    pass

class NsrInstantiationFailed(Exception):
    """ Failed to instantiate network service """
    pass


class VnfInstantiationFailed(Exception):
    """ Failed to instantiate virtual network function"""
    pass


class VnffgInstantiationFailed(Exception):
    """ Failed to instantiate virtual network function"""
    pass


class VnfDescriptorError(Exception):
    """Failed to instantiate virtual network function"""
    pass


class ScalingOperationError(Exception):
    pass


class ScaleGroupMissingError(Exception):
    pass


class PlacementGroupError(Exception):
    pass


class NsrNsdUpdateError(Exception):
    pass


class NsrVlUpdateError(NsrNsdUpdateError):
    pass

class VirtualLinkRecordError(Exception):
    """ Virtual Links Record Error """
    pass


class VlRecordState(Enum):
    """ VL Record State """
    INIT = 101
    INSTANTIATION_PENDING = 102
    ACTIVE = 103
    TERMINATE_PENDING = 104
    TERMINATED = 105
    FAILED = 106


class VnffgRecordState(Enum):
    """ VNFFG Record State """
    INIT = 101
    INSTANTIATION_PENDING = 102
    ACTIVE = 103
    TERMINATE_PENDING = 104
    TERMINATED = 105
    FAILED = 106


class VnffgRecord(object):
    """ Vnffg Records class"""
    SFF_DP_PORT = 4790
    SFF_MGMT_PORT = 5000
    def __init__(self, dts, log, loop, vnffgmgr, nsr, nsr_name, vnffgd_msg, sdn_account_name,cloud_account_name):

        self._dts = dts
        self._log = log
        self._loop = loop
        self._vnffgmgr = vnffgmgr
        self._nsr = nsr
        self._nsr_name = nsr_name
        self._vnffgd_msg = vnffgd_msg
        self._cloud_account_name = cloud_account_name
        if sdn_account_name is None:
            self._sdn_account_name = ''
        else:
            self._sdn_account_name = sdn_account_name

        self._vnffgr_id = str(uuid.uuid4())
        self._vnffgr_rsp_id = list()
        self._vnffgr_state = VnffgRecordState.INIT

    @property
    def id(self):
        """ VNFFGR id """
        return self._vnffgr_id

    @property
    def state(self):
        """ state of this VNF """
        return self._vnffgr_state

    def fetch_vnffgr(self):
        """
        Get VNFFGR message to be published
        """

        if self._vnffgr_state == VnffgRecordState.INIT:
            vnffgr_dict = {"id": self._vnffgr_id,
                           "vnffgd_id_ref": self._vnffgd_msg.id,
                           "vnffgd_name_ref": self._vnffgd_msg.name,
                           "sdn_account": self._sdn_account_name,
                           "operational_status": 'init',
                           }
            vnffgr = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_Vnffgr.from_dict(vnffgr_dict)
        elif self._vnffgr_state == VnffgRecordState.TERMINATED:
            vnffgr_dict = {"id": self._vnffgr_id,
                           "vnffgd_id_ref": self._vnffgd_msg.id,
                           "vnffgd_name_ref": self._vnffgd_msg.name,
                           "sdn_account": self._sdn_account_name,
                           "operational_status": 'terminated',
                           }
            vnffgr = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_Vnffgr.from_dict(vnffgr_dict)
        else:
            try:
                vnffgr = self._vnffgmgr.fetch_vnffgr(self._vnffgr_id)
            except Exception:
                self._log.exception("Fetching VNFFGR for VNFFG with id %s failed", self._vnffgr_id)
                self._vnffgr_state = VnffgRecordState.FAILED
                vnffgr_dict = {"id": self._vnffgr_id,
                               "vnffgd_id_ref": self._vnffgd_msg.id,
                               "vnffgd_name_ref": self._vnffgd_msg.name,
                               "sdn_account": self._sdn_account_name,
                               "operational_status": 'failed',
                               }
                vnffgr = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_Vnffgr.from_dict(vnffgr_dict)

        return vnffgr

    @asyncio.coroutine
    def vnffgr_create_msg(self):
        """ Virtual Link Record message for Creating VLR in VNS """
        vnffgr_dict = {"id": self._vnffgr_id,
                       "vnffgd_id_ref": self._vnffgd_msg.id,
                       "vnffgd_name_ref": self._vnffgd_msg.name,
                       "sdn_account": self._sdn_account_name,
                       "cloud_account": self._cloud_account_name,
                    }
        vnffgr = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_Vnffgr.from_dict(vnffgr_dict)
        for rsp in self._vnffgd_msg.rsp:
            vnffgr_rsp = vnffgr.rsp.add()
            vnffgr_rsp.id = str(uuid.uuid4())
            vnffgr_rsp.name = self._nsr.name + '.' + rsp.name
            self._vnffgr_rsp_id.append(vnffgr_rsp.id)
            vnffgr_rsp.vnffgd_rsp_id_ref =  rsp.id
            vnffgr_rsp.vnffgd_rsp_name_ref = rsp.name
            for rsp_cp_ref in rsp.vnfd_connection_point_ref:
                vnfd =  [vnfr.vnfd for vnfr in self._nsr.vnfrs.values() if vnfr.vnfd.id == rsp_cp_ref.vnfd_id_ref]
                self._log.debug("VNFD message during VNFFG instantiation is %s",vnfd)
                if len(vnfd) > 0 and vnfd[0].has_field('service_function_type'):
                    self._log.debug("Service Function Type for VNFD ID %s is %s",
                                    rsp_cp_ref.vnfd_id_ref, vnfd[0].service_function_type)
                else:
                    self._log.error("Service Function Type not available for VNFD ID %s; Skipping in chain",
                                    rsp_cp_ref.vnfd_id_ref)
                    continue

                vnfr_cp_ref =  vnffgr_rsp.vnfr_connection_point_ref.add()
                vnfr_cp_ref.member_vnf_index_ref = rsp_cp_ref.member_vnf_index_ref
                vnfr_cp_ref.hop_number = rsp_cp_ref.order
                vnfr_cp_ref.vnfd_id_ref =rsp_cp_ref.vnfd_id_ref
                vnfr_cp_ref.service_function_type = vnfd[0].service_function_type
                for nsr_vnfr in self._nsr.vnfrs.values():
                   if (nsr_vnfr.vnfd.id == vnfr_cp_ref.vnfd_id_ref and
                      nsr_vnfr.member_vnf_index == vnfr_cp_ref.member_vnf_index_ref):
                       vnfr_cp_ref.vnfr_id_ref = nsr_vnfr.id
                       vnfr_cp_ref.vnfr_name_ref = nsr_vnfr.name
                       vnfr_cp_ref.vnfr_connection_point_ref = rsp_cp_ref.vnfd_connection_point_ref

                       vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                       self._log.debug(" Received VNFR is %s", vnfr)
                       while vnfr.operational_status != 'running':
                           self._log.info("Received vnf op status is %s; retrying",vnfr.operational_status)
                           if vnfr.operational_status == 'failed':
                               self._log.error("Fetching VNFR for  %s failed", vnfr.id)
                               raise NsrInstantiationFailed("Failed NS %s instantiation due to VNFR %s failure" %
                                                            (self.id, vnfr.id))
                           yield from asyncio.sleep(2, loop=self._loop)
                           vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                           self._log.debug("Received VNFR is %s", vnfr)

                       vnfr_cp_ref.connection_point_params.mgmt_address =  vnfr.mgmt_interface.ip_address
                       for cp in vnfr.connection_point:
                           if cp.name == vnfr_cp_ref.vnfr_connection_point_ref:
                               vnfr_cp_ref.connection_point_params.port_id = cp.connection_point_id
                               vnfr_cp_ref.connection_point_params.name = self._nsr.name + '.' + cp.name
                               for vdu in vnfr.vdur:
                                   for intf in vdu.interface:
                                       if intf.type_yang == "EXTERNAL" and intf.external_connection_point_ref == vnfr_cp_ref.vnfr_connection_point_ref:
                                           vnfr_cp_ref.connection_point_params.vm_id =  vdu.vim_id
                                           self._log.debug("VIM ID for CP %s in VNFR %s is %s",cp.name,nsr_vnfr.id,
                                                            vnfr_cp_ref.connection_point_params.vm_id)
                                           break

                               vnfr_cp_ref.connection_point_params.address =  cp.ip_address
                               vnfr_cp_ref.connection_point_params.port = VnffgRecord.SFF_DP_PORT

        for vnffgd_classifier in self._vnffgd_msg.classifier:
            _rsp =  [rsp for rsp in vnffgr.rsp if rsp.vnffgd_rsp_id_ref == vnffgd_classifier.rsp_id_ref]
            if len(_rsp) > 0:
                rsp_id_ref = _rsp[0].id
                rsp_name = _rsp[0].name
            else:
                self._log.error("RSP with ID %s not found during classifier creation for classifier id %s",
                                vnffgd_classifier.rsp_id_ref,vnffgd_classifier.id)
                continue
            vnffgr_classifier = vnffgr.classifier.add()
            vnffgr_classifier.id = vnffgd_classifier.id
            vnffgr_classifier.name =  self._nsr.name + '.' + vnffgd_classifier.name
            _rsp[0].classifier_name = vnffgr_classifier.name
            vnffgr_classifier.rsp_id_ref = rsp_id_ref
            vnffgr_classifier.rsp_name = rsp_name
            for nsr_vnfr in self._nsr.vnfrs.values():
               if (nsr_vnfr.vnfd.id == vnffgd_classifier.vnfd_id_ref and
                      nsr_vnfr.member_vnf_index == vnffgd_classifier.member_vnf_index_ref):
                       vnffgr_classifier.vnfr_id_ref = nsr_vnfr.id
                       vnffgr_classifier.vnfr_name_ref = nsr_vnfr.name
                       vnffgr_classifier.vnfr_connection_point_ref = vnffgd_classifier.vnfd_connection_point_ref

                       if nsr_vnfr.vnfd.service_function_chain == 'CLASSIFIER':
                           vnffgr_classifier.sff_name = nsr_vnfr.name

                       vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                       self._log.debug(" Received VNFR is %s", vnfr)
                       while vnfr.operational_status != 'running':
                           self._log.info("Received vnf op status is %s; retrying",vnfr.operational_status)
                           if vnfr.operational_status == 'failed':
                               self._log.error("Fetching VNFR for  %s failed", vnfr.id)
                               raise NsrInstantiationFailed("Failed NS %s instantiation due to VNFR %s failure" %
                                                            (self.id, vnfr.id))
                           yield from asyncio.sleep(2, loop=self._loop)
                           vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                           self._log.debug("Received VNFR is %s", vnfr)

                       for cp in vnfr.connection_point:
                           if cp.name == vnffgr_classifier.vnfr_connection_point_ref:
                               vnffgr_classifier.port_id = cp.connection_point_id
                               vnffgr_classifier.ip_address = cp.ip_address
                               for vdu in vnfr.vdur:
                                   for intf in vdu.interface:
                                       if intf.type_yang == "EXTERNAL" and intf.external_connection_point_ref == vnffgr_classifier.vnfr_connection_point_ref:
                                           vnffgr_classifier.vm_id =  vdu.vim_id
                                           self._log.debug("VIM ID for CP %s in VNFR %s is %s",
                                                           cp.name,nsr_vnfr.id,
                                                           vnfr_cp_ref.connection_point_params.vm_id)
                                           break

        self._log.info("VNFFGR msg to be sent is %s", vnffgr)
        return vnffgr

    @asyncio.coroutine
    def vnffgr_nsr_sff_list(self):
        """ SFF List for VNFR """
        sff_list = {}
        sf_list = [nsr_vnfr.name for nsr_vnfr in self._nsr.vnfrs.values() if nsr_vnfr.vnfd.service_function_chain == 'SF']

        for nsr_vnfr in self._nsr.vnfrs.values():
            if (nsr_vnfr.vnfd.service_function_chain == 'CLASSIFIER' or nsr_vnfr.vnfd.service_function_chain == 'SFF'):
                vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                self._log.debug(" Received VNFR is %s", vnfr)
                while vnfr.operational_status != 'running':
                    self._log.info("Received vnf op status is %s; retrying",vnfr.operational_status)
                    if vnfr.operational_status == 'failed':
                       self._log.error("Fetching VNFR for  %s failed", vnfr.id)
                       raise NsrInstantiationFailed("Failed NS %s instantiation due to VNFR %s failure" % (self.id, vnfr.id))
                    yield from asyncio.sleep(2, loop=self._loop)
                    vnfr = yield from self._nsr.fetch_vnfr(nsr_vnfr.xpath)
                    self._log.debug("Received VNFR is %s", vnfr)

                sff =  RwsdnalYang.YangData_RwProject_Project_Vnffgs_VnffgChain_Sff()
                sff_list[nsr_vnfr.vnfd.id] = sff
                sff.name = nsr_vnfr.name
                sff.function_type = nsr_vnfr.vnfd.service_function_chain

                sff.mgmt_address = vnfr.mgmt_interface.ip_address
                sff.mgmt_port = VnffgRecord.SFF_MGMT_PORT
                for cp in vnfr.connection_point:
                    sff_dp = sff.dp_endpoints.add()
                    sff_dp.name = self._nsr.name + '.' + cp.name
                    sff_dp.address = cp.ip_address
                    sff_dp.port  = VnffgRecord.SFF_DP_PORT
                if nsr_vnfr.vnfd.service_function_chain == 'SFF':
                    for sf_name in sf_list:
                        _sf = sff.vnfr_list.add()
                        _sf.vnfr_name = sf_name

        return sff_list

    @asyncio.coroutine
    def instantiate(self):
        """ Instantiate this VNFFG """

        self._log.info("Instaniating VNFFGR with vnffgd %s",
                       self._vnffgd_msg)


        vnffgr_request = yield from self.vnffgr_create_msg()
        vnffg_sff_list = yield from self.vnffgr_nsr_sff_list()

        try:
            vnffgr = self._vnffgmgr.create_vnffgr(vnffgr_request,self._vnffgd_msg.classifier,vnffg_sff_list)
        except Exception as e:
            self._log.exception("VNFFG instantiation failed: %s", str(e))
            self._vnffgr_state = VnffgRecordState.FAILED
            raise NsrInstantiationFailed("Failed NS %s instantiation due to VNFFGR %s failure" % (self.id, vnffgr_request.id))

        self._vnffgr_state = VnffgRecordState.INSTANTIATION_PENDING

        self._log.info("Instantiated VNFFGR :%s", vnffgr)
        self._vnffgr_state = VnffgRecordState.ACTIVE

        self._log.info("Invoking update_state to update NSR state for NSR ID: %s", self._nsr.id)
        yield from self._nsr.update_state()

    def vnffgr_in_vnffgrm(self):
        """ Is there a VNFR record in VNFM """
        if (self._vnffgr_state == VnffgRecordState.ACTIVE or
                self._vnffgr_state == VnffgRecordState.INSTANTIATION_PENDING or
                self._vnffgr_state == VnffgRecordState.FAILED):
            return True

        return False

    @asyncio.coroutine
    def terminate(self):
        """ Terminate this VNFFGR """
        if not self.vnffgr_in_vnffgrm():
            self._log.error("Ignoring terminate request for id %s in state %s",
                            self.id, self._vnffgr_state)
            return

        self._log.info("Terminating VNFFGR id:%s", self.id)
        self._vnffgr_state = VnffgRecordState.TERMINATE_PENDING

        self._vnffgmgr.terminate_vnffgr(self._vnffgr_id)

        self._vnffgr_state = VnffgRecordState.TERMINATED
        self._log.debug("Terminated VNFFGR id:%s", self.id)


class VirtualLinkRecord(object):
    """ Virtual Link Records class"""
    XPATH = "D,/vlr:vlr-catalog/vlr:vlr"
    @staticmethod
    @asyncio.coroutine
    def create_record(dts, log, loop, project, nsr_name, vld_msg,
                      datacenter, ip_profile, nsr_id, restart_mode=False):
        """Creates a new VLR object based on the given data.

        If restart mode is enabled, then we look for existing records in the
        DTS and create a VLR records using the exiting data(ID)

        Returns:
            VirtualLinkRecord
        """
        vlr_obj = VirtualLinkRecord(
                      dts,
                      log,
                      loop,
                      project,
                      nsr_name,
                      vld_msg,
                      datacenter,
                      ip_profile,
                      nsr_id,
                      )

        if restart_mode:
            res_iter = yield from dts.query_read(
                              project.add_project("D,/vlr:vlr-catalog/vlr:vlr"),
                              rwdts.XactFlag.MERGE)

            for fut in res_iter:
                response = yield from fut
                vlr = response.result

                # Check if the record is already present, if so use the ID of
                # the existing record. Since the name of the record is uniquely
                # formed we can use it as a search key!
                if vlr.name == vlr_obj.name:
                    vlr_obj.reset_id(vlr.id)
                    break

        return vlr_obj

    def __init__(self, dts, log, loop, project, nsr_name, vld_msg,
                 datacenter, ip_profile, nsr_id):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._nsr_name = nsr_name
        self._vld_msg = vld_msg
        self._datacenter_name = datacenter
        self._assigned_subnet = None
        self._nsr_id = nsr_id
        self._ip_profile = ip_profile
        self._vlr_id = str(uuid.uuid4())
        self._state = VlRecordState.INIT
        self._prev_state = None
        self._create_time = int(time.time())
        self.state_failed_reason = None

    @property
    def xpath(self):
        """ path for this object """
        return self._project.add_project("D,/vlr:vlr-catalog/vlr:vlr[vlr:id={}]".
                                         format(quoted_key(self._vlr_id)))

    @property
    def id(self):
        """ VLR id """
        return self._vlr_id

    @property
    def nsr_name(self):
        """ Get NSR name for this VL """
        return self.nsr_name

    @property
    def vld_msg(self):
        """ Virtual Link Desciptor """
        return self._vld_msg

    @property
    def assigned_subnet(self):
        """ Subnet assigned to this VL"""
        return self._assigned_subnet

    @property
    def name(self):
        """
        Get the name for this VLR.
        VLR name is "nsr name:VLD name"
        """
        if self.vld_msg.vim_network_name:
            return self.vld_msg.vim_network_name
        elif self.vld_msg.name == "multisite":
            # This is a temporary hack to identify manually provisioned inter-site network
            return self.vld_msg.name
        else:
            return self._project.name + "." +self._nsr_name + "." + self.vld_msg.name

    @property
    def datacenter_name(self):
        """ Datacenter  that this VLR should be created in """
        return self._datacenter_name

    @staticmethod
    def vlr_xpath(vlr):
        """ Get the VLR path from VLR """
        return (VirtualLinkRecord.XPATH + "[vlr:id={}]").format(quoted_key(vlr.id))

    @property
    def state(self):
        """ VLR state """
        return self._state

    @state.setter
    def state(self, value):
        """ VLR set state """
        self._state = value

    @property
    def prev_state(self):
        """ VLR previous state """
        return self._prev_state

    @prev_state.setter
    def prev_state(self, value):
        """ VLR set previous state """
        self._prev_state = value

    @property
    def vlr_msg(self):
        """ Virtual Link Record message for Creating VLR in VNS """
        vld_fields = ["short_name",
                      "vendor",
                      "description",
                      "version",
                      "type_yang",
                      "vim_network_name",
                      "provider_network"]

        vld_copy_dict = {k: v for k, v in self.vld_msg.as_dict().items()
                         if k in vld_fields}

        vlr_dict = {"id": self._vlr_id,
                    "nsr_id_ref": self._nsr_id,
                    "vld_ref": self.vld_msg.id,
                    "name": self.name,
                    "create_time": self._create_time,
                    "datacenter": self._datacenter_name,
                    }

        if self._ip_profile and self._ip_profile.has_field('ip_profile_params'):
            vlr_dict['ip_profile_params' ] = self._ip_profile.ip_profile_params.as_dict()


        vlr_dict.update(vld_copy_dict)
        vlr = RwVlrYang.YangData_RwProject_Project_VlrCatalog_Vlr.from_dict(vlr_dict)

        if self.vld_msg.has_field('virtual_connection_points'):
            for cp in self.vld_msg.virtual_connection_points:
                vcp = vlr.virtual_connection_points.add()
                vcp.from_dict(cp.as_dict())
        return vlr

    def reset_id(self, vlr_id):
        self._vlr_id = vlr_id

    def create_nsr_vlr_msg(self, vnfrs):
        """ The VLR message"""
        nsr_vlr = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_Vlr()
        nsr_vlr.vlr_ref = self._vlr_id
        nsr_vlr.assigned_subnet = self.assigned_subnet
        nsr_vlr.datacenter = self._datacenter_name

        for conn in self.vld_msg.vnfd_connection_point_ref:
            for vnfr in vnfrs:
                if (vnfr.vnfd.id == conn.vnfd_id_ref and
                        vnfr.member_vnf_index == conn.member_vnf_index_ref and
                        self._datacenter_name == vnfr._datacenter_name):
                    cp_entry = nsr_vlr.vnfr_connection_point_ref.add()
                    cp_entry.vnfr_id = vnfr.id
                    cp_entry.connection_point = conn.vnfd_connection_point_ref

        return nsr_vlr

    @asyncio.coroutine
    def instantiate(self):
        """ Instantiate this VL """
        self._log.debug("Instaniating VLR key %s, vld %s",
                        self.xpath, self._vld_msg)
        vlr = None
        self._state = VlRecordState.INSTANTIATION_PENDING
        self._log.debug("Executing VL create path:%s msg:%s",
                        self.xpath, self.vlr_msg)

        with self._dts.transaction(flags=0) as xact:
            block = xact.block_create()
            block.add_query_create(self.xpath, self.vlr_msg)
            self._log.debug("Executing VL create path:%s msg:%s",
                            self.xpath, self.vlr_msg)
            res_iter = yield from block.execute(now=True)
            for ent in res_iter:
                res = yield from ent
                vlr = res.result

            if vlr is None:
                self._state = VlRecordState.FAILED
                raise NsrInstantiationFailed("Failed NS %s instantiation due to empty response" % self.id)

        if vlr.operational_status == 'failed':
            self._log.debug("NS Id:%s VL creation failed for vlr id %s", self.id, vlr.id)
            self._state = VlRecordState.FAILED
            raise NsrInstantiationFailed("Failed VL %s instantiation (%s)" % (vlr.id, vlr.operational_status_details))

        self._log.info("Instantiated VL with xpath %s and vlr:%s",
                       self.xpath, vlr)
        self._assigned_subnet = vlr.assigned_subnet

    def vlr_in_vns(self):
        """ Is there a VLR record in VNS """
        if (self._state == VlRecordState.ACTIVE or
            self._state == VlRecordState.INSTANTIATION_PENDING or
            self._state == VlRecordState.TERMINATE_PENDING or
            self._state == VlRecordState.FAILED):
            return True

        return False

    @asyncio.coroutine
    def terminate(self):
        """ Terminate this VL """
        if not self.vlr_in_vns():
            self._log.debug("Ignoring terminate request for id %s in state %s",
                            self.id, self._state)
            return

        self._log.debug("Terminating VL id:%s", self.id)
        self._state = VlRecordState.TERMINATE_PENDING

        with self._dts.transaction(flags=0) as xact:
            block = xact.block_create()
            block.add_query_delete(self.xpath)
            yield from block.execute(flags=0, now=True)

        self._state = VlRecordState.TERMINATED
        self._log.debug("Terminated VL id:%s", self.id)

    def set_state_from_op_status(self, operational_status):
        """ Set the state of this VL based on operational_status"""

        self._log.debug("set_state_from_op_status called for vlr id %s with value %s", self.id, operational_status)
        if operational_status == 'running':
            self._state = VlRecordState.ACTIVE
        elif operational_status == 'failed':
            self._state = VlRecordState.FAILED
        elif operational_status == 'vl_alloc_pending':
            self._state = VlRecordState.INSTANTIATION_PENDING
        else:
            raise VirtualLinkRecordError("Unknown operational_status %s" % (operational_status))

class VnfRecordState(Enum):
    """ Vnf Record State """
    INIT = 101
    INSTANTIATION_PENDING = 102
    ACTIVE = 103
    TERMINATE_PENDING = 104
    TERMINATED = 105
    FAILED = 106


class VirtualNetworkFunctionRecord(object):
    """ Virtual Network Function Record class"""
    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr"

    @staticmethod
    @asyncio.coroutine
    def create_record(dts, log, loop, project, vnfd, nsr_config, const_vnfd_msg, nsd_id, nsr_name,
                datacenter_name, nsr_id, group_name, group_instance_id,
                placement_groups, cloud_config, restart_mode=False):
        """Creates a new VNFR object based on the given data.

        If restart mode is enabled, then we look for existing records in the
        DTS and create a VNFR records using the exiting data(ID)

        Returns:
            VirtualNetworkFunctionRecord
        """

        vnfr_obj = VirtualNetworkFunctionRecord(
                          dts,
                          log,
                          loop,
                          project,
                          vnfd,
                          nsr_config,
                          const_vnfd_msg,
                          nsd_id,
                          nsr_name,
                          datacenter_name,
                          nsr_id,
                          group_name,
                          group_instance_id,
                          placement_groups,
                          cloud_config,
                          restart_mode=restart_mode)

        if restart_mode:
            res_iter = yield from dts.query_read(
                              project.add_project("D,/vnfr:vnfr-catalog/vnfr:vnfr"),
                              rwdts.XactFlag.MERGE)

            for fut in res_iter:
                response = yield from fut
                vnfr = response.result

                if vnfr.name == vnfr_obj.name:
                    vnfr_obj.reset_id(vnfr.id)
                    break

        return vnfr_obj

    def __init__(self,
                 dts,
                 log,
                 loop,
                 project,
                 vnfd,
                 nsr_config,
                 const_vnfd_msg,
                 nsd_id,
                 nsr_name,
                 datacenter_name,
                 nsr_id,
                 group_name=None,
                 group_instance_id=None,
                 placement_groups = [],
                 cloud_config = None,
                 restart_mode = False):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._vnfd = vnfd
        self._nsr_config = nsr_config
        self._const_vnfd_msg = const_vnfd_msg
        self._nsd_id = nsd_id
        self._nsr_name = nsr_name
        self._nsr_id = nsr_id
        self._datacenter_name = datacenter_name
        self._group_name = group_name
        self._group_instance_id = group_instance_id
        self._placement_groups = placement_groups
        self._cloud_config = cloud_config
        self.restart_mode = restart_mode

        self._config_status = NsrYang.ConfigStates.INIT
        self._create_time = int(time.time())

        self._prev_state = VnfRecordState.INIT
        self._state = VnfRecordState.INIT
        self._state_failed_reason = None

        self._active_vdus = 0

        self.config_store = rift.mano.config_data.config.ConfigStore(self._log)
        self.configure()

        self._vnfr_id = str(uuid.uuid4())
        self._name = None

        self.substitute_vnf_input_parameters = VnfInputParameterSubstitution(self._log,
                                                                             self._const_vnfd_msg,
                                                                             self._project)
        self._vnfr_msg = self.create_vnfr_msg()
        self._log.debug("Set VNFR {} config type to {}".
                        format(self.name, self.config_type))


        if group_name is None and group_instance_id is not None:
            raise ValueError("Group instance id must not be provided with an empty group name")

    @property
    def id(self):
        """ VNFR id """
        return self._vnfr_id

    @property
    def xpath(self):
        """ VNFR xpath """
        return self._project.add_project("D,/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]"
                                         .format(quoted_key(self.id)))

    @property
    def vnfr_msg(self):
        """ VNFR message """
        return self._vnfr_msg

    @property
    def const_vnfr_msg(self):
        """ VNFR message """
        return RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConstituentVnfrRef(
            vnfr_id=self.id, datacenter=self._datacenter_name)

    @property
    def vnfd(self):
        """ vnfd """
        return self._vnfd

    @property
    def datacenter_name(self):
        """ Datacenter that this VNF should be created in """
        return self._datacenter_name


    @property
    def active(self):
        """ Is this VNF actve """
        return True if self._state == VnfRecordState.ACTIVE else False

    @property
    def state(self):
        """ state of this VNF """
        return self._state

    @property
    def state_failed_reason(self):
        """ Error message in case this VNF is in failed state """
        return self._state_failed_reason

    @property
    def member_vnf_index(self):
        """ Member VNF index """
        return self._const_vnfd_msg.member_vnf_index

    @property
    def nsr_name(self):
        """ NSR name"""
        return self._nsr_name

    @property
    def name(self):
        """ Name of this VNFR """
        if self._name is not None:
            return self._name

        name_tags = [self._project.name, self._nsr_name]

        if self._group_name is not None:
            name_tags.append(self._group_name)

        if self._group_instance_id is not None:
            name_tags.append(str(self._group_instance_id))

        name_tags.extend([self.vnfd.name, str(self.member_vnf_index)])

        self._name = "__".join(name_tags)

        return self._name

    @staticmethod
    def vnfr_xpath(vnfr):
        """ Get the VNFR path from VNFR """
        return (VirtualNetworkFunctionRecord.XPATH +
                "[vnfr:id={}]").format(quoted_key(vnfr.id))

    @property
    def config_type(self):
        cfg_types = ['netconf', 'juju', 'script']
        for method in cfg_types:
            if self._vnfd.vnf_configuration.has_field(method):
                return method
        return 'none'

    @property
    def config_status(self):
        """Return the config status as YANG ENUM string"""
        self._log.debug("Map VNFR {} config status {} ({})".
                        format(self.name, self._config_status, self.config_type))
        if self.config_type == 'none':
            return 'config_not_needed'
        elif self._config_status == NsrYang.ConfigStates.CONFIGURED:
            return 'configured'
        elif self._config_status == NsrYang.ConfigStates.FAILED:
            return 'failed'

        return 'configuring'

    def set_state(self, state):
        """ set the state of this object """
        self._prev_state = self._state
        self._state = state

    def reset_id(self, vnfr_id):
        self._vnfr_id = vnfr_id
        self._vnfr_msg = self.create_vnfr_msg()

    def configure(self):
        self.config_store.merge_vnfd_config(
                    self._project.name,
                    self._nsd_id,
                    self._vnfd,
                    self.member_vnf_index,
                    )

    def create_vnfr_msg(self):
        """ VNFR message for this VNFR """
        vnfd_fields = [
                "short_name",
                "vendor",
                "description",
                "version",
                "type_yang",
                ]
        vnfd_copy_dict = {k: v for k, v in self._vnfd.as_dict().items() if k in vnfd_fields}
        vnfr_dict = {
                "id": self.id,
                "nsr_id_ref": self._nsr_id,
                "name": self.name,
                "datacenter": self._datacenter_name,
                "config_status": self.config_status
                }
        vnfr_dict.update(vnfd_copy_dict)

        vnfr = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr.from_dict(vnfr_dict)
        vnfr.vnfd = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_Vnfd. \
                    from_dict(self.vnfd.as_dict())
        vnfr.member_vnf_index_ref = self.member_vnf_index
        vnfr.vnf_configuration.from_dict(self._vnfd.vnf_configuration.as_dict())

        if self._vnfd.mgmt_interface.has_field("port"):
            vnfr.mgmt_interface.port = self._vnfd.mgmt_interface.port

        for group_info in self._placement_groups:
            group = vnfr.placement_groups_info.add()
            group.from_dict(group_info.as_dict())

        if self._cloud_config and len(self._cloud_config.as_dict()):
            self._log.debug("Cloud config during vnfr create is {}".format(self._cloud_config))
            vnfr.cloud_config = self._cloud_config

        # UI expects the monitoring param field to exist
        vnfr.monitoring_param = []

        self._log.debug("Get vnfr_msg for VNFR {} : {}".format(self.name, vnfr))

        if self.restart_mode:
            vnfr.operational_status = 'init'
        else:
            # Set Operational Status as pre-init for Input Param Substitution
            if self._state not in [VnfRecordState.ACTIVE, VnfRecordState.TERMINATE_PENDING,
                                  VnfRecordState.TERMINATED, VnfRecordState.FAILED]:
                # To make sure that an active VNFR is not updated with a previous state.
                # This can happen during config state updates.
                vnfr.operational_status = 'pre_init'
            else:
                vnfr.operational_status = self._state

        return vnfr

    @asyncio.coroutine
    def update_vnfm(self):
        self._log.debug("Send an update to VNFM for VNFR {} with {}".
                        format(self.name, self.vnfr_msg))
        yield from self._dts.query_update(
                self.xpath,
                rwdts.XactFlag.REPLACE,
                self.vnfr_msg
                )

    def get_config_status(self):
        """Return the config status as YANG ENUM"""
        return self._config_status

    @asyncio.coroutine
    def set_config_status(self, status):

        def status_to_string(status):
            status_dc = {
                NsrYang.ConfigStates.INIT : 'init',
                NsrYang.ConfigStates.CONFIGURING : 'configuring',
                NsrYang.ConfigStates.CONFIG_NOT_NEEDED : 'config_not_needed',
                NsrYang.ConfigStates.CONFIGURED : 'configured',
                NsrYang.ConfigStates.FAILED : 'failed',
            }

            return status_dc[status]

        self._log.debug("Update VNFR {} from {} ({}) to {}".
                        format(self.name, self._config_status,
                               self.config_type, status))
        if self._config_status == NsrYang.ConfigStates.CONFIGURED:
            self._log.warning("Updating already configured VNFR {}".
                              format(self.name))
            return

        if self._config_status != status:
            try:
                self._config_status = status
                # I don't think this is used. Original implementor can check.
                # Caused Exception, so corrected it by status_to_string
                # But not sure whats the use of this variable?
                self.vnfr_msg.config_status = status_to_string(status)
            except Exception as e:
                self._log.exception("Exception=%s", str(e))

            self._log.debug("Updated VNFR {} status to {}".format(self.name, status))

            if self._config_status != NsrYang.ConfigStates.INIT:
                try:
                    # Publish only after VNFM has the VNFR created
                    yield from self.update_vnfm()
                except Exception as e:
                    self._log.error("Exception updating VNFM with new status {} of VNFR {}: {}".
                                format(status, self.name, e))
                    self._log.exception(e)

    def is_configured(self):
        if self.config_type == 'none':
            return True

        if self._config_status == NsrYang.ConfigStates.CONFIGURED:
            return True

        return False

    @asyncio.coroutine
    def update_config_primitives(self, vnf_config, nsr):
        # Update only after we are configured
        if self._config_status == NsrYang.ConfigStates.INIT:
            return

        if not vnf_config.as_dict():
            return

        self._log.debug("Update VNFR {} config: {}".
                        format(self.name, vnf_config.as_dict()))

        # Update config primitive
        updated = False
        for prim in self._vnfd.vnf_configuration.config_primitive:
            for p in vnf_config.config_primitive:
                if prim.name == p.name:
                    for param in prim.parameter:
                        for pa in p.parameter:
                            if pa.name == param.name:
                                if pa.default_value and \
                                   (pa.default_value != param.default_value):
                                    param.default_value = pa.default_value
                                    param.read_only = pa.read_only
                                    updated = True
                                break
                    self._log.debug("Prim: {}".format(prim.as_dict()))
                    break

        if updated:
            self._log.debug("Updated VNFD {} config: {}".
                            format(self._vnfd.name,
                                   self._vnfd.vnf_configuration))
            self._vnfr_msg = self.create_vnfr_msg()

            try:
                yield from nsr.nsm_plugin.update_vnfr(self)
            except Exception as e:
                self._log.error("Exception updating VNFM with new config "
                                "primitive for VNFR {}: {}".
                                format(self.name, e))
                self._log.exception(e)

    @asyncio.coroutine
    def instantiate(self, nsr):
        """ Instantiate this VNFR"""

        self._log.debug("Instaniating VNFR key %s, vnfd %s",
                        self.xpath, self._vnfd)

        self._log.debug("Create VNF with xpath %s and vnfr %s",
                        self.xpath, self.vnfr_msg)

        self.set_state(VnfRecordState.INSTANTIATION_PENDING)

        def find_vlr_for_cp(conn):
            """ Find VLR for the given connection point """
            for vlr_id, vlr in nsr.vlrs.items():
                for vnfd_cp in vlr.vld_msg.vnfd_connection_point_ref:
                    if (vnfd_cp.vnfd_id_ref == self._vnfd.id and
                            vnfd_cp.vnfd_connection_point_ref == conn.name and
                            vnfd_cp.member_vnf_index_ref == self.member_vnf_index and
                             vlr._datacenter_name == self._datacenter_name):
                        self._log.debug("Found VLR for cp_name:%s and vnf-index:%d",
                                        conn.name, self.member_vnf_index)
                        return vlr
            return None

        # For every connection point in the VNFD fill in the identifier
        self._log.debug("Add connection point for VNF %s: %s",
                        self.vnfr_msg.name, self._vnfd.connection_point)
        for conn_p in self._vnfd.connection_point:
            cpr = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_ConnectionPoint()
            cpr.name = conn_p.name
            cpr.type_yang = conn_p.type_yang
            if conn_p.has_field('port_security_enabled'):
              cpr.port_security_enabled = conn_p.port_security_enabled

            vlr_ref = find_vlr_for_cp(conn_p)
            if vlr_ref is None:
                msg = "Failed to find VLR for cp = %s" % conn_p.name
                self._log.debug("%s", msg)
#                raise VirtualNetworkFunctionRecordError(msg)
                continue

            cpr.vlr_ref = vlr_ref.id

            self.vnfr_msg.connection_point.append(cpr)
            self._log.debug("Connection point [%s] added, vnf id=%s vnfd id=%s",
                            cpr, self.vnfr_msg.id, self.vnfr_msg.vnfd.id)

        self._log.debug("VNFR {} restart mode {}".
                        format(self.vnfr_msg.id, self.restart_mode))
        if not self.restart_mode:
            # Checking for NS Terminate.
            if nsr._ns_terminate_received == False:
                # Create with pre-init operational state publishes the vnfr for substitution.
                yield from self._dts.query_create(self.xpath, 0, self.vnfr_msg)
                # Call to substitute VNF Input Parameter
                self.substitute_vnf_input_parameters(self.vnfr_msg, self._nsr_config)
                # Calling Update with pre-init operational data after Param substitution to instatntiate vnfr
                yield from self._dts.query_update(self.xpath, 0, self.vnfr_msg)

        else:
            yield from self._dts.query_update(self.xpath,
                                              0,
                                              self.vnfr_msg)

        self._log.info("Created VNF with xpath %s and vnfr %s",
                        self.xpath, self.vnfr_msg)

    @asyncio.coroutine
    def update_state(self, vnfr_msg):
        """ Update this VNFR"""
        if vnfr_msg.operational_status == "running":
            if self.vnfr_msg.operational_status != "running":
                yield from self.is_active()
        elif vnfr_msg.operational_status == "failed":
            yield from self.instantiation_failed(failed_reason=vnfr_msg.operational_status_details)

    @asyncio.coroutine
    def is_active(self):
        """ This VNFR is active """
        self._log.debug("VNFR %s is active", self._vnfr_id)
        self.set_state(VnfRecordState.ACTIVE)

    @asyncio.coroutine
    def instantiation_failed(self, failed_reason=None):
        """ This VNFR instantiation failed"""
        self._log.debug("VNFR %s instantiation failed", self._vnfr_id)
        self.set_state(VnfRecordState.FAILED)
        self._state_failed_reason = failed_reason

    def vnfr_in_vnfm(self):
        """ Is there a VNFR record in VNFM """
        if (self._state == VnfRecordState.ACTIVE or
                self._state == VnfRecordState.INSTANTIATION_PENDING or
                self._state == VnfRecordState.FAILED):
            return True

        return False

    @asyncio.coroutine
    def terminate(self):
        """ Terminate this VNF """
        if not self.vnfr_in_vnfm():
            self._log.debug("Ignoring terminate request for id %s in state %s",
                            self.id, self._state)
            return

        self._log.debug("Terminating VNF id:%s", self.id)
        self.set_state(VnfRecordState.TERMINATE_PENDING)
        with self._dts.transaction(flags=0) as xact:
            block = xact.block_create()
            block.add_query_delete(self.xpath)
            yield from block.execute(flags=0)
        self.set_state(VnfRecordState.TERMINATED)
        self._log.debug("Terminated VNF id:%s", self.id)


class NetworkServiceStatus(object):
    """ A class representing the Network service's status """
    MAX_EVENTS_RECORDED = 10
    """ Network service Status class"""
    def __init__(self, dts, log, loop):
        self._dts = dts
        self._log = log
        self._loop = loop

        self._state = NetworkServiceRecordState.INIT
        self._events = deque([])

    @asyncio.coroutine
    def create_notification(self, evt, evt_desc, evt_details):
        xp = "N,/rw-nsr:nsm-notification"
        notif = RwNsrYang.YangNotif_RwNsr_NsmNotification()
        notif.event = evt
        notif.description = evt_desc
        notif.details = evt_details if evt_details is not None else None

        yield from self._dts.query_create(xp, rwdts.XactFlag.ADVISE, notif)
        self._log.info("Notification called by creating dts query: %s", notif)

    def record_event(self, evt, evt_desc, evt_details):
        """ Record an event """
        self._log.debug("Recording event - evt %s, evt_descr %s len = %s",
                        evt, evt_desc, len(self._events))
        if len(self._events) >= NetworkServiceStatus.MAX_EVENTS_RECORDED:
            self._events.popleft()
        self._events.append((int(time.time()), evt, evt_desc,
                             evt_details if evt_details is not None else None))

        self._loop.create_task(self.create_notification(evt,evt_desc,evt_details))

    def set_state(self, state):
        """ set the state of this status object """
        self._state = state

    def yang_str(self):
        """ Return the state as a yang enum string """
        state_to_str_map = {"INIT": "init",
                            "VL_INIT_PHASE": "vl_init_phase",
                            "VNF_INIT_PHASE": "vnf_init_phase",
                            "VNFFG_INIT_PHASE": "vnffg_init_phase",
                            "SCALING_GROUP_INIT_PHASE": "scaling_group_init_phase",
                            "RUNNING": "running",
                            "SCALING_OUT": "scaling_out",
                            "SCALING_IN": "scaling_in",
                            "TERMINATE_RCVD": "terminate_rcvd",
                            "TERMINATE": "terminate",
                            "VL_TERMINATE_PHASE": "vl_terminate_phase",
                            "VNF_TERMINATE_PHASE": "vnf_terminate_phase",
                            "VNFFG_TERMINATE_PHASE": "vnffg_terminate_phase",
                            "TERMINATED": "terminated",
                            "FAILED": "failed",
                            "VL_INSTANTIATE": "vl_instantiate",
                            "VL_TERMINATE": "vl_terminate",
        }
        return state_to_str_map[self._state.name]

    @property
    def state(self):
        """ State of this status object """
        return self._state

    @property
    def msg(self):
        """ Network Service Record as a message"""
        event_list = []
        idx = 1
        for entry in self._events:
            event = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_OperationalEvents()
            event.id = idx
            idx += 1
            event.timestamp, event.event, event.description, event.details = entry
            event_list.append(event)
        return event_list


class NetworkServiceRecord(object):
    """ Network service record """
    XPATH = "D,/nsr:ns-instance-opdata/nsr:nsr"

    def __init__(self, dts, log, loop, nsm, nsm_plugin, nsr_cfg_msg,
                 sdn_account_name, key_pairs, project, restart_mode=False,
                 vlr_handler=None):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm
        self._nsr_cfg_msg = nsr_cfg_msg
        self._nsm_plugin = nsm_plugin
        self._sdn_account_name = sdn_account_name
        self._vlr_handler = vlr_handler
        self._project = project

        self._nsd = None
        self._nsr_msg = None
        self._nsr_regh = None
        self._key_pairs = key_pairs
        self._ssh_key_file = None
        self._ssh_pub_key = None
        self._vlrs = {}
        self._vnfrs = {}
        self._vnfds = {}
        self._vnffgrs = {}
        self._param_pools = {}
        self._scaling_groups = {}
        self._create_time = int(time.time())
        self._op_status = NetworkServiceStatus(dts, log, loop)
        self._config_status = NsrYang.ConfigStates.CONFIGURING
        self._config_status_details = None
        self._job_id = 0
        self.restart_mode = restart_mode
        self.config_store = rift.mano.config_data.config.ConfigStore(self._log)
        self._debug_running = False
        self._is_active = False
        self._vl_phase_completed = False
        self._vnf_phase_completed = False
        self.instantiated = set()

        # Used for orchestration_progress
        self._active_vms = 0
        self._active_networks = 0

        # A flag to indicate if the NS has failed, currently it is recorded in
        # operational status, but at the time of termination this field is
        # over-written making it difficult to identify the failure.
        self._is_failed = False

        # Initalise the state to init
        # The NSR moves through the following transitions
        # 1. INIT -> VLS_READY once all the VLs in the NSD are created
        # 2. VLS_READY - VNFS_READY when all the VNFs in the NSD are created
        # 3. VNFS_READY - READY when the NSR is published

        self.set_state(NetworkServiceRecordState.INIT)

        self.substitute_input_parameters = InputParameterSubstitution(self._log, self._project)

        # Create an asyncio loop to know when the virtual links are ready
        self._vls_ready = asyncio.Event(loop=self._loop)

        # This variable stores all the terminate events received per NS. This is then used to prevent any
        # further nsr non-terminate updates received in case of terminate being called bedore ns in in running state. 
        self._ns_terminate_received = False

    @property
    def nsm_plugin(self):
        """ NSM Plugin """
        return self._nsm_plugin

    def set_state(self, state):
        """ Set state for this NSR"""
        # We are in init phase and is moving to the next state
        # The new state could be a FAILED state or VNF_INIIT_PHASE
        if self.state == NetworkServiceRecordState.VL_INIT_PHASE:
            self._vl_phase_completed = True

        if self.state == NetworkServiceRecordState.VNF_INIT_PHASE:
            self._vnf_phase_completed = True

        self._op_status.set_state(state)

        self._nsm_plugin.set_state(self.id, state)

    @property
    def id(self):
        """ Get id for this NSR"""
        return self._nsr_cfg_msg.id

    @property
    def name(self):
        """ Name of this network service record """
        return self._nsr_cfg_msg.name

    @property
    def _datacenter_name(self):
        if self._nsr_cfg_msg.has_field('datacenter'):
            return self._nsr_cfg_msg.datacenter
        return None

    @property
    def state(self):
        """State of this NetworkServiceRecord"""
        return self._op_status.state

    @property
    def active(self):
        """ Is this NSR active ?"""
        return True if self._op_status.state == NetworkServiceRecordState.RUNNING else False

    @property
    def vlrs(self):
        """ VLRs associated with this NSR"""
        return self._vlrs

    @property
    def vnfrs(self):
        """ VNFRs associated with this NSR"""
        return self._vnfrs

    @property
    def vnffgrs(self):
        """ VNFFGRs associated with this NSR"""
        return self._vnffgrs

    @property
    def scaling_groups(self):
        """ Scaling groups associated with this NSR """
        return self._scaling_groups

    @property
    def param_pools(self):
        """ Parameter value pools associated with this NSR"""
        return self._param_pools

    @property
    def nsr_cfg_msg(self):
        return self._nsr_cfg_msg

    @nsr_cfg_msg.setter
    def nsr_cfg_msg(self, msg):
        self._nsr_cfg_msg = msg

    @property
    def nsd_msg(self):
        """ NSD Protobuf for this NSR """
        if self._nsd is not None:
            return self._nsd
        self._nsd = self._nsr_cfg_msg.nsd
        return self._nsd

    @property
    def nsd_id(self):
        """ NSD ID for this NSR """
        return self.nsd_msg.id

    @property
    def job_id(self):
        ''' Get a new job id for config primitive'''
        self._job_id += 1
        return self._job_id

    @property
    def config_status(self):
        """ Config status for NSR """
        return self._config_status

    @property
    def nsm(self):
        """NS Manager"""
        return self._nsm

    @property
    def is_failed(self):
      return self._is_failed

    @property
    def public_key(self):
        return self._ssh_pub_key

    @property
    def private_key(self):
        return self._ssh_key_file

    def resolve_placement_group_cloud_construct(self, input_group):
        """
        Returns the cloud specific construct for placement group
        """
        copy_dict = ['name', 'requirement', 'strategy']

        for group_info in self._nsr_cfg_msg.nsd_placement_group_maps:
            if group_info.placement_group_ref == input_group.name:
                group = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_PlacementGroupsInfo()
                group_dict = {k:v for k,v in
                              group_info.as_dict().items() if k != 'placement_group_ref'}
                for param in copy_dict:
                    group_dict.update({param: getattr(input_group, param)})
                group.from_dict(group_dict)
                return group
        return None


    def __str__(self):
        return "NSR(name={}, nsd_id={}, data center={})".format(
                self.name, self.nsd_id, self._datacenter_name
                )

    def _get_vnfd(self, vnfd_id, config_xact):
        """  Fetch vnfd msg for the passed vnfd id """
        return self._nsm.get_vnfd(vnfd_id, config_xact)

    def _get_vnfd_datacenter(self, vnfd_member_index):
        """  Fetch datacenter for the passed vnfd id """
        if self._nsr_cfg_msg.vnf_datacenter_map:
           vim_accounts = [vnf.datacenter for vnf in self._nsr_cfg_msg.vnf_datacenter_map \
                           if str(vnfd_member_index) == str(vnf.member_vnf_index_ref)]
           if vim_accounts and vim_accounts[0]:
               return vim_accounts[0]
        return self._datacenter_name

    def _get_constituent_vnfd_msg(self, vnf_index):
        for const_vnfd in self.nsd_msg.constituent_vnfd:
            if const_vnfd.member_vnf_index == vnf_index:
                return const_vnfd

        raise ValueError("Constituent VNF index %s not found" % vnf_index)

    def record_event(self, evt, evt_desc, evt_details=None, state=None):
        """ Record an event """
        self._op_status.record_event(evt, evt_desc, evt_details)
        if state is not None:
            self.set_state(state)

    def scaling_trigger_str(self, trigger):
        SCALING_TRIGGER_STRS = {
            NsdBaseYang.ScalingTrigger.PRE_SCALE_IN : 'pre-scale-in',
            NsdBaseYang.ScalingTrigger.POST_SCALE_IN : 'post-scale-in',
            NsdBaseYang.ScalingTrigger.PRE_SCALE_OUT : 'pre-scale-out',
            NsdBaseYang.ScalingTrigger.POST_SCALE_OUT : 'post-scale-out',
        }
        try:
            return SCALING_TRIGGER_STRS[trigger]
        except Exception as e:
            self._log.error("Scaling trigger mapping error for {} : {}".
                            format(trigger, e))
            self._log.exception(e)
            return "Unknown trigger"

    def generate_ssh_key_pair(self, config_xact):
        '''Generate a ssh key pair if required'''
        if self._ssh_key_file:
            self._log.debug("Key pair already generated")
            return

        gen_key = False
        for cv in self.nsd_msg.constituent_vnfd:
            vnfd = self._get_vnfd(cv.vnfd_id_ref, config_xact)
            if vnfd and vnfd.mgmt_interface.ssh_key:
                gen_key = True
                break

        if not gen_key:
            return

        try:
            key = ManoSshKey(self._log)
            path = tempfile.mkdtemp()
            key.write_to_disk(name=self.id, directory=path)
            self._ssh_key_file = "file://{}".format(key.private_key_file)
            self._ssh_pub_key = key.public_key
        except Exception as e:
            self._log.exception("Error generating ssh key for {}: {}".
                                format(self.nsr_cfg_msg.name, e))

    @asyncio.coroutine
    def instantiate_vls(self):
        """
        This function instantiates VLs for every VL in this Network Service
        """
        self._log.debug("Instantiating %d VLs in NSD id %s", len(self._vlrs),
                        self.id)
        for vlr_id, vlr in self._vlrs.items():
            yield from self.nsm_plugin.instantiate_vl(self, vlr)

        if not isinstance(self.nsm_plugin, rwnsmplugin.RwNsPlugin):
            self._vls_ready.set()

        # Wait for the VLs to be ready before yielding control out
        self._log.debug("Waitng for %d  VLs in NSR id %s to be active",
                        len(self._vlrs), self.id)
        if self._vlrs:
            self._log.debug("NSR id:%s, name:%s - Waiting for %d VLs to be ready",
                            self.id, self.name, len(self._vlrs))
            yield from self._vls_ready.wait()
        else:
            self._log.debug("NSR id:%s, name:%s, No virtual links found",
                            self.id, self.name)
            self._vls_ready.set()

        self._log.info("All  %d  VLs in NSR id %s are active, start the VNFs",
                        len(self._vlrs), self.id)
    @asyncio.coroutine
    def create(self, config_xact):
        """ Create this network service"""
        self._log.debug("Create NS {} for {}".format(self.name, self._project.name))
        # Create virtual links  for all the external vnf
        # connection points in this NS
        yield from self.create_vls()

        # Create VNFs in this network service
        yield from self.create_vnfs(config_xact)

        # Create VNFFG for network service
        self.create_vnffgs()

        # Create Scaling Groups for each scaling group in NSD
        self.create_scaling_groups()

        # Create Parameter Pools
        self.create_param_pools()

    @asyncio.coroutine
    def apply_scale_group_config_script(self, script, group, scale_instance, trigger, vnfrs=None):
        """ Apply config based on script for scale group """
        rift_var_root_dir = os.environ['RIFT_VAR_ROOT']

        @asyncio.coroutine
        def add_vnfrs_data(vnfrs_list):
            """ Add as a dict each of the VNFRs data """
            vnfrs_data = []

            for vnfr in vnfrs_list:
                self._log.debug("Add VNFR {} data".format(vnfr))
                vnfr_data = dict()
                vnfr_data['name'] = vnfr.name
                if trigger in [NsdBaseYang.ScalingTrigger.PRE_SCALE_IN,
                               NsdBaseYang.ScalingTrigger.POST_SCALE_OUT]:
                    # Get VNF management and other IPs, etc
                    opdata = yield from self.fetch_vnfr(vnfr.xpath)
                    self._log.debug("VNFR {} op data: {}".format(vnfr.name, opdata))
                    try:
                        vnfr_data['rw_mgmt_ip'] = opdata.mgmt_interface.ip_address
                        vnfr_data['rw_mgmt_port'] = opdata.mgmt_interface.port
                        vnfr_data['member_vnf_index_ref'] = opdata.member_vnf_index_ref
                        vnfr_data['vdur_data'] = []
                        for vdur in opdata.vdur:
                            vdur_data = dict()
                            vdur_data['vm_name'] = vdur.name
                            vdur_data['vm_mgmt_ip'] = vdur.vm_management_ip
                            vnfr_data['vdur_data'].append(vdur_data)
                    except Exception as e:
                        self._log.error("Unable to get management IP for vnfr {}:{}".
                                        format(vnfr.name, e))

                    try:
                        vnfr_data['connection_points'] = []
                        for cp in opdata.connection_point:
                            con_pt = dict()
                            con_pt['name'] = cp.name
                            con_pt['ip_address'] = cp.ip_address
                            vnfr_data['connection_points'].append(con_pt)
                    except Exception as e:
                        self._log.error("Exception getting connections points for VNFR {}: {}".
                                        format(vnfr.name, e))

                vnfrs_data.append(vnfr_data)
                self._log.debug("VNFRs data: {}".format(vnfrs_data))

            return vnfrs_data

        def add_nsr_data(nsr):
            nsr_data = dict()
            nsr_data['name'] = nsr.name
            return nsr_data

        if script is None or len(script) == 0:
            self._log.error("Script not provided for scale group config: {}".format(group.name))
            return False

        if script[0] == '/':
            path = script
        else:
            path = os.path.join(rift_var_root_dir,
                                    'launchpad/packages/nsd',
                                    self._project.name,
                                    self.nsd_id, 'scripts',
                                    script)

        if not os.path.exists(path):
            self._log.error("Config failed for scale group {}: Script does not exist at {}".
                            format(group.name, path))
            return False

        # Build a YAML file with all parameters for the script to execute
        # The data consists of 5 sections
        # 1. Trigger
        # 2. Scale group config
        # 3. VNFRs in the scale group
        # 4. VNFRs outside scale group
        # 5. NSR data
        data = dict()
        data['trigger'] = group.trigger_map(trigger)
        data['config'] = group.group_msg.as_dict()

        if vnfrs:
            data["vnfrs_in_group"] = yield from add_vnfrs_data(vnfrs)
        else:
            data["vnfrs_in_group"] = yield from add_vnfrs_data(scale_instance.vnfrs)

        data["vnfrs_others"] = yield from add_vnfrs_data(self.vnfrs.values())
        data["nsr"] = add_nsr_data(self)

        tmp_file = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data, default_flow_style=True)
                    .encode("UTF-8"))

        self._log.debug("Creating a temp file: {} with input data: {}".
                        format(tmp_file.name, data))

        cmd = "{} {}".format(path, tmp_file.name)
        self._log.debug("Running the CMD: {}".format(cmd))
        proc = yield from asyncio.create_subprocess_shell(cmd, loop=self._loop)
        rc = yield from proc.wait()
        if rc:
            self._log.error("The script {} for scale group {} config returned: {}".
                            format(script, group.name, rc))
            return False

        # Success
        return True


    @asyncio.coroutine
    def apply_scaling_group_config(self, trigger, group, scale_instance, vnfrs=None):
        """ Apply the config for the scaling group based on trigger """
        if group is None or scale_instance is None:
            return False

        @asyncio.coroutine
        def update_config_status(success=True, err_msg=None):
            """ This is ugly!!!
                We are trying to determine the scaling instance's config status
                as a collation of the config status associated with 4 different triggers
            """
            self._log.debug("Update %s scaling config status to %r : %s",
                            scale_instance, success, err_msg)
            if (scale_instance.config_status == "failed"):
                # Do not update the config status if it is already in failed state
                return

            if scale_instance.config_status == "configured":
                # Update only to failed state an already configured scale instance
                if not success:
                    scale_instance.config_status = "failed"
                    scale_instance.config_err_msg = err_msg
                    yield from self.update_state()
            else:
                # We are in configuring state
                # Only after post scale out mark instance as configured
                if trigger == NsdBaseYang.ScalingTrigger.POST_SCALE_OUT:
                    if success:
                        scale_instance.config_status = "configured"
                        for vnfr in scale_instance.vnfrs:
                          if vnfr.config_status == "configuring":
                            vnfr.vnfr_msg.config_status = "configured"
                            yield from vnfr.update_vnfm()
                    else:
                        scale_instance.config_status = "failed"
                        scale_instance.config_err_msg = err_msg

                    yield from self.update_state()
                    # Publish config state as update_state seems to care only operational status
                    yield from self.publish()

        config = group.trigger_config(trigger)
        if config is None:
            if trigger == NsdBaseYang.ScalingTrigger.POST_SCALE_OUT:
                self._log.debug("No config needed, update %s scaling config status to configured",
                            scale_instance)
                scale_instance.config_status = "configured"
            return True

        self._log.debug("Scaling group {} config: {}".format(group.name, config))
        if config.has_field("ns_service_primitive_name_ref"):
            config_name = config.ns_service_primitive_name_ref
            nsd_msg = self.nsd_msg
            config_primitive = None
            for ns_cfg_prim in nsd_msg.service_primitive:
                if ns_cfg_prim.name == config_name:
                    config_primitive = ns_cfg_prim
                    break

            if config_primitive is None:
                raise ValueError("Could not find ns_cfg_prim %s in nsr %s" % (config_name, self.name))

            self._log.debug("Scaling group {} config primitive: {}".format(group.name, config_primitive))
            if config_primitive.has_field("user_defined_script"):
                script_path = '/'.join(["launchpad/packages/nsd", self._project.name, nsd_msg.id, "scripts", config_primitive.user_defined_script])
                rc = yield from self.apply_scale_group_config_script(script_path,
                                                                     group, scale_instance, trigger, vnfrs)
                err_msg = None
                if not rc:
                    err_msg = "Failed config for trigger {} using config script '{}'". \
                              format(self.scaling_trigger_str(trigger),
                                     config_primitive.user_defined_script)
                yield from update_config_status(success=rc, err_msg=err_msg)
                return rc
            else:
                err_msg = "Failed config for trigger {} as config script is not specified". \
                          format(self.scaling_trigger_str(trigger))
                yield from update_config_status(success=False, err_msg=err_msg)
                raise NotImplementedError("Only script based config support for scale group for now: {}".
                                          format(group.name))
        else:
            err_msg = "Failed config for trigger {} as config primitive is not specified".\
                      format(self.scaling_trigger_str(trigger))
            yield from update_config_status(success=False, err_msg=err_msg)
            self._log.error("Config primitive not specified for config action in scale group %s" %
                            (group.name))
        return False

    def create_scaling_groups(self):
        """ This function creates a NSScalingGroup for every scaling
        group defined in he NSD"""

        for scaling_group_msg in self.nsd_msg.scaling_group_descriptor:
            self._log.debug("Found scaling_group %s in nsr id %s",
                            scaling_group_msg.name, self.id)

            group_record = scale_group.ScalingGroup(
                    self._log,
                    scaling_group_msg
                    )

            self._scaling_groups[group_record.name] = group_record

    @asyncio.coroutine
    def create_scale_group_instance(self, group_name, index, config_xact, is_default=False):
        group = self._scaling_groups[group_name]
        scale_instance = group.create_instance(index, is_default)

        @asyncio.coroutine
        def create_vnfs():
            self._log.debug("Creating %u VNFs associated with NS id %s scaling group %s",
                            len(self.nsd_msg.constituent_vnfd), self.id, self)

            vnfrs = []
            for vnf_index, count in group.vnf_index_count_map.items():
                const_vnfd_msg = self._get_constituent_vnfd_msg(vnf_index)
                vnfd_msg = self._get_vnfd(const_vnfd_msg.vnfd_id_ref, config_xact)

                datacenter_name = self._get_vnfd_datacenter(const_vnfd_msg.member_vnf_index)
                if datacenter_name is None:
                    datacenter_name = self._datacenter_name
                for _ in range(count):
                    vnfr = yield from self.create_vnf_record(vnfd_msg, const_vnfd_msg, datacenter_name, group_name, index)
                    scale_instance.add_vnfr(vnfr)
                    vnfrs.append(vnfr)
            return vnfrs

        @asyncio.coroutine
        def instantiate_instance():
            self._log.debug("Creating %s VNFRS", scale_instance)
            vnfrs = yield from create_vnfs()
            yield from self.publish()

            self._log.debug("Instantiating %s VNFRS for %s", len(vnfrs), scale_instance)
            scale_instance.operational_status = "vnf_init_phase"
            yield from self.update_state()

            try:
                rc = yield from self.apply_scaling_group_config(NsdBaseYang.ScalingTrigger.PRE_SCALE_OUT,
                                                                group, scale_instance, vnfrs)
                if not rc:
                    self._log.error("Pre scale out config for scale group {} ({}) failed".
                                    format(group.name, index))
                    scale_instance.operational_status = "failed"
                else:
                    yield from self.instantiate_vnfs(vnfrs, scaleout=True)


            except Exception as e:
                self._log.exception("Failed to begin instantiatiation of vnfs for scale group {}: {}".
                                    format(group.name, e))
                self._log.exception(e)
                scale_instance.operational_status = "failed"

            yield from self.update_state()

        yield from instantiate_instance()

    @asyncio.coroutine
    def delete_scale_group_instance(self, group_name, index):
        group = self._scaling_groups[group_name]
        scale_instance = group.get_instance(index)
        if scale_instance.is_default:
            raise ScalingOperationError("Cannot terminate a default scaling group instance")

        scale_instance.operational_status = "terminate"
        yield from self.update_state()

        @asyncio.coroutine
        def terminate_instance():
            self._log.debug("Terminating scaling instance %s VNFRS" % scale_instance)
            rc = yield from self.apply_scaling_group_config(NsdBaseYang.ScalingTrigger.PRE_SCALE_IN,
                                                            group, scale_instance)
            if not rc:
                self._log.error("Pre scale in config for scale group {} ({}) failed".
                                format(group.name, index))

            # Going ahead with terminate, even if there is an error in pre-scale-in config
            # as this could be result of scale out failure and we need to cleanup this group
            yield from self.terminate_vnfrs(scale_instance.vnfrs, scalein=True)
            group.delete_instance(index)

            scale_instance.operational_status = "vnf_terminate_phase"
            yield from self.update_state()

        yield from terminate_instance()

    @asyncio.coroutine
    def _update_scale_group_instances_status(self):
        @asyncio.coroutine
        def post_scale_out_task(group, instance):
            # Apply post scale out config once all VNFRs are active
            rc = yield from self.apply_scaling_group_config(NsdBaseYang.ScalingTrigger.POST_SCALE_OUT,
                                                            group, instance)
            instance.operational_status = "running"
            if rc:
                self._log.debug("Scale out for group {} and instance {} succeeded".
                                format(group.name, instance.instance_id))
            else:
                self._log.error("Post scale out config for scale group {} ({}) failed".
                                format(group.name, instance.instance_id))

            yield from self.update_state()

        group_instances = {group: group.instances for group in self._scaling_groups.values()}
        for group, instances in group_instances.items():
            self._log.debug("Updating %s instance status", group)
            for instance in instances:
                instance_vnf_state_list = [vnfr.state for vnfr in instance.vnfrs]
                self._log.debug("Got vnfr instance states: %s", instance_vnf_state_list)
                if instance.operational_status == "vnf_init_phase":
                    if all([state == VnfRecordState.ACTIVE for state in instance_vnf_state_list]):
                        instance.operational_status = "running"

                        # Create a task for post scale out to allow us to sleep before attempting
                        # to configure newly created VM's
                        self._loop.create_task(post_scale_out_task(group, instance))

                    elif any([state == VnfRecordState.FAILED for state in instance_vnf_state_list]):
                        self._log.debug("Scale out for group {} and instance {} failed".
                                        format(group.name, instance.instance_id))
                        instance.operational_status = "failed"

                elif instance.operational_status == "vnf_terminate_phase":
                    if all([state == VnfRecordState.TERMINATED for state in instance_vnf_state_list]):
                        instance.operational_status = "terminated"
                        rc = yield from self.apply_scaling_group_config(NsdBaseYang.ScalingTrigger.POST_SCALE_IN,
                                                                         group, instance)
                        if rc:
                            self._log.debug("Scale in for group {} and instance {} succeeded".
                                            format(group.name, instance.instance_id))
                        else:
                            self._log.error("Post scale in config for scale group {} ({}) failed".
                                            format(group.name, instance.instance_id))

    def create_vnffgs(self):
        """ This function creates VNFFGs for every VNFFG in the NSD
        associated with this NSR"""

        for vnffgd in self.nsd_msg.vnffgd:
            self._log.debug("Found vnffgd %s in nsr id %s", vnffgd, self.id)
            vnffgr = VnffgRecord(self._dts,
                                 self._log,
                                 self._loop,
                                 self._nsm._vnffgmgr,
                                 self,
                                 self.name,
                                 vnffgd,
                                 self._sdn_account_name,
                                 self._datacenter_name
                                 )
            self._vnffgrs[vnffgr.id] = vnffgr

    def resolve_vld_ip_profile(self, nsd_msg, vld):
        self._log.debug("Receieved ip profile ref is %s",vld.ip_profile_ref)
        if not vld.has_field('ip_profile_ref'):
            return None
        profile = [profile for profile in nsd_msg.ip_profiles if profile.name == vld.ip_profile_ref]
        return profile[0] if profile else None

    @asyncio.coroutine
    def _create_vls(self, vld, datacenter):
        """Create a VLR in the cloud account specified using the given VLD

        Args:
            vld : VLD yang obj
            datacenter : Cloud account name

        Returns:
            VirtualLinkRecord
        """
        vlr = yield from VirtualLinkRecord.create_record(
                self._dts,
                self._log,
                self._loop,
                self._project,
                self.name,
                vld,
                datacenter,
                self.resolve_vld_ip_profile(self.nsd_msg, vld),
                self.id,
                restart_mode=self.restart_mode)

        return vlr

    def _extract_datacenters_for_vl(self, vld):
        """
        Extracts the list of cloud accounts from the NS Config obj

        Rules:
        1. Cloud accounts based connection point (vnf_datacenter_map)
        Args:
            vld : VLD yang object

        Returns:
            TYPE: Description
        """
        datacenter_list = []

        if self._nsr_cfg_msg.vnf_datacenter_map:
            # Handle case where datacenter is None
            vnf_datacenter_map = {}
            for vnf in self._nsr_cfg_msg.vnf_datacenter_map:
                if vnf.datacenter is not None or vnf.datacenter is not None:
                    vnf_datacenter_map[vnf.member_vnf_index_ref] = \
                                        vnf.datacenter

            for vnfc in vld.vnfd_connection_point_ref:
                datacenter = vnf_datacenter_map.get(
                        vnfc.member_vnf_index_ref, self._datacenter_name)

                datacenter_list.append(datacenter)

        if self._nsr_cfg_msg.vl_datacenter_map:
            for vld_map in self._nsr_cfg_msg.vl_datacenter_map:
                if vld_map.vld_id_ref == vld.id:
                    for datacenter in vld_map.datacenters:
                        datacenter_list.append(datacenter)

        # If no config has been provided then fall-back to the default
        # account
        if not datacenter_list:
            datacenter_list.append(self._datacenter_name)

        self._log.debug("VL {} data center list: {}".
                        format(vld.name, datacenter_list))
        return set(datacenter_list)

    @asyncio.coroutine
    def create_vls(self):
        """ This function creates VLs for every VLD in the NSD
        associated with this NSR"""
        for vld in self.nsd_msg.vld:

            self._log.debug("Found vld %s in nsr id %s", vld, self.id)
            datacenter_list = self._extract_datacenters_for_vl(vld)
            for datacenter in datacenter_list:
                vlr = yield from self._create_vls(vld, datacenter)
                self._vlrs[vlr.id] = vlr
                self._nsm.add_vlr_id_nsr_map(vlr.id, self)

    @asyncio.coroutine
    def create_vl_instance(self, vld):
        self._log.error("Create VL for {}: {}".format(self.id, vld.as_dict()))
        # Check if the VL is already present
        vlr = None
        for vl_id, vl in self._vlrs.items():
            if vl.vld_msg.id == vld.id:
                self._log.error("The VLD %s already in NSR %s as VLR %s with status %s",
                                vld.id, self.id, vl.id, vl.state)
                vlr = vl
                if vlr.state != VlRecordState.TERMINATED:
                    err_msg = "VLR for VL {} in NSR {} already instantiated". \
                               format(vld, self.id)
                    self._log.error(err_msg)
                    raise NsrVlUpdateError(err_msg)
                break

        if vlr is None:
            datacenter_list = self._extract_datacenters_for_vl(vld)
            for datacenter in datacenter_list:
                vlr = yield from self._create_vls(vld, account, datacenter)
                self._vlrs[vlr.id] = vlr
                self._nsm.add_vlr_id_nsr_map(vlr.id, self)

        vlr.state = VlRecordState.INSTANTIATION_PENDING
        yield from self.update_state()

        try:
            yield from self.nsm_plugin.instantiate_vl(self, vlr)

        except Exception as e:
            err_msg = "Error instantiating VL for NSR {} and VLD {}: {}". \
                      format(self.id, vld.id, e)
            self._log.error(err_msg)
            self._log.exception(e)
            vlr.state = VlRecordState.FAILED

        yield from self.update_state()

    @asyncio.coroutine
    def delete_vl_instance(self, vld):
        for vlr_id, vlr in self._vlrs.items():
            if vlr.vld_msg.id == vld.id:
                self._log.debug("Found VLR %s for VLD %s in NSR %s",
                                vlr.id, vld.id, self.id)
                vlr.state = VlRecordState.TERMINATE_PENDING
                yield from self.update_state()

                try:
                    yield from self.nsm_plugin.terminate_vl(vlr)
                    vlr.state = VlRecordState.TERMINATED
                    del self._vlrs[vlr]
                    self.remove_vlr_id_nsr_map(vlr.id)

                except Exception as e:
                    err_msg = "Error terminating VL for NSR {} and VLD {}: {}". \
                              format(self.id, vld.id, e)
                    self._log.error(err_msg)
                    self._log.exception(e)
                    vlr.state = VlRecordState.FAILED

                yield from self.update_state()
                break

    @asyncio.coroutine
    def create_vnfs(self, config_xact):
        """
        This function creates VNFs for every VNF in the NSD
        associated with this NSR
        """
        self._log.debug("Creating %u VNFs associated with this NS id %s",
                        len(self.nsd_msg.constituent_vnfd), self.id)

        for const_vnfd in self.nsd_msg.constituent_vnfd:
            if not const_vnfd.start_by_default:
                self._log.debug("start_by_default set to False in constituent VNF (%s). Skipping start.",
                                const_vnfd.member_vnf_index)
                continue

            vnfd_msg = self._get_vnfd(const_vnfd.vnfd_id_ref, config_xact)
            datacenter_name = self._get_vnfd_datacenter(const_vnfd.member_vnf_index)
            if datacenter_name is None:
                datacenter_name = self._datacenter_name
            yield from self.create_vnf_record(vnfd_msg, const_vnfd, datacenter_name)

    def get_placement_groups(self, vnfd_msg, const_vnfd):
        placement_groups = []
        for group in self.nsd_msg.placement_groups:
            for member_vnfd in group.member_vnfd:
                if (member_vnfd.vnfd_id_ref == vnfd_msg.id) and \
                   (member_vnfd.member_vnf_index_ref == str(const_vnfd.member_vnf_index)):
                    group_info = self.resolve_placement_group_cloud_construct(group)
                    if group_info is None:
                        self._log.info("Could not resolve cloud-construct for placement group: %s", group.name)
                        ### raise PlacementGroupError("Could not resolve cloud-construct for placement group: {}".format(group.name))
                    else:
                        self._log.info("Successfully resolved cloud construct for placement group: %s for VNF: %s (Member Index: %s)",
                                       str(group_info),
                                       vnfd_msg.name,
                                       const_vnfd.member_vnf_index)
                        placement_groups.append(group_info)
        return placement_groups

    def get_cloud_config(self):
        cloud_config = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_CloudConfig()
        self._log.debug("Received key pair is {}".format(self._key_pairs))

        for authorized_key in self.nsr_cfg_msg.ssh_authorized_key:
            if authorized_key.key_pair_ref in  self._key_pairs:
                key_pair = cloud_config.key_pair.add()
                key_pair.from_dict(self._key_pairs[authorized_key.key_pair_ref].as_dict())
        for nsd_key_pair in self.nsd_msg.key_pair:
            key_pair = cloud_config.key_pair.add()
            key_pair.from_dict(key_pair.as_dict())
        for nsr_cfg_user in self.nsr_cfg_msg.user:
            user = cloud_config.user.add()
            user.name = nsr_cfg_user.name
            user.user_info = nsr_cfg_user.user_info
            for ssh_key in nsr_cfg_user.ssh_authorized_key:
               if ssh_key.key_pair_ref in self._key_pairs:
                   key_pair = user.key_pair.add()
                   key_pair.from_dict(self._key_pairs[ssh_key.key_pair_ref].as_dict())
        for nsd_user in self.nsd_msg.user:
            user = cloud_config.user.add()
            user.from_dict(nsd_user.as_dict())

        self._log.debug("Formed cloud-config msg is {}".format(cloud_config))
        return cloud_config

    @asyncio.coroutine
    def create_vnf_record(self, vnfd_msg, const_vnfd, datacenter_name, group_name=None, group_instance_id=None):
        # Fetch the VNFD associated with this VNF
        placement_groups = self.get_placement_groups(vnfd_msg, const_vnfd)
        cloud_config = self.get_cloud_config()
        self._log.info("Cloud Account for VNF %d is %s",const_vnfd.member_vnf_index,datacenter_name)
        self._log.info("Launching VNF: %s (Member Index: %s) in NSD plancement Groups: %s",
                       vnfd_msg.name,
                       const_vnfd.member_vnf_index,
                       [ group.name for group in placement_groups])

        vnfr = yield from VirtualNetworkFunctionRecord.create_record(self._dts,
                                            self._log,
                                            self._loop,
                                            self._project,
                                            vnfd_msg,
                                            self._nsr_cfg_msg,
                                            const_vnfd,
                                            self.nsd_id,
                                            self.name,
                                            datacenter_name,
                                            self.id,
                                            group_name,
                                            group_instance_id,
                                            placement_groups,
                                            cloud_config,
                                            restart_mode=self.restart_mode,
                                            )
        if vnfr.id in self._vnfrs:
            err = "VNF with VNFR id %s already in vnf list" % (vnfr.id,)
            raise NetworkServiceRecordError(err)

        self._vnfrs[vnfr.id] = vnfr
        self._nsm.vnfrs[vnfr.id] = vnfr

        yield from vnfr.set_config_status(NsrYang.ConfigStates.INIT)

        self._log.debug("Added VNFR %s to NSM VNFR list with id %s",
                        vnfr.name,
                        vnfr.id)

        return vnfr

    def create_param_pools(self):
        for param_pool in self.nsd_msg.parameter_pool:
            self._log.debug("Found parameter pool %s in nsr id %s", param_pool, self.id)

            start_value = param_pool.range.start_value
            end_value = param_pool.range.end_value
            if end_value < start_value:
                raise NetworkServiceRecordError(
                        "Parameter pool %s has invalid range (start: {}, end: {})".format(
                            start_value, end_value
                            )
                        )

            self._param_pools[param_pool.name] = config_value_pool.ParameterValuePool(
                    self._log,
                    param_pool.name,
                    range(start_value, end_value)
                    )

    @asyncio.coroutine
    def fetch_vnfr(self, vnfr_path):
        """ Fetch VNFR record """
        vnfr = None
        self._log.debug("Fetching VNFR with key %s while instantiating %s",
                        vnfr_path, self.id)
        res_iter = yield from self._dts.query_read(vnfr_path, rwdts.XactFlag.MERGE)

        for ent in res_iter:
            res = yield from ent
            vnfr = res.result

        return vnfr

    @asyncio.coroutine
    def instantiate_vnfs(self, vnfrs, scaleout=False):
        """
        This function instantiates VNFs for every VNF in this Network Service
        """
        @asyncio.coroutine
        def instantiate_vnf(vnf):
            self._log.debug("Instantiating VNF: %s in NS %s", vnf, self.id)
            vnfd_id = vnf.vnfr_msg.vnfd.id
            for dependency_vnf in  dependencies[vnfd_id]:
                while dependency_vnf not in self.instantiated:
                     yield from asyncio.sleep(1, loop=self._loop)
            
            yield from self.nsm_plugin.instantiate_vnf(self, vnf,scaleout)
            self.instantiated.add(vnfd_id)
        
        self._log.debug("Instantiating %u VNFs in NS %s", len(vnfrs), self.id)
        dependencies = collections.defaultdict(list)
        for dependency_vnf in self._nsr_cfg_msg.nsd.vnf_dependency:
            dependencies[dependency_vnf.vnf_source_ref].append(dependency_vnf.vnf_depends_on_ref)

        # The dictionary copy is to ensure that if a terminate is initiated right after instantiation, the 
        # Runtime error for "dictionary changed size during iteration" does not occur.
        # vnfrs - 'dict_values' object
        # vnfrs_copy - list object
        vnfrs_copy = list(vnfrs)
        tasks = []
        for vnf in vnfrs_copy:
            vnf_task = self._loop.create_task(instantiate_vnf(vnf))
            tasks.append(vnf_task)

        if len(tasks) > 0:
            self._log.debug("Waiting for %s instantiate_vnf tasks to complete", len(tasks))
            done, pending = yield from asyncio.wait(tasks, loop=self._loop, timeout=30)
            if pending:
                self._log.error("The Instantiate vnf task timed out after 30 seconds.")
                raise VirtualNetworkFunctionRecordError("Task tied out : ", pending)

    @asyncio.coroutine
    def instantiate_vnffgs(self):
        """
        This function instantiates VNFFGs for every VNFFG in this Network Service
        """
        self._log.debug("Instantiating %u VNFFGs in NS %s",
                        len(self.nsd_msg.vnffgd), self.id)
        for _, vnfr in self.vnfrs.items():
            while vnfr.state in [VnfRecordState.INSTANTIATION_PENDING, VnfRecordState.INIT]:
                self._log.debug("Received vnfr state for vnfr %s is %s; retrying",vnfr.name,vnfr.state)
                yield from asyncio.sleep(2, loop=self._loop)
            if vnfr.state == VnfRecordState.ACTIVE:
                self._log.debug("Received vnfr state for vnfr %s is %s ",vnfr.name,vnfr.state)
                continue
            else:
                self._log.debug("Received vnfr state for vnfr %s is %s; failing vnffg creation",vnfr.name,vnfr.state)
                self._vnffgr_state = VnffgRecordState.FAILED
                return

        self._log.info("Waiting for 90 seconds for VMs to come up")
        yield from asyncio.sleep(90, loop=self._loop)
        self._log.info("Starting VNFFG orchestration")
        for vnffg in self._vnffgrs.values():
            self._log.debug("Instantiating VNFFG: %s in NS %s", vnffg, self.id)
            yield from vnffg.instantiate()

    @asyncio.coroutine
    def instantiate_scaling_instances(self, config_xact):
        """ Instantiate any default scaling instances in this Network Service """
        for group in self._scaling_groups.values():
            for i in range(group.min_instance_count):
                self._log.debug("Instantiating %s default scaling instance %s", group, i)
                yield from self.create_scale_group_instance(
                        group.name, i, config_xact, is_default=True
                        )

            for group_msg in self._nsr_cfg_msg.scaling_group:
                if group_msg.scaling_group_name_ref != group.name:
                    continue

                for instance in group_msg.instance:
                    self._log.debug("Reloading %s scaling instance %s", group_msg, instance.id)
                    yield from self.create_scale_group_instance(
                            group.name, instance.id, config_xact, is_default=False
                            )

    def has_scaling_instances(self):
        """ Return boolean indicating if the network service has default scaling groups """
        for group in self._scaling_groups.values():
            if group.min_instance_count > 0:
                return True

        for group_msg in self._nsr_cfg_msg.scaling_group:
            if len(group_msg.instance) > 0:
                return True

        return False

    @asyncio.coroutine
    def publish(self):
        """ This function publishes this NSR """

        self._nsr_msg = self.create_msg()

        self._log.debug("Publishing the NSR with xpath %s and nsr %s",
                        self.nsr_xpath,
                        self._nsr_msg)

        if self._debug_running:
            self._log.debug("Publishing NSR in RUNNING state!")
            #raise()

        yield from self._nsm.nsr_handler.update(None, self.nsr_xpath, self._nsr_msg)
        if self._op_status.state == NetworkServiceRecordState.RUNNING:
            self._debug_running = True

    @asyncio.coroutine
    def unpublish(self, xact=None):
        """ Unpublish this NSR object """
        self._log.debug("Unpublishing Network service id %s", self.id)

        yield from self._nsm.nsr_handler.delete(xact, self.nsr_xpath)

    @property
    def nsr_xpath(self):
        """ Returns the xpath associated with this NSR """
        return self._project.add_project((
            "D,/nsr:ns-instance-opdata" +
            "/nsr:nsr[nsr:ns-instance-config-ref={}]"
        ).format(quoted_key(self.id)))

    @staticmethod
    def xpath_from_nsr(nsr):
        """ Returns the xpath associated with this NSR  op data"""
        return (NetworkServiceRecord.XPATH +
                "[nsr:ns-instance-config-ref={}]").format(quoted_key(nsr.id))

    @property
    def nsd_xpath(self):
        """ Return NSD config xpath."""
        return self._project.add_project((
            "C,/project-nsd:nsd-catalog/project-nsd:nsd[project-nsd:id={}]"
        ).format(quoted_key(self.nsd_id)))

    @asyncio.coroutine
    def instantiate(self, config_xact):
        """"Instantiates a NetworkServiceRecord.

        This function instantiates a Network service
        which involves the following steps,

        * Instantiate every VL in NSD by sending create VLR request to DTS.
        * Instantiate every VNF in NSD by sending create VNF reuqest to DTS.
        * Publish the NSR details to DTS

        Arguments:
            nsr:  The NSR configuration request containing nsr-id and nsd
            config_xact: The configuration transaction which initiated the instatiation

        Raises:
            NetworkServiceRecordError if the NSR creation fails

        Returns:
            No return value
        """

        self._log.debug("Instantiating NS - %s xact - %s", self, config_xact)

        # Move the state to INIITALIZING
        self.set_state(NetworkServiceRecordState.INIT)

        event_descr = "Instantiation Request Received NSR Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("instantiating", event_descr)

        # Find the NSD
        self._nsd = self._nsr_cfg_msg.nsd

        # Merge any config and initial config primitive values
        self.config_store.merge_nsd_config(self.nsd_msg, self._project.name)
        self._log.debug("Merged NSD: {}".format(self.nsd_msg.as_dict()))

        event_descr = "Fetched NSD with descriptor id %s, NS Name: %s" % (self.nsd_id, self.name)
        self.record_event("nsd-fetched", event_descr)

        if self._nsd is None:
            msg = "Failed to fetch NSD with nsd-id [%s] for nsr-id %s"
            self._log.debug(msg, self.nsd_id, self.id)
            raise NetworkServiceRecordError(self)

        self._log.debug("Got nsd result %s", self._nsd)

        # Substitute any input parameters
        self.substitute_input_parameters(self._nsd, self._nsr_cfg_msg)

        # Create the record
        yield from self.create(config_xact)

        # Publish the NSR to DTS
        yield from self.publish()

        @asyncio.coroutine
        def do_instantiate():
            """
                Instantiate network service
            """
            self._log.debug("Instantiating VLs nsr id [%s] nsd id [%s]",
                            self.id, self.nsd_id)

            # instantiate the VLs
            event_descr = ("Instantiating %s external VLs for NSR id: %s, NS Name: %s " %
                           (len(self.nsd_msg.vld), self.id, self.name))
            self.record_event("begin-external-vls-instantiation", event_descr)

            self.set_state(NetworkServiceRecordState.VL_INIT_PHASE)

            # Publish the NSR to DTS
            yield from self.publish()

            if self._ns_terminate_received:
                self._log.debug("Terminate Received. Interrupting Instantiation at event : begin-external-vls-instantiation.")
                # Setting this flag as False again as this is a state where neither VL or VNF have been instantiated.
                self._ns_terminate_received = False
                # At this stage only ns-instance opdata is published. Cleaning up the record.
                yield from self.unpublish()
                return

            yield from self.instantiate_vls()

            event_descr = ("Finished instantiating %s external VLs for NSR id: %s, NS Name: %s " %
                           (len(self.nsd_msg.vld), self.id, self.name))
            self.record_event("end-external-vls-instantiation", event_descr)

            self.set_state(NetworkServiceRecordState.VNF_INIT_PHASE)

            # Publish the NSR to DTS
            yield from self.publish()

            self._log.debug("Instantiating VNFs  ...... nsr[%s], nsd[%s]",
                            self.id, self.nsd_id)

            # instantiate the VNFs
            event_descr = ("Instantiating %s VNFS for NSR id: %s, NS Name: %s " %
                           (len(self.nsd_msg.constituent_vnfd), self.id, self.name))

            self.record_event("begin-vnf-instantiation", event_descr)

            if self._ns_terminate_received:
                self._log.debug("Terminate Received. Interrupting Instantiation at event : end-external-vls-instantiation.")
                return
            
            yield from self.instantiate_vnfs(self._vnfrs.values())

            self._log.debug(" Finished instantiating %d VNFs for NSR id: %s, NS Name: %s",
                            len(self.nsd_msg.constituent_vnfd), self.id, self.name)

            event_descr = ("Finished instantiating %s VNFs for NSR id: %s, NS Name: %s" %
                           (len(self.nsd_msg.constituent_vnfd), self.id, self.name))
            self.record_event("end-vnf-instantiation", event_descr)

            # Publish the NSR to DTS
            yield from self.publish()

            if len(self.vnffgrs) > 0:
                #self.set_state(NetworkServiceRecordState.VNFFG_INIT_PHASE)
                event_descr = ("Instantiating %s VNFFGS for NSR id: %s, NS Name: %s" %
                               (len(self.nsd_msg.vnffgd), self.id, self.name))

                self.record_event("begin-vnffg-instantiation", event_descr)

                if self._ns_terminate_received:
                    self._log.debug("Terminate Received. Interrupting Instantiation at event : begin-vnffg-instantiation.")
                    return

                yield from self.instantiate_vnffgs()

                event_descr = ("Finished instantiating %s VNFFGDs for NSR id: %s, NS Name: %s" %
                               (len(self.nsd_msg.vnffgd), self.id, self.name))
                self.record_event("end-vnffg-instantiation", event_descr)

            if self.has_scaling_instances():
                event_descr = ("Instantiating %s Scaling Groups for NSR id: %s, NS Name: %s" %
                               (len(self._scaling_groups), self.id, self.name))

                self.record_event("begin-scaling-group-instantiation", event_descr)

                if self._ns_terminate_received:
                    self._log.debug("Terminate Received. Interrupting Instantiation at event : begin-scaling-group-instantiation.")
                    return
                
                yield from self.instantiate_scaling_instances(config_xact)
                self.record_event("end-scaling-group-instantiation", event_descr)

            # Give the plugin a chance to deploy the network service now that all
            # virtual links and vnfs are instantiated
            yield from self.nsm_plugin.deploy(self._nsr_msg)

            self._log.debug("Publishing  NSR...... nsr[%s], nsd[%s], for NS[%s]",
                            self.id, self.nsd_id, self.name)

            # Publish the NSR to DTS
            yield from self.publish()

            self._log.debug("Published  NSR...... nsr[%s], nsd[%s], for NS[%s]",
                            self.id, self.nsd_id, self.name)

        def on_instantiate_done(fut):
            # If the do_instantiate fails, then publish NSR with failed result
            e = fut.exception()
            if e is not None:
                import traceback, sys
                print(traceback.format_exception(None,e, e.__traceback__), file=sys.stderr, flush=True)
                self._log.error("NSR instantiation failed for NSR id %s: %s", self.id, str(e))
                self._loop.create_task(self.instantiation_failed(failed_reason=str(e)))

        instantiate_task = self._loop.create_task(do_instantiate())
        instantiate_task.add_done_callback(on_instantiate_done)

    @asyncio.coroutine
    def set_config_status(self, status, status_details=None):
        if self.config_status != status:
            self._log.debug("Updating NSR {} status for {} to {}".
                            format(self.name, self.config_status, status))
            self._config_status = status
            self._config_status_details = status_details

            if self._config_status == NsrYang.ConfigStates.FAILED:
                self.record_event("config-failed", "NS configuration failed",
                        evt_details=self._config_status_details)

            yield from self.publish()

            if status == NsrYang.ConfigStates.TERMINATE:
                yield from self.terminate_ns_cont()

    @asyncio.coroutine
    def is_active(self):
        """ This NS is active """
        self.set_state(NetworkServiceRecordState.RUNNING)
        if self._is_active:
            return

        # Publish the NSR to DTS
        self._log.debug("Network service %s is active ", self.id)
        self._is_active = True

        event_descr = "NSR in running state for NSR id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("ns-running", event_descr)

        yield from self.publish()

    @asyncio.coroutine
    def instantiation_failed(self, failed_reason=None):
        """ The NS instantiation failed"""
        self._log.error("Network service id:%s, name:%s instantiation failed",
                        self.id, self.name)
        self.set_state(NetworkServiceRecordState.FAILED)
        self._is_failed = True

        event_descr = "Instantiation of NS %s - %s failed" % (self.id, self.name)
        self.record_event("ns-failed", event_descr, evt_details=failed_reason)

        # Publish the NSR to DTS
        yield from self.publish()

    @asyncio.coroutine
    def terminate_vnfrs(self, vnfrs, scalein=False):
        """ Terminate VNFRS in this network service """
        self._log.debug("Terminating VNFs in network service %s - %s", self.id, self.name)
        vnfr_ids = []
        scaleIn = scalein
        for vnfr in list(vnfrs):
            self._log.debug("Terminating VNFs in network service %s %s", vnfr.id, self.id)
            # The below check is added for determining which of the VNFRS are scaling ones 
            # under OPENMANO. Need to pass scalein True when terminate received to OPENAMNO
            # Plugin.
            if isinstance(self.nsm_plugin, openmano_nsm.OpenmanoNsPlugin):
                for scaling_group in self._scaling_groups.values():
                    scaling_instances = scaling_group.create_record_msg().instance
                    for sc in scaling_instances:
                        if vnfr.id in sc.vnfrs:
                            scaleIn = True
                            self._log.debug("Found a Scaling VNF for Openmano during Terminate")

            yield from self.nsm_plugin.terminate_vnf(self, vnfr, scalein=scaleIn)
            scaleIn = scalein
            vnfr_ids.append(vnfr.id)

        for vnfr_id in vnfr_ids:
            self._vnfrs.pop(vnfr_id, None)

    @asyncio.coroutine
    def terminate(self):
        """Start terminate of a NetworkServiceRecord."""
        # Move the state to TERMINATE
        self.set_state(NetworkServiceRecordState.TERMINATE)
        event_descr = "Terminate being processed for NS Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("terminate", event_descr)
        self._log.debug("Terminating network service id: %s, NS Name: %s", self.id, self.name)

        # Adding the NSR ID on terminate Evet. This will be checked to halt the instantiation if not already finished. 
        self._ns_terminate_received = True

        yield from self.publish()

        if self._is_failed:
            # IN case the instantiation failed, then trigger a cleanup immediately
            # don't wait for Cfg manager, as it will have no idea of this NSR.
            # Due to the failure
            yield from self.terminate_ns_cont()


    @asyncio.coroutine
    def terminate_ns_cont(self):
        """Config script related to terminate finished, continue termination"""
        def terminate_vnffgrs():
            """ Terminate VNFFGRS in this network service """
            self._log.debug("Terminating VNFFGRs in network service %s - %s", self.id, self.name)
            for vnffgr in self.vnffgrs.values():
                yield from vnffgr.terminate()

        def terminate_vlrs():
            """ Terminate VLRs in this netork service """
            self._log.debug("Terminating VLs in network service %s - %s", self.id, self.name)
            for vlr_id, vlr in self.vlrs.items():
                yield from self.nsm_plugin.terminate_vl(vlr)
                vlr.state = VlRecordState.TERMINATED

        # Move the state to VNF_TERMINATE_PHASE
        self._log.debug("Terminating VNFFGs in NS ID: %s, NS Name: %s", self.id, self.name)
        self.set_state(NetworkServiceRecordState.VNFFG_TERMINATE_PHASE)
        event_descr = "Terminating VNFFGS in NS Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("terminating-vnffgss", event_descr)
        yield from terminate_vnffgrs()

        # Move the state to VNF_TERMINATE_PHASE
        self.set_state(NetworkServiceRecordState.VNF_TERMINATE_PHASE)
        event_descr = "Terminating VNFS in NS Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("terminating-vnfs", event_descr)
        yield from self.terminate_vnfrs(self.vnfrs.values())

        # Move the state to VL_TERMINATE_PHASE
        self.set_state(NetworkServiceRecordState.VL_TERMINATE_PHASE)
        event_descr = "Terminating VLs in NS Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("terminating-vls", event_descr)
        yield from terminate_vlrs()
        yield from self.nsm_plugin.terminate_ns(self)
        # Remove the generated SSH key
        if self._ssh_key_file:
            p = urlparse(self._ssh_key_file)
            if p[0] == 'file':
                path = os.path.dirname(p[2])
                self._log.debug("NSR {}: Removing keys in {}".format(self.name,
                                                                     path))
                shutil.rmtree(path, ignore_errors=True)

        # Move the state to TERMINATED
        self.set_state(NetworkServiceRecordState.TERMINATED)
        event_descr = "Terminated NS Id: %s, NS Name: %s" % (self.id, self.name)
        self.record_event("terminated", event_descr)

        # Unpublish the NSR record
        self._log.debug("Unpublishing the network service %s - %s", self.id, self.name)
        yield from self.unpublish()

        # Finaly delete the NS instance from this NS Manager
        self._log.debug("Deleting the network service %s - %s", self.id, self.name)
        self.nsm.delete_nsr(self.id)

    def enable(self):
        """"Enable a NetworkServiceRecord."""
        pass

    def disable(self):
        """"Disable a NetworkServiceRecord."""
        pass

    def map_config_status(self):
        self._log.debug("Config status for ns {} is {}".
                        format(self.name, self._config_status))
        if self._config_status == NsrYang.ConfigStates.CONFIGURING:
            return 'configuring'
        if self._config_status == NsrYang.ConfigStates.FAILED:
            return 'failed'
        return 'configured'

    def vl_phase_completed(self):
        """ Are VLs created in this NS?"""
        return self._vl_phase_completed

    def vnf_phase_completed(self):
        """ Are VLs created in this NS?"""
        return self._vnf_phase_completed

    def create_msg(self):
        """ The network serice record as a message """
        nsr_dict = {"ns_instance_config_ref": self.id}
        nsr = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr.from_dict(nsr_dict)
        #nsr.datacenter = self.cloud_account_name
        nsr.sdn_account = self._sdn_account_name
        nsr.name_ref = self.name
        nsr.nsd_ref = self.nsd_id
        nsr.nsd_name_ref = self.nsd_msg.name
        nsr.operational_events = self._op_status.msg
        nsr.operational_status = self._op_status.yang_str()
        nsr.config_status = self.map_config_status()
        nsr.config_status_details = self._config_status_details
        nsr.create_time = self._create_time
        nsr.uptime = int(time.time()) - self._create_time

        # Added for OpenMano
        
        nsr.orchestration_progress.networks.total = len(self.nsd_msg.vld)
        if isinstance(self.nsm_plugin, openmano_nsm.OpenmanoNsPlugin):
            # Taking the last update by OpenMano 
            nsr.orchestration_progress.networks.active = self.nsm_plugin._openmano_nsrs[self.id]._active_nets
        else:
            nsr.orchestration_progress.networks.active = self._active_networks
        no_of_vdus = 0
        for vnfr_id, vnfr in self._vnfrs.items():
            no_of_vdus += len(vnfr.vnfd.vdu)

        nsr.orchestration_progress.vms.total = no_of_vdus
        if isinstance(self.nsm_plugin, openmano_nsm.OpenmanoNsPlugin):
            # Taking the last update by OpenMano
            nsr.orchestration_progress.vms.active = self.nsm_plugin._openmano_nsrs[self.id]._active_vms
        else:
            nsr.orchestration_progress.vms.active = self._active_vms

        # Generated SSH key
        if self._ssh_pub_key:
            nsr.ssh_key_generated.private_key_file = self._ssh_key_file
            nsr.ssh_key_generated.public_key = self._ssh_pub_key

        for cfg_prim in self.nsd_msg.service_primitive:
            cfg_prim = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ServicePrimitive.from_dict(
                    cfg_prim.as_dict())
            nsr.service_primitive.append(cfg_prim)

        for init_cfg in self.nsd_msg.initial_service_primitive:
            prim = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_InitialServicePrimitive.from_dict(
                init_cfg.as_dict())
            nsr.initial_service_primitive.append(prim)

        for term_cfg in self.nsd_msg.terminate_service_primitive:
            prim = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_TerminateServicePrimitive.from_dict(
                term_cfg.as_dict())
            nsr.terminate_service_primitive.append(prim)

        if self.vl_phase_completed():
            for vlr_id, vlr in self.vlrs.items():
                nsr.vlr.append(vlr.create_nsr_vlr_msg(self.vnfrs.values()))

        if self.vnf_phase_completed():
            for vnfr_id in self.vnfrs:
                nsr.constituent_vnfr_ref.append(self.vnfrs[vnfr_id].const_vnfr_msg)
            for vnffgr in self.vnffgrs.values():
                nsr.vnffgr.append(vnffgr.fetch_vnffgr())
            for scaling_group in self._scaling_groups.values():
                nsr.scaling_group_record.append(scaling_group.create_record_msg())

        return nsr

    def all_vnfs_active(self):
        """ Are all VNFS in this NS active? """
        for _, vnfr in self.vnfrs.items():
            if vnfr.active is not True:
                return False
        return True

    @asyncio.coroutine
    def update_state(self):
        """ Re-evaluate this  NS's state """
        curr_state = self._op_status.state

        # This means that the terminate has been fired before the NS was UP.
        if self._ns_terminate_received:
            # Resetting this flag so that terminate ns is not called via subsequent DTS Handlers after the intial call.
            self._ns_terminate_received = False
            yield from self.terminate_ns_cont()
        else:
            if curr_state == NetworkServiceRecordState.TERMINATED:
                self._log.debug("NS (%s - %s) in terminated state, not updating state", self.id, self.name)
                return

            new_state = NetworkServiceRecordState.RUNNING
            self._log.debug("Received update_state for nsr: %s, curr-state: %s",
                           self.id, curr_state)

            # check all VLs
            if (isinstance(self.nsm_plugin, rwnsmplugin.RwNsPlugin)):
                for vlr_id, vl in self.vlrs.items():
                    self._log.debug("VLR %s state %s", vlr_id, vl.state)
                    if vl.state in [VlRecordState.ACTIVE, VlRecordState.TERMINATED]:
                        continue
                    elif vl.state == VlRecordState.FAILED:
                        if vl.prev_state != vl.state:
                            event_descr = "Instantiation of VL %s failed" % vl.id
                            event_error_details = vl.state_failed_reason
                            self.record_event("vl-failed", event_descr, evt_details=event_error_details)
                            vl.prev_state = vl.state
                            new_state = NetworkServiceRecordState.FAILED
                            break
                        else:
                            self._log.debug("VL already in failed state")
                    else:
                        if vl.state in [VlRecordState.INSTANTIATION_PENDING, VlRecordState.INIT]:
                            new_state = NetworkServiceRecordState.VL_INSTANTIATE
                            break

                        if vl.state in [VlRecordState.TERMINATE_PENDING]:
                            new_state = NetworkServiceRecordState.VL_TERMINATE
                            break
            
            # Check all the VNFRs are present
            if new_state == NetworkServiceRecordState.RUNNING:
                for _, vnfr in self.vnfrs.items():
                    self._log.debug("VNFR state %s", vnfr.state)
                    if vnfr.state in [VnfRecordState.ACTIVE, VnfRecordState.TERMINATED]:
                        active_vdus = 0
                        for vnfr in self.vnfrs:
                            active_vdus += self.nsm._vnfrs[vnfr]._active_vdus
                        
                        if self._active_vms != active_vdus:
                            self._active_vms = active_vdus
                            yield from self.publish()
                        
                        continue
                        
                    elif vnfr.state == VnfRecordState.FAILED:
                        if vnfr._prev_state != vnfr.state:
                            event_descr = "Instantiation of VNF %s for NS: %s failed" % (vnfr.id, self.name)
                            event_error_details = vnfr.state_failed_reason
                            self.record_event("vnf-failed", event_descr, evt_details=event_error_details)
                            vnfr.set_state(VnfRecordState.FAILED)
                        else:
                            self._log.info("VNF state did not change, curr=%s, prev=%s",
                                           vnfr.state, vnfr._prev_state)
                        new_state = NetworkServiceRecordState.FAILED
                        break
                    else:
                        self._log.debug("VNF %s in NSR %s - %s is still not active; current state is: %s",
                                       vnfr.id, self.id, self.name, vnfr.state)
                        new_state = curr_state
            
            # If new state is RUNNING; check VNFFGRs are also active
            if new_state == NetworkServiceRecordState.RUNNING:
                for _, vnffgr in self.vnffgrs.items():
                    self._log.debug("Checking vnffgr state for nsr %s is: %s",
                                   self.id, vnffgr.state)
                    if vnffgr.state == VnffgRecordState.ACTIVE:
                        continue
                    elif vnffgr.state == VnffgRecordState.FAILED:
                        event_descr = "Instantiation of VNFFGR %s failed" % vnffgr.id
                        self.record_event("vnffg-failed", event_descr)
                        new_state = NetworkServiceRecordState.FAILED
                        break
                    else:
                        self._log.info("VNFFGR %s in NSR %s - %s is still not active; current state is: %s",
                                           vnffgr.id, self.id, self.name, vnffgr.state)
                        new_state = curr_state

            # Update all the scaling group instance operational status to
            # reflect the state of all VNFR within that instance
            yield from self._update_scale_group_instances_status()

            for _, group in self._scaling_groups.items():
                if group.state == scale_group.ScaleGroupState.SCALING_OUT:
                    new_state = NetworkServiceRecordState.SCALING_OUT
                    break
                elif group.state == scale_group.ScaleGroupState.SCALING_IN:
                    new_state = NetworkServiceRecordState.SCALING_IN
                    break

            if new_state != curr_state:
                self._log.debug("Changing state of Network service %s - %s from %s to %s",
                                self.id, self.name, curr_state, new_state)
                if new_state == NetworkServiceRecordState.RUNNING:
                    yield from self.is_active()
                elif new_state == NetworkServiceRecordState.FAILED:
                    # If the NS is already active and we entered scaling_in, scaling_out,
                    # do not mark the NS as failing if scaling operation failed.
                    if curr_state in [NetworkServiceRecordState.SCALING_OUT,
                                      NetworkServiceRecordState.SCALING_IN] and self._is_active:
                        new_state = NetworkServiceRecordState.RUNNING
                        self.set_state(new_state)
                    else:
                        yield from self.instantiation_failed()
                else:
                    self.set_state(new_state)

                yield from self.publish()

    def vl_instantiation_state(self):
        """ Check if all VLs in this NS are active """
        for vl_id, vlr in self.vlrs.items():
            if vlr.state == VlRecordState.ACTIVE:
                continue
            elif vlr.state == VlRecordState.FAILED:
                return VlRecordState.FAILED
            elif vlr.state == VlRecordState.TERMINATED:
                return VlRecordState.TERMINATED
            elif vlr.state == VlRecordState.INSTANTIATION_PENDING:
                return VlRecordState.INSTANTIATION_PENDING
            else:
                self._log.error("vlr %s still in state %s", vlr, vlr.state)
                raise VirtualLinkRecordError("Invalid state %s" %(vlr.state))
        return VlRecordState.ACTIVE

    def vl_instantiation_successful(self):
        """ Mark that all VLs in this NS are active """
        if self._vls_ready.is_set():
            self._log.error("NSR id %s, vls_ready is already set", self.id)

        if self.vl_instantiation_state() == VlRecordState.ACTIVE:
            self._log.debug("NSR id %s, All %d vlrs are in active state %s",
                            self.id, len(self.vlrs), self.vl_instantiation_state)
            self._vls_ready.set()

    def vlr_event(self, vlr, action):
        self._log.debug("Received VLR %s with action:%s", vlr, action)

        if vlr.id not in self.vlrs:
            self._log.error("VLR %s:%s  received  for unknown id, state:%s",
            vlr.id, vlr.name, vlr.operational_status)
            return

        vlr_local = self.vlrs[vlr.id]

        if action == rwdts.QueryAction.CREATE or action == rwdts.QueryAction.UPDATE:
            if vlr.operational_status == 'running':
                vlr_local.set_state_from_op_status(vlr.operational_status)
                self._active_networks += 1
                self._log.info("VLR %s:%s moving to active state",
                               vlr.id,vlr.name)
            elif vlr.operational_status == 'failed':
                vlr_local.set_state_from_op_status(vlr.operational_status)
                vlr_local.state_failed_reason = vlr.operational_status_details
                asyncio.ensure_future(self.update_state(), loop=self._loop)
                self._log.info("VLR %s:%s moving to failed state",
                               vlr.id,vlr.name)
            else:
                self._log.warning("VLR %s:%s  received  state:%s",
                                  vlr.id, vlr.name, vlr.operational_status)

            if isinstance(self.nsm_plugin, rwnsmplugin.RwNsPlugin):
                self.vl_instantiation_successful()

            # self.update_state() is responsible for publishing the NSR state. Its being called by vlr_event and update_vnfr.
            # The call from vlr_event occurs only if vlr reaches a failed state. Hence implementing the check here to handle 
            # ns terminate received after other vlr states as vl-alloc-pending, vl-init, running.
            if self._ns_terminate_received:
                # Resetting this flag so that terminate ns is not called via subsequent DTS Handlers after the intial call.
                if vlr.operational_status in ['running', 'failed']:
                    self._ns_terminate_received = False
                    asyncio.ensure_future(self.terminate_ns_cont(), loop=self._loop)


class InputParameterSubstitution(object):
    """
    This class is responsible for substituting input parameters into an NSD.
    """

    def __init__(self, log, project):
        """Create an instance of InputParameterSubstitution

        Arguments:
            log - a logger for this object to use

        """
        self.log = log
        self.project = project

    def _fix_xpath(self, xpath):
        # Fix the parameter.xpath to include project and correct namespace
        self.log.debug("Provided xpath: {}".format(xpath))
        #Split the xpath at the /
        attrs = xpath.split('/')
        new_xp = attrs[0]
        for attr in attrs[1:]:
            new_ns = 'project-nsd'
            name = attr
            if ':' in attr:
                # Includes namespace
                ns, name = attr.split(':', 2)
                if ns == "rw-nsd":
                    ns = "rw-project-nsd"

            new_xp = new_xp + '/' + new_ns + ':' + name

        updated_xpath = self.project.add_project(new_xp)

        self.log.error("Updated xpath: {}".format(updated_xpath))
        return updated_xpath

    def __call__(self, nsd, nsr_config):
        """Substitutes input parameters from the NSR config into the NSD

        This call modifies the provided NSD with the input parameters that are
        contained in the NSR config.

        Arguments:
            nsd        - a GI NSD object
            nsr_config - a GI NSR config object

        """
        if nsd is None or nsr_config is None:
            return

        # Create a lookup of the xpath elements that this descriptor allows
        # to be modified
        optional_input_parameters = set()
        for input_parameter in nsd.input_parameter_xpath:
            optional_input_parameters.add(input_parameter.xpath)

        # Apply the input parameters to the descriptor
        if nsr_config.input_parameter:
            for param in nsr_config.input_parameter:
                if param.xpath not in optional_input_parameters:
                    msg = "tried to set an invalid input parameter ({})"
                    self.log.error(msg.format(param.xpath))
                    continue

                self.log.debug(
                        "input-parameter:{} = {}".format(
                            param.xpath,
                            param.value,
                            )
                        )

                try:
                    xp = self._fix_xpath(param.xpath)
                    xpath.setxattr(nsd, xp, param.value)

                except Exception as e:
                    self.log.exception(e)


class VnfInputParameterSubstitution(object):
    """
        This class is responsible for substituting input parameters into a VNFD.
    """

    def __init__(self, log, const_vnfd, project):
        """Create an instance of VnfInputParameterSubstitution

        Arguments:
            log - a logger for this object to use
            const_vnfd - id refs for vnfs in a ns
            project - project for the VNFs
        """

        self.log = log
        self.member_vnf_index = const_vnfd.member_vnf_index
        self.vnfd_id_ref = const_vnfd.vnfd_id_ref
        self.project = project

    def __call__(self, vnfr, nsr_config):
        """Substitutes vnf input parameters from the NSR config into the VNFD

        This call modifies the provided VNFD with the input parameters that are
        contained in the NSR config.

        Arguments:
            vnfr        - a GI VNFR object
            nsr_config - a GI NSR Config object

        """

        def compose_xpath(xpath, id):
            prefix = "/rw-project:project[rw-project:name={}]".format(quoted_key(self.project.name)) + \
              "/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]/vnfr:vnfd/".format(quoted_key(id))

            suffix = '/'.join(xpath.split('/')[3:]).replace('vnfd', 'vnfr')
            return prefix + suffix

        def substitute_xpath(ip_xpath, substitute_value, vnfr):
            vnfr_xpath = compose_xpath(ip_xpath, vnfr.id)

            try:
                verify_xpath_wildcarded = xpath.getxattr(vnfr, vnfr_xpath)

                self.log.debug(
                "vnf-input-parameter:{} = {}, for VNF : [member-vnf-index : {}, vnfd-id-ref : {}]".format(
                    ip_xpath,
                    substitute_value,
                    self.member_vnf_index,
                    self.vnfd_id_ref
                    )
                )
                try:
                    xpath.setxattr(vnfr, vnfr_xpath, substitute_value)

                except Exception as e:
                    self.log.exception(e)

            except Exception as e:
                self.log.exception("Wildcarded xpath {} is listy in nature. Can not update. Exception => {}"
                                                   .format(ip_xpath, e))

        if vnfr is None or nsr_config is None:
            return

        optional_input_parameters = set()
        for input_parameter in nsr_config.nsd.input_parameter_xpath:
            optional_input_parameters.add(input_parameter.xpath)

        # Apply the input parameters to the vnfr
        if nsr_config.vnf_input_parameter:
            for param in nsr_config.vnf_input_parameter:
                if (param.member_vnf_index_ref == self.member_vnf_index and param.vnfd_id_ref == self.vnfd_id_ref):
                    if param.input_parameter:
                        for ip in param.input_parameter:
                            if ip.xpath not in optional_input_parameters:
                                msg = "Substitution Failed. Tried to set an invalid vnf input parameter ({}) for vnf [member-vnf-index : {}, vnfd-id-ref : {}]"
                                self.log.error(msg.format(ip.xpath, self.member_vnf_index, self.vnfd_id_ref))
                                continue

                            try:
                                substitute_xpath(ip.xpath, ip.value, vnfr)
                            except Exception as e:
                                self.log.exception(e)
        else:
            self.log.debug("Substituting Xpaths with default Values")
            for input_parameter in nsr_config.nsd.input_parameter_xpath:
                if input_parameter.default_value is not None:
                    try:
                        if "vnfd-catalog" in input_parameter.xpath:
                            substitute_xpath(input_parameter.xpath, input_parameter.default_value, vnfr)
                    except Exception as e:
                        self.log.exception(e)


class NetworkServiceDescriptor(object):
    """
    Network service descriptor class
    """

    def __init__(self, dts, log, loop, nsd, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop

        self._nsd = nsd
        self._nsm = nsm

    @property
    def id(self):
        """ Returns nsd id """
        return self._nsd.id

    @property
    def name(self):
        """ Returns name of nsd """
        return self._nsd.name

    @property
    def msg(self):
        """ Return the message associated with this NetworkServiceDescriptor"""
        return self._nsd

    @staticmethod
    def path_for_id(nsd_id):
        """ Return path for the passed nsd_id"""
        return self._nsm._project.add_project(
            "C,/project-nsd:nsd-catalog/project-nsd:nsd[project-nsd:id = '{}'".
            format(nsd_id))

    def path(self):
        """ Return the message associated with this NetworkServiceDescriptor"""
        return NetworkServiceDescriptor.path_for_id(self.id)

    def update(self, nsd):
        """ Update the NSD descriptor """
        self._nsd = nsd


class NsdDtsHandler(object):
    """ The network service descriptor DTS handler """
    XPATH = "C,/project-nsd:nsd-catalog/project-nsd:nsd"

    def __init__(self, dts, log, loop, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm

        self._regh = None
        self._project = nsm._project

    @property
    def regh(self):
        """ Return registration handle """
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for Nsd create/update/delete/read requests from dts """

        if self._regh:
            self._log.warning("DTS handler already registered for project {}".
                              format(self._project.name))
            return

        def on_apply(dts, acg, xact, action, scratch):
            """Apply the  configuration"""
            is_recovery = xact.xact is None and action == rwdts.AppconfAction.INSTALL
            self._log.debug("Got nsd apply cfg (xact:%s) (action:%s)",
                            xact, action)

            if self._regh:
                # Create/Update an NSD record
                for cfg in self._regh.get_xact_elements(xact):
                    # Only interested in those NSD cfgs whose ID was received in prepare callback
                    if cfg.id in scratch.get('nsds', []) or is_recovery:
                        self._nsm.update_nsd(cfg)

            else:
                # This can happen if we do the deregister
                # during project delete before this is called
                self._log.debug("No reg handle for {} for project {}".
                                format(self.__class__, self._project.name))

            scratch.pop('nsds', None)

            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for NSD config """

            self._log.info("Got nsd prepare - config received nsd id %s, msg %s",
                           msg.id, msg)

            fref = ProtobufC.FieldReference.alloc()
            fref.goto_whole_message(msg.to_pbcm())

            if fref.is_field_deleted():
                # Delete an NSD record
                self._log.debug("Deleting NSD with id %s", msg.id)
                self._nsm.delete_nsd(msg.id)
            else:
                # Add this NSD to scratch to create/update in apply callback
                nsds = scratch.setdefault('nsds', [])
                nsds.append(msg.id)
                # acg._scratch['nsds'].append(msg.id)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(NsdDtsHandler.XPATH)
        self._log.debug(
            "Registering for NSD config using xpath: %s",
            xpath,
            )

        acg_hdl = rift.tasklets.AppConfGroup.Handler(on_apply=on_apply)
        with self._dts.appconf_group_create(handler=acg_hdl) as acg:
            # Need a list in scratch to store NSDs to create/update later
            # acg._scratch['nsds'] = list()
            self._regh = acg.register(
                xpath=xpath,
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                on_prepare=on_prepare)

    def deregister(self):
        self._log.debug("De-register NSD handler for project {}".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None


class VnfdDtsHandler(object):
    """ DTS handler for VNFD config changes """
    XPATH = "C,/project-vnfd:vnfd-catalog/project-vnfd:vnfd"

    def __init__(self, dts, log, loop, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm
        self._regh = None
        self._project = nsm._project

    @property
    def regh(self):
        """ DTS registration handle """
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for VNFD configuration"""

        if self._regh:
            self._log.warning("DTS handler already registered for project {}".
                              format(self._project.name))
            return

        @asyncio.coroutine
        def on_apply(dts, acg, xact, action, scratch):
            """Apply the  configuration"""
            self._log.debug("Got NSM VNFD apply (xact: %s) (action: %s)(scr: %s)",
                            xact, action, scratch)

            is_recovery = xact.xact is None and action == rwdts.AppconfAction.INSTALL

            if self._regh:
                # Create/Update a VNFD record
                for cfg in self._regh.get_xact_elements(xact):
                    # Only interested in those VNFD cfgs whose ID was received in prepare callback
                    if cfg.id in scratch.get('vnfds', []) or is_recovery:
                        self._nsm.update_vnfd(cfg)

                for cfg in self._regh.elements:
                    if cfg.id in scratch.get('deleted_vnfds', []):
                        yield from self._nsm.delete_vnfd(cfg.id)

            else:
                self._log.warning("Reg handle none for {} in project {}".
                                  format(self.__class__, self._project))

            scratch.pop('vnfds', None)
            scratch.pop('deleted_vnfds', None)

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ on prepare callback """
            xpath = ks_path.to_xpath(NsdYang.get_schema())
            self._log.debug("Got on prepare for VNFD (path: %s) (action: %s) (msg: %s)",
                            xpath, xact_info.query_action, msg)

            fref = ProtobufC.FieldReference.alloc()
            fref.goto_whole_message(msg.to_pbcm())

            # Handle deletes in prepare_callback, but adds/updates in apply_callback
            if fref.is_field_deleted():
                self._log.debug("Adding msg to deleted field")
                deleted_vnfds = scratch.setdefault('deleted_vnfds', [])
                deleted_vnfds.append(msg.id)
            else:
                # Add this VNFD to scratch to create/update in apply callback
                vnfds = scratch.setdefault('vnfds', [])
                vnfds.append(msg.id)

            try:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
            except rift.tasklets.dts.ResponseError as e:
                self._log.warning(
                    "VnfdDtsHandler in project {} with path {} for action {} failed: {}".
                    format(self._project, xpath, xact_info.query_action, e))


        xpath = self._project.add_project(VnfdDtsHandler.XPATH)
        self._log.debug(
            "Registering for VNFD config using xpath {} for project {}"
            .format(xpath, self._project))
        acg_hdl = rift.tasklets.AppConfGroup.Handler(on_apply=on_apply)
        with self._dts.appconf_group_create(handler=acg_hdl) as acg:
            # Need a list in scratch to store VNFDs to create/update later
            # acg._scratch['vnfds'] = list()
            # acg._scratch['deleted_vnfds'] = list()
            self._regh = acg.register(
                xpath=xpath,
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY,
                on_prepare=on_prepare)

    def deregister(self):
        self._log.debug("De-register VNFD handler for project {}".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None


class NsrRpcDtsHandler(object):
    """ The network service instantiation RPC DTS handler """
    EXEC_NSR_CONF_XPATH = "I,/nsr:start-network-service"
    EXEC_NSR_CONF_O_XPATH = "O,/nsr:start-network-service"
    NETCONF_IP_ADDRESS = "127.0.0.1"
    NETCONF_PORT = 2022
    RESTCONF_PORT = 8008
    NETCONF_USER = "@rift"
    NETCONF_PW = "rift"
    REST_BASE_V2_URL = 'https://{}:{}/v2/api/'.format("127.0.0.1",
                                                      RESTCONF_PORT)

    def __init__(self, dts, log, loop, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm
        self._project = nsm._project
        self._nsd = None

        self._ns_regh = None

        self._manager = None
        self._nsr_config_url = NsrRpcDtsHandler.REST_BASE_V2_URL + \
                               'project/{}/'.format(self._project) + \
                               'config/ns-instance-config'

        self._model = RwYang.Model.create_libncx()
        self._model.load_schema_ypbc(RwNsrYang.get_schema())

    @property
    def nsm(self):
        """ Return the NS manager instance """
        return self._nsm

    @staticmethod
    def wrap_netconf_config_xml(xml):
        xml = '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">{}</config>'.format(xml)
        return xml

    @asyncio.coroutine
    def _connect(self, timeout_secs=240):

        start_time = time.time()
        while (time.time() - start_time) < timeout_secs:

            try:
                self._log.debug("Attemping NsmTasklet netconf connection.")

                manager = yield from ncclient.asyncio_manager.asyncio_connect(
                        loop=self._loop,
                        host=NsrRpcDtsHandler.NETCONF_IP_ADDRESS,
                        port=NsrRpcDtsHandler.NETCONF_PORT,
                        username=NsrRpcDtsHandler.NETCONF_USER,
                        password=NsrRpcDtsHandler.NETCONF_PW,
                        allow_agent=False,
                        look_for_keys=False,
                        hostkey_verify=False,
                        )

                return manager

            except ncclient.transport.errors.SSHError as e:
                self._log.warning("Netconf connection to launchpad %s failed: %s",
                                  NsrRpcDtsHandler.NETCONF_IP_ADDRESS, str(e))

            yield from asyncio.sleep(5, loop=self._loop)

        raise NsrInstantiationFailed("Failed to connect to Launchpad within %s seconds" %
                                      timeout_secs)

    def _apply_ns_instance_config(self,payload_dict):
        req_hdr= {'accept':'application/vnd.yang.data+json','content-type':'application/vnd.yang.data+json'}
        response=requests.post(self._nsr_config_url,
                               headers=req_hdr,
                               auth=(NsrRpcDtsHandler.NETCONF_USER, NsrRpcDtsHandler.NETCONF_PW),
                               data=payload_dict,
                               verify=False)
        return response

    @asyncio.coroutine
    def register(self):
        """ Register for NS monitoring read from dts """

        @asyncio.coroutine
        def on_ns_config_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts start-network-service"""
            assert action == rwdts.QueryAction.RPC

            if not self._project.rpc_check(msg, xact_info):
                return

            rpc_ip = msg
            rpc_op = NsrYang.YangOutput_Nsr_StartNetworkService.from_dict({
                    "nsr_id":str(uuid.uuid4())
                })

            if not ('name' in rpc_ip and  'nsd_ref' in rpc_ip and
                    ('cloud_account' in rpc_ip or 'om_datacenter' in rpc_ip)):
                errmsg = (
                    "Mandatory parameters name or nsd_ref or cloud account not found in start-network-service {}".
                    format(rpc_ip))
                self._log.error(errmsg)
                xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           NsrRpcDtsHandler.EXEC_NSR_CONF_O_XPATH,
                                           errmsg)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK,
                                        NsrRpcDtsHandler.EXEC_NSR_CONF_O_XPATH)
                return

            self._log.debug("start-network-service RPC input: {}".format(rpc_ip))

            try:
                # Add used value to the pool
                self._log.debug("RPC output: {}".format(rpc_op))

                nsd_copy = self.nsm.get_nsd(rpc_ip.nsd_ref)

                self._log.debug("Configuring ns-instance-config with name  %s nsd-ref: %s",
                        rpc_ip.name, rpc_ip.nsd_ref)

                ns_instance_config_dict = {"id":rpc_op.nsr_id, "admin_status":"ENABLED"}
                ns_instance_config_copy_dict = {k:v for k, v in rpc_ip.as_dict().items()
                                                if k in RwNsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr().fields}
                ns_instance_config_dict.update(ns_instance_config_copy_dict)

                ns_instance_config = RwNsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr.from_dict(ns_instance_config_dict)
                ns_instance_config.nsd = RwNsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_Nsd()
                ns_instance_config.nsd.from_dict(nsd_copy.msg.as_dict())

                payload_dict = ns_instance_config.to_json(self._model)

                self._log.debug("Sending configure ns-instance-config json to %s: %s",
                        self._nsr_config_url,ns_instance_config)

                response = yield from self._loop.run_in_executor(
                    None,
                    self._apply_ns_instance_config,
                    payload_dict
                    )
                response.raise_for_status()
                self._log.debug("Received edit config response: %s", response.json())

                xact_info.respond_xpath(rwdts.XactRspCode.ACK,
                                        NsrRpcDtsHandler.EXEC_NSR_CONF_O_XPATH,
                                        rpc_op)
            except Exception as e:
                errmsg = ("Exception processing the "
                          "start-network-service: {}".format(e))
                self._log.exception(errmsg)
                xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           NsrRpcDtsHandler.EXEC_NSR_CONF_O_XPATH,
                                           errmsg)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK,
                                        NsrRpcDtsHandler.EXEC_NSR_CONF_O_XPATH)

        self._ns_regh = yield from self._dts.register(
                xpath=NsrRpcDtsHandler.EXEC_NSR_CONF_XPATH,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_ns_config_prepare),
                flags=rwdts.Flag.PUBLISHER,
            )

    def deregister(self):
        if self._ns_regh:
            self._ns_regh.deregister()
            self._ns_regh = None


class NsrDtsHandler(object):
    """ The network service DTS handler """
    NSR_XPATH = "C,/nsr:ns-instance-config/nsr:nsr"
    SCALE_INSTANCE_XPATH = "C,/nsr:ns-instance-config/nsr:nsr/nsr:scaling-group/nsr:instance"
    KEY_PAIR_XPATH = "C,/nsr:key-pair"

    def __init__(self, dts, log, loop, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm
        self._project = self._nsm._project

        self._nsr_regh = None
        self._scale_regh = None
        self._key_pair_regh = None

    @property
    def nsm(self):
        """ Return the NS manager instance """
        return self._nsm

    @asyncio.coroutine
    def register(self):
        """ Register for Nsr create/update/delete/read requests from dts """

        if self._nsr_regh:
            self._log.warning("DTS handler already registered for project {}".
                              format(self._project.name))
            return

        def nsr_id_from_keyspec(ks):
            nsr_path_entry = RwNsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr.schema().keyspec_to_entry(ks)
            nsr_id = nsr_path_entry.key00.id
            return nsr_id

        def group_name_from_keyspec(ks):
            group_path_entry = NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_ScalingGroup.schema().keyspec_to_entry(ks)
            group_name = group_path_entry.key00.scaling_group_name_ref
            return group_name

        def is_instance_in_reg_elements(nsr_id, group_name, instance_id):
            """ Return boolean indicating if scaling group instance was already commited previously.

            By looking at the existing elements in this registration handle (elements not part
            of this current xact), we can tell if the instance was configured previously without
            keeping any application state.
            """
            for instance_cfg, keyspec in self._nsr_regh.get_xact_elements(include_keyspec=True):
                elem_nsr_id = nsr_id_from_keyspec(keyspec)
                elem_group_name = group_name_from_keyspec(keyspec)

                if elem_nsr_id != nsr_id or group_name != elem_group_name:
                    continue

                if instance_cfg.id == instance_id:
                    return True

            return False

        def get_scale_group_instance_delta(nsr_id, group_name, xact):
            delta = {"added": [], "deleted": []}
            for instance_cfg, keyspec in self._scale_regh.get_xact_elements(xact, include_keyspec=True):
                elem_nsr_id = nsr_id_from_keyspec(keyspec)
                if elem_nsr_id != nsr_id:
                    continue

                elem_group_name = group_name_from_keyspec(keyspec)
                if elem_group_name != group_name:
                    continue

                delta["added"].append(instance_cfg.id)

            for instance_cfg, keyspec in self._scale_regh.get_xact_elements(include_keyspec=True):
                elem_nsr_id = nsr_id_from_keyspec(keyspec)
                if elem_nsr_id != nsr_id:
                    continue

                elem_group_name = group_name_from_keyspec(keyspec)
                if elem_group_name != group_name:
                    continue

                if instance_cfg.id in delta["added"]:
                    delta["added"].remove(instance_cfg.id)
                else:
                    delta["deleted"].append(instance_cfg.id)

            return delta

        @asyncio.coroutine
        def update_nsr_nsd(nsr_id, xact, scratch):

            @asyncio.coroutine
            def get_nsr_vl_delta(nsr_id, xact, scratch):
                delta = {"added": [], "deleted": []}
                for instance_cfg, keyspec in self._nsr_regh.get_xact_elements(xact, include_keyspec=True):
                    elem_nsr_id = nsr_id_from_keyspec(keyspec)
                    if elem_nsr_id != nsr_id:
                        continue

                    if 'vld' in instance_cfg.nsd:
                        for vld in instance_cfg.nsd.vld:
                            delta["added"].append(vld)

                for instance_cfg, keyspec in self._nsr_regh.get_xact_elements(include_keyspec=True):
                    self._log.debug("NSR update: %s", instance_cfg)
                    elem_nsr_id = nsr_id_from_keyspec(keyspec)
                    if elem_nsr_id != nsr_id:
                        continue

                    if 'vld' in instance_cfg.nsd:
                        for vld in instance_cfg.nsd.vld:
                            if vld in delta["added"]:
                                delta["added"].remove(vld)
                            else:
                                delta["deleted"].append(vld)

                return delta

            vl_delta = yield from get_nsr_vl_delta(nsr_id, xact, scratch)
            self._log.debug("Got NSR:%s VL instance delta: %s", nsr_id, vl_delta)

            for vld in vl_delta["added"]:
                yield from self._nsm.nsr_instantiate_vl(nsr_id, vld)

            for vld in vl_delta["deleted"]:
                yield from self._nsm.nsr_terminate_vl(nsr_id, vld)

        def get_nsr_key_pairs(dts_member_reg, xact):
            key_pairs = {}
            for instance_cfg, keyspec in dts_member_reg.get_xact_elements(xact, include_keyspec=True):
                self._log.debug("Key pair received is {} KS: {}".format(instance_cfg, keyspec))
                xpath = keyspec.to_xpath(RwNsrYang.get_schema())
                key_pairs[instance_cfg.name] = instance_cfg
            return key_pairs

        def on_apply(dts, acg, xact, action, scratch):
            """Apply the  configuration"""
            self._log.debug("Got nsr apply (xact: %s) (action: %s)(scr: %s)",
                            xact, action, scratch)

            @asyncio.coroutine
            def handle_create_nsr(msg, key_pairs=None, restart_mode=False):
                # Handle create nsr requests """
                # Do some validations
                if not msg.has_field("nsd"):
                    err = "NSD not provided"
                    self._log.error(err)
                    raise NetworkServiceRecordError(err)

                self._log.debug("Creating NetworkServiceRecord %s  from nsr config  %s",
                               msg.id, msg.as_dict())
                nsr = yield from self.nsm.create_nsr(msg,
                                                     xact,
                                                     key_pairs=key_pairs,
                                                     restart_mode=restart_mode)
                return nsr

            def handle_delete_nsr(msg):
                @asyncio.coroutine
                def delete_instantiation(ns_id):
                    """ Delete instantiation """
                    yield from self._nsm.terminate_ns(ns_id, None)

                # Handle delete NSR requests
                self._log.info("Delete req for  NSR Id: %s received", msg.id)
                # Terminate the NSR instance
                nsr = self._nsm.get_ns_by_nsr_id(msg.id)

                nsr.set_state(NetworkServiceRecordState.TERMINATE_RCVD)
                event_descr = "Terminate rcvd for NS Id: %s, NS Name: %s" % (msg.id, msg.name)
                nsr.record_event("terminate-rcvd", event_descr)

                self._loop.create_task(delete_instantiation(msg.id))

            @asyncio.coroutine
            def begin_instantiation(nsr):
                # Begin instantiation
                self._log.info("Beginning NS instantiation: %s", nsr.id)
                try:
                    yield from self._nsm.instantiate_ns(nsr.id, xact)
                except Exception as e:
                    self._log.exception(e)
                    raise e

            @asyncio.coroutine
            def instantiate_ns(msg, key_pairs, restart_mode=False):
                nsr = yield from handle_create_nsr(msg, key_pairs, restart_mode=restart_mode)
                yield from begin_instantiation(nsr)

            def on_instantiate_done(fut, msg):
                # If the do_instantiate fails, then publish NSR with failed result
                e = fut.exception()
                if e is not None:
                    import traceback
                    print(traceback.format_exception(None, e, e.__traceback__), file=sys.stderr, flush=True)
                    self._log.error("NSR instantiation failed for NSR id %s: %s", msg.id, str(e))
                    failed_nsr = self._nsm.nsrs[msg.id]
                    self._loop.create_task(failed_nsr.instantiation_failed(failed_reason=str(e)))


            self._log.debug("Got nsr apply (xact: %s) (action: %s)(scr: %s)",
                            xact, action, scratch)

            if action == rwdts.AppconfAction.INSTALL and xact.id is None:
                key_pairs = []
                if self._key_pair_regh:
                    for element in self._key_pair_regh.elements:
                        key_pairs.append(element)
                else:
                    self._log.error("Reg handle none for key pair in project {}".
                                    format(self._project))

                if self._nsr_regh:
                    for element in self._nsr_regh.elements:
                        if element.id not in self.nsm._nsrs:
                            instantiate_task = self._loop.create_task(instantiate_ns(element, key_pairs,
                                                                  restart_mode=True))
                            instantiate_task.add_done_callback(functools.partial(on_instantiate_done, msg=element))
                else:
                    self._log.error("Reg handle none for NSR in project {}".
                                    format(self._project))

                return RwTypes.RwStatus.SUCCESS

            (added_msgs, deleted_msgs, updated_msgs) = get_add_delete_update_cfgs(self._nsr_regh,
                                                                                  xact,
                                                                                  "id")
            self._log.debug("Added: %s, Deleted: %s, Updated: %s", added_msgs,
                            deleted_msgs, updated_msgs)

            for msg in added_msgs:
                if msg.id not in self._nsm.nsrs:
                    self._log.info("Create NSR received in on_apply to instantiate NS:%s", msg.id)
                    key_pairs = get_nsr_key_pairs(self._key_pair_regh, xact)
                    instantiate_task = self._loop.create_task(instantiate_ns(msg,key_pairs))
                    instantiate_task.add_done_callback(functools.partial(on_instantiate_done, msg=msg))

            for msg in deleted_msgs:
                self._log.info("Delete NSR received in on_apply to terminate NS:%s", msg.id)
                try:
                    handle_delete_nsr(msg)
                except Exception:
                    self._log.exception("Failed to terminate NS:%s", msg.id)

            for msg in updated_msgs:
                self._log.info("Update NSR received in on_apply: %s", msg)
                self._nsm.nsr_update_cfg(msg.id, msg)

                if 'nsd' in msg:
                    self._loop.create_task(update_nsr_nsd(msg.id, xact, scratch))

                for group in msg.scaling_group:
                    instance_delta = get_scale_group_instance_delta(msg.id, group.scaling_group_name_ref, xact)
                    self._log.debug("Got NSR:%s scale group instance delta: %s", msg.id, instance_delta)

                    for instance_id in instance_delta["added"]:
                        self._nsm.scale_nsr_out(msg.id, group.scaling_group_name_ref, instance_id, xact)

                    for instance_id in instance_delta["deleted"]:
                        self._nsm.scale_nsr_in(msg.id, group.scaling_group_name_ref, instance_id)


            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare calllback from DTS for NSR """

            xpath = ks_path.to_xpath(RwNsrYang.get_schema())
            action = xact_info.query_action
            self._log.debug(
                    "Got Nsr prepare callback (xact: %s) (action: %s) (info: %s), %s:%s)",
                    xact, action, xact_info, xpath, msg
                    )

            fref = ProtobufC.FieldReference.alloc()
            fref.goto_whole_message(msg.to_pbcm())

            def send_err_msg(err_msg):
                self._log.error(errmsg)
                xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           xpath,
                                           errmsg)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)


            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE, rwdts.QueryAction.DELETE]:
                # if this is an NSR create
                if action != rwdts.QueryAction.DELETE and msg.id not in self._nsm.nsrs:
                    # Ensure the Cloud account/datacenter has been specified
                    if not msg.has_field("datacenter") and not msg.has_field("datacenter"):
                        errmsg = ("Cloud account or datacenter not specified in NS {}".
                                  format(msg.name))
                        send_err_msg(errmsg)
                        return

                    # Check if nsd is specified
                    if not msg.has_field("nsd"):
                        errmsg = ("NSD not specified in NS {}".
                                  format(msg.name))
                        send_err_msg(errmsg)
                        return

                else:
                    nsr = self._nsm.nsrs[msg.id]
                    if msg.has_field("nsd"):
                        if nsr.state != NetworkServiceRecordState.RUNNING:
                            errmsg = ("Unable to update VL when NS {} not in running state".
                                      format(msg.name))
                            send_err_msg(errmsg)
                            return

                        if 'vld' not in msg.nsd or len(msg.nsd.vld) == 0:
                            errmsg = ("NS config {} NSD should have atleast 1 VLD".
                                      format(msg.name))
                            send_err_msg(errmsg)
                            return

                    if msg.has_field("scaling_group"):
                        self._log.debug("ScaleMsg %s", msg)
                        self._log.debug("NSSCALINGSTATE %s", nsr.state)
                        if nsr.state != NetworkServiceRecordState.RUNNING:
                            errmsg = ("Unable to perform scaling action when NS {} not in running state".
                                      format(msg.name))
                            send_err_msg(errmsg)
                            return

                        if len(msg.scaling_group) > 1:
                            errmsg = ("Only a single scaling group can be configured at a time for NS {}".
                                      format(msg.name))
                            send_err_msg(errmsg)
                            return

                        for group_msg in msg.scaling_group:
                            num_new_group_instances = len(group_msg.instance)
                            if num_new_group_instances > 1:
                                errmsg = ("Only a single scaling instance can be modified at a time for NS {}".
                                          format(msg.name))
                                send_err_msg(errmsg)
                                return

                            elif num_new_group_instances == 1:
                                scale_group = nsr.scaling_groups[group_msg.scaling_group_name_ref]
                                if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                                    if len(scale_group.instances) == scale_group.max_instance_count:
                                        errmsg = (" Max instances for {} reached for NS {}".
                                                  format(str(scale_group), msg.name))
                                        send_err_msg(errmsg)
                                        return

            acg.handle.prepare_complete_ok(xact_info.handle)


        xpath = self._project.add_project(NsrDtsHandler.NSR_XPATH)
        self._log.debug("Registering for NSR config using xpath: {}".
                        format(xpath))

        acg_hdl = rift.tasklets.AppConfGroup.Handler(on_apply=on_apply)
        with self._dts.appconf_group_create(handler=acg_hdl) as acg:
            self._nsr_regh = acg.register(
                xpath=xpath,
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                on_prepare=on_prepare
            )

            self._scale_regh = acg.register(
                xpath=self._project.add_project(NsrDtsHandler.SCALE_INSTANCE_XPATH),
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY| rwdts.Flag.CACHE,
            )

            self._key_pair_regh = acg.register(
                xpath=self._project.add_project(NsrDtsHandler.KEY_PAIR_XPATH),
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
            )

    def deregister(self):
        self._log.debug("De-register NSR config for project {}".
                        format(self._project.name))
        if self._nsr_regh:
            self._nsr_regh.deregister()
            self._nsr_regh = None
        if self._scale_regh:
            self._scale_regh.deregister()
            self._scale_regh = None
        if self._key_pair_regh:
            self._key_pair_regh.deregister()
            self._key_pair_regh = None


class VnfrDtsHandler(object):
    """ The virtual network service DTS handler """
    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr"

    def __init__(self, dts, log, loop, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm

        self._regh = None

    @property
    def regh(self):
        """ Return registration handle """
        return self._regh

    @property
    def nsm(self):
        """ Return the NS manager instance """
        return self._nsm

    @asyncio.coroutine
    def register(self):
        """ Register for vnfr create/update/delete/ advises from dts """
        if self._regh:
            self._log.warning("VNFR DTS handler already registered for project {}".
                              format(self._project.name))
            return

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts """
            xpath = ks_path.to_xpath(RwNsrYang.get_schema())
            self._log.debug(
                "Got vnfr on_prepare cb (xact_info: %s, action: %s): %s:%s",
                xact_info, action, ks_path, msg
                )

            schema = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr.schema()
            path_entry = schema.keyspec_to_entry(ks_path)
            if not path_entry or (path_entry.key00.id not in self._nsm._vnfrs):
                # This can happen when using external RO or after delete with monitoring params
                self._log.debug("%s request for non existent record path %s",
                                action, xpath)
                xact_info.respond_xpath(rwdts.XactRspCode.NA, xpath)

                return

            if action == rwdts.QueryAction.CREATE or action == rwdts.QueryAction.UPDATE:
                yield from self._nsm.update_vnfr(msg)
            elif action == rwdts.QueryAction.DELETE:
                self._log.debug("Deleting VNFR with id %s", path_entry.key00.id)

                self._nsm.delete_vnfr(path_entry.key00.id)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK, xpath)

        self._log.debug("Registering for VNFR using xpath: %s",
                        VnfrDtsHandler.XPATH)

        hdl = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare,)
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=self._nsm._project.add_project(
                VnfrDtsHandler.XPATH),
                                        handler=hdl,
                                        flags=(rwdts.Flag.SUBSCRIBER),)

    def deregister(self):
        self._log.debug("De-register VNFR for project {}".
                        format(self._nsm._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None

class NsManager(object):
    """ The Network Service Manager class"""
    def __init__(self, dts, log, loop, project,
                 nsr_handler, vnfr_handler, vlr_handler, ro_plugin_selector,
                 vnffgmgr, vnfd_pub_handler, cloud_account_handler):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._nsr_handler = nsr_handler
        self._vnfr_pub_handler = vnfr_handler
        self._vlr_pub_handler = vlr_handler
        self._vnffgmgr = vnffgmgr
        self._vnfd_pub_handler = vnfd_pub_handler
        self._cloud_account_handler = cloud_account_handler

        self._ro_plugin_selector = ro_plugin_selector

        # Intialize the set of variables for implementing Scaling RPC using REST.
        self._headers = {"content-type":"application/json", "accept":"application/json"}
        self._user = '@rift'
        self._password = 'rift'
        self._ip = 'localhost'
        self._rport = 8008
        self._conf_url = "https://{ip}:{port}/api/config/project/{project}". \
                       format(ip=self._ip,
                              port=self._rport,
                              project=self._project.name)

        self._nsrs = {}
        self._nsds = {}
        self._vnfds = {}
        self._vnfrs = {}
        self._nsr_for_vlr = {}

        self.cfgmgr_obj = conman.ROConfigManager(log, loop, dts, self)

        # TODO: All these handlers should move to tasklet level.
        # Passing self is often an indication of bad design
        self._nsd_dts_handler = NsdDtsHandler(dts, log, loop, self)
        self._vnfd_dts_handler = VnfdDtsHandler(dts, log, loop, self)
        self._dts_handlers = [self._nsd_dts_handler,
                              VnfrDtsHandler(dts, log, loop, self),
                              NsrDtsHandler(dts, log, loop, self),
                              ScalingRpcHandler(log, dts, loop, self, self.scale_rpc_callback),
                              # NsrRpcDtsHandler(dts, log, loop, self),
                              self._vnfd_dts_handler,
                              self.cfgmgr_obj,
                              ]


    @property
    def log(self):
        """ Log handle """
        return self._log

    @property
    def loop(self):
        """ Loop """
        return self._loop

    @property
    def dts(self):
        """ DTS handle """
        return self._dts

    @property
    def nsr_handler(self):
        """" NSR handler """
        return self._nsr_handler

    @property
    def so_obj(self):
        """" So Obj handler """
        return self._so_obj

    @property
    def nsrs(self):
        """ NSRs in this NSM"""
        return self._nsrs

    @property
    def nsds(self):
        """ NSDs in this NSM"""
        return self._nsds

    @property
    def vnfds(self):
        """ VNFDs in this NSM"""
        return self._vnfds

    @property
    def vnfrs(self):
        """ VNFRs in this NSM"""
        return self._vnfrs

    @property
    def nsr_pub_handler(self):
        """ NSR publication handler """
        return self._nsr_handler

    @property
    def vnfr_pub_handler(self):
        """ VNFR publication handler """
        return self._vnfr_pub_handler

    @property
    def vlr_pub_handler(self):
        """ VLR publication handler """
        return self._vlr_pub_handler

    @property
    def vnfd_pub_handler(self):
        return self._vnfd_pub_handler

    @asyncio.coroutine
    def register(self):
        """ Register all static DTS handlers """
        self._log.debug("Register DTS handlers for project {}".format(self._project))
        for dts_handle in self._dts_handlers:
            if asyncio.iscoroutinefunction(dts_handle.register):
                yield from dts_handle.register()
            else:
                dts_handle.register()

    def deregister(self):
        """ Register all static DTS handlers """
        for dts_handle in self._dts_handlers:
            dts_handle.deregister()


    def get_ns_by_nsr_id(self, nsr_id):
        """ get NSR by nsr id """
        if nsr_id not in self._nsrs:
            raise NetworkServiceRecordError("NSR id %s not found" % nsr_id)

        return self._nsrs[nsr_id]

    def scale_nsr_out(self, nsr_id, scale_group_name, instance_id, config_xact):
        self.log.debug("Scale out NetworkServiceRecord (nsr_id: %s) (scaling group: %s) (instance_id: %s)",
                       nsr_id,
                       scale_group_name,
                       instance_id
                       )
        nsr = self._nsrs[nsr_id]
        if nsr.state != NetworkServiceRecordState.RUNNING:
            raise ScalingOperationError("Cannot perform scaling operation if NSR is not in running state")

        self._loop.create_task(nsr.create_scale_group_instance(scale_group_name, instance_id, config_xact))

    def scale_nsr_in(self, nsr_id, scale_group_name, instance_id):
        self.log.debug("Scale in NetworkServiceRecord (nsr_id: %s) (scaling group: %s) (instance_id: %s)",
                       nsr_id,
                       scale_group_name,
                       instance_id,
                       )
        nsr = self._nsrs[nsr_id]
        if nsr.state != NetworkServiceRecordState.RUNNING:
            raise ScalingOperationError("Cannot perform scaling operation if NSR is not in running state")

        self._loop.create_task(nsr.delete_scale_group_instance(scale_group_name, instance_id))

    def scale_rpc_callback(self, xact, msg, action):
        """Callback handler for RPC calls
        Args:
            xact : Transaction Handler
            msg : RPC input
            action : Scaling Action
        """
        def get_scaling_group_information():
            scaling_group_url = "{url}/ns-instance-config/nsr/{nsr_id}".format(url=self._conf_url, nsr_id=msg.nsr_id_ref)
            output = requests.get(scaling_group_url, headers=self._headers, auth=(self._user, self._password), verify=False)
            if output.text is None or len(output.text) == 0:
                self.log.error("nsr id %s information not present", self._nsr_id)
                return None
            scaling_group_info = json.loads(output.text)
            return scaling_group_info

        def config_scaling_group_information(scaling_group_info):
            data_str = json.dumps(scaling_group_info)

            scale_out_url = "{url}/ns-instance-config/nsr/{nsr_id}".format(url=self._conf_url, nsr_id=msg.nsr_id_ref)
            response = requests.put(scale_out_url, data=data_str, verify=False,
                                    auth=(self._user, self._password), headers=self._headers)
            response.raise_for_status()

        def scale_out():
            scaling_group_info = get_scaling_group_information()
            self._log.debug("Scale out info: {}".format(scaling_group_info))
            if scaling_group_info is None:
                return

            scaling_group_present = False
            if "scaling-group" in scaling_group_info["nsr:nsr"]:
                scaling_group_array = scaling_group_info["nsr:nsr"]["scaling-group"]
                for scaling_group in scaling_group_array:
                    if scaling_group["scaling-group-name-ref"] == msg.scaling_group_name_ref:
                        scaling_group_present = True
                        if 'instance' not in scaling_group:
                            scaling_group['instance'] = []
                        for instance in scaling_group['instance']:
                            if instance["id"] == int(msg.instance_id):
                                self.log.error("scaling group with instance id %s exists for scale out", msg.instance_id)
                                return
                        scaling_group["instance"].append({"id": int(msg.instance_id)})

            if not scaling_group_present:
                scaling_group_info["nsr:nsr"]["scaling-group"] = [{"scaling-group-name-ref": msg.scaling_group_name_ref,
                                                                   "instance": [{"id": msg.instance_id}]}]

            config_scaling_group_information(scaling_group_info)
            return

        def scale_in():
            scaling_group_info = get_scaling_group_information()
            if scaling_group_info is None:
                return

            scaling_group_array = scaling_group_info["nsr:nsr"]["scaling-group"]
            scaling_group_present = False
            instance_id_present = False
            for scaling_group in scaling_group_array:
                if scaling_group["scaling-group-name-ref"] == msg.scaling_group_name_ref:
                    scaling_group_present = True
                    if 'instance' in scaling_group:
                        instance_array = scaling_group["instance"];
                        for index in range(len(instance_array)):
                            if instance_array[index]["id"] == int(msg.instance_id):
                                instance_array.pop(index)
                                instance_id_present = True
                                break

            if not scaling_group_present:
                self.log.error("Scaling group %s doesnot exists for scale in", msg.scaling_group_name_ref)
                return

            if not instance_id_present:
                self.log.error("Instance id %s doesnot exists for scale in", msg.instance_id)
                return

            config_scaling_group_information(scaling_group_info)
            return

        if action == ScalingRpcHandler.ACTION.SCALE_OUT:
            self._loop.run_in_executor(None, scale_out)
        else:
            self._loop.run_in_executor(None, scale_in)

    def nsr_update_cfg(self, nsr_id, msg):
        nsr = self._nsrs[nsr_id]
        nsr.nsr_cfg_msg= msg

    def nsr_instantiate_vl(self, nsr_id, vld):
        self.log.error("NSR {} create VL {}".format(nsr_id, vld))
        nsr = self._nsrs[nsr_id]
        if nsr.state != NetworkServiceRecordState.RUNNING:
            raise NsrVlUpdateError("Cannot perform VL instantiate if NSR is not in running state")

        # Not calling in a separate task as this is called from a separate task
        yield from nsr.create_vl_instance(vld)

    def nsr_terminate_vl(self, nsr_id, vld):
        self.log.debug("NSR {} delete VL {}".format(nsr_id, vld.id))
        nsr = self._nsrs[nsr_id]
        if nsr.state != NetworkServiceRecordState.RUNNING:
            raise NsrVlUpdateError("Cannot perform VL terminate if NSR is not in running state")

        # Not calling in a separate task as this is called from a separate task
        yield from nsr.delete_vl_instance(vld)

    @asyncio.coroutine
    def create_nsr(self, nsr_msg, config_xact, key_pairs=None,restart_mode=False):
        """ Create an NSR instance """
        self._log.debug("NSRMSG %s", nsr_msg)
        if nsr_msg.id in self._nsrs:
            msg = "NSR id %s already exists" % nsr_msg.id
            self._log.error(msg)
            raise NetworkServiceRecordError(msg)

        self._log.debug("Create NetworkServiceRecord nsr id %s from nsd_id %s",
                       nsr_msg.id,
                       nsr_msg.nsd.id)

        nsm_plugin = self._ro_plugin_selector.get_ro_plugin(nsr_msg.resource_orchestrator)
        #Work Around - openmano expects datacenter id instead of datacenter name
        if isinstance(nsm_plugin, openmano_nsm.OpenmanoNsPlugin):
            for uuid, name in nsm_plugin._cli_api.datacenter_list():
                if name == nsr_msg.datacenter:
                    nsr_msg.datacenter = uuid

        sdn_account_name = self._cloud_account_handler.get_cloud_account_sdn_name(nsr_msg.datacenter)

        nsr = NetworkServiceRecord(self._dts,
                                   self._log,
                                   self._loop,
                                   self,
                                   nsm_plugin,
                                   nsr_msg,
                                   sdn_account_name,
                                   key_pairs,
                                   self._project,
                                   restart_mode=restart_mode,
                                   vlr_handler=self._vlr_pub_handler
                                   )
        self._nsrs[nsr_msg.id] = nsr

        try:
            # Generate ssh key pair if required
            nsr.generate_ssh_key_pair(config_xact)
        except Exception as e:
            self._log.exception("SSH key: {}".format(e))

        self._log.debug("NSR {}: SSh key generated: {}".format(nsr_msg.name,
                                                               nsr.public_key))

        ssh_key = {'private_key': nsr.private_key,
                   'public_key': nsr.public_key
        }

        nsm_plugin.create_nsr(nsr_msg, nsr_msg.nsd, key_pairs, ssh_key=ssh_key)

        return nsr

    def delete_nsr(self, nsr_id):
        """
        Delete NSR with the passed nsr id
        """
        del self._nsrs[nsr_id]

    @asyncio.coroutine
    def instantiate_ns(self, nsr_id, config_xact):
        """ Instantiate an NS instance """
        self._log.debug("Instantiating Network service id %s", nsr_id)
        if nsr_id not in self._nsrs:
            err = "NSR id %s not found " % nsr_id
            self._log.error(err)
            raise NetworkServiceRecordError(err)

        nsr = self._nsrs[nsr_id]
        try:
            yield from nsr.nsm_plugin.instantiate_ns(nsr, config_xact)
        except Exception as e:
            self._log.exception("NS instantiate: {}".format(e))
            raise e

    @asyncio.coroutine
    def update_vnfr(self, vnfr):
        """Create/Update an VNFR """

        vnfr_state = self._vnfrs[vnfr.id].state
        self._log.debug("Updating VNFR with state %s: vnfr %s", vnfr_state, vnfr)
        
        no_of_active_vms = 0    
        for vdur in vnfr.vdur:
            if vdur.operational_status == 'running':
                no_of_active_vms += 1
        
        self._vnfrs[vnfr.id]._active_vdus = no_of_active_vms
        yield from self._vnfrs[vnfr.id].update_state(vnfr)
        nsr = self.find_nsr_for_vnfr(vnfr.id)
        if nsr is not None:
            nsr._vnf_inst_started = False
            yield from nsr.update_state()

    def find_nsr_for_vnfr(self, vnfr_id):
        """ Find the NSR which )has the passed vnfr id"""
        for nsr in list(self.nsrs.values()):
            for vnfr in list(nsr.vnfrs.values()):
                if vnfr.id == vnfr_id:
                    return nsr
        return None

    def delete_vnfr(self, vnfr_id):
        """ Delete VNFR  with the passed id"""
        del self._vnfrs[vnfr_id]

    @asyncio.coroutine
    def get_nsr_config(self, nsd_id):
        xpath = self._project.add_project("C,/nsr:ns-instance-config")
        results = yield from self._dts.query_read(xpath, rwdts.XactFlag.MERGE)

        for result in results:
            entry = yield from result
            ns_instance_config = entry.result

            for nsr in ns_instance_config.nsr:
                if nsr.nsd.id == nsd_id:
                    return nsr

        return None

    def get_nsd(self, nsd_id):
        """ Get network service descriptor for the passed nsd_id"""
        if nsd_id not in self._nsds:
            self._log.error("Cannot find NSD id:%s", nsd_id)
            raise NetworkServiceDescriptorError("Cannot find NSD id:%s", nsd_id)

        return self._nsds[nsd_id]

    def create_nsd(self, nsd_msg):
        """ Create a network service descriptor """
        self._log.debug("Create network service descriptor - %s", nsd_msg)
        if nsd_msg.id in self._nsds:
            self._log.error("Cannot create NSD %s -NSD ID already exists", nsd_msg)
            raise NetworkServiceDescriptorError("NSD already exists-%s", nsd_msg.id)

        nsd = NetworkServiceDescriptor(
                self._dts,
                self._log,
                self._loop,
                nsd_msg,
                self
                )
        self._nsds[nsd_msg.id] = nsd

        return nsd

    def update_nsd(self, nsd):
        """ update the Network service descriptor """
        self._log.debug("Update network service descriptor - %s", nsd)
        if nsd.id not in self._nsds:
            self._log.debug("No NSD found - creating NSD id = %s", nsd.id)
            self.create_nsd(nsd)
        else:
            self._log.debug("Updating NSD id = %s, nsd = %s", nsd.id, nsd)
            self._nsds[nsd.id].update(nsd)

    def delete_nsd(self, nsd_id):
        """ Delete the Network service descriptor with the passed id """
        self._log.debug("Deleting the network service descriptor - %s", nsd_id)
        if nsd_id not in self._nsds:
            self._log.debug("Delete NSD failed - cannot find nsd-id %s", nsd_id)
            raise NetworkServiceDescriptorNotFound("Cannot find %s", nsd_id)
        del self._nsds[nsd_id]

    def get_vnfd_config(self, xact):
        vnfd_dts_reg = self._vnfd_dts_handler.regh
        for cfg in vnfd_dts_reg.get_xact_elements(xact):
            if cfg.id not in self._vnfds:
                self.create_vnfd(cfg)

    def get_vnfd(self, vnfd_id, xact):
        """ Get virtual network function descriptor for the passed vnfd_id"""
        if vnfd_id not in self._vnfds:
            self._log.error("Cannot find VNFD id:%s", vnfd_id)
            self.get_vnfd_config(xact)

            if vnfd_id not in self._vnfds:
                self._log.error("Cannot find VNFD id:%s", vnfd_id)
                raise VnfDescriptorError("Cannot find VNFD id:%s", vnfd_id)

        return self._vnfds[vnfd_id]

    def create_vnfd(self, vnfd):
        """ Create a virtual network function descriptor """
        self._log.debug("Create virtual network function descriptor - %s", vnfd)
        if vnfd.id in self._vnfds:
            self._log.error("Cannot create VNFD %s -VNFD ID already exists", vnfd)
            raise VnfDescriptorError("VNFD already exists-%s", vnfd.id)

        self._vnfds[vnfd.id] = vnfd
        return self._vnfds[vnfd.id]

    def update_vnfd(self, vnfd):
        """ Update the virtual network function descriptor """
        self._log.debug("Update virtual network function descriptor- %s", vnfd)


        if vnfd.id not in self._vnfds:
            self._log.debug("No VNFD found - creating VNFD id = %s", vnfd.id)
            self.create_vnfd(vnfd)
        else:
            self._log.debug("Updating VNFD id = %s, vnfd = %s", vnfd.id, vnfd)
            self._vnfds[vnfd.id] = vnfd

    @asyncio.coroutine
    def delete_vnfd(self, vnfd_id):
        """ Delete the virtual network function descriptor with the passed id """
        self._log.debug("Deleting the virtual network function descriptor - %s", vnfd_id)
        if vnfd_id not in self._vnfds:
            self._log.debug("Delete VNFD failed - cannot find vnfd-id %s", vnfd_id)
            raise VnfDescriptorError("Cannot find %s", vnfd_id)

        del self._vnfds[vnfd_id]

    @asyncio.coroutine
    def publish_nsr(self, xact, path, msg):
        """ Publish a NSR """
        self._log.debug("Publish NSR with path %s, msg %s",
                        path, msg)
        yield from self.nsr_handler.update(xact, path, msg)

    @asyncio.coroutine
    def unpublish_nsr(self, xact, path):
        """ Un Publish an NSR """
        self._log.debug("Publishing delete NSR with path %s", path)
        yield from self.nsr_handler.delete(path, xact)

    def vnfr_is_ready(self, vnfr_id):
        """ VNFR with the id is ready """
        self._log.debug("VNFR id %s ready", vnfr_id)
        if vnfr_id not in self._vnfds:
            err = "Did not find VNFR ID with id %s" % vnfr_id
            self._log.critical("err")
            raise VirtualNetworkFunctionRecordError(err)
        self._vnfrs[vnfr_id].is_ready()


    @asyncio.coroutine
    def terminate_ns(self, nsr_id, xact):
        """
        Terminate network service for the given NSR Id
        """

        if nsr_id not in self._nsrs:
            return

        # Terminate the instances/networks assocaited with this nw service
        self._log.debug("Terminating the network service %s", nsr_id)
        try :
            yield from self._nsrs[nsr_id].terminate()
        except Exception as e:
            self.log.exception("Failed to terminate NSR[id=%s]", nsr_id)

    def vlr_event(self, vlr, action):
        self._log.debug("Received VLR %s with action:%s", vlr, action)
        # Find the NS and see if we can proceed
        nsr = self.find_nsr_for_vlr_id(vlr.id)
        if nsr is None:
            self._log.error("VLR %s:%s  received  for NSR, state:%s",
            vlr.id, vlr.name, vlr.operational_status)
            return
        nsr.vlr_event(vlr, action)

    def add_vlr_id_nsr_map(self, vlr_id, nsr):
        """ Add a mapping for vlr_id into NSR """
        self._nsr_for_vlr[vlr_id] = nsr

    def remove_vlr_id_nsr_map(self, vlr_id):
        """ Remove a mapping for vlr_id into NSR """
        if vlr_id in self._nsr_for_vlr:
            del self._nsr_for_vlr[vlr_id]

    def find_nsr_for_vlr_id(self, vlr_id):
        """ Find NSR for VLR id """
        nsr = None
        if vlr_id in self._nsr_for_vlr:
            nsr = self._nsr_for_vlr[vlr_id]
        return nsr


class NsmRecordsPublisherProxy(object):
    """ This class provides a publisher interface that allows plugin objects
        to publish NSR/VNFR/VLR"""

    def __init__(self, dts, log, loop, project, nsr_pub_hdlr,
                 vnfr_pub_hdlr, vlr_pub_hdlr,):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._nsr_pub_hdlr = nsr_pub_hdlr
        self._vlr_pub_hdlr = vlr_pub_hdlr
        self._vnfr_pub_hdlr = vnfr_pub_hdlr

    @asyncio.coroutine
    def publish_nsr_opdata(self, xact, nsr):
        """ Publish an NSR """
        path = ("D,/nsr:ns-instance-opdata" + "/nsr:nsr[nsr:ns-instance-config-ref={}]"
                    ).format(quoted_key(nsr.ns_instance_config_ref))
        return (yield from self._nsr_pub_hdlr.update(xact, path, nsr))

    @asyncio.coroutine
    def publish_nsr(self, xact, nsr):
        """ Publish an NSR """
        path = self._project.add_project(NetworkServiceRecord.xpath_from_nsr(nsr))
        return (yield from self._nsr_pub_hdlr.update(xact, path, nsr))

    @asyncio.coroutine
    def unpublish_nsr(self, xact, nsr):
        """ Unpublish an NSR """
        path = self._project.add_project(NetworkServiceRecord.xpath_from_nsr(nsr))
        return (yield from self._nsr_pub_hdlr.delete(xact, path))

    @asyncio.coroutine
    def publish_vnfr(self, xact, vnfr):
        """ Publish an VNFR """
        path = self._project.add_project(VirtualNetworkFunctionRecord.vnfr_xpath(vnfr))
        return (yield from self._vnfr_pub_hdlr.update(xact, path, vnfr))

    @asyncio.coroutine
    def unpublish_vnfr(self, xact, vnfr):
        """ Unpublish a VNFR """
        path = self._project.add_project(VirtualNetworkFunctionRecord.vnfr_xpath(vnfr))
        yield from self._vnfr_pub_hdlr.delete(xact, path)
        # NOTE: The regh delete does not send the on_prepare to VNFM tasklet as well
        # as remove all the VNFR elements. So need to send this additional delete block.
        with self._dts.transaction(flags = 0) as xact:
            block = xact.block_create()
            block.add_query_delete(path)
            yield from block.execute(flags=0, now=True)

    @asyncio.coroutine
    def publish_vlr(self, xact, vlr):
        """ Publish a VLR """
        path = self._project.add_project(VirtualLinkRecord.vlr_xpath(vlr))
        return (yield from self._vlr_pub_hdlr.update(xact, path, vlr))

    @asyncio.coroutine
    def unpublish_vlr(self, xact, vlr):
        """ Unpublish a VLR """
        path = self._project.add_project(VirtualLinkRecord.vlr_xpath(vlr))
        return (yield from self._vlr_pub_hdlr.delete(xact, path))

class ScalingRpcHandler(mano_dts.DtsHandler):
    """ The Network service Monitor DTS handler """
    SCALE_IN_INPUT_XPATH = "I,/nsr:exec-scale-in"
    SCALE_IN_OUTPUT_XPATH = "O,/nsr:exec-scale-in"

    SCALE_OUT_INPUT_XPATH = "I,/nsr:exec-scale-out"
    SCALE_OUT_OUTPUT_XPATH = "O,/nsr:exec-scale-out"

    ACTION = Enum('ACTION', 'SCALE_IN SCALE_OUT')

    def __init__(self, log, dts, loop, nsm, callback=None):
        super().__init__(log, dts, loop, nsm._project)
        self._nsm = nsm
        self.callback = callback
        self.last_instance_id = defaultdict(int)

        self._reg_in = None
        self._reg_out = None

    @asyncio.coroutine
    def register(self):

        def send_err_msg(err_msg, xact_info, ks_path, e=False):
            xpath = ks_path.to_xpath(NsrYang.get_schema())
            if e:
                self._log.exception(err_msg)
            else:
                self._log.error(err_msg)
            xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                       xpath,
                                       err_msg)
            xact_info.respond_xpath(rwdts.XactRspCode.NACK)

        @asyncio.coroutine
        def on_scale_in_prepare(xact_info, action, ks_path, msg):
            assert action == rwdts.QueryAction.RPC

            self._log.debug("Scale in called: {}".format(msg.as_dict()))
            if not self.project.rpc_check(msg, xact_info):
                return

            try:
                rpc_op = NsrYang.YangOutput_Nsr_ExecScaleIn.from_dict({
                      "instance_id": msg.instance_id})

                nsr = self._nsm.nsrs[msg.nsr_id_ref]
                if nsr.state != NetworkServiceRecordState.RUNNING:
                    errmsg = ("Unable to perform scaling action when NS {}({}) not in running state".
                              format(nsr.name, nsr.id))
                    send_err_msg(errmsg, xact_info, ks_path)
                    return

                xact_info.respond_xpath(
                    rwdts.XactRspCode.ACK,
                    self.__class__.SCALE_IN_OUTPUT_XPATH,
                    rpc_op)

                if self.callback:
                    self.callback(xact_info.xact, msg, self.ACTION.SCALE_IN)

            except Exception as e:
                errmsg = ("Exception doing scale in using {}: {}".
                          format(msg, e))
                send_err_msg(errmsg, xact_info, ks_path, e=True)

        @asyncio.coroutine
        def on_scale_out_prepare(xact_info, action, ks_path, msg):
            assert action == rwdts.QueryAction.RPC

            self._log.debug("Scale out called: {}".format(msg.as_dict()))
            if not self.project.rpc_check(msg, xact_info):
                return

            try:
                scaling_group = msg.scaling_group_name_ref
                if not msg.instance_id:
                    last_instance_id = self.last_instance_id[scale_group]
                    msg.instance_id  = last_instance_id + 1
                    self.last_instance_id[scale_group] += 1

                nsr = self._nsm.nsrs[msg.nsr_id_ref]
                if nsr.state != NetworkServiceRecordState.RUNNING:
                    errmsg = ("Unable to perform scaling action when NS {}({}) not in running state".
                              format(nsr.name, nsr.id))
                    send_err_msg(errmsg, xact_info, ks_path)
                    return

                rpc_op = NsrYang.YangOutput_Nsr_ExecScaleOut.from_dict({
                      "instance_id": msg.instance_id})

                xact_info.respond_xpath(
                    rwdts.XactRspCode.ACK,
                    self.__class__.SCALE_OUT_OUTPUT_XPATH,
                    rpc_op)

                if self.callback:
                    self.callback(xact_info.xact, msg, self.ACTION.SCALE_OUT)

            except Exception as e:
                errmsg = ("Exception doing scale in using {}: {}".
                          format(msg, e))
                send_err_msg(errmsg, xact_info, ks_path, e=True)

        self._reg_in = yield from self.dts.register(
            xpath=self.__class__.SCALE_IN_INPUT_XPATH,
            handler=rift.tasklets.DTS.RegistrationHandler(
                on_prepare=on_scale_in_prepare),
            flags=rwdts.Flag.PUBLISHER)

        self._reg_out = yield from self.dts.register(
            xpath=self.__class__.SCALE_OUT_INPUT_XPATH,
            handler=rift.tasklets.DTS.RegistrationHandler(
                on_prepare=on_scale_out_prepare),
            flags=rwdts.Flag.PUBLISHER)

    def deregister(self):
        if self._reg_in:
            self._reg_in.deregister()
            self._reg_in = None

        if self._reg_out:
            self._reg_out.deregister()
            self._reg_out = None


class NsmProject(ManoProject):

    def __init__(self, name, tasklet, **kw):
        super(NsmProject, self).__init__(tasklet.log, name)
        self.update(tasklet)
        self._nsm = None

        self._ro_plugin_selector = None
        self._vnffgmgr = None

        self._nsr_pub_handler = None
        self._vnfr_pub_handler = None
        self._vlr_pub_handler = None
        self._vnfd_pub_handler = None
        self._scale_cfg_handler = None

        self._records_publisher_proxy = None

    def vlr_event(self, vlr, action):
        """ VLR Event callback """
        self.log.debug("VLR Event received for VLR %s with action %s", vlr, action)
        self._nsm.vlr_event(vlr, action)

    @asyncio.coroutine
    def register(self):
        self.log.debug("Register NsmProject for {}".format(self.name))

        self._nsr_pub_handler = publisher.NsrOpDataDtsHandler(
            self._dts, self.log, self.loop, self)
        yield from self._nsr_pub_handler.register()

        self._vnfr_pub_handler = publisher.VnfrPublisherDtsHandler(
            self._dts, self.log, self.loop, self)
        yield from self._vnfr_pub_handler.register()

        self._vlr_pub_handler = publisher.VlrPublisherDtsHandler(
            self._dts, self.log, self.loop, self)
        yield from self._vlr_pub_handler.register()

        self._vlr_sub_handler = subscriber.VlrSubscriberDtsHandler(self.log,
                                                                   self._dts,
                                                                   self.loop,
                                                                   self,
                                                                   self.vlr_event,
        )
        yield from self._vlr_sub_handler.register()

        manifest = self._tasklet.tasklet_info.get_pb_manifest()
        use_ssl = manifest.bootstrap_phase.rwsecurity.use_ssl
        ssl_cert = manifest.bootstrap_phase.rwsecurity.cert
        ssl_key = manifest.bootstrap_phase.rwsecurity.key

        self._vnfd_pub_handler = publisher.VnfdPublisher(
            use_ssl, ssl_cert, ssl_key, self.loop, self)

        self._records_publisher_proxy = NsmRecordsPublisherProxy(
                self._dts,
                self.log,
                self.loop,
                self,
                self._nsr_pub_handler,
                self._vnfr_pub_handler,
                self._vlr_pub_handler,
                )

        # Register the NSM to receive the nsm plugin
        # when cloud account is configured
        self._ro_plugin_selector = cloud.ROAccountConfigSubscriber(
                self._dts,
                self.log,
                self.loop,
                self,
                self._records_publisher_proxy
                )
        yield from self._ro_plugin_selector.register()

        self._cloud_account_handler = cloud.CloudAccountConfigSubscriber(
                self._log,
                self._dts,
                self.log_hdl,
                self,
                )

        yield from self._cloud_account_handler.register()

        self._vnffgmgr = rwvnffgmgr.VnffgMgr(self._dts, self.log, self.log_hdl, self.loop,
                                             self, self._cloud_account_handler)
        yield from self._vnffgmgr.register()

        self._nsm = NsManager(
                self._dts,
                self.log,
                self.loop,
                self,
                self._nsr_pub_handler,
                self._vnfr_pub_handler,
                self._vlr_pub_handler,
                self._ro_plugin_selector,
                self._vnffgmgr,
                self._vnfd_pub_handler,
                self._cloud_account_handler,
                )

        yield from self._nsm.register()
        self.log.debug("Register NsmProject for {} complete".format(self.name))

    def deregister(self):
        self._log.debug("Project {} de-register".format(self.name))
        self._nsm.deregister()
        self._vnffgmgr.deregister()
        self._cloud_account_handler.deregister()
        self._ro_plugin_selector.deregister()
        self._nsr_pub_handler.deregister()
        self._vnfr_pub_handler.deregister()
        self._vlr_pub_handler.deregister()
        self._vlr_sub_handler.deregister()
        self._nsm = None

    @asyncio.coroutine
    def delete_prepare(self):
        if self._nsm and self._nsm._nsrs:
            delete_msg = "Project has NSR associated with it. Delete all Project NSR and try again."
            return False, delete_msg
        return True, "True"


class NsmTasklet(rift.tasklets.Tasklet):
    """
    The network service manager  tasklet
    """
    def __init__(self, *args, **kwargs):
        super(NsmTasklet, self).__init__(*args, **kwargs)
        self.rwlog.set_category("rw-mano-log")
        self.rwlog.set_subcategory("nsm")

        self._dts = None
        self.project_handler = None
        self.projects = {}

    @property
    def dts(self):
        return self._dts

    def start(self):
        """ The task start callback """
        super(NsmTasklet, self).start()
        self.log.info("Starting NsmTasklet")

        self.log.debug("Registering with dts")
        self._dts = rift.tasklets.DTS(self.tasklet_info,
                                      RwNsmYang.get_schema(),
                                      self.loop,
                                      self.on_dts_state_change)

        self.log.debug("Created DTS Api GI Object: %s", self._dts)

    def stop(self):
        try:
            self._dts.deinit()
        except Exception:
            print("Caught Exception in NSM stop:", sys.exc_info()[0])
            raise

    def on_instance_started(self):
        """ Task instance started callback """
        self.log.debug("Got instance started callback")

    @asyncio.coroutine
    def init(self):
        """ Task init callback """
        self.log.debug("Got instance started callback")

        self.log.debug("creating project handler")
        self.project_handler = ProjectHandler(self, NsmProject)
        self.project_handler.register()



    @asyncio.coroutine
    def run(self):
        """ Task run callback """
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
            self.log.debug("Changing state to %s", next_state)
            self._dts.handle.set_state(next_state)
