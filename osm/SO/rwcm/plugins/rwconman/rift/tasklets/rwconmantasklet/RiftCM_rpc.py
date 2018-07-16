
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
import os
import re
import tempfile
import time
import yaml


from . import riftcm_config_plugin
import rift.mano.config_agent

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwNsrYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    NsrYang,
)

class RiftCMRPCHandler(object):
    """ The Network service Monitor DTS handler """
    EXEC_NS_CONF_XPATH = "I,/nsr:exec-ns-service-primitive"
    EXEC_NS_CONF_O_XPATH = "O,/nsr:exec-ns-service-primitive"

    GET_NS_CONF_XPATH = "I,/nsr:get-ns-service-primitive-values"
    GET_NS_CONF_O_XPATH = "O,/nsr:get-ns-service-primitive-values"

    def __init__(self, dts, log, loop, project, nsm):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._nsm = nsm

        self._ns_regh = None
        self._vnf_regh = None
        self._get_ns_conf_regh = None

        self.job_manager = rift.mano.config_agent.ConfigAgentJobManager(dts, log, loop,
                                                                        project, nsm)

        self._rift_install_dir = os.environ['RIFT_INSTALL']
        self._rift_var_root_dir = os.environ['RIFT_VAR_ROOT']

    @property
    def reghs(self):
        """ Return registration handles """
        return (self._ns_regh, self._vnf_regh, self._get_ns_conf_regh)

    @property
    def nsm(self):
        """ Return the NS manager instance """
        return self._nsm

    def deregister(self):
        self._log.debug("De-register conman rpc handlers for project {}".
                        format(self._project))
        for reg in self.reghs:
            if reg:
                reg.deregister()
                reg = None

        self.job_manager.deregister()
        self.job_manager = None

    def prepare_meta(self, rpc_ip):

        try:
            nsr_id = rpc_ip.nsr_id_ref
            nsr = self._nsm.nsrs[nsr_id]
            vnfrs = {}
            for vnfr in nsr.vnfrs:
                vnfr_id = vnfr.id
                # vnfr is a dict containing all attributes
                vnfrs[vnfr_id] = vnfr

            return nsr, vnfrs
        except KeyError as e:
            raise ValueError("Record not found", str(e))

    @asyncio.coroutine
    def _get_ns_cfg_primitive(self, nsr_id, ns_cfg_name):
        nsd_msg = yield from self._nsm.get_nsd(nsr_id)

        def get_nsd_cfg_prim(name):
            for ns_cfg_prim in nsd_msg.service_primitive:
                if ns_cfg_prim.name == name:
                    return ns_cfg_prim
            return None

        ns_cfg_prim_msg = get_nsd_cfg_prim(ns_cfg_name)
        if ns_cfg_prim_msg is not None:
            ret_cfg_prim_msg = ns_cfg_prim_msg.deep_copy()
            return ret_cfg_prim_msg
        return None

    @asyncio.coroutine
    def _get_vnf_primitive(self, vnfr_id, nsr_id, primitive_name):
        vnf = self._nsm.get_vnfr_msg(vnfr_id, nsr_id)
        self._log.debug("vnfr_msg:%s", vnf)
        if vnf:
            self._log.debug("nsr/vnf {}/{}, vnf_configuration: %s",
                            vnf.vnf_configuration)
            for primitive in vnf.vnf_configuration.config_primitive:
                if primitive.name == primitive_name:
                    return primitive

        raise ValueError("Could not find nsr/vnf {}/{} primitive {}"
                         .format(nsr_id, vnfr_id, primitive_name))

    @asyncio.coroutine
    def _apply_ns_config(self, agent_nsr, agent_vnfrs, rpc_ip):
        """
        Hook: Runs the user defined script. Feeds all the necessary data
        for the script thro' yaml file.

        TBD: Add support to pass multiple CA accounts if configures
             Remove apply_ns_config from the Config Agent Plugins

        Args:
            rpc_ip (YangInput_Nsr_ExecNsConfigPrimitive): The input data.
            nsr (NetworkServiceRecord): Description
            vnfrs (dict): VNFR ID => VirtualNetworkFunctionRecord

        """
        def xlate(tag, tags):
            # TBD
            if tag is None or tags is None:
                return tag
            val = tag
            if re.search('<.*>', tag):
                try:
                    if tag == '<rw_mgmt_ip>':
                        val = tags['rw_mgmt_ip']
                except KeyError as e:
                    self._log.info("RiftCA: Did not get a value for tag %s, e=%s",
                                   tag, e)
            return val

        def get_meta(agent_nsr, agent_vnfrs):
            unit_names, initial_params, vnfr_index_map, vnfr_data_map = {}, {}, {}, {}

            for vnfr_id in agent_nsr.vnfr_ids:
                vnfr = agent_vnfrs[vnfr_id]
                self._log.debug("CA-RPC: VNFR metadata: {}".format(vnfr))

                # index->vnfr ref
                vnfr_index_map[vnfr.member_vnf_index] = vnfr_id
                vnfr_data_dict = dict()
                if 'mgmt_interface' in vnfr.vnfr:
                    vnfr_data_dict['mgmt_interface'] = vnfr.vnfr['mgmt_interface']

                vnfr_data_dict['name'] = vnfr.vnfr['name']
                vnfr_data_dict['connection_point'] = []
                if 'connection_point' in vnfr.vnfr:
                    for cp in vnfr.vnfr['connection_point']:
                        cp_dict = dict(name = cp['name'],
                                       ip_address = cp['ip_address'],
                                       connection_point_id = cp['connection_point_id'])
                        if 'virtual_cps' in cp:
                            cp_info['virtual_cps'] = [ {k:v for k,v in vcp.items()
                                                        if k in ['ip_address', 'mac_address']}
                                                       for vcp in cp['virtual_cps'] ]

                        vnfr_data_dict['connection_point'].append(cp_dict)

                try:
                    vnfr_data_dict['vdur'] = []
                    vdu_data = [(vdu['name'], vdu['management_ip'], vdu['vm_management_ip'], vdu['id'], vdu['vdu_id_ref'])
                                for vdu in vnfr.vnfr['vdur']]

                    for data in vdu_data:
                        data = dict(zip(['name', 'management_ip', 'vm_management_ip', 'id', 'vdu_id_ref'] , data))
                        vnfr_data_dict['vdur'].append(data)

                    vnfr_data_map[vnfr.member_vnf_index] = vnfr_data_dict
                except KeyError as e:
                    self._log.warn("Error getting VDU data for VNFR {}".format(vnfr))

                # Unit name
                unit_names[vnfr_id] = None
                for config_plugin in self.nsm.config_agent_plugins:
                    name = config_plugin.get_service_name(vnfr_id)
                    if name:
                        unit_names[vnfr_id] = name
                        break

                # Flatten the data for simplicity
                param_data = {}
                if 'initial_config_primitive' in vnfr.vnf_configuration:
                    for primitive in vnfr.vnf_configuration['initial_config_primitive']:
                        if 'parameter' in primitive:
                            for parameter in primitive['parameter']:
                                try:
                                    value = xlate(parameter['value'], vnfr.tags)
                                    param_data[parameter['name']] = value
                                except KeyError as e:
                                    self._log.warn("Unable to parse the parameter{}:  {}".
                                                   format(parameter))

                initial_params[vnfr_id] = param_data


            return unit_names, initial_params, vnfr_index_map, vnfr_data_map

        def get_config_agent():
            ret = {}
            for config_plugin in self.nsm.config_agent_plugins:
                if config_plugin.agent_type in [riftcm_config_plugin.DEFAULT_CAP_TYPE]:
                    ret = config_plugin.agent_data
                else:
                    # Currently the first non default plugin is returned
                    return config_plugin.agent_data
            return ret

        unit_names, init_data, vnfr_index_map, vnfr_data_map = get_meta(agent_nsr, agent_vnfrs)

        # The data consists of 4 sections
        # 1. Account data
        # 2. The input passed.
        # 3. Juju unit names (keyed by vnfr ID).
        # 4. Initial config data (keyed by vnfr ID).
        data = dict()
        data['config_agent'] = get_config_agent()
        data["rpc_ip"] = rpc_ip.as_dict()
        data["unit_names"] = unit_names
        data["init_config"] = init_data
        data["vnfr_index_map"] = vnfr_index_map
        data["vnfr_data_map"] = vnfr_data_map

        tmp_file = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data, default_flow_style=True)
                    .encode("UTF-8"))

        self._log.debug("CA-RPC: Creating a temp file {} with input data: {}".
                        format(tmp_file.name, data))

        # Get the full path to the script
        script = ''
        if rpc_ip.user_defined_script[0] == '/':
            # The script has full path, use as is
            script = rpc_ip.user_defined_script
        else:
            script = os.path.join(self._rift_var_root_dir,
                                  'launchpad/packages/nsd',
                                  self._project.name,
                                  agent_nsr.nsd_id, 'scripts',
                                  rpc_ip.user_defined_script)
            self._log.debug("CA-RPC: Checking for script in %s", script)

        cmd = "{} {}".format(script, tmp_file.name)
        self._log.debug("CA-RPC: Running the CMD: {}".format(cmd))

        process = yield from asyncio.create_subprocess_shell(
            cmd)

        return process

    @asyncio.coroutine
    def register(self):
        """ Register for NS monitoring read from dts """
        yield from self.job_manager.register()

        @asyncio.coroutine
        def on_ns_config_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts exec-ns-service-primitive"""
            assert action == rwdts.QueryAction.RPC

            if not self._project.rpc_check(msg, xact_info):
                return

            rpc_ip = msg
            rpc_op = NsrYang.YangOutput_Nsr_ExecNsServicePrimitive.from_dict({
                    "triggered_by": rpc_ip.triggered_by,
                    "create_time": int(time.time()),
                    "parameter": [param.as_dict() for param in rpc_ip.parameter],
                    "parameter_group": [pg.as_dict() for pg in rpc_ip.parameter_group]
                })

            try:
                ns_cfg_prim_name = rpc_ip.name
                nsr_id = rpc_ip.nsr_id_ref
                nsr = self._nsm.nsrs[nsr_id]

                nsd_cfg_prim_msg = yield from self._get_ns_cfg_primitive(nsr_id, ns_cfg_prim_name)

                def find_nsd_vnf_prim_param_pool(vnf_index, vnf_prim_name, param_name):
                    for vnf_prim_group in nsd_cfg_prim_msg.vnf_primitive_group:
                        if vnf_prim_group.member_vnf_index_ref != vnf_index:
                            continue

                        for vnf_prim in vnf_prim_group.primitive:
                            if vnf_prim.name != vnf_prim_name:
                                continue

                            try:
                                nsr_param_pool = nsr.param_pools[pool_param.parameter_pool]
                            except KeyError:
                                raise ValueError("Parameter pool %s does not exist in nsr" % vnf_prim.parameter_pool)

                            self._log.debug("Found parameter pool %s for vnf index(%s), vnf_prim_name(%s), param_name(%s)",
                                            nsr_param_pool, vnf_index, vnf_prim_name, param_name)
                            return nsr_param_pool

                    self._log.debug("Could not find parameter pool for vnf index(%s), vnf_prim_name(%s), param_name(%s)",
                                vnf_index, vnf_prim_name, param_name)
                    return None

                rpc_op.nsr_id_ref = nsr_id
                rpc_op.name = ns_cfg_prim_name

                nsr, vnfrs = self.prepare_meta(rpc_ip)
                rpc_op.job_id = nsr.job_id

                # Copy over the NS level Parameters

                # Give preference to user defined script.
                if nsd_cfg_prim_msg and nsd_cfg_prim_msg.has_field("user_defined_script"):
                    rpc_ip.user_defined_script = nsd_cfg_prim_msg.user_defined_script

                    task = yield from self._apply_ns_config(
                        nsr,
                        vnfrs,
                        rpc_ip)

                    self.job_manager.add_job(rpc_op, [task])
                else:
                    # Otherwise create VNF primitives.
                    for vnf in rpc_ip.vnf_list:
                        vnf_op = rpc_op.vnf_out_list.add()
                        vnf_member_idx = vnf.member_vnf_index_ref
                        vnfr_id = vnf.vnfr_id_ref
                        vnf_op.vnfr_id_ref = vnfr_id
                        vnf_op.member_vnf_index_ref = vnf_member_idx

                        idx = 0
                        for primitive in vnf.vnf_primitive:
                            op_primitive = vnf_op.vnf_out_primitive.add()
                            op_primitive.index = idx
                            idx += 1
                            op_primitive.name = primitive.name
                            op_primitive.execution_id = ''
                            op_primitive.execution_status = 'pending'
                            op_primitive.execution_error_details = ''

                            # Copy over the VNF pimitive's input parameters
                            for param in primitive.parameter:
                                output_param = op_primitive.parameter.add()
                                output_param.name = param.name
                                output_param.value = param.value

                            self._log.debug("%s:%s Got primitive %s:%s",
                                            nsr_id, vnf.member_vnf_index_ref, primitive.name, primitive.parameter)

                            nsd_vnf_primitive = yield from self._get_vnf_primitive(
                                vnfr_id,
                                nsr_id,
                                primitive.name
                            )
                            for param in nsd_vnf_primitive.parameter:
                                if not param.has_field("parameter_pool"):
                                    continue

                                try:
                                    nsr_param_pool = nsr.param_pools[param.parameter_pool]
                                except KeyError:
                                    raise ValueError("Parameter pool %s does not exist in nsr" % param.parameter_pool)
                                nsr_param_pool.add_used_value(param.value)

                            for config_plugin in self.nsm.config_agent_plugins:
                                # TODO: Execute these in separate threads to prevent blocking
                                yield from config_plugin.vnf_config_primitive(nsr_id,
                                                                              vnfr_id,
                                                                              primitive,
                                                                              op_primitive)

                    self.job_manager.add_job(rpc_op)

                # Get NSD
                # Find Config Primitive
                # For each vnf-primitive with parameter pool
                # Find parameter pool
                # Add used value to the pool
                self._log.debug("RPC output: {}".format(rpc_op))
                xact_info.respond_xpath(rwdts.XactRspCode.ACK,
                                        RiftCMRPCHandler.EXEC_NS_CONF_O_XPATH,
                                        rpc_op)
            except Exception as e:
                self._log.error("Exception processing the "
                                "exec-ns-service-primitive: {}".format(e))
                self._log.exception(e)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK,
                                        RiftCMRPCHandler.EXEC_NS_CONF_O_XPATH)

        @asyncio.coroutine
        def on_get_ns_config_values_prepare(xact_info, action, ks_path, msg):
            assert action == rwdts.QueryAction.RPC

            if not self._project.rpc_check(msg, xact_info):
                return

            nsr_id = msg.nsr_id_ref
            cfg_prim_name = msg.name
            try:
                nsr = self._nsm.nsrs[nsr_id]

                rpc_op = NsrYang.YangOutput_Nsr_GetNsServicePrimitiveValues()

                ns_cfg_prim_msg = yield from self._get_ns_cfg_primitive(nsr_id, cfg_prim_name)

                # Get pool values for NS-level parameters
                for ns_param in ns_cfg_prim_msg.parameter:
                    if not ns_param.has_field("parameter_pool"):
                        continue

                    try:
                        nsr_param_pool = nsr.param_pools[ns_param.parameter_pool]
                    except KeyError:
                        raise ValueError("Parameter pool %s does not exist in nsr" % ns_param.parameter_pool)

                    new_ns_param = rpc_op.ns_parameter.add()
                    new_ns_param.name = ns_param.name
                    new_ns_param.value = str(nsr_param_pool.get_next_unused_value())

                # Get pool values for NS-level parameters
                for vnf_prim_group in ns_cfg_prim_msg.vnf_primitive_group:
                    rsp_prim_group = rpc_op.vnf_primitive_group.add()
                    rsp_prim_group.member_vnf_index_ref = vnf_prim_group.member_vnf_index_ref
                    if vnf_prim_group.has_field("vnfd_id_ref"):
                        rsp_prim_group.vnfd_id_ref = vnf_prim_group.vnfd_id_ref

                    for index, vnf_prim in enumerate(vnf_prim_group.primitive):
                        rsp_prim = rsp_prim_group.primitive.add()
                        rsp_prim.name = vnf_prim.name
                        rsp_prim.index = index
                        vnf_primitive = yield from self._get_vnf_primitive(
                                vnf_prim_group.vnfd_id_ref,
                                nsr_id,
                                vnf_prim.name
                        )
                        for param in vnf_primitive.parameter:
                            if not param.has_field("parameter_pool"):
                                continue

                # Get pool values for NS-level parameters
                for ns_param in ns_cfg_prim_msg.parameter:
                    if not ns_param.has_field("parameter_pool"):
                        continue

                    try:
                        nsr_param_pool = nsr.param_pools[ns_param.parameter_pool]
                    except KeyError:
                        raise ValueError("Parameter pool %s does not exist in nsr" % ns_param.parameter_pool)

                    new_ns_param = rpc_op.ns_parameter.add()
                    new_ns_param.name = ns_param.name
                    new_ns_param.value = str(nsr_param_pool.get_next_unused_value())

                # Get pool values for NS-level parameters
                for vnf_prim_group in ns_cfg_prim_msg.vnf_primitive_group:
                    rsp_prim_group = rpc_op.vnf_primitive_group.add()
                    rsp_prim_group.member_vnf_index_ref = vnf_prim_group.member_vnf_index_ref
                    if vnf_prim_group.has_field("vnfd_id_ref"):
                        rsp_prim_group.vnfd_id_ref = vnf_prim_group.vnfd_id_ref

                    for index, vnf_prim in enumerate(vnf_prim_group.primitive):
                        rsp_prim = rsp_prim_group.primitive.add()
                        rsp_prim.name = vnf_prim.name
                        rsp_prim.index = index
                        vnf_primitive = yield from self._get_vnf_primitive(
                                nsr_id,
                                vnf_prim_group.member_vnf_index_ref,
                                vnf_prim.name
                                )
                        for param in vnf_primitive.parameter:
                            if not param.has_field("parameter_pool"):
                                continue

                            try:
                                nsr_param_pool = nsr.param_pools[param.parameter_pool]
                            except KeyError:
                                raise ValueError("Parameter pool %s does not exist in nsr" % vnf_prim.parameter_pool)

                            vnf_param = rsp_prim.parameter.add()
                            vnf_param.name = param.name
                            vnf_param.value = str(nsr_param_pool.get_next_unused_value())

                self._log.debug("RPC output: {}".format(rpc_op))
                xact_info.respond_xpath(rwdts.XactRspCode.ACK,
                                        RiftCMRPCHandler.GET_NS_CONF_O_XPATH, rpc_op)
            except Exception as e:
                self._log.error("Exception processing the "
                                "get-ns-service-primitive-values: {}".format(e))
                self._log.exception(e)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK,
                                        RiftCMRPCHandler.GET_NS_CONF_O_XPATH)

        hdl_ns = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_ns_config_prepare,)
        hdl_ns_get = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_get_ns_config_values_prepare,)

        with self._dts.group_create() as group:
            self._ns_regh = group.register(xpath=RiftCMRPCHandler.EXEC_NS_CONF_XPATH,
                                           handler=hdl_ns,
                                           flags=rwdts.Flag.PUBLISHER,
                                           )
            self._get_ns_conf_regh = group.register(xpath=RiftCMRPCHandler.GET_NS_CONF_XPATH,
                                                    handler=hdl_ns_get,
                                                    flags=rwdts.Flag.PUBLISHER,
                                                    )
