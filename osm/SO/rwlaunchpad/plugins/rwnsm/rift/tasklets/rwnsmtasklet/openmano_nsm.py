
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
import os
import sys
import time
import yaml

gi.require_version('RwDts', '1.0')
gi.require_version('RwVnfrYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    RwVnfrYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.openmano.rift2openmano as rift2openmano
import rift.openmano.openmano_client as openmano_client
from . import nsmpluginbase
from enum import Enum

import ipaddress
import rift.tasklets

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async


DUMP_OPENMANO_DIR = os.path.join(
        os.environ["RIFT_VAR_ROOT"],
    "openmano_descriptors"
)


def dump_openmano_descriptor(name, descriptor_str):
    filename = "{}_{}.yaml".format(
        time.strftime("%Y%m%d-%H%M%S"),
        name
    )

    filepath = os.path.join(
        DUMP_OPENMANO_DIR,
        filename
    )

    try:
        if not os.path.exists(DUMP_OPENMANO_DIR):
            os.makedirs(DUMP_OPENMANO_DIR)

        with open(filepath, 'w') as hdl:
            hdl.write(descriptor_str)

    except OSError as e:
        print("Failed to dump openmano descriptor: %s" % str(e))

    return filepath

class VNFExistError(Exception):
    pass

class VnfrConsoleOperdataDtsHandler(object):
    """ registers 'D,/vnfr:vnfr-console/vnfr:vnfr[id]/vdur[id]' and handles CRUD from DTS"""
    @property
    def vnfr_vdu_console_xpath(self):
        """ path for resource-mgr"""
        return self._project.add_project(
            "D,/rw-vnfr:vnfr-console/rw-vnfr:vnfr[rw-vnfr:id={}]/rw-vnfr:vdur[vnfr:id={}]".format(
                quoted_key(self._vnfr_id), quoted_key(self._vdur_id)))

    def __init__(self, project, dts, log, loop, nsr, vnfr_id, vdur_id, vdu_id):
        self._project = project
        self._dts = dts
        self._log = log
        self._loop = loop
        self._regh = None
        self._nsr = nsr

        self._vnfr_id = vnfr_id
        self._vdur_id = vdur_id
        self._vdu_id = vdu_id

    @asyncio.coroutine
    def register(self):
        """ Register for VNFR VDU Operational Data read from dts """

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts """
            xpath = ks_path.to_xpath(RwVnfrYang.get_schema())
            self._log.debug(
                "Got VNFR VDU Opdata xact_info: %s, action: %s): %s:%s",
                xact_info, action, xpath, msg
            )

            if action == rwdts.QueryAction.READ:
                schema = RwVnfrYang.YangData_RwProject_Project_VnfrConsole_Vnfr_Vdur.schema()
                path_entry = schema.keyspec_to_entry(ks_path)

                try:
                    console_url = yield from self._loop.run_in_executor(
                        None,
                        self._nsr._http_api.get_instance_vm_console_url,
                        self._nsr._nsr_uuid,
                        self._vdur_id
                    )

                    self._log.debug("Got console response: %s for NSR ID %s vdur ID %s",
                                        console_url,
                                        self._nsr._nsr_uuid,
                                        self._vdur_id
                                       )
                    vdur_console = RwVnfrYang.YangData_RwProject_Project_VnfrConsole_Vnfr_Vdur()
                    vdur_console.id = self._vdur_id
                    if console_url:
                        vdur_console.console_url = console_url
                    else:
                        vdur_console.console_url = 'none'
                    self._log.debug("Recevied console URL for vdu {} is {}".format(self._vdu_id,vdur_console))
                except openmano_client.InstanceStatusError as e:
                    self._log.error("Could not get NS instance console URL: %s",
                                        str(e))
                    vdur_console = RwVnfrYang.YangData_RwProject_Project_VnfrConsole_Vnfr_Vdur()
                    vdur_console.id = self._vdur_id
                    vdur_console.console_url = 'none'

                xact_info.respond_xpath(rsp_code=rwdts.XactRspCode.ACK,
                                        xpath=self.vnfr_vdu_console_xpath,
                                        msg=vdur_console)
            else:
                #raise VnfRecordError("Not supported operation %s" % action)
                self._log.error("Not supported operation %s" % action)
                xact_info.respond_xpath(rsp_code=rwdts.XactRspCode.ACK)
                return

        self._log.debug("Registering for VNFR VDU using xpath: %s",
                        self.vnfr_vdu_console_xpath)
        hdl = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare,)
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=self.vnfr_vdu_console_xpath,
                                        handler=hdl,
                                        flags=rwdts.Flag.PUBLISHER,
                                        )



class OpenmanoVnfr(object):
    def __init__(self, project, log, loop, cli_api, http_api, vnfr, nsd, ssh_key=None):
        self._project = project
        self._log = log
        self._loop = loop
        self._cli_api = cli_api
        self._http_api = http_api
        self._vnfr = vnfr
        self._vnfd_id = vnfr.vnfd.id

        self._vnf_id = None

        self._created = False

        self.nsd = nsd
        self._ssh_key = ssh_key

    @property
    def vnfd(self):
        return rift2openmano.RiftVNFD(self._vnfr.vnfd)

    @property
    def vnfr(self):
        return self._vnfr

    @property
    def rift_vnfd_id(self):
        return self._vnfd_id

    @property
    def openmano_vnfd_id(self):
        return self._vnf_id

    @property
    def openmano_vnfd(self):
        self._log.debug("Converting vnfd %s from rift to openmano", self.vnfd.id)
        openmano_vnfd = rift2openmano.rift2openmano_vnfd(self.vnfd, self.nsd, self._http_api, self._project.name)
        return openmano_vnfd

    @property
    def openmano_vnfd_yaml(self):
        return yaml.safe_dump(self.openmano_vnfd, default_flow_style=False)

    @asyncio.coroutine
    def create(self):
        try:
            self._log.debug("Created openmano vnfd")
            # The self.openmano_vnfd_yaml internally creates the vnf if not found.
            # Assigning the yaml to a variable so that the api is not fired unnecessarily.
            openmano_vnfd = self.openmano_vnfd
            name = openmano_vnfd["name"]

            self._vnf_id = openmano_vnfd['uuid']

            self._created = True
        except Exception as e:
            self._log.error("Failed to create vnf on Openmano RO : %s", e)
            raise e

    def delete(self):
        if not self._created:
            return

        self._log.debug("Deleting openmano vnfd")
        if self._vnf_id is None:
            self._log.warning("Openmano vnf id not set.  Cannot delete.")
            return
        try:
            self._cli_api.vnf_delete(self._vnf_id)
        except Exception as e:
            self._log.error(e)
            raise e

class OpenmanoNSRecordState(Enum):
    """ Network Service Record State """
    # Make sure the values match with NetworkServiceRecordState
    INIT = 101
    INSTANTIATION_PENDING = 102
    RUNNING = 106
    SCALING_OUT = 107
    SCALING_IN = 108
    TERMINATE = 109
    TERMINATE_RCVD = 110
    TERMINATED = 114
    FAILED = 115
    VL_INSTANTIATE = 116
    VL_TERMINATE = 117


class OpenmanoNsr(object):
    TIMEOUT_SECS = 300
    INSTANCE_TERMINATE_TIMEOUT = 60

    def __init__(self, project, dts, log, loop, publisher, cli_api, http_api, nsd_msg,
                 nsr_config_msg, key_pairs, ssh_key, rift_vnfd_id=None ):
        self._project = project
        self._log = log
        self._dts = dts
        self._loop = loop
        self._publisher = publisher
        self._cli_api = cli_api
        self._http_api = http_api

        self._nsd_msg = nsd_msg
        self._nsr_config_msg = nsr_config_msg
        self._vlrs = []
        self._vnfrs = []
        self._nsrs = {}
        self._vdur_console_handler = {}
        self._key_pairs = key_pairs
        self._ssh_key = ssh_key

        self._nsd_uuid = None
        self._nsr_uuid = None
        self._nsd_msg = nsd_msg

        self._nsr_msg = None

        self._created = False

        self._monitor_task = None
        self._rift_vnfd_id = rift_vnfd_id
        self._state = OpenmanoNSRecordState.INIT

        self._active_vms = 0
        self._active_nets = 0

    @property
    def nsd(self):
        return rift2openmano.RiftNSD(self._nsd_msg)

    @property
    def rift_vnfd_id(self):
        return self._rift_vnfd_id

    @property
    def nsd_msg(self):
        return self._nsd_msg

    @property
    def nsr_config_msg(self):
        return self._nsr_config_msg


    @property
    def vnfds(self):
        return {v.rift_vnfd_id: v.vnfd for v in self._vnfrs}

    @property
    def vnfr_ids(self):
        return {v.rift_vnfd_id: v.openmano_vnfd_id for v in self._vnfrs}

    @property
    def vnfrs(self):
        return self._vnfrs

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def nsr_msg(self):
        return self._nsr_msg

    @property
    def vlrs(self):
        return self._vlrs

    @property
    def http_api(self):
        return self._http_api

    @property
    def openmano_nsd_yaml(self):
        self._log.debug("Converting nsd %s from rift to openmano", self.nsd.id)
        openmano_nsd = rift2openmano.rift2openmano_nsd(self.nsd, self.vnfds,self.vnfr_ids, self.http_api)
        return yaml.safe_dump(openmano_nsd, default_flow_style=False)

    @property
    def openmano_scaling_yaml(self):
        self._log.debug("Creating Openmano Scaling Descriptor %s")
        try:
            openmano_vnfd_nsd = rift2openmano.rift2openmano_vnfd_nsd(self.nsd, self.vnfds, self.vnfr_ids, self.http_api, self._rift_vnfd_id)
            return yaml.safe_dump(openmano_vnfd_nsd, default_flow_style=False)
        except Exception as e:
            self._log.exception("Scaling Descriptor Exception: %s", str(e))

    def get_ssh_key_pairs(self):
        cloud_config = {}
        key_pairs = list()
        for authorized_key in self._nsr_config_msg.ssh_authorized_key:
            self._log.debug("Key pair ref present is %s",authorized_key.key_pair_ref)
            if authorized_key.key_pair_ref in  self._key_pairs:
                key_pairs.append(self._key_pairs[authorized_key.key_pair_ref].key)

        for authorized_key in self._nsd_msg.key_pair:
            self._log.debug("Key pair  NSD  is %s",authorized_key)
            key_pairs.append(authorized_key.key)

        if self._ssh_key['public_key']:
            self._log.debug("Pub key  NSD  is %s", self._ssh_key['public_key'])
            key_pairs.append(self._ssh_key['public_key'])

        if key_pairs:
            cloud_config["key-pairs"] = key_pairs

        users = list()
        for user_entry in self._nsr_config_msg.user:
            self._log.debug("User present is  %s",user_entry)
            user = {}
            user["name"] = user_entry.name
            user["key-pairs"] = list()
            for ssh_key in user_entry.ssh_authorized_key:
                if ssh_key.key_pair_ref in  self._key_pairs:
                    user["key-pairs"].append(self._key_pairs[ssh_key.key_pair_ref].key)
            users.append(user)

        for user_entry in self._nsd_msg.user:
            self._log.debug("User present in NSD is  %s",user_entry)
            user = {}
            user["name"] = user_entry.name
            user["key-pairs"] = list()
            for ssh_key in user_entry.key_pair:
                user["key-pairs"].append(ssh_key.key)
            users.append(user)

        if users:
            cloud_config["users"] = users

        self._log.debug("Cloud config formed is %s",cloud_config)
        return cloud_config


    @property
    def openmano_instance_create_yaml(self):
        try:
            self._log.debug("Creating instance-scenario-create input file for nsd %s with name %s", self.nsd.id, self._nsr_config_msg.name)
            openmano_instance_create = {}
            openmano_instance_create["name"] = self._nsr_config_msg.name
            openmano_instance_create["description"] = self._nsr_config_msg.description
            openmano_instance_create["scenario"] = self._nsd_uuid

            cloud_config = self.get_ssh_key_pairs()
            if cloud_config:
                openmano_instance_create["cloud-config"] = cloud_config
            if self._nsr_config_msg.has_field("datacenter"):
                openmano_instance_create["datacenter"] = self._nsr_config_msg.datacenter
            openmano_instance_create["vnfs"] = {}
            for vnfr in self._vnfrs:
                if "datacenter" in vnfr.vnfr.vnfr_msg:
                    vnfr_name = vnfr.vnfr.vnfd.name + "." + str(vnfr.vnfr.vnfr_msg.member_vnf_index_ref)
                    openmano_instance_create["vnfs"][vnfr_name] = {"datacenter": vnfr.vnfr.vnfr_msg.datacenter}
            openmano_instance_create["networks"] = {}
            for vld_msg in self._nsd_msg.vld:
                openmano_instance_create["networks"][vld_msg.name] = {}
                openmano_instance_create["networks"][vld_msg.name]["sites"] = list()
                for vlr in self._vlrs:
                    if vlr.vld_msg.name == vld_msg.name:
                        self._log.debug("Received VLR name %s, VLR DC: %s for VLD: %s",vlr.vld_msg.name,
                                        vlr.datacenter_name,vld_msg.name)
                        #network["vim-network-name"] = vld_msg.name
                        network = {}
                        ip_profile = {}
                        if vld_msg.vim_network_name:
                            network["netmap-use"] = vld_msg.vim_network_name
                        elif vlr._ip_profile and vlr._ip_profile.has_field("ip_profile_params"):
                            ip_profile_params = vlr._ip_profile.ip_profile_params
                            if ip_profile_params.ip_version == "ipv6":
                                ip_profile['ip-version'] = "IPv6"
                            else:
                                ip_profile['ip-version'] = "IPv4"
                            if ip_profile_params.has_field('subnet_address'):
                                ip_profile['subnet-address'] = ip_profile_params.subnet_address
                            if ip_profile_params.has_field('gateway_address'):
                                ip_profile['gateway-address'] = ip_profile_params.gateway_address
                            if ip_profile_params.has_field('dns_server') and len(ip_profile_params.dns_server) > 0:
                                ip_profile['dns-address'] =  ip_profile_params.dns_server[0].address
                            if ip_profile_params.has_field('dhcp_params'):
                                ip_profile['dhcp'] = {}
                                ip_profile['dhcp']['enabled'] = ip_profile_params.dhcp_params.enabled
                                ip_profile['dhcp']['start-address'] = ip_profile_params.dhcp_params.start_address
                                ip_profile['dhcp']['count'] = ip_profile_params.dhcp_params.count
                                if ip_profile['dhcp']['enabled'] is True and ip_profile['dhcp']['start-address'] is None:
                                    addr_pool = list(ipaddress.ip_network(ip_profile['subnet-address']).hosts())
                                    gateway_ip_addr = ip_profile.get('gateway-address', None) 
                                    if gateway_ip_addr is None:
                                        gateway_ip_addr = str(next(iter(addr_pool)))
                                        ip_profile['gateway-address'] = gateway_ip_addr
                                    
                                    self._log.debug("Gateway Address {}".format(gateway_ip_addr))
                                                                                                  
                                    if ipaddress.ip_address(gateway_ip_addr) in addr_pool:
                                        addr_pool.remove(ipaddress.ip_address(gateway_ip_addr))
                                    if len(addr_pool) > 0:
                                        ip_profile['dhcp']['start-address'] = str(next(iter(addr_pool)))
                                        #DHCP count more than 200 is not instantiating any instances using OPENMANO RO
                                        #So restricting it to a feasible count of 100. 
                                        dhcp_count = ip_profile['dhcp']['count']
                                        if dhcp_count is None or dhcp_count == 0 or dhcp_count > len(addr_pool):
                                            ip_profile['dhcp']['count'] = min(len(addr_pool), 100)
                                self._log.debug("DHCP start Address {} DHCP count {}".
                                                format(ip_profile['dhcp']['start-address'], ip_profile['dhcp']['count']))
                        else:
                            network["netmap-create"] = vlr.name
                        if vlr.datacenter_name:
                            network["datacenter"] = vlr.datacenter_name
                        elif vld_msg.has_field("datacenter"):
                            network["datacenter"] = vld_msg.datacenter
                        elif "datacenter" in openmano_instance_create:
                            network["datacenter"] = openmano_instance_create["datacenter"]
                        if network:
                            openmano_instance_create["networks"][vld_msg.name]["sites"].append(network)
                        if ip_profile:
                            openmano_instance_create["networks"][vld_msg.name]['ip-profile'] = ip_profile
        except Exception as e:
            self._log.error("Error while creating openmano_instance_yaml : {}". format(str(e)))

        return yaml.safe_dump(openmano_instance_create, default_flow_style=False,width=1000)

    @property
    def scaling_instance_create_yaml(self, scaleout=False):
        try:
            self._log.debug("Creating instance-scenario-create input file for nsd %s with name %s", self.nsd.id, self._nsr_config_msg.name+"scal1")
            scaling_instance_create = {}
            for group_list in self._nsd_msg.scaling_group_descriptor:
                scaling_instance_create["name"] = self._nsr_config_msg.name + "__"+group_list.name
                if scaleout:
                    scaling_instance_create["scenario"] = self._nsd_uuid + "__" +group_list.name
                else:
                    scaling_instance_create["scenario"] = self._nsd_uuid
            scaling_instance_create["description"] = self._nsr_config_msg.description

            if self._nsr_config_msg.has_field("datacenter"):
                scaling_instance_create["datacenter"] = self._nsr_config_msg.datacenter
            scaling_instance_create["vnfs"] = {}
            for vnfr in self._vnfrs:
                if "datacenter" in vnfr.vnfr.vnfr_msg:
                    vnfr_name = vnfr.vnfr.vnfd.name + "." + str(vnfr.vnfr.vnfr_msg.member_vnf_index_ref)
                    scaling_instance_create["vnfs"][vnfr_name] = {"datacenter": self._nsr_config_msg.datacenter}
            scaling_instance_create["networks"] = {}
            for vld_msg in self._nsd_msg.vld:
                scaling_instance_create["networks"][vld_msg.name] = {}
                scaling_instance_create["networks"][vld_msg.name]["sites"] = list()
                for vlr in self._vlrs:
                    if vlr.vld_msg.name == vld_msg.name:
                        self._log.debug("Received VLR name %s, VLR DC: %s for VLD: %s",vlr.vld_msg.name,
                                    vlr.datacenter_name,vld_msg.name)
                        #network["vim-network-name"] = vld_msg.name
                        network = {}
                        ip_profile = {}
                        if vld_msg.vim_network_name:
                            network["netmap-use"] = vld_msg.vim_network_name
                        #else:
                        #    network["netmap-create"] = vlr.name
                        if vlr.datacenter_name:
                            network["datacenter"] = vlr.datacenter_name
                        elif vld_msg.has_field("datacenter"):
                            network["datacenter"] = vld_msg.datacenter
                        elif "datacenter" in scaling_instance_create:
                            network["datacenter"] = scaling_instance_create["datacenter"]
                        if network:
                            scaling_instance_create["networks"][vld_msg.name]["sites"].append(network)
        except Exception as e:
            self._log.error("Error while creating scaling_instance_yaml : {}". format(str(e)))

        return yaml.safe_dump(scaling_instance_create, default_flow_style=False, width=1000)

    @asyncio.coroutine
    def add_vlr(self, vlr):
        self._vlrs.append(vlr)
        yield from self._publisher.publish_vlr(None, vlr.vlr_msg)
        yield from asyncio.sleep(1, loop=self._loop)

    @asyncio.coroutine
    def remove_vlr(self, vlr):
        if vlr in self._vlrs:
            self._vlrs.remove(vlr)
            yield from self._publisher.unpublish_vlr(None, vlr.vlr_msg)
        yield from asyncio.sleep(1, loop=self._loop)

    @asyncio.coroutine
    def remove_vnf(self,vnf):
        self._log.debug("Unpublishing VNFR - {}".format(vnf))

        delete_vnfr = None
        for vnfr in self._vnfrs:
            # Find the vnfr by id
            if vnfr.vnfr.id == vnf.id:
                self._log.debug("Found vnfr for delete !")
                delete_vnfr = vnfr
                break

        if delete_vnfr:
            self._log.debug("Removing VNFR : {}".format(delete_vnfr.vnfr.id))
            self._vnfrs.remove(vnfr)
            yield from self._publisher.unpublish_vnfr(None, delete_vnfr.vnfr.vnfr_msg)
            self._log.debug("Removed VNFR : {}".format(delete_vnfr.vnfr.id))

        yield from asyncio.sleep(1, loop=self._loop)

    @asyncio.coroutine
    def delete_vlr(self, vlr):
        if vlr in self._vlrs:
            self._vlrs.remove(vlr)
            if not  vlr.vld_msg.vim_network_name:
                yield from self._loop.run_in_executor(
                    None,
                    self._cli_api.ns_vim_network_delete,
                    vlr.name,
                    vlr.datacenter_name)
            yield from self._publisher.unpublish_vlr(None, vlr.vlr_msg)
        yield from asyncio.sleep(1, loop=self._loop)

    @asyncio.coroutine
    def add_vnfr(self, vnfr):
        vnfr = OpenmanoVnfr(self._project, self._log, self._loop, self._cli_api, self.http_api,
                                vnfr, nsd=self.nsd, ssh_key=self._ssh_key)
        yield from vnfr.create()
        self._vnfrs.append(vnfr)

    @asyncio.coroutine
    def add_nsr(self, nsr, vnfr):
        self._nsrs[vnfr.id] = nsr

    def delete(self):
        if not self._created:
            self._log.debug("NSD wasn't created.  Skipping delete.")
            return

        self._log.debug("Deleting openmano nsr")
        # Here we need to check for existing instances using this scenario.
        # This would exist when we use Scaling Descriptors.
        # Deleting a scenario before deleting instances results in a orphaned state
        # TODO: The RO should implement the check done here.

        self._log.debug("Fetching Instance Scenario List before Deleting Scenario")

        instances = self.http_api.instances()

        scenarios_instances = False

        self._log.debug("Fetched Instances List. Checking if scenario is used")
        for instance in instances:
            if instance["scenario_id"] == self._nsd_uuid:
                scenarios_instances = True
                break

        self._log.debug("Scenario Instances Dependency Exists : %s", scenarios_instances)

        if not scenarios_instances:
            try:
                self._cli_api.ns_delete(self._nsd_uuid)
            except Exception as e:
                self._log.error(e)

            self._log.debug("Deleting openmano vnfrs(non scaling vnfs)")
            deleted_vnf_id_list = []
            for vnfr in self._vnfrs:
                if vnfr.vnfr.vnfd.id not in deleted_vnf_id_list:
                    try:
                        vnfr.delete()
                    except Exception as e:
                        self._log.error("Failed to delete the vnf at the RO")
                        if "Resource is not free" in str(e):
                            self._log.error("Resource is not free, hence forego the vnf-delete")
                        else:
                            raise e
                    deleted_vnf_id_list.append(vnfr.vnfr.vnfd.id)

    @asyncio.coroutine
    def create(self):
        try:
            self._log.debug("Created openmano scenario")
            # The self.openmano_nsd_yaml internally creates the scenario if not found.
            # Assigning the yaml to a variable so that the api is not fired unnecessarily.
            nsd_yaml = self.openmano_nsd_yaml

            self._nsd_uuid = yaml.load(nsd_yaml)['uuid']
            fpath = dump_openmano_descriptor(
                "{}_nsd".format(self._nsd_msg.name),
                nsd_yaml,
            )

            self._log.debug("Dumped Openmano NS descriptor to: %s", fpath)

            self._created = True
        except Exception as e:
            self._log.error("Failed to create scenario on Openmano RO : %s", e)
            raise e

    @asyncio.coroutine
    def scaling_scenario_create(self):
        self._log.debug("Creating scaling openmano scenario")

        # The self.openmano_nsd_yaml internally creates the scenario if not found.
        # Assigning the yaml to a variable so that the api is not fired unnecessarily.
        nsd_yaml = self.openmano_scaling_yaml
        
        self._nsd_uuid = yaml.load(nsd_yaml)['uuid']

        fpath = dump_openmano_descriptor(
            "{}_sgd".format(self._nsd_msg.name),
            self.scaling_instance_create_yaml,
        )
        self._created = True


    @asyncio.coroutine
    def get_nsr_opdata(self):
        """ NSR opdata associated with this VNFR """
        xpath = self._project.add_project(
            "D,/nsr:ns-instance-opdata/nsr:nsr" \
            "[nsr:ns-instance-config-ref={}]". \
            format(quoted_key(self.nsr_config_msg.id)))

        results = yield from self._dts.query_read(xpath, rwdts.XactFlag.MERGE)

        for result in results:
            entry = yield from result
            nsr_op = entry.result
            return nsr_op

        return None


    @asyncio.coroutine
    def instance_monitor_task(self):
        self._log.debug("Starting Instance monitoring task")

        start_time = time.time()
        active_vnfs = []
        nsr = yield from self.get_nsr_opdata()
        while True:
            active_vms = 0
            active_nets = 0
        
            yield from asyncio.sleep(1, loop=self._loop)

            try:
                instance_resp_json = yield from self._loop.run_in_executor(
                    None,
                    self._http_api.get_instance,
                    self._nsr_uuid,
                )

                self._log.debug("Got instance response: %s for NSR ID %s",
                                instance_resp_json,
                                self._nsr_uuid)

                for vnf in instance_resp_json['vnfs']:
                    for vm in vnf['vms']:
                        if vm['status'] == 'ACTIVE':
                            active_vms += 1
                for net in instance_resp_json['nets']:
                    if net['status'] == 'ACTIVE':
                        active_nets += 1

                nsr.orchestration_progress.vms.active = active_vms
                nsr.orchestration_progress.networks.active = active_nets

                # This is for accesibility of the status from nsm when the control goes back.
                self._active_vms = active_vms
                self._active_nets = active_nets

                yield from self._publisher.publish_nsr_opdata(None, nsr)

            except openmano_client.InstanceStatusError as e:
                self._log.error("Could not get NS instance status: %s", str(e))
                continue


            def all_vms_active(vnf):
                for vm in vnf["vms"]:
                    vm_status = vm["status"]
                    vm_uuid = vm["uuid"]
                    if vm_status != "ACTIVE":
                        self._log.debug("VM is not yet active: %s (status: %s)", vm_uuid, vm_status)
                        return False

                return True

            def any_vm_active_nomgmtip(vnf):
                for vm in vnf["vms"]:
                    vm_status = vm["status"]
                    vm_uuid = vm["uuid"]
                    if vm_status != "ACTIVE":
                        self._log.debug("VM is not yet active: %s (status: %s)", vm_uuid, vm_status)
                        return False

                return True

            def any_vms_error(vnf):
                for vm in vnf["vms"]:
                    vm_status = vm["status"]
                    vm_vim_info = vm["vim_info"]
                    vm_uuid = vm["uuid"]
                    if "ERROR" in vm_status:
                        self._log.error("VM Error: %s (vim_info: %s)", vm_uuid, vm_vim_info)
                        return True, vm['error_msg']

                return False, ''

            def get_vnf_ip_address(vnf):
                if "ip_address" in vnf:
                    return vnf["ip_address"].strip()

                else:
                    cp_info_list = get_ext_cp_info(vnf)
                    
                    for cp_name, ip, mac in cp_info_list:
                        for vld in self.nsd.vlds:
                            if not vld.mgmt_network:
                                continue

                            for vld_cp in vld.vnfd_connection_point_ref:
                                if vld_cp.vnfd_connection_point_ref == cp_name:
                                    return ip
                return None

            def get_vnf_mac_address(vnf):
                if "mac_address" in vnf:
                    return vnf["mac_address"].strip()
                return None

            def get_ext_cp_info(vnf):
                cp_info_list = []
                for vm in vnf["vms"]:
                    if "interfaces" not in vm:
                        continue

                    for intf in vm["interfaces"]:
                        if "external_name" not in intf:
                            continue

                        if not intf["external_name"]:
                            continue

                        ip_address = intf["ip_address"]
                        if ip_address is None:
                            ip_address = "0.0.0.0"

                        mac_address = intf["mac_address"]
                        if mac_address is None:
                            mac_address="00:00:00:00:00:00"

                        cp_info_list.append((intf["external_name"], ip_address, mac_address))

                return cp_info_list

            def get_vnf_status(vnfr):
                # When we create an openmano descriptor we use <name>.<idx>
                # to come up with openmano constituent VNF name.  Use this
                # knowledge to map the vnfr back.
                openmano_vnfr_suffix = ".{}".format(
                    vnfr.vnfr.vnfr_msg.member_vnf_index_ref
                )

                for vnf in instance_resp_json["vnfs"]:
                    if vnf["vnf_name"].endswith(openmano_vnfr_suffix):
                        return vnf
                        
                self._log.warning("Could not find vnf status with name that ends with: %s",
                                  openmano_vnfr_suffix)
                return None

            for vnfr in self._vnfrs:
                if vnfr in active_vnfs:
                    # Skipping, so we don't re-publish the same VNF message.
                    continue

                vnfr_msg = vnfr.vnfr.vnfr_msg.deep_copy()
                vnfr_msg.operational_status = "init"

                try:
                    vnf_status = get_vnf_status(vnfr)
                    self._log.debug("Found VNF status: %s", vnf_status)
                    if vnf_status is None:
                        self._log.error("Could not find VNF status from openmano")
                        self._state = OpenmanoNSRecordState.FAILED
                        vnfr_msg.operational_status = "failed"
                        yield from self._publisher.publish_vnfr(None, vnfr_msg)
                        return

                    # If there was a VNF that has a errored VM, then just fail the VNF and stop monitoring.
                    vm_error, vm_err_msg = any_vms_error(vnf_status)
                    if vm_error:
                        self._log.error("VM was found to be in error state.  Marking as failed.")
                        self._state = OpenmanoNSRecordState.FAILED
                        vnfr_msg.operational_status = "failed"
                        vnfr_msg.operational_status_details = vm_err_msg
                        yield from self._publisher.publish_vnfr(None, vnfr_msg)
                        return

                    if (time.time() - start_time) > OpenmanoNsr.TIMEOUT_SECS:
                        self._log.error("NSR timed out before reaching running state")
                        self._state = OpenmanoNSRecordState.FAILED
                        vnfr_msg.operational_status = "failed"
                        yield from self._publisher.publish_vnfr(None, vnfr_msg)
                        return

                    if all_vms_active(vnf_status):
                        vnf_ip_address = get_vnf_ip_address(vnf_status)
                        vnf_mac_address = get_vnf_mac_address(vnf_status)

                        if vnf_ip_address is None:
                            self._log.error("No IP address obtained "
                                              "for VNF: {}, will retry.".format(
                                vnf_status['vnf_name']))
                            continue

                        self._log.debug("All VMs in VNF are active.  Marking as running.")
                        vnfr_msg.operational_status = "running"

                        self._log.debug("Got VNF ip address: %s, mac-address: %s",
                                        vnf_ip_address, vnf_mac_address)
                        vnfr_msg.mgmt_interface.ip_address = vnf_ip_address
                        
                        if vnfr._ssh_key:
                            vnfr_msg.mgmt_interface.ssh_key.public_key = \
                                                    vnfr._ssh_key['public_key']
                            vnfr_msg.mgmt_interface.ssh_key.private_key_file = \
                                                    vnfr._ssh_key['private_key']

                        for vm in vnf_status["vms"]:
                            if vm["uuid"] not in self._vdur_console_handler:
                                vdur_console_handler = VnfrConsoleOperdataDtsHandler(self._project, self._dts, self._log, self._loop,
                                                                                     self, vnfr_msg.id,vm["uuid"],vm["name"])
                                yield from vdur_console_handler.register()
                                self._vdur_console_handler[vm["uuid"]] = vdur_console_handler

                            vdur_msg = vnfr_msg.vdur.add()
                            vdur_msg.vim_id = vm["vim_vm_id"]
                            vdur_msg.id = vm["uuid"]

                        # Add connection point information for the config manager
                        cp_info_list = get_ext_cp_info(vnf_status)
                        for (cp_name, cp_ip, cp_mac_addr) in cp_info_list:
                            cp = vnfr_msg.connection_point.add()
                            cp.name = cp_name
                            cp.short_name = cp_name
                            cp.ip_address = cp_ip
                            cp.mac_address = cp_mac_addr

                        yield from self._publisher.publish_vnfr(None, vnfr_msg)
                        active_vnfs.append(vnfr)

                except Exception as e:
                    vnfr_msg.operational_status = "failed"
                    self._state = OpenmanoNSRecordState.FAILED
                    yield from self._publisher.publish_vnfr(None, vnfr_msg)
                    self._log.exception("Caught exception publishing vnfr info: %s", str(e))
                    return

            if len(active_vnfs) == len(self._vnfrs):
                self._state = OpenmanoNSRecordState.RUNNING
                self._log.debug("All VNF's are active.  Exiting NSR monitoring task")
                return

    @asyncio.coroutine
    def deploy(self,nsr_msg):
        if self._nsd_uuid is None:
            raise ValueError("Cannot deploy an uncreated nsd")

        self._log.debug("Deploying openmano instance scenario")

        name_uuid_map = yield from self._loop.run_in_executor(
            None,
            self._cli_api.ns_instance_list,
        )

        if self._nsr_config_msg.name in name_uuid_map:
            self._log.debug("Found existing instance with nsr name: %s", self._nsr_config_msg.name)
            self._nsr_uuid = name_uuid_map[self._nsr_config_msg.name]
        else:
            self._nsr_msg = nsr_msg
            fpath = dump_openmano_descriptor(
                "{}_instance_sce_create".format(self._nsr_config_msg.name),
                self.openmano_instance_create_yaml,
            )
            self._log.debug("Dumped Openmano instance Scenario Cretae to: %s", fpath)

            self._nsr_uuid = yield from self._loop.run_in_executor(
                None,
                self._cli_api.ns_instance_scenario_create,
                self.openmano_instance_create_yaml)

        self._state = OpenmanoNSRecordState.INSTANTIATION_PENDING

        self._monitor_task = asyncio.ensure_future(
            self.instance_monitor_task(), loop=self._loop
        )

    @asyncio.coroutine
    def deploy_scaling(self, nsr_msg, rift_vnfd_id):
        self._log.debug("Deploying Scaling instance scenario")
        self._nsr_msg = nsr_msg
        self._rift_vnfd_id = rift_vnfd_id
        fpath = dump_openmano_descriptor(
            "{}_scale_instance".format(self._nsr_config_msg.name),
            self.scaling_instance_create_yaml
            )
        self._nsr_uuid = yield from self._loop.run_in_executor(
                None,
                self._cli_api.ns_instance_scenario_create,
                self.scaling_instance_create_yaml)

        self._state = OpenmanoNSRecordState.INSTANTIATION_PENDING

        self._monitor_task = asyncio.ensure_future(
            self.instance_monitor_task(), loop=self._loop
        )

        self._state = OpenmanoNSRecordState.INIT


    def terminate(self):
        if self._nsr_uuid is None:
            start_time = time.time()
            while ((time.time() - start_time) < OpenmanoNsr.INSTANCE_TERMINATE_TIMEOUT) and (self._nsr_uuid is None):
                time.sleep(5)
                self._log.warning("Waiting for nsr to get instatiated")
            if self._nsr_uuid is None:
                self._log.warning("Cannot terminate an un-instantiated nsr")
                return

        if self._monitor_task is not None:
            self._monitor_task.cancel()
            self._monitor_task = None

        self._log.debug("Terminating openmano nsr")
        self._cli_api.ns_terminate(self._nsr_uuid)

    @asyncio.coroutine
    def create_vlr(self,vlr):
        self._log.error("Creating openmano vim network VLR name %s, VLR DC: %s",vlr.vld_msg.name,
                        vlr.datacenter_name)
        net_create = {}
        net = {}
        net['name'] = vlr.name
        net['shared'] = True
        net['type'] = 'bridge'
        self._log.error("Received ip profile is %s",vlr._ip_profile)
        if vlr._ip_profile and vlr._ip_profile.has_field("ip_profile_params"):
            ip_profile_params = vlr._ip_profile.ip_profile_params
            ip_profile = {}
            if ip_profile_params.ip_version == "ipv6":
                ip_profile['ip_version'] = "IPv6"
            else:
                ip_profile['ip_version'] = "IPv4"
            if ip_profile_params.has_field('subnet_address'):
                ip_profile['subnet_address'] = ip_profile_params.subnet_address
            if ip_profile_params.has_field('gateway_address'):
                ip_profile['gateway_address'] = ip_profile_params.gateway_address
            if ip_profile_params.has_field('dns_server') and len(ip_profile_params.dns_server) > 0:
                ip_profile['dns_address'] =  ip_profile_params.dns_server[0].address
            if ip_profile_params.has_field('dhcp_params'):
                ip_profile['dhcp_enabled'] = ip_profile_params.dhcp_params.enabled
                ip_profile['dhcp_start_address'] = ip_profile_params.dhcp_params.start_address
                ip_profile['dhcp_count'] = ip_profile_params.dhcp_params.count
            net['ip_profile'] = ip_profile
        net_create["network"]= net

        net_create_msg = yaml.safe_dump(net_create,default_flow_style=False)
        fpath = dump_openmano_descriptor(
            "{}_vim_net_create_{}".format(self._nsr_config_msg.name,vlr.name),
            net_create_msg)
        self._log.error("Dumped Openmano VIM Net create to: %s", fpath)

        vim_network_uuid = yield from self._loop.run_in_executor(
            None,
            self._cli_api.ns_vim_network_create,
            net_create_msg,
            vlr.datacenter_name)
        self._vlrs.append(vlr)



class OpenmanoNsPlugin(nsmpluginbase.NsmPluginBase):
    """
        RW Implentation of the NsmPluginBase
    """
    def __init__(self, dts, log, loop, publisher, ro_account, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._publisher = publisher
        self._project = project
        
        self._cli_api = None
        self._http_api = None
        self._openmano_nsrs = {}
        self._openmano_nsr_by_vnfr_id = {}
        #self._nsr_uuid = None

        self._set_ro_account(ro_account)

    def _set_ro_account(self, ro_account):
        self._log.debug("Setting openmano plugin cloud account: %s", ro_account)
        self._cli_api = openmano_client.OpenmanoCliAPI(
            self.log,
            ro_account.openmano.host,
            ro_account.openmano.port,
            ro_account.openmano.tenant_id,
        )

        self._http_api = openmano_client.OpenmanoHttpAPI(
            self.log,
            ro_account.openmano.host,
            ro_account.openmano.port,
            ro_account.openmano.tenant_id,
        )

    def set_state(self, nsr_id, state):
        # Currently we update only during terminate to
        # decide how to handle VL terminate
        if state.value == OpenmanoNSRecordState.TERMINATE.value:
            self._openmano_nsrs[nsr_id]._state = \
                [member.value for name, member in \
                 OpenmanoNSRecordState.__members__.items() \
                 if member.value == state.value]

    def create_nsr(self, nsr_config_msg, nsd_msg, key_pairs=None, ssh_key=None):
        """
        Create Network service record
        """
        openmano_nsr = OpenmanoNsr(
                self._project,
                self._dts,
                self._log,
                self._loop,
                self._publisher,
                self._cli_api,
                self._http_api,
                nsd_msg,
                nsr_config_msg,
                key_pairs,
                ssh_key,
                )
        self.log.debug("NSR created in openmano nsm %s", openmano_nsr)
        self._openmano_nsrs[nsr_config_msg.id] = openmano_nsr

    @asyncio.coroutine
    def deploy(self, nsr_msg):
        self._log.debug("Received NSR Deploy msg : %s", nsr_msg)
        openmano_nsr = self._openmano_nsrs[nsr_msg.ns_instance_config_ref]
        yield from openmano_nsr.create()
        yield from openmano_nsr.deploy(nsr_msg)

    @asyncio.coroutine
    def instantiate_ns(self, nsr, xact):
        """
        Instantiate NSR with the passed nsr id
        """
        yield from nsr.instantiate(xact)

    @asyncio.coroutine
    def instantiate_vnf(self, nsr, vnfr, scaleout=False):
        """
        Instantiate NSR with the passed nsr id
        """
        openmano_nsr = self._openmano_nsrs[nsr.id]
        if scaleout:
            self._log.debug("Scaleout set as True. Creating Scaling VNFR : {}".format(vnfr))
            openmano_vnf_nsr = OpenmanoNsr(
                self._project,
                self._dts,
                self._log,
                self._loop,
                self._publisher,
                self._cli_api,
                self._http_api,
                openmano_nsr.nsd_msg,
                openmano_nsr.nsr_config_msg,
                openmano_nsr.key_pairs,
                None,
                rift_vnfd_id=vnfr.vnfd.id,
            )
            self._openmano_nsr_by_vnfr_id[nsr.id] = openmano_nsr
            if vnfr.id in self._openmano_nsr_by_vnfr_id:
                raise VNFExistError("VNF %s already exist", vnfr.id)
            self._openmano_nsr_by_vnfr_id[vnfr.id] = openmano_vnf_nsr
            self._log.debug("VNFRID %s %s %s", type(self._openmano_nsr_by_vnfr_id), type(openmano_vnf_nsr), type(self._openmano_nsr_by_vnfr_id[vnfr.id]))
            self._log.debug("Inserting VNFR - {}, in NSR - {}".format(vnfr.id, self._openmano_nsr_by_vnfr_id))
            for vlr in openmano_nsr.vlrs:
                yield from openmano_vnf_nsr.add_vlr(vlr)
            try:
                yield from openmano_nsr.add_nsr(openmano_vnf_nsr, vnfr)
            except Exception as e:
                self.log.exception(str(e))
            try:
                yield from openmano_vnf_nsr.add_vnfr(vnfr)
            except Exception as e:
                self.log.exception(str(e))
            try:
                yield from openmano_vnf_nsr.scaling_scenario_create()
            except Exception as e:
                self.log.exception(str(e))
            try:
                yield from openmano_vnf_nsr.deploy_scaling(openmano_vnf_nsr.nsr_msg, vnfr.id)
            except Exception as e:
                self.log.exception(str(e))
        else:
            self._log.debug("Creating constituent VNFR - {}; for NSR - {}".format(vnfr, nsr))
            yield from openmano_nsr.add_vnfr(vnfr)

        # Mark the VNFR as running
        # TODO: Create a task to monitor nsr/vnfr status
        vnfr_msg = vnfr.vnfr_msg.deep_copy()
        vnfr_msg.operational_status = "init"

        self._log.debug("Attempting to publish openmano vnf: %s", vnfr_msg)
        yield from self._publisher.publish_vnfr(None, vnfr_msg)

    def update_vnfr(self, vnfr):
        vnfr_msg = vnfr.vnfr_msg.deep_copy()
        self._log.debug("Attempting to publish openmano vnf: %s", vnfr_msg)
        yield from self._publisher.publish_vnfr(None, vnfr_msg)

    @asyncio.coroutine
    def instantiate_vl(self, nsr, vlr):
        """
        Instantiate NSR with the passed nsr id
        """
        self._log.debug("Received instantiate VL for NSR {}; VLR {}".format(nsr.id,vlr))
        openmano_nsr = self._openmano_nsrs[nsr.id]
        if openmano_nsr._state == OpenmanoNSRecordState.RUNNING:
            yield from openmano_nsr.create_vlr(vlr)
            yield from self._publisher.publish_vlr(None, vlr.vlr_msg)
        else:
            yield from openmano_nsr.add_vlr(vlr)

    @asyncio.coroutine
    def terminate_ns(self, nsr):
        """
        Terminate the network service
        """
        self._log.debug("Terminate Received for Openamno NSR - {}".format(nsr))
        nsr_id = nsr.id
        openmano_nsr = self._openmano_nsrs[nsr_id]

        for _,handler in openmano_nsr._vdur_console_handler.items():
            handler._regh.deregister()

        yield from self._loop.run_in_executor(
               None,
               self.terminate,
               openmano_nsr,
               )

        for vnfr in openmano_nsr.vnfrs:
            self._log.debug("Unpublishing Constituent VNFR: %s", vnfr.vnfr.vnfr_msg)
            yield from self._publisher.unpublish_vnfr(None, vnfr.vnfr.vnfr_msg)

        del self._openmano_nsrs[nsr_id]

    def terminate(self, openmano_nsr):
        try:
            openmano_nsr.terminate()
            openmano_nsr.delete()
        except Exception as e:
            self._log.error("The NSR terminate failed for {}".format(openmano_nsr))
            raise e

    @asyncio.coroutine
    def terminate_vnf(self, nsr, vnfr, scalein=False):
        """
        Terminate the network service
        """
        if scalein:
            self._log.debug("Terminating Scaling VNFR - {}".format(vnfr))
            openmano_vnf_nsr = self._openmano_nsr_by_vnfr_id[vnfr.id]
            try:
                openmano_vnf_nsr.terminate()
                openmano_vnf_nsr.delete()
            except Exception as e:
                self._log.error("The NSR terminate failed for {}".format(openmano_nsr))
                raise e

            yield from openmano_vnf_nsr.remove_vnf(vnfr)

    @asyncio.coroutine
    def terminate_vl(self, vlr):
        """
        Terminate the virtual link
        """
        self._log.debug("Received terminate VL for VLR {}".format(vlr))
        openmano_nsr = self._openmano_nsrs[vlr._nsr_id]
        if openmano_nsr._state == OpenmanoNSRecordState.RUNNING:
            yield from openmano_nsr.delete_vlr(vlr)
        else:
            yield from openmano_nsr.remove_vlr(vlr)
