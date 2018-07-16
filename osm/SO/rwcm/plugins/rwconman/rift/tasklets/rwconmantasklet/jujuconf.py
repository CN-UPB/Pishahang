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

import rift.mano.utils.juju_api as juju
from . import riftcm_config_plugin


def get_vnf_unique_name(nsr_name, vnfr_name, member_vnf_index):
    """Get the unique VNF name.
    Charm names accepts only a to z and non-consecutive - characters."""
    name = "{}-{}-{}".format(nsr_name, vnfr_name, member_vnf_index)
    new_name = ''
    for c in name:
        if c.isdigit():
            c = chr(97 + int(c))
        elif not c.isalpha():
            c = "-"
        new_name += c
    return re.sub('\-+', '-', new_name.lower())


class JujuConfigPlugin(riftcm_config_plugin.RiftCMConfigPluginBase):
    """
        Juju implementation of the riftcm_config_plugin.RiftCMConfigPluginBase
    """
    def __init__(self, dts, log, loop, project, account):
        riftcm_config_plugin.RiftCMConfigPluginBase.__init__(self, dts, log, loop,
                                                             project, account)
        self._name = account.name
        self._type = 'juju'
        self._ip_address = account.juju.ip_address
        self._port = account.juju.port
        self._user = account.juju.user
        self._secret = account.juju.secret
        self._rift_install_dir = os.environ['RIFT_INSTALL']
        self._rift_var_root_dir = os.environ['RIFT_VAR_ROOT']

        ############################################################
        # This is wrongfully overloaded with 'juju' private data.  #
        # Really need to separate agent_vnfr from juju vnfr data.  #
        # Currently, this holds agent_vnfr, which has actual vnfr, #
        # then this juju overloads actual vnfr with its own        #
        # dictionary elemetns (WRONG!!!)                           #
        self._juju_vnfs = {}
        ############################################################

        self._tasks = {}
        self._api = juju.JujuApi(log, loop,
                                 self._ip_address, self._port,
                                 self._user, self._secret)

    @property
    def name(self):
        return self._name

    @property
    def agent_type(self):
        return self._type

    @property
    def api(self):
        return self._api

    @property
    def agent_data(self):
        return dict(
            type=self.agent_type,
            name=self.name,
            host=self._ip_address,
            port=self._port,
            user=self._user,
            secret=self._secret
        )

    def vnfr(self, vnfr_id):
        try:
            vnfr = self._juju_vnfs[vnfr_id].vnfr
        except KeyError:
            self._log.error("jujuCA: Did not find VNFR %s in juju plugin", vnfr_id)
            return None

        return vnfr

    def get_service_name(self, vnfr_id):
        vnfr = self.vnfr(vnfr_id)
        if vnfr and 'vnf_juju_name' in vnfr:
            return vnfr['vnf_juju_name']
        return None

    def juju_log(self, level, name, log_str, *args):
        if name is not None:
            g_log_str = 'jujuCA:({}) {}'.format(name, log_str)
        else:
            g_log_str = 'jujuCA: {}'.format(log_str)
        getattr(self._log, level)(g_log_str, *args)

    # TBD: Do a better, similar to config manager
    def xlate(self, tag, tags):
        # TBD
        if tag is None:
            return tag
        val = tag
        if re.search('<.*>', tag):
            self._log.debug("jujuCA: Xlate value %s", tag)
            try:
                if tag == '<rw_mgmt_ip>':
                    val = tags['rw_mgmt_ip']
            except KeyError as e:
                self._log.info("jujuCA: Did not get a value for tag %s, e=%s",
                               tag, e)
        return val

    @asyncio.coroutine
    def notify_create_vlr(self, agent_nsr, agent_vnfr, vld, vlr):
        """
        Notification of create VL record
        """
        return True

    @asyncio.coroutine
    def notify_create_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of create Network VNF record
        Returns True if configured using config_agent
        """
        # Deploy the charm if specified for the vnf
        self._log.debug("jujuCA: create vnfr nsr=%s  vnfr=%s",
                        agent_nsr.name, agent_vnfr.name)
        self._log.debug("jujuCA: Config = %s",
                        agent_vnfr.vnf_configuration)
        try:
            vnf_config = agent_vnfr.vnfr_msg.vnf_configuration
            self._log.debug("jujuCA: vnf_configuration = %s", vnf_config)
            if not vnf_config.has_field('juju'):
                return False
            charm = vnf_config.juju.charm
            self._log.debug("jujuCA: charm = %s", charm)
        except Exception as e:
            self._log.Error("jujuCA: vnf_configuration error for vnfr {}: {}".
                            format(agent_vnfr.name, e))
            return False

        # Prepare unique name for this VNF
        vnf_unique_name = get_vnf_unique_name(agent_nsr.name,
                                              agent_vnfr.name,
                                              agent_vnfr.member_vnf_index)
        if vnf_unique_name in self._tasks:
            self._log.warn("jujuCA: Service %s already deployed",
                           vnf_unique_name)

        vnfr_dict = agent_vnfr.vnfr
        vnfr_dict.update({'vnf_juju_name': vnf_unique_name,
                          'charm': charm,
                          'nsr_id': agent_nsr.id,
                          'member_vnf_index': agent_vnfr.member_vnf_index,
                          'tags': {},
                          'active': False,
                          'config': vnf_config,
                          'vnfr_name': agent_vnfr.name})
        self._log.debug("jujuCA: Charm %s for vnf %s to be deployed as %s",
                        charm, agent_vnfr.name, vnf_unique_name)

        # Find the charm directory
        try:
            path = os.path.join(self._rift_var_root_dir,
                                'launchpad/packages/vnfd',
                                self._project.name,
                                agent_vnfr.vnfr_msg.vnfd.id,
                                'charms',
                                charm)
            self._log.debug("jujuCA: Charm dir is {}".format(path))
            if not os.path.isdir(path):
                msg = "jujuCA: Did not find the charm directory at {}".format(path)
                self._log.error(msg)
                path = None
                # Return from here instead of forwarding the config request to juju_api
                raise Exception(msg)
        except Exception as e:
            self.log.exception(e)
            return False

        if vnf_unique_name not in self._tasks:
            self._tasks[vnf_unique_name] = {}

        self._log.debug("jujuCA: Deploying service %s",
                        vnf_unique_name)
        yield from self.api.deploy_application(
            charm,
            vnf_unique_name,
            path=path,
        )
        return True

    @asyncio.coroutine
    def notify_instantiate_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of Instantiate NSR with the passed nsr id
        """
        return True

    @asyncio.coroutine
    def notify_instantiate_vlr(self, agent_nsr, agent_vnfr, vlr):
        """
        Notification of Instantiate NSR with the passed nsr id
        """
        return True

    @asyncio.coroutine
    def notify_terminate_nsr(self, agent_nsr, agent_vnfr):
        """
        Notification of Terminate the network service
        """
        return True

    @asyncio.coroutine
    def notify_terminate_vnfr(self, agent_nsr, agent_vnfr):
        """
        Notification of Terminate the network service
        """
        self._log.debug("jujuCA: Terminate VNFr {}, current vnfrs={}".
                        format(agent_vnfr.name, self._juju_vnfs))
        try:
            vnfr = agent_vnfr.vnfr
            service = vnfr['vnf_juju_name']

            self._log.debug("jujuCA: Terminating VNFr {}, {}".format(
                agent_vnfr.name,
                service,
            ))
            yield from self.api.remove_application(service)

            del self._juju_vnfs[agent_vnfr.id]
            self._log.debug("jujuCA: current vnfrs={}".
                            format(self._juju_vnfs))
            if service in self._tasks:
                tasks = []
                for action in self._tasks[service].keys():
                    tasks.append(action)
                del tasks
        except KeyError as e:
            self._log.debug ("jujuCA: Terminating charm service for VNFr {}, e={}".
                             format(agent_vnfr.name, e))
        except Exception as e:
            self._log.error("jujuCA: Exception terminating charm service for VNFR {}: {}".
                            format(agent_vnfr.name, e))

        return True

    @asyncio.coroutine
    def notify_terminate_vlr(self, agent_nsr, agent_vnfr, vlr):
        """
        Notification of Terminate the virtual link
        """
        return True

    @asyncio.coroutine
    def _vnf_config_primitive(self, nsr_id, vnfr_id, primitive,
                              vnf_config=None, wait=False):
        self._log.debug("jujuCA: VNF config primitive {} for nsr {}, "
                        "vnfr_id {}".
                        format(primitive, nsr_id, vnfr_id))

        if vnf_config is None:
            vnfr_msg = yield from self.get_vnfr(vnfr_id)
            if vnfr_msg is None:
                msg = "Unable to get VNFR {} through DTS".format(vnfr_id)
                self._log.error(msg)
                return 3, msg

            vnf_config = vnfr_msg.vnf_configuration
        self._log.debug("VNF config= %s", vnf_config.as_dict())

        try:
            vnfr = self._juju_vnfs[vnfr_id].vnfr
            service = vnfr['vnf_juju_name']
            self._log.debug("VNF config %s", vnf_config)
            configs = vnf_config.config_primitive
            for config in configs:
                if config.name == primitive.name:
                    self._log.debug("jujuCA: Found the config primitive %s",
                                    config.name)
                    params = {}
                    for parameter in config.parameter:
                        val = None
                        for p in primitive.parameter:
                            if p.name == parameter.name:
                                if p.value:
                                    val = self.xlate(p.value, vnfr['tags'])
                                break

                        if val is None:
                            val = parameter.default_value

                        if val is None:
                            # Check if mandatory parameter
                            if parameter.mandatory:
                                msg = "VNFR {}: Primitive {} called " \
                                      "without mandatory parameter {}". \
                                      format(vnfr_msg.name, config.name,
                                             parameter.name)
                                self._log.error(msg)
                                return 'failed', '', msg

                        if val:
                            val = self.convert_value(val, parameter.data_type)
                            params.update({parameter.name: val})

                    rc = ''
                    exec_id = ''
                    details = ''
                    if config.name == 'config':
                        exec_id = 'config'
                        if len(params):
                            self._log.debug("jujuCA: applying config with "
                                            "params {} for service {}".
                                            format(params, service))

                            rc = yield from self.api.apply_config(params, application=service)

                            if rc:
                                rc = "completed"
                                self._log.debug("jujuCA: applied config {} "
                                                "on {}".format(params, service))
                            else:
                                rc = 'failed'
                                details = \
                                    'Failed to apply config: {}'.format(params)
                                self._log.error("jujuCA: Error applying "
                                                "config {} on service {}".
                                                format(params, service))
                        else:
                            self._log.warn("jujuCA: Did not find valid "
                                           "parameters for config : {}".
                                           format(primitive.parameter))
                            rc = "completed"
                    else:
                        self._log.debug("jujuCA: Execute action {} on "
                                        "service {} with params {}".
                                        format(config.name, service, params))

                        resp = yield from self.api.execute_action(
                            service,
                            config.name,
                            **params,
                        )

                        if resp:
                            if 'error' in resp:
                                details = resp['error']['message']
                            else:
                                exec_id = resp['action']['tag']
                                rc = resp['status']
                                if rc == 'failed':
                                    details = resp['message']

                            self._log.debug("jujuCA: execute action {} on "
                                            "service {} returned {}".
                                            format(config.name, service, rc))
                        else:
                            self._log.error("jujuCA: error executing action "
                                            "{} for {} with {}".
                                            format(config.name, service,
                                                   params))
                            exec_id = ''
                            rc = 'failed'
                            details = "Failed to queue the action"
                    break

        except KeyError as e:
            msg = "VNF %s does not have config primitives, e=%s", \
                  vnfr_id, e
            self._log.exception(msg)
            raise ValueError(msg)

        while wait and (rc in ['pending', 'running']):
            self._log.debug("JujuCA: action {}, rc {}".
                            format(exec_id, rc))
            yield from asyncio.sleep(0.2, loop=self._loop)
            status = yield from self.api.get_action_status(exec_id)
            rc = status['status']

        return rc, exec_id, details

    @asyncio.coroutine
    def vnf_config_primitive(self, nsr_id, vnfr_id, primitive, output):
        try:
            vnfr = self._juju_vnfs[vnfr_id].vnfr
        except KeyError:
            msg = "Did not find VNFR {} in Juju plugin".format(vnfr_id)
            self._log.debug(msg)
            return

        output.execution_status = "failed"
        output.execution_id = ''
        output.execution_error_details = ''

        rc, exec_id, err = yield from self._vnf_config_primitive(
            nsr_id,
            vnfr_id,
            primitive)

        self._log.debug("VNFR {} primitive {} exec status: {}".
                        format(vnfr_id, primitive.name, rc))
        output.execution_status = rc
        output.execution_id = exec_id
        output.execution_error_details = err

    @asyncio.coroutine
    def apply_config(self, agent_nsr, agent_vnfr, config, rpc_ip):
        """ Notification on configuration of an NSR """
        pass

    @asyncio.coroutine
    def apply_ns_config(self, agent_nsr, agent_vnfrs, rpc_ip):
        """

        ###### TBD - This really does not belong here. Looks more like NS level script ####
        ###### apply_config should be called for a particular VNF only here ###############

        Hook: Runs the user defined script. Feeds all the necessary data
        for the script thro' yaml file.

        Args:
            rpc_ip (YangInput_Nsr_ExecNsConfigPrimitive): The input data.
            nsr (NetworkServiceRecord): Description
            vnfrs (dict): VNFR ID => VirtualNetworkFunctionRecord

        """
        def get_meta(agent_nsr):
            unit_names, initial_params, vnfr_index_map = {}, {}, {}

            for vnfr_id in agent_nsr.vnfr_ids:
                juju_vnf = self._juju_vnfs[vnfr_id].vnfr

                # Vnfr -> index ref
                vnfr_index_map[vnfr_id] = juju_vnf['member_vnf_index']

                # Unit name
                unit_names[vnfr_id] = juju_vnf['vnf_juju_name']

                # Flatten the data for simplicity
                param_data = {}
                self._log.debug("Juju Config:%s", juju_vnf['config'])
                for primitive in juju_vnf['config'].initial_config_primitive:
                    for parameter in primitive.parameter:
                        value = self.xlate(parameter.value, juju_vnf['tags'])
                        param_data[parameter.name] = value

                initial_params[vnfr_id] = param_data


            return unit_names, initial_params, vnfr_index_map

        unit_names, init_data, vnfr_index_map = get_meta(agent_nsr)

        # The data consists of 4 sections
        # 1. Account data
        # 2. The input passed.
        # 3. Juju unit names (keyed by vnfr ID).
        # 4. Initial config data (keyed by vnfr ID).
        data = dict()
        data['config_agent'] = dict(
                name=self._name,
                host=self._ip_address,
                port=self._port,
                user=self._user,
                secret=self._secret
                )
        data["rpc_ip"] = rpc_ip.as_dict()
        data["unit_names"] = unit_names
        data["init_config"] = init_data
        data["vnfr_index_map"] = vnfr_index_map

        tmp_file = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data, default_flow_style=True)
                    .encode("UTF-8"))

        self._log.debug("jujuCA: Creating a temp file: {} with input data".format(
                tmp_file.name))

        # Get the full path to the script
        script = ''
        if rpc_ip.user_defined_script[0] == '/':
            # The script has full path, use as is
            script = rpc_ip.user_defined_script
        else:
            script = os.path.join(self._rift_var_root_dir, 'launchpad/nsd',
                                  self._project.name,
                                  agent_nsr.id, 'scripts',
                                  rpc_ip.user_defined_script)
            self.log.debug("jujuCA: Checking for script in %s", script)
            if not os.path.exists(script):
                script = os.path.join(self._rift_install_dir, 'usr/bin', rpc_ip.user_defined_script)

        cmd = "{} {}".format(rpc_ip.user_defined_script, tmp_file.name)
        self._log.debug("jujuCA: Running the CMD: {}".format(cmd))

        coro = asyncio.create_subprocess_shell(cmd, loop=self._loop,
                                               stderr=asyncio.subprocess.PIPE)
        process = yield from coro
        err = yield from process.stderr.read()
        task = self._loop.create_task(process.wait())

        return task, err

    @asyncio.coroutine
    def apply_initial_config(self, agent_nsr, agent_vnfr):
        """
        Apply the initial configuration
        Expect config directives mostly, not actions
        Actions in initial config may not work based on charm design
        """

        try:
            vnfr = self._juju_vnfs[agent_vnfr.id].vnfr
            service = vnfr['vnf_juju_name']
        except KeyError:
            self._log.debug("Did not find VNFR %s in Juju plugin",
                            agent_vnfr.name)
            return False

        vnfr_msg = yield from self.get_vnfr(agent_vnfr.id)
        if vnfr_msg is None:
            msg = "Unable to get VNFR {} ({}) through DTS". \
                  format(agent_vnfr.id, agent_vnfr.name)
            self._log.error(msg)
            raise RuntimeError(msg)

        vnf_config = vnfr_msg.vnf_configuration
        self._log.debug("VNFR %s config: %s", vnfr_msg.name,
                        vnf_config.as_dict())

        # Sort the primitive based on the sequence number
        primitives = sorted(vnf_config.initial_config_primitive,
                            key=lambda k: k.seq)
        if not primitives:
            self._log.debug("VNFR {}: No initial-config-primitive specified".
                            format(vnfr_msg.name))
            return True

        rc = yield from self.api.is_application_up(application=service)
        if not rc:
            return False

        try:
            if vnfr_msg.mgmt_interface.ip_address:
                vnfr['tags'].update({'rw_mgmt_ip': vnfr_msg.mgmt_interface.ip_address})
                self._log.debug("jujuCA:(%s) tags: %s", vnfr['vnf_juju_name'], vnfr['tags'])

            for primitive in primitives:
                self._log.debug("(%s) Initial config primitive %s",
                                vnfr['vnf_juju_name'], primitive.as_dict())
                if primitive.config_primitive_ref:
                    # Reference to a primitive in config primitive
                    class Primitive:
                        def __init__(self, name):
                            self.name = name
                            self.value = None
                            self.parameter = []

                    prim = Primitive(primitive.config_primitive_ref)
                    rc, eid, err = yield from self._vnf_config_primitive(
                        agent_nsr.id,
                        agent_vnfr.id,
                        prim,
                        vnf_config,
                        wait=True)

                    if rc == "failed":
                        msg = "Error executing initial config primitive" \
                              " {} in VNFR {}: rc={}, stderr={}". \
                              format(prim.name, vnfr_msg.name, rc, err)
                        self._log.error(msg)
                        return False

                elif primitive.name:
                    config = {}
                    if primitive.name == 'config':
                        for param in primitive.parameter:
                            if vnfr['tags']:
                                val = self.xlate(param.value,
                                                 vnfr['tags'])
                                config.update({param.name: val})

                        if config:
                            self.juju_log('info', vnfr['vnf_juju_name'],
                                          "Applying Initial config:%s",
                                          config)

                            rc = yield from self.api.apply_config(
                                config,
                                application=service,
                            )
                            if rc is False:
                                self.log.error("Service {} is in error state".format(service))
                                return False
                    else:
                        # Apply any actions specified as part of initial config
                        for primitive in vnfr['config'].initial_config_primitive:
                            if primitive.name != 'config':
                                self._log.debug("jujuCA:(%s) Initial config action primitive %s",
                                                vnfr['vnf_juju_name'], primitive)
                                action = primitive.name
                                params = {}
                                for param in primitive.parameter:
                                    val = self.xlate(param.value, vnfr['tags'])
                                    params.update({param.name: val})

                                self._log.info("jujuCA:(%s) Action %s with params %s",
                                               vnfr['vnf_juju_name'], action, params)
                                self._log.debug("executing action")
                                resp = yield from self.api.execute_action(
                                    service,
                                    action,
                                    **params,
                                )
                                self._log.debug("executed action")
                                if 'error' in resp:
                                    self._log.error("Applying initial config on {} failed for {} with {}: {}".
                                                    format(vnfr['vnf_juju_name'], action, params, resp))
                                    return False
        except KeyError as e:
            self._log.info("Juju config agent(%s): VNFR %s not managed by Juju",
                           vnfr['vnf_juju_name'], agent_vnfr.id)
            return False
        except Exception as e:
            self._log.exception("jujuCA:(%s) Exception juju "
                                "apply_initial_config for VNFR {}: {}".
                                format(vnfr['vnf_juju_name'],
                                       agent_vnfr.id, e))
            return False

        return True

    def add_vnfr_managed(self, agent_vnfr):
        if agent_vnfr.id not in self._juju_vnfs.keys():
            self._log.info("juju config agent: add vnfr={}/{}".
                           format(agent_vnfr.name, agent_vnfr.id))
            self._juju_vnfs[agent_vnfr.id] = agent_vnfr

    def is_vnfr_managed(self, vnfr_id):
        try:
            if vnfr_id in self._juju_vnfs:
                return True
        except Exception as e:
            self._log.debug("jujuCA: Is VNFR {} managed: {}".
                            format(vnfr_id, e))
        return False

    @asyncio.coroutine
    def is_configured(self, vnfr_id):
        try:
            agent_vnfr = self._juju_vnfs[vnfr_id]
            vnfr = agent_vnfr.vnfr
            if vnfr['active']:
                return True

            vnfr = self._juju_vnfs[vnfr_id].vnfr
            service = vnfr['vnf_juju_name']
            resp = self.api.is_application_active(application=service)
            self._juju_vnfs[vnfr_id]['active'] = resp
            self._log.debug("jujuCA: Service state for {} is {}".
                            format(service, resp))
            return resp

        except KeyError:
            self._log.debug("jujuCA: VNFR id {} not found in config agent".
                            format(vnfr_id))
            return False
        except Exception as e:
            self._log.error("jujuCA: VNFR id {} is_configured: {}".
                            format(vnfr_id, e))
        return False

    @asyncio.coroutine
    def get_config_status(self, agent_nsr, agent_vnfr):
        """Get the configuration status for the VNF"""
        rc = 'unknown'

        try:
            vnfr = agent_vnfr.vnfr
            service = vnfr['vnf_juju_name']
        except KeyError:
            # This VNF is not managed by Juju
            return rc

        rc = 'configuring'

        try:
            # Get the status of the application
            resp = yield from self.api.get_application_status(service)

            # No status means the application is still pending deployment
            if resp is None:
                return rc

            if resp == 'error':
                return 'error'
            if resp == 'active':
                return 'configured'
        except KeyError:
            self._log.error("jujuCA: Check unknown service %s status", service)
        except Exception as e:
            self._log.error("jujuCA: Caught exception when checking for service is active: %s", e)
            self._log.exception(e)

        return rc

    def get_action_status(self, execution_id):
        ''' Get the action status for an execution ID
            *** Make sure this is NOT a asyncio coroutine function ***
        '''

        try:
            self._log.debug("jujuCA: Get action status for {}".format(execution_id))
            resp = self.api._get_action_status(execution_id)
            self._log.debug("jujuCA: Action status: {}".format(resp))
            return resp
        except Exception as e:
            self._log.error("jujuCA: Error fetching execution status for %s",
                            execution_id)
            self._log.exception(e)
            raise e

    def get_service_status(self, vnfr_id):
        '''Get the service status, used by job status handle
           Make sure this is NOT a coroutine
        '''
        service = self.get_service_name(vnfr_id)
        if service is None:
            self._log.error("jujuCA: VNFR {} not managed by this Juju agent".
                            format(vnfr_id))
            return None

        # Delay for 3 seconds before checking as config apply takes a
        # few seconds to transfer to the service
        time.sleep(3)
        return self.api._get_service_status(service=service)
