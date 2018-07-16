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
import concurrent.futures
import os
import re
import shlex
import tempfile
import yaml

from gi.repository import (
    RwDts as rwdts,
)

from . import riftcm_config_plugin

class RiftCAConfigPlugin(riftcm_config_plugin.RiftCMConfigPluginBase):
    """
        Implementation of the riftcm_config_plugin.RiftCMConfigPluginBase
    """
    def __init__(self, dts, log, loop, project, account):
        riftcm_config_plugin.RiftCMConfigPluginBase.__init__(self, dts, log,
                                                             loop, project, account)
        self._name = account.name
        self._type = riftcm_config_plugin.DEFAULT_CAP_TYPE
        self._rift_install_dir = os.environ['RIFT_INSTALL']
        self._rift_var_root_dir = os.environ['RIFT_VAR_ROOT']
        self._rift_vnfs = {}
        self._tasks = {}

    @property
    def name(self):
        return self._name

    @property
    def agent_type(self):
        return self._type

    @property
    def agent_data(self):
        return dict(
            type=self.agent_type,
            name=self.name,
        )

    def vnfr(self, vnfr_id):
        try:
            vnfr = self._rift_vnfs[vnfr_id].vnfr
        except KeyError:
            self._log.debug("RiftCA: Did not find VNFR %s in Rift plugin", vnfr_id)
            return None

        return vnfr

    def get_service_name(self, vnfr_id):
        vnfr = self.vnfr(vnfr_id)
        if vnfr:
            return vnfr['name']
        return None

    @asyncio.coroutine
    def notify_create_vlr(self, agent_nsr, agent_vnfr, vld, vlr):
        """
        Notification of create VL record
        """
        pass

    @asyncio.coroutine
    def is_vnf_configurable(self, agent_vnfr):
        '''
        This needs to be part of abstract class
        '''
        loop_count = 10
        while loop_count:
            loop_count -= 1
            # Set this VNF's configurability status (need method to check)
            yield from asyncio.sleep(2, loop=self._loop)

    def riftca_log(self, name, level, log_str, *args):
        getattr(self._log, level)('RiftCA:({}) {}'.format(name, log_str), *args)

    @asyncio.coroutine
    def notify_create_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of create Network VNF record
        """
        # Deploy the charm if specified for the vnf
        self._log.debug("Rift config agent: create vnfr nsr={}  vnfr={}"
                        .format(agent_nsr.name, agent_vnfr.name))
        try:
            self._loop.create_task(self.is_vnf_configurable(agent_vnfr))
        except Exception as e:
            self._log.debug("Rift config agent: vnf_configuration error for VNF:%s/%s: %s",
                            agent_nsr.name, agent_vnfr.name, str(e))
            return False

        return True

    @asyncio.coroutine
    def notify_instantiate_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of Instantiate NSR with the passed nsr id
        """
        pass

    @asyncio.coroutine
    def notify_instantiate_vlr(self, agent_nsr, agent_vnfr, vlr):
        """
        Notification of Instantiate NSR with the passed nsr id
        """
        pass

    @asyncio.coroutine
    def notify_terminate_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of Terminate the network service
        """

    @asyncio.coroutine
    def notify_terminate_vlr(self, agent_nsr, agent_vnfr, vlr):
        """
        Notification of Terminate the virtual link
        """
        pass

    @asyncio.coroutine
    def _vnf_config_primitive(self, nsr_id, vnfr_id, primitive,
                             vnf_config=None, vnfd_descriptor=None):
        '''
        Pass vnf_config to avoid querying DTS each time
        '''
        self._log.debug("VNF config primitive {} for nsr {}, vnfr {}".
                        format(primitive.name, nsr_id, vnfr_id))

        if vnf_config is None or vnfd_descriptor is None:
            vnfr_msg = yield from self.get_vnfr(vnfr_id)
            if vnfr_msg is None:
                msg = "Unable to get VNFR {} through DTS".format(vnfr_id)
                self._log.error(msg)
                return 3, msg

            vnf_config = vnfr_msg.vnf_configuration
            vnfd_descriptor = vnfr_msg.vnfd
        self._log.debug("VNF config= %s", vnf_config.as_dict())
        self._log.debug("VNFD descriptor= %s", vnfd_descriptor.as_dict())

        data = {}
        script = None
        found = False

        configs = vnf_config.config_primitive
        for config in configs:
            if config.name == primitive.name:
                found = True
                self._log.debug("RiftCA: Found the config primitive %s",
                                config.name)

                spt = config.user_defined_script
                if spt is None:
                    self._log.error("RiftCA: VNFR {}, Did not find "
                                    "script defined in config {}".
                                    format(vnfr['name'], config.as_dict()))
                    return 1, "Did not find user defined script for " \
                        "config primitive {}".format(primitive.name)

                spt = shlex.quote(spt.strip())
                if spt[0] == '/':
                    script = spt
                else:
                    script = os.path.join(self._rift_var_root_dir,
                                          'launchpad/packages/vnfd',
                                          self._project.name,
                                          vnfd_descriptor.id,
                                          'scripts',
                                          spt)
                    self._log.debug("Rift config agent: Checking for script "
                                    "in %s", script)
                    if not os.path.exists(script):
                        self._log.debug("Rift config agent: Did not find "
                                            "script %s", script)
                        return 1, "Did not find user defined " \
                                "script {}".format(spt)

                params = {}
                for param in config.parameter:
                    val = None
                    for p in primitive.parameter:
                        if p.name == param.name:
                            val = p.value
                            break

                    if val is None:
                        val = param.default_value

                    if val is None:
                        # Check if mandatory parameter
                        if param.mandatory:
                            msg = "VNFR {}: Primitive {} called " \
                                  "without mandatory parameter {}". \
                                  format(vnfr.name, config.name,
                                         param.name)
                            self._log.error(msg)
                            return 1, msg

                    if val:
                        val = self.convert_value(val, param.data_type)
                        params.update({param.name: val})

                data['parameters'] = params
                break

        if not found:
            msg = "Did not find the primitive {} in VNFR {}". \
                  format(primitive.name, vnfr.name)
            self._log.error(msg)
            return 1, msg

        rc, script_err = yield from self.exec_script(script, data)
        return rc, script_err

    @asyncio.coroutine
    def vnf_config_primitive(self, nsr_id, vnfr_id, primitive, output):
        '''
        primitives support by RiftCA

        Pass vnf_config to avoid querying DTS each time
        '''
        try:
            vnfr = self._rift_vnfs[vnfr_id].vnfr
        except KeyError:
            msg = "Did not find VNFR {} in Rift plugin".format(vnfr_id)
            self._log.debug(msg)
            return

        output.execution_status = "failed"
        output.execution_id = ''
        output.execution_error_details = ''

        rc, err = yield from self._vnf_config_primitive(nsr_id,
                                                        vnfr_id,
                                                        primitive)
        self._log.debug("VNFR {} primitive {} exec status: {}".
                        format(vnfr_id, primitive.name, rc))

        if rc == 0:
            output.execution_status = "completed"
        else:
            self._rift_vnfs[vnfr_id].error = True

        output.execution_error_details = '{}'.format(err)

    @asyncio.coroutine
    def apply_config(self, config, nsr, vnfr, rpc_ip):
        """ Notification on configuration of an NSR """
        pass

    @asyncio.coroutine
    def apply_ns_config(self, agent_nsr, agent_vnfrs, rpc_ip):
        """Hook: Runs the user defined script. Feeds all the necessary data
        for the script thro' yaml file.

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

                # index->vnfr ref
                vnfr_index_map[vnfr.member_vnf_index] = vnfr_id
                vnfr_data_dict = dict()
                if 'mgmt_interface' in vnfr.vnfr:
                    vnfr_data_dict['mgmt_interface'] = vnfr.vnfr['mgmt_interface']

                vnfr_data_dict['connection_point'] = []
                vnfr_data_dict['name'] = vnfr.vnfr['name']
                vnfr_data_dict['datacenter'] = vnfr.vnfr['datacenter']
                if 'connection_point' in vnfr.vnfr:
                    for cp in vnfr.vnfr['connection_point']:
                        cp_dict = dict()
                        cp_dict['name'] = cp['name']
                        cp_dict['ip_address'] = cp['ip_address']
                        cp_dict['connection_point_id'] = cp['connection_point_id']
                        if 'virtual_cps' in cp:
                            cp_dict['virtual_cps'] = [ {k:v for k,v in vcp.items()
                                                        if k in ['ip_address', 'mac_address']}
                                                       for vcp in cp['virtual_cps'] ]
                        vnfr_data_dict['connection_point'].append(cp_dict)

                vnfr_data_dict['vdur'] = []
                vdu_data = [(vdu['name'], vdu['management_ip'], vdu['vm_management_ip'], vdu['id'], vdu['vdu_id_ref'])
                        for vdu in vnfr.vnfr['vdur']]

                for data in vdu_data:
                    data = dict(zip(['name', 'management_ip', 'vm_management_ip', 'id', 'vdu_id_ref'] , data))
                    vnfr_data_dict['vdur'].append(data)

                vnfr_data_map[vnfr.member_vnf_index] = vnfr_data_dict
                # Unit name
                unit_names[vnfr_id] = vnfr.name
                # Flatten the data for simplicity
                param_data = {}
                if 'initial_config_primitive' in vnfr.vnf_configuration:
                    for primitive in vnfr.vnf_configuration['initial_config_primitive']:
                        for parameter in primitive.parameter:
                            value = xlate(parameter.value, vnfr.tags)
                            param_data[parameter.name] = value

                initial_params[vnfr_id] = param_data


            return unit_names, initial_params, vnfr_index_map, vnfr_data_map

        unit_names, init_data, vnfr_index_map, vnfr_data_map = get_meta(agent_nsr, agent_vnfrs)
        # The data consists of 4 sections
        # 1. Account data
        # 2. The input passed.
        # 3. Unit names (keyed by vnfr ID).
        # 4. Initial config data (keyed by vnfr ID).
        data = dict()
        data['config_agent'] = dict(
                name=self._name,
                )
        data["rpc_ip"] = rpc_ip.as_dict()
        data["unit_names"] = unit_names
        data["init_config"] = init_data
        data["vnfr_index_map"] = vnfr_index_map
        data["vnfr_data_map"] = vnfr_data_map

        tmp_file = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data, default_flow_style=True)
                    .encode("UTF-8"))

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
            self._log.debug("Rift config agent: Checking for script in %s", script)
            if not os.path.exists(script):
                self._log.error("Rift config agent: Did not find script %s", script)

        cmd = "{} {}".format(script, tmp_file.name)
        self._log.debug("Rift config agent: Running the CMD: {}".format(cmd))

        coro = asyncio.create_subprocess_shell(cmd, loop=self._loop,
                                               stderr=asyncio.subprocess.PIPE)
        process = yield from coro
        err = yield from process.stderr.read()
        task = self._loop.create_task(process.wait())

        return task, err

    @asyncio.coroutine
    def apply_initial_config_new(self, agent_nsr, agent_vnfr):
        self._log.debug("RiftCA: VNF initial config primitive for nsr {}, vnfr {}".
                        format(agent_nsr.name, agent_vnfr.name))

        try:
            vnfr = self._rift_vnfs[agent_vnfr.id].vnfr
        except KeyError:
            self._log.error("RiftCA: Did not find VNFR %s in RiftCA plugin",
                            agent_vnfr.name)
            return False

        class Primitive:
            def __init__(self, name):
                self.name = name
                self.value = None
                self.parameter = []

        vnfr = yield from self.get_vnfr(agent_vnfr.id)
        if vnfr is None:
            msg = "Unable to get VNFR {} ({}) through DTS". \
                  format(agent_vnfr.id, agent_vnfr.name)
            self._log.error(msg)
            raise RuntimeError(msg)

        vnf_config = vnfr.vnf_configuration
        self._log.debug("VNFR %s config: %s", vnfr.name,
                        vnf_config.as_dict())

        vnfd_descriptor = vnfr.vnfd
        self._log.debug("VNFR  %s vnfd descriptor: %s", vnfr.name,
                        vnfd_descriptor.as_dict())


        # Sort the primitive based on the sequence number
        primitives = sorted(vnf_config.initial_config_primitive,
                            key=lambda k: k.seq)
        if not primitives:
            self._log.debug("VNFR {}: No initial-config-primitive specified".
                            format(vnfr.name))
            return True

        for primitive in primitives:
            if primitive.config_primitive_ref:
                # Reference to a primitive in config primitive
                prim = Primitive(primitive.config_primitive_ref)
                rc, err = yield from self._vnf_config_primitive(agent_nsr.id,
                                                                agent_vnfr.id,
                                                                prim,
                                                                vnf_config, vnfd_descriptor)
                if rc != 0:
                    msg = "Error executing initial config primitive" \
                          " {} in VNFR {}: rc={}, stderr={}". \
                          format(prim.name, vnfr.name, rc, err)
                    self._log.error(msg)
                    return False

            elif primitive.name:
                if not primitive.user_defined_script:
                    msg = "Primitive {} definition in initial config " \
                          "primitive for VNFR {} not supported yet". \
                          format(primitive.name, vnfr.name)
                    self._log.error(msg)
                    raise NotImplementedError(msg)

        return True

    @asyncio.coroutine
    def apply_initial_config(self, agent_nsr, agent_vnfr):
        """
        Apply the initial configuration
        """
        self._log.debug("Rift config agent: Apply initial config to VNF:%s/%s",
                        agent_nsr.name, agent_vnfr.name)
        rc = False

        try:
            if agent_vnfr.id in self._rift_vnfs.keys():
                rc = yield from self.apply_initial_config_new(agent_nsr, agent_vnfr)
                if not rc:
                    agent_vnfr._error = True

            else:
                rc = True
        except Exception as e:
            self._log.error("Rift config agent: Error on initial configuration to VNF:{}/{}, e {}"
                            .format(agent_nsr.name, agent_vnfr.name, str(e)))

            self._log.exception(e)
            agent_vnfr.error = True
            return False

        return rc

    def is_vnfr_managed(self, vnfr_id):
        try:
            if vnfr_id in self._rift_vnfs:
                return True
        except Exception as e:
            self._log.debug("Rift config agent: Is VNFR {} managed: {}".
                            format(vnfr_id, e))
        return False

    def add_vnfr_managed(self, agent_vnfr):
        if agent_vnfr.id not in self._rift_vnfs.keys():
            self._log.info("Rift config agent: add vnfr={}/{}".format(agent_vnfr.name, agent_vnfr.id))
            self._rift_vnfs[agent_vnfr.id] = agent_vnfr

    @asyncio.coroutine
    def get_config_status(self, agent_nsr, agent_vnfr):
            if agent_vnfr.id in self._rift_vnfs.keys():
                if agent_vnfr.error:
                    return 'error'
                return 'configured'
            return 'unknown'


    def get_action_status(self, execution_id):
        ''' Get the action status for an execution ID
            *** Make sure this is NOT a asyncio coroutine function ***
        '''
        return None
