
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
import stat
import subprocess
import sys
import tempfile
import yaml

from gi.repository import (
    RwDts as rwdts,
    RwConmanYang as conmanY,
    ProtobufC,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.tasklets
import rift.package.script
import rift.package.store

from . import rwconman_conagent as conagent
from . import RiftCM_rpc
from . import riftcm_config_plugin


if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async

def get_vnf_unique_name(nsr_name, vnfr_name, member_vnf_index):
    return "{}.{}.{}".format(nsr_name, vnfr_name, member_vnf_index)


class ConmanConfigError(Exception):
    pass


class InitialConfigError(ConmanConfigError):
    pass


class ScriptNotFoundError(InitialConfigError):
    pass


def log_this_vnf(vnf_cfg):
    log_vnf = ""
    used_item_list = ['nsr_name', 'vnfr_name', 'member_vnf_index', 'mgmt_ip_address']
    for item in used_item_list:
        if item in vnf_cfg:
            if item == 'mgmt_ip_address':
                log_vnf += "({})".format(vnf_cfg[item])
            else:
                log_vnf += "{}/".format(vnf_cfg[item])
    return log_vnf

class PretendNsm(object):
    def __init__(self, dts, log, loop, parent):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._parent = parent
        self._nsrs = {}
        self._nsr_dict = parent._nsr_dict
        self._config_agent_plugins = []
        self._nsd_msg = {}

    @property
    def nsrs(self):
        # Expensive, instead use get_nsr, if you know id.
        self._nsrs = {}
        # Update the list of nsrs (agent nsr)
        for id, nsr_obj in self._nsr_dict.items():
            self._nsrs[id] = nsr_obj.agent_nsr
        return self._nsrs

    def get_nsr(self, nsr_id):
        if nsr_id in self._nsr_dict:
            nsr_obj = self._nsr_dict[nsr_id]
            return nsr_obj._nsr
        return None

    def get_vnfr_msg(self, vnfr_id, nsr_id=None):
        self._log.debug("get_vnfr_msg(vnfr=%s, nsr=%s)",
                        vnfr_id, nsr_id)
        found = False
        if nsr_id:
            if nsr_id in self._nsr_dict:
                nsr_obj = self._nsr_dict[nsr_id]
                if vnfr_id in nsr_obj._vnfr_dict:
                    found = True
        else:
            for nsr_obj in self._nsr_dict.values():
                if vnfr_id in nsr_obj._vnfr_dict:
                    # Found it
                    found = True
                    break
        if found:
            vnf_cfg = nsr_obj._vnfr_dict[vnfr_id]['vnf_cfg']
            return vnf_cfg['agent_vnfr'].vnfr_msg
        else:
            return None

    @asyncio.coroutine
    def get_nsd(self, nsr_id):
        if nsr_id not in self._nsd_msg:
            nsr_config = yield from self._parent.cmdts_obj.get_nsr_config(nsr_id)
            self._nsd_msg[nsr_id] = nsr_config.nsd
        return self._nsd_msg[nsr_id]

    @property
    def config_agent_plugins(self):
        self._config_agent_plugins = []
        for agent in self._parent._config_agent_mgr._plugin_instances.values():
            self._config_agent_plugins.append(agent)
        return self._config_agent_plugins

class ConfigManagerConfig(object):
    def __init__(self, dts, log, loop, parent):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._parent = parent
        self._project = parent._project

        self._nsr_dict = {}
        self.pending_cfg = {}
        self.terminate_cfg = {}
        self.pending_tasks = [] # User for NSRid get retry
                                # (mainly excercised at restart case)

        self._opdata_xpath = self._project.add_project("D,/rw-conman:cm-state")

        # Initialize cm-state
        self.cm_state = {}
        self.cm_state['cm_nsr'] = []
        self.cm_state['states'] = "Initialized"

        # Initialize objects to register
        self.cmdts_obj = ConfigManagerDTS(self._log, self._loop, self, self._dts, self._project)
        self._config_agent_mgr = conagent.RiftCMConfigAgent(
            self._dts,
            self._log,
            self._loop,
            self,
        )

        self.riftcm_rpc_handler = RiftCM_rpc.RiftCMRPCHandler(self._dts, self._log, self._loop, self._project,
                                        PretendNsm(
                                            self._dts, self._log, self._loop, self))

        self.reg_handles = [
            self.cmdts_obj,
            self._config_agent_mgr,
            self.riftcm_rpc_handler
        ]
        self._op_reg = None

    def is_nsr_valid(self, nsr_id):
        if nsr_id in self._nsr_dict:
            return True
        return False

    def add_to_pending_tasks(self, task):
        if self.pending_tasks:
            for p_task in self.pending_tasks:
                if (p_task['nsrid'] == task['nsrid']) and \
                   (p_task['event'] == task['event']):
                    # Already queued
                    return
        try:
            self.pending_tasks.append(task)
            self._log.debug("add_to_pending_tasks (nsrid:%s)",
                            task['nsrid'])
            if len(self.pending_tasks) >= 1:
                self._loop.create_task(self.ConfigManagerConfig_pending_loop())
                # TBD - change to info level
                self._log.debug("Started pending_loop!")

        except Exception as e:
            self._log.error("Failed adding to pending tasks (%s)", str(e))

    def del_from_pending_tasks(self, task):
        try:
            self.pending_tasks.remove(task)
        except Exception as e:
            self._log.error("Failed removing from pending tasks (%s)", str(e))

    @asyncio.coroutine
    def ConfigManagerConfig_pending_loop(self):
        loop_sleep = 2
        while True:
            yield from asyncio.sleep(loop_sleep, loop=self._loop)
            """
            This pending task queue is ordred by events,
            must finish previous task successfully to be able to go on to the next task
            """
            if self.pending_tasks:
                self._log.debug("self.pending_tasks len=%s", len(self.pending_tasks))
                task = self.pending_tasks.pop(0)
                done = False
                if 'nsrid' in task:
                    nsrid = task['nsrid']
                    self._log.debug("Will execute pending task for NSR id: %s", nsrid)
                    try:
                        # Try to configure this NSR
                        task['retries'] -= 1
                        done = yield from self.config_NSR(nsrid, task['event'])
                        self._log.info("self.config_NSR status=%s", done)

                    except Exception as e:
                        self._log.error("Failed(%s) configuring NSR(%s) for task %s," \
                                        "retries remained:%d!",
                                        str(e), nsrid, task['event'] , task['retries'])
                        self._log.exception(e)
                        if task['event'] == 'terminate':
                            # Ignore failure
                            done = True

                    if done:
                        self._log.debug("Finished pending task NSR id: %s", nsrid)
                    else:
                        self._log.error("Failed configuring NSR(%s), retries remained:%d!",
                                        nsrid, task['retries'])

                        # Failed, re-insert (append at the end)
                        # this failed task to be retried later
                        # If any retries remained.
                        if task['retries']:
                            self.pending_tasks.append(task)
            else:
                self._log.debug("Stopped pending_loop!")
                break

    @asyncio.coroutine
    def register(self):
        yield from self.register_cm_state_opdata()

        # Initialize all handles that needs to be registered
        for reg in self.reg_handles:
            yield from reg.register()

    def deregister(self):
        # De-register all reg handles
        self._log.debug("De-register ConfigManagerConfig for project {}".
                        format(self._project))

        for reg in self.reg_handles:
            reg.deregister()
            reg = None

        self._op_reg.delete_element(self._opdata_xpath)
        self._op_reg.deregister()

    @asyncio.coroutine
    def register_cm_state_opdata(self):

        def state_to_string(state):
            state_dict = {
                conmanY.RecordState.INIT : "init",
                conmanY.RecordState.RECEIVED : "received",
                conmanY.RecordState.CFG_PROCESS : "cfg_process",
                conmanY.RecordState.CFG_PROCESS_FAILED : "cfg_process_failed",
                conmanY.RecordState.CFG_SCHED : "cfg_sched",
                conmanY.RecordState.CONNECTING : "connecting",
                conmanY.RecordState.FAILED_CONNECTION : "failed_connection",
                conmanY.RecordState.CFG_SEND : "cfg_send",
                conmanY.RecordState.CFG_FAILED : "cfg_failed",
                conmanY.RecordState.READY_NO_CFG : "ready_no_cfg",
                conmanY.RecordState.READY : "ready",
                conmanY.RecordState.TERMINATE : "terminate",
                }
            return state_dict[state]

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):

            self._log.debug("Received cm-state: msg=%s, action=%s", msg, action)

            if action == rwdts.QueryAction.READ:
                self._log.debug("Responding to SHOW cm-state: %s", self.cm_state)
                show_output = conmanY.YangData_RwProject_Project_CmState()
                show_output.from_dict(self.cm_state)
                xact_info.respond_xpath(rwdts.XactRspCode.ACK,
                                        xpath=self._opdata_xpath,
                                        msg=show_output)
            else:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._log.info("Registering for cm-opdata xpath: %s",
                        self._opdata_xpath)

        try:
            handler=rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare)
            self._op_reg = yield from self._dts.register(xpath=self._opdata_xpath,
                                                         handler=handler,
                                                         flags=rwdts.Flag.PUBLISHER)
            self._log.info("Successfully registered for opdata(%s)", self._opdata_xpath)
        except Exception as e:
            self._log.error("Failed to register for opdata as (%s)", e)
   
    def get_config_method(self, vnf_config):
          cfg_types = ['juju', 'script']
          for method in cfg_types:
              if method in vnf_config:
                  return method
          return None

    @asyncio.coroutine
    def process_nsd_vnf_configuration(self, nsr_obj, vnfr):

        # Get vnf_configuration from vnfr
        vnf_config = vnfr['vnf_configuration']

        # Save some parameters needed as short cuts in flat structure (Also generated)
        vnf_cfg = vnfr['vnf_cfg']
        # Prepare unique name for this VNF
        vnf_cfg['vnf_unique_name'] = get_vnf_unique_name(
            vnf_cfg['nsr_name'], vnfr['name'], vnfr['member_vnf_index_ref'])

        self._log.debug("vnf_configuration = %s", vnf_config)

        method = self.get_config_method(vnf_config)

        if method is not None:
            self._log.debug("config method=%s", method)
            vnf_cfg['config_method'] = method

            # Set config agent based on method
            self._config_agent_mgr.set_config_agent(
                  nsr_obj.agent_nsr, vnf_cfg['agent_vnfr'], method)
        else:
            self._log.info("VNF:(%s) is not to be configured by Configuration Manager!",
                             log_this_vnf(vnfr['vnf_cfg']))
            yield from nsr_obj.update_vnf_cm_state(vnfr, conmanY.RecordState.READY_NO_CFG)

        # Update the cm-state
        nsr_obj.populate_cm_state_from_vnf_cfg()

    @asyncio.coroutine
    def update_config_primitives(self, nsr_obj):

         # Process all config-primitives in the member VNFs
        for vnfr in nsr_obj.vnfrs:
            vnfd = vnfr['vnf_cfg']['agent_vnfr'].vnfd

            try:
                prims = vnfd.vnf_configuration.config_primitive
                if not prims:
                    self._log.debug("VNFR {} with VNFD {} has no config primitives defined".
                                    format(vnfr['name'], vnfd.name))
                    return
            except AttributeError as e:
                self._log.error("No config primitives found on VNFR {} ({})".
                                format(vnfr['name'], vnfd.name))
                continue

            cm_state = nsr_obj.find_vnfr_cm_state(vnfr['id'])
            srcs = cm_state['config_parameter']['config_parameter_source']
            reqs = cm_state['config_parameter']['config_parameter_request']

            vnf_configuration = vnfd.vnf_configuration.as_dict()
            vnf_configuration['config_primitive'] = []
            
            for prim in prims:
                confp = prim.as_dict()
                if 'parameter' not in confp:
                    continue

                for param in confp['parameter']:
                    # First check the param in capabilities
                    found = False
                    for src in srcs:
                        for p in src['parameter']:
                            if (p['config_primitive_ref'] == confp['name']) \
                               and (p['parameter_ref'] == param['name']):
                                param['default_value'] = src['value']
                                found = True
                                break
                        if found:
                            break

                    if not found:
                        for req in reqs:
                            for p in req['parameter']:
                                if (p['config_primitive_ref'] == confp['name']) \
                                   and (p['parameter_ref'] == param['name']):
                                    param['default_value'] = req['value']
                                    found = True
                                    break
                            if found:
                                break

                self._log.debug("Config primitive: {}".format(confp))
                vnf_configuration['config_primitive'].append(confp)

            cm_state['vnf_configuration'] = vnf_configuration

    @asyncio.coroutine
    def get_resolved_xpath(self, xpath, name, vnf_name, xpath_prefix):
        # For now, use DTS to resolve the path
        # TODO (pjoseph): Add better xpath support

        dts_path = xpath
        if xpath.startswith('../'):
            prefix = xpath_prefix
            xp = xpath
            while xp.startswith('../'):
                idx = prefix.rfind('/')
                if idx == -1:
                    raise ValueError("VNF {}, Did not find the xpath specified: {}".
                                     format(vnf_name, xpath))
                prefix = prefix[:idx]
                xp = xp[3:]

            dts_path = prefix + '/' + xp

        elif xpath.startswith('/'):
            dts_path = 'C,' + xpath
        elif xpath.startswith('C,/') or xpath.startswith('D,/'):
            dts_path = xpath
        else:
            self._log.error("Invalid xpath {} for source {} in VNF {}".
                            format(xpath, name, vnf_name))
            raise ValueError("Descriptor xpath {} in source {} for VNF {} "
                             "is invalid".
                             format(xpath, name, vnf_name))

        dts_path = self._project.add_project(dts_path)
        return dts_path

    @asyncio.coroutine
    def resolve_xpath(self, xpath, name, vnfd):
        xpath_prefix = "C,/project-vnfd:vnfd-catalog/vnfd[id={}]/config-parameter" \
                "/config-parameter-source[name={}]" \
                "/descriptor".format(quoted_key(vnfd.id), quoted_key(name))

        dts_path = yield from self.get_resolved_xpath(xpath, name,
                                                      vnfd.name, xpath_prefix)
        idx = dts_path.rfind('/')
        if idx == -1:
            raise ValueError("VNFD {}, descriptor xpath {} should point to " \
                             "an attribute".format(vnfd.name, xpath))

        attr = dts_path[idx+1:]
        dts_path = dts_path[:idx]
        self._log.debug("DTS path: {}, attribute: {}".format(dts_path, attr))

        resp = yield from self.cmdts_obj.get_xpath(dts_path)
        if resp is None:
            raise ValueError("Xpath {} in capability {} for VNFD {} is not found".
                             format(xpath, name, vnfd.name))
        self._log.debug("DTS response: {}".format(resp.as_dict()))

        try:
            val = getattr(resp, attr)
        except AttributeError as e:
            self._log.error("Did not find attribute : {}".format(attr))
            try:
                val = getattr(resp, attr.replace('-', '_'))
            except AttributeError as e:
                raise ValueError("Did not find attribute {} in XPath {} "
                                 "for capability {} in VNF {}".
                                 format(attr, dts_path, vnfd.name))

        self._log.debug("XPath {}: {}".format(xpath, val))
        return val

    @asyncio.coroutine
    def resolve_attribute(self, attribute, name, vnfd, vnfr):
        idx = attribute.rfind(',')
        if idx == -1:
            raise ValueError ("Invalid attribute {} for capability {} in "
                              "VNFD specified".
                              format(attribute, name, vnfd.name))
        xpath = attribute[:idx].strip()
        attr = attribute[idx+1:].strip()
        self._log.debug("Attribute {}, {}".format(xpath, attr))
        if xpath.startswith('C,/'):
            raise ValueError("Attribute {} for capability {} in VNFD cannot "
                             "be a config".
                             format(attribute, name, vnfd.name))

        xpath_prefix = "D,/vnfr:vnfr-catalog/vnfr[id={}]/config_parameter" \
                "/config-parameter-source[name={}]" \
                "/attribute".format(quoted_key(vnfr['id']), quoted_key(name))
        dts_path = yield from self.get_resolved_xpath(xpath, name,
                                                      vnfr['name'],
                                                      xpath_prefix)
        self._log.debug("DTS query: {}".format(dts_path))

        resp = yield from self.cmdts_obj.get_xpath(dts_path)
        if resp is None:
            raise ValueError("Attribute {} in request {} for VNFD {} is " \
                             "not found".
                             format(xpath, name, vnfd.name))
        self._log.debug("DTS response: {}".format(resp.as_dict()))

        try:
            val = getattr(resp, attr)
        except AttributeError as e:
            self._log.debug("Did not find attribute {}".format(attr))
            try:
                val = getattr(resp, attr.replace('-', '_'))
            except AttributeError as e:
                raise ValueError("Did not find attribute {} in XPath {} "
                                 "for source {} in VNF {}".
                                 format(attr, dts_path, vnfd.name))

        self._log.debug("Attribute {}: {}".format(attribute, val))
        return val

    @asyncio.coroutine
    def process_vnf_config_parameter(self, nsr_obj):
        nsd = nsr_obj.agent_nsr.nsd

        # Process all capabilities in all the member VNFs
        for vnfr in nsr_obj.vnfrs:
            vnfd = vnfr['vnf_cfg']['agent_vnfr'].vnfd

            try:
                cparam = vnfd.config_parameter
            except AttributeError as e:
                self._log.debug("VNFR {} does not have VNF config parameter".
                                format(vnfr.name))
                continue

            srcs = []
            try:
                srcs = cparam.config_parameter_source
            except AttributeError as e:
                self._log.debug("VNFR {} has no source defined".
                                format(vnfr.name))

            # Get the cm state dict for this vnfr
            cm_state = nsr_obj.find_vnfr_cm_state(vnfr['id'])

            cm_srcs = []
            for src in srcs:
                self._log.debug("VNFR {}: source {}".
                                format(vnfr['name'], src.as_dict()))

                param_refs = []
                for p in src.parameter:
                    param_refs.append({
                        'config_primitive_ref': p.config_primitive_name_ref,
                        'parameter_ref': p.config_primitive_parameter_ref
                    })

                try:
                    val = src.value
                    self._log.debug("Got value {}".format(val))
                    if val:
                        cm_srcs.append({'name': src.name,
                                        'value': str(val),
                                        'parameter': param_refs})
                        continue
                except AttributeError as e:
                    pass

                try:
                    xpath = src.descriptor
                    # resolve xpath
                    if xpath:
                        val = yield from self.resolve_xpath(xpath, src.name, vnfd)
                        self._log.debug("Got xpath value: {}".format(val))
                        cm_srcs.append({'name': src.name,
                                        'value': str(val),
                                        'parameter': param_refs})
                        continue
                except AttributeError as e:
                    pass

                try:
                    attribute = src.attribute
                    # resolve attribute
                    if attribute:
                        val = yield from self.resolve_attribute(attribute,
                                                                src.name,
                                                                vnfd, vnfr)
                        self._log.debug("Got attribute value: {}".format(val))
                        cm_srcs.append({'name': src.name,
                                        'value': str(val),
                                        'parameter': param_refs})
                        continue
                except AttributeError as e:
                    pass

                try:
                    prim = src.primitive_ref
                    if prim:
                        raise NotImplementedError("{}: VNF config parameter {}"
                                                  "source support for config"
                                                  "primitive not yet supported".
                                                  format(vnfr.name, prim))
                except AttributeError as e:
                    pass

            self._log.debug("VNF config parameter sources: {}".format(cm_srcs))
            cm_state['config_parameter']['config_parameter_source'] = cm_srcs

            try:
                reqs = cparam.config_parameter_request
            except AttributeError as e:
                self._log.debug("VNFR {} has no requests defined".
                                format(vnfr.name))
                continue

            cm_reqs = []
            for req in reqs:
                self._log.debug("VNFR{}: request {}".
                                format(vnfr['name'], req.as_dict()))
                param_refs = []
                for p in req.parameter:
                    param_refs.append({
                        'config_primitive_ref': p.config_primitive_name_ref,
                        'parameter_ref': p.config_primitive_parameter_ref
                    })
                cm_reqs.append({'name': req.name,
                                'parameter': param_refs})

            self._log.debug("VNF requests: {}".format(cm_reqs))
            cm_state['config_parameter']['config_parameter_request'] = cm_reqs

        # Publish all config parameter for the VNFRs
        # yield from nsr_obj.publish_cm_state()

        cparam_map = []
        try:
            cparam_map = nsd.config_parameter_map
        except AttributeError as e:
            self._log.warning("No config parameter map specified for nsr: {}".
                            format(nsr_obj.nsr_name))

        for cp in cparam_map:
            src_vnfr = nsr_obj.agent_nsr.get_member_vnfr(
                cp.config_parameter_source.member_vnf_index_ref)
            cm_state = nsr_obj.find_vnfr_cm_state(src_vnfr.id)
            if cm_state is None:
                raise ValueError("Config parameter sources are not defined "
                        "for VNF member {} ({})".
                        format(cp.config_parameter_source.member_vnf_index_ref,
                               src_vnfr.name))
            srcs = cm_state['config_parameter']['config_parameter_source']

            src_attr = cp.config_parameter_source.config_parameter_source_ref
            val = None
            for src in srcs:
                if src['name'] == src_attr:
                    val = src['value']
                    break

            req_vnfr = nsr_obj.agent_nsr.get_member_vnfr(
                cp.config_parameter_request.member_vnf_index_ref)
            req_attr = cp.config_parameter_request.config_parameter_request_ref
            cm_state = nsr_obj.find_vnfr_cm_state(req_vnfr.id)
            try:
                cm_reqs = cm_state['config_parameter']['config_parameter_request']
            except KeyError as e:
                raise ValueError("VNFR index {} ({}) has no requests defined".
                        format(cp.config_parameter_reequest.member_vnf_index_ref,
                               req_vnfr['name']))

            for i, item in enumerate(cm_reqs):
                if item['name'] == req_attr:
                    item['value'] = str(val)
                    cm_reqs[i] = item
                    self._log.debug("Request in VNFR {}: {}".
                                    format(req_vnfr.name, item))
                    break

        yield from self.update_config_primitives(nsr_obj)

        # TODO: Confd crashing with the config-parameter publish
        # So removing config-parameter and publishing cm-state
        for vnfr in nsr_obj.vnfrs:
            # Get the cm state dict for this vnfr
            cm_state = nsr_obj.find_vnfr_cm_state(vnfr['id'])
            del cm_state['config_parameter']['config_parameter_source']
            del cm_state['config_parameter']['config_parameter_request']

        # Publish resolved dependencies for the VNFRs
        yield from nsr_obj.publish_cm_state()

    @asyncio.coroutine
    def config_NSR(self, id, event):

        cmdts_obj = self.cmdts_obj
        if event == 'running':
            self._log.info("Configure NSR running, id = %s", id)
            try:
                nsr_obj = None
                try:
                    if id not in self._nsr_dict:
                        nsr_obj = ConfigManagerNSR(self._log, self._loop, self, self._project, id)
                        self._nsr_dict[id] = nsr_obj
                    else:
                        self._log.info("NSR(%s) is already initialized!", id)
                        nsr_obj = self._nsr_dict[id]

                except Exception as e:
                    self._log.error("Failed creating NSR object for (%s) as (%s)", id, str(e))
                    raise e

                # Try to configure this NSR only if not already processed
                if nsr_obj.cm_nsr['state'] != nsr_obj.state_to_string(conmanY.RecordState.INIT):
                    self._log.debug("NSR(%s) is already processed, state=%s",
                                    nsr_obj.nsr_name, nsr_obj.cm_nsr['state'])
                    # Publish again in case NSM restarted
                    yield from nsr_obj.publish_cm_state()
                    return True

                # Fetch NSR
                nsr = yield from cmdts_obj.get_nsr(id)
                self._log.debug("Full NSR : %s", nsr)
                if nsr['operational_status'] != "running":
                    self._log.info("NSR(%s) is not ready yet!", nsr['nsd_name_ref'])
                    return False
                self._nsr = nsr

                # Create Agent NSR class
                nsr_config = yield from cmdts_obj.get_nsr_config(id)
                self._log.debug("NSR {} config: {}".format(id, nsr_config))

                if nsr_config is None:
                    # The NST Terminate has been initiated before the configuration. Hence 
                    # not proceeding with config.
                    self._log.warning("NSR - %s is deleted before Configuration. Not proceeding with configuration.", id)
                    return True

                nsr_obj.agent_nsr = riftcm_config_plugin.RiftCMnsr(nsr, nsr_config,
                                                                   self._project)

                unique_cfg_vnfr_list = list()
                unique_agent_vnfr_list = list()
                try:
                    yield from nsr_obj.update_ns_cm_state(conmanY.RecordState.RECEIVED)

                    nsr_obj.set_nsr_name(nsr['name_ref'])
                    for const_vnfr in nsr['constituent_vnfr_ref']:
                        self._log.debug("Fetching VNFR (%s)", const_vnfr['vnfr_id'])
                        vnfr_msg = yield from cmdts_obj.get_vnfr(const_vnfr['vnfr_id'])
                        if vnfr_msg:
                            vnfr = vnfr_msg.as_dict()
                            self._log.info("create VNF:{}/{} operational status {}".format(nsr_obj.nsr_name, vnfr['name'], vnfr['operational_status']))
                            agent_vnfr = yield from nsr_obj.add_vnfr(vnfr, vnfr_msg)
                            method = self.get_config_method(vnfr['vnf_configuration'])
                            if method is not None:
                                unique_cfg_vnfr_list.append(vnfr)
                                unique_agent_vnfr_list.append(agent_vnfr)

                            #  Process VNF Cfg 
                            # Set up the config agent based on the method
                            yield from self.process_nsd_vnf_configuration(nsr_obj, vnfr)
                        else:
                            self._log.warning("NSR %s, VNFR not found yet (%s)", nsr_obj.nsr_name, const_vnfr['vnfr_id'])

                    # Process VNF config parameter
                    yield from self.process_vnf_config_parameter(nsr_obj)

                    # Invoke the config agent plugin
                    for agent_vnfr in unique_agent_vnfr_list:
                        yield from self._config_agent_mgr.invoke_config_agent_plugins(
                                'notify_create_vnfr',
                                 nsr_obj.agent_nsr,
                                 agent_vnfr)

                except Exception as e:
                    self._log.error("Failed processing NSR (%s) as (%s)", nsr_obj.nsr_name, str(e))
                    self._log.exception(e)
                    yield from nsr_obj.update_ns_cm_state(conmanY.RecordState.CFG_PROCESS_FAILED)
                    raise e

                self._log.debug("Starting to configure each VNF")

                try:
                    for cfg_vnfr in unique_cfg_vnfr_list:
		        # Apply configuration 
                        vnf_unique_name = get_vnf_unique_name(
                            nsr_obj.nsr_name,
                            cfg_vnfr['name'],
                            str(cfg_vnfr['member_vnf_index_ref']),
                        )

                        # Find vnfr for this vnf_unique_name
                        if vnf_unique_name not in nsr_obj._vnfr_dict:
                            self._log.error("NS (%s) - Can not find VNF to be configured: %s", nsr_obj.nsr_name, vnf_unique_name)
                        else:
                            # Save this unique VNF's config input parameters
                            nsr_obj.ConfigVNF(nsr_obj._vnfr_dict[vnf_unique_name])

                    # Now add the entire NS to the pending config list.
                    self._log.info("Scheduling NSR:{} configuration ".format(nsr_obj.nsr_name))
                    self._parent.add_to_pending(nsr_obj, unique_cfg_vnfr_list)
                    self._parent.add_nsr_obj(nsr_obj)

                except Exception as e:
                    self._log.error("Failed processing input parameters for NS (%s) as %s", nsr_obj.nsr_name, str(e))
                    self._log.exception(e)
                    raise

            except Exception as e:
                self._log.exception(e)
                if nsr_obj:
                    self._log.error("Failed to configure NS (%s) as (%s)", nsr_obj.nsr_name, str(e))
                    yield from nsr_obj.update_ns_cm_state(conmanY.RecordState.CFG_PROCESS_FAILED)
                raise e

        elif event == 'terminate':
            self._log.info("Configure NSR terminate, id = %s", id)
            nsr_obj = self._parent.get_nsr_obj(id)
            if nsr_obj is None:
                # Can be none if the terminate is called again due to DTS query
                return True

            try:
                yield from self.process_ns_terminate_config(nsr_obj, self._project.name)
            except Exception as e:
                self._log.warn("Terminate config failed for NSR {}: {}".
                               format(id, e))
                self._log.exception(e)

            try:
                yield from nsr_obj.update_ns_cm_state(conmanY.RecordState.TERMINATE)
                yield from self.terminate_NSR(id)
            except Exception as e:
                self._log.error("Terminate failed for NSR {}: {}".
                               format(id, e))
                self._log.exception(e)

        return True

    @asyncio.coroutine
    def terminate_NSR(self, id):
        if id not in self._nsr_dict:
            self._log.error("NSR(%s) does not exist!", id)
            return
        else:
            nsr_obj = self._nsr_dict[id]

            # Remove this NSR if we have it on pending task list
            for task in self.pending_tasks:
                if task['nsrid'] == id:
                    self.del_from_pending_tasks(task)

            # Remove any scheduled configuration event
            for nsr_obj_p in self._parent.pending_cfg:
                if nsr_obj_p == nsr_obj:
                    assert id == nsr_obj_p._nsr_id
                    # Mark this as being deleted so we do not try to reconfigure it
                    # if we are in cfg_delay (will wake up and continue to process otherwise)
                    nsr_obj_p.being_deleted = True
                    self._log.info("Removed scheduled configuration for NSR(%s)", nsr_obj.nsr_name)

            # Call Config Agent to clean up for each VNF
            for agent_vnfr in nsr_obj.agent_nsr.vnfrs:
                yield from self._config_agent_mgr.invoke_config_agent_plugins(
                    'notify_terminate_vnfr',
                    nsr_obj.agent_nsr,
                    agent_vnfr)

            self._log.info("NSR(%s/%s) is terminated", nsr_obj.nsr_name, id)

    @asyncio.coroutine
    def delete_NSR(self, id):
        if id not in self._nsr_dict:
            self._log.debug("NSR(%s) does not exist!", id)
            return
        else:
            # Remove this NSR if we have it on pending task list
            for task in self.pending_tasks:
                if task['nsrid'] == id:
                    self.del_from_pending_tasks(task)

        # Remove this object from global list
        nsr_obj = self._nsr_dict.pop(id, None)

        # Remove this NS cm-state from global status list
        self.cm_state['cm_nsr'].remove(nsr_obj.cm_nsr)

        self._parent.remove_nsr_obj(id)

        # publish delete cm-state (cm-nsr)
        yield from nsr_obj.delete_cm_nsr()

        # Deleting any config jobs for NSR.
        job_manager = self.riftcm_rpc_handler.job_manager.handler
        job_manager._terminate_nsr(id)        

        #####################TBD###########################
        # yield from self._config_agent_mgr.invoke_config_agent_plugins('notify_terminate_ns', self.id)

        self._log.info("NSR(%s/%s) is deleted", nsr_obj.nsr_name, id)

    @asyncio.coroutine
    def process_initial_config(self, nsr_obj, conf, script, vnfr_name=None):
        '''Apply the initial-config-primitives specified in NSD or VNFD'''

        def get_input_file(parameters):
            inp = {}

            # Add NSR name to file
            inp['nsr_name'] = nsr_obj.nsr_name

            # Add VNFR name if available
            if vnfr_name:
                inp['vnfr_name'] = vnfr_name

            # Add parameters for initial config
            inp['parameter'] = {}
            for parameter in parameters:
                try:
                    inp['parameter'][parameter['name']] = parameter['value']
                except KeyError as e:
                    if vnfr_name:
                        self._log.info("VNFR {} initial config parameter {} with no value: {}".
                                       format(vnfr_name, parameter, e))
                    else:
                        self._log.info("NSR {} initial config parameter {} with no value: {}".
                                       format(nsr_obj.nsr_name, parameter, e))


            # Add config agents specific to each VNFR
            inp['config-agent'] = {}
            for vnfr in nsr_obj.agent_nsr.vnfrs:
                # Get the config agent for the VNFR
                # If vnfr name is specified, add only CA specific to that
                if (vnfr_name is None) or \
                   (vnfr_name == vnfr.name):
                    agent = self._config_agent_mgr.get_vnfr_config_agent(vnfr.vnfr_msg)
                    if agent:
                        if agent.agent_type != riftcm_config_plugin.DEFAULT_CAP_TYPE:
                            inp['config-agent'][vnfr.member_vnf_index] = agent.agent_data
                            inp['config-agent'][vnfr.member_vnf_index] \
                                ['service-name'] = agent.get_service_name(vnfr.id)

            # Add vnfrs specific data
            inp['vnfr'] = {}
            for vnfr in nsr_obj.vnfrs:
                v = {}

                v['name'] = vnfr['name']
                v['mgmt_ip_address'] = vnfr['vnf_cfg']['mgmt_ip_address']
                v['mgmt_port'] = vnfr['vnf_cfg']['port']
                v['datacenter'] = vnfr['datacenter']

                if 'dashboard_url' in vnfr:
                    v['dashboard_url'] = vnfr['dashboard_url']

                if 'connection_point' in vnfr:
                    v['connection_point'] = []
                    for cp in vnfr['connection_point']:
                        cp_info = dict(name=cp['name'],
                                       ip_address=cp['ip_address'],
                                       mac_address=cp.get('mac_address', None),
                                       connection_point_id=cp.get('connection_point_id',None))
                        
                        if 'virtual_cps' in cp:
                            cp_info['virtual_cps'] = [ {k:v for k,v in vcp.items()
                                                        if k in ['ip_address', 'mac_address']}
                                                       for vcp in cp['virtual_cps'] ]
                        v['connection_point'].append(cp_info)

                
                if 'vdur' in vnfr:
                    vdu_data = [(vdu.get('name',None), vdu.get('management_ip',None), vdu.get('vm_management_ip',None), vdu.get('id',None))
                                for vdu in vnfr['vdur']]
    
                    v['vdur'] = [ dict(zip(['name', 'management_ip', 'vm_management_ip', 'id', 'vdu_id_ref'] , data)) for data in vdu_data ]

                inp['vnfr'][vnfr['member_vnf_index_ref']] = v


            self._log.debug("Input data for {}: {}".
                            format((vnfr_name if vnfr_name else nsr_obj.nsr_name),
                                   inp))

            # Convert to YAML string
            yaml_string = yaml.dump(inp, default_flow_style=False)

            # Write the inputs as yaml file
            tmp_file = None
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(yaml_string.encode("UTF-8"))
            self._log.debug("Input file created for {}: {}".
                            format((vnfr_name if vnfr_name \
                                    else nsr_obj.nsr_name),
                                   tmp_file.name))

            return tmp_file.name

        parameters = []
        try:
            parameters = conf['parameter']
        except Exception as e:
            self._log.debug("Parameter conf: {}, e: {}".
                            format(conf, e))

        inp_file = get_input_file(parameters)

        cmd = "{0} {1}".format(script, inp_file)
        self._log.debug("Running the CMD: {}".format(cmd))

        process = yield from asyncio.create_subprocess_shell(cmd,
                                                             loop=self._loop,
                                                             stdout=subprocess.PIPE,
                                                             stderr=subprocess.PIPE)
        stdout, stderr = yield from process.communicate()
        rc = yield from process.wait()

        if rc:
            msg = "NSR/VNFR {} initial config using {} failed with {}: {}". \
                  format(vnfr_name if vnfr_name else nsr_obj.nsr_name,
                         script, rc, stderr)
            self._log.error(msg)
            raise InitialConfigError(msg)

        try:
            os.remove(inp_file)
        except Exception as e:
            self._log.error("Error removing input file {}: {}".
                            format(inp_file, e))

    def get_script_file(self, script_name, d_name, d_id, d_type, project=None):
        # Get the full path to the script
        script = os.path.join(os.getenv('RIFT_VAR_ROOT'),
                                      'launchpad/packages',
                                      d_type,
                                      project if project else "",
                                      d_id,
                                      'scripts',
                                      script_name) 

        self._log.debug("Checking for script at %s", script)
        if not os.path.exists(script):
            err_msg = ("{} {}: Did not find script {} for config".
                       format(d_type, d_name, script))
            self._log.error(err_msg)
            raise ScriptNotFoundError(err_msg)

        # Seen cases in jenkins, where the script execution fails
        # with permission denied. Setting the permission on script
        # to make sure it has execute permission
        perm = os.stat(script).st_mode
        if not (perm  &  stat.S_IXUSR):
            self._log.warning("NSR/VNFR {} script {} " \
                                    "without execute permission: {}".
                                    format(d_name, script, perm))
            os.chmod(script, perm | stat.S_IXUSR)
        return script

    @asyncio.coroutine
    def process_ns_initial_config(self, nsr_obj, project=None):
        '''Apply the initial-service-primitives specified in NSD'''
        nsr = yield from self.cmdts_obj.get_nsr(nsr_obj.nsr_id)
        self._log.debug("NS initial config: {}".format(nsr))
        if 'initial_service_primitive' not in nsr:
            return
        if nsr is not None:
            nsd = yield from self.cmdts_obj.get_nsd(nsr_obj.nsr_id)
            for conf in nsr['initial_service_primitive']:
                self._log.debug("NSR {} initial config: {}".
                                format(nsr_obj.nsr_name, conf))
                script = self.get_script_file(conf['user_defined_script'],
                                              nsd.name,
                                              nsd.id,
                                              'nsd', 
                                              project
                                            )

                yield from self.process_initial_config(nsr_obj, conf, script)

    @asyncio.coroutine
    def process_vnf_initial_config(self, nsr_obj, vnfr, project=None):
        '''Apply the initial-config-primitives specified in VNFD'''
        vnfr_name = vnfr.name

        vnfd = vnfr.vnfd
        vnf_cfg = vnfd.vnf_configuration

        for conf in vnf_cfg.initial_config_primitive:
                self._log.debug("VNFR {} initial config: {} for vnfd id {}".
                                format(vnfr_name, conf, vnfd.id))

                if not conf.user_defined_script:
                    self._log.debug("VNFR {} did not find user defined script: {}".
                                    format(vnfr_name, conf))
                    continue

                script = self.get_script_file(conf.user_defined_script,
                                              vnfd.name,
                                              vnfd.id,
                                              'vnfd', 
                                               project
                                                )

                yield from self.process_initial_config(nsr_obj,
                                                       conf.as_dict(),
                                                       script,
                                                       vnfr_name=vnfr_name)

    @asyncio.coroutine
    def process_ns_terminate_config(self, nsr_obj, project=None):
        '''Apply the terminate-service-primitives specified in NSD'''

        nsr = self._nsr
        if 'terminate_service_primitive' not in nsr: 
            return

        if nsr is not None:
            nsd = nsr_obj.agent_nsr.nsd
            for conf in nsr['terminate_service_primitive']:
                self._log.debug("NSR {} terminate service: {}". 
                                format(nsr_obj.nsr_name, conf))
                script = self.get_script_file(conf['user_defined_script'],
                                              nsd.name,
                                              nsd.id,
                                              'nsd', 
                                               project)

                try:
                    yield from self.process_initial_config(nsr_obj, conf, script)

                except Exception as e:
                    # Ignore any failures on terminate
                    self._log.warning("NSR {} terminate config script {} failed: {}".
                                      format(nsr_obj.nsr_name, script, e))
                    break


class ConfigManagerNSR(object):
    def __init__(self, log, loop, parent, project, id):
        self._log = log
        self._loop = loop
        self._rwcal = None
        self._vnfr_dict = {}
        self._cp_dict = {}
        self._nsr_id = id
        self._parent = parent
        self._project = project
        self._log.info("Instantiated NSR entry for id=%s", id)
        self.nsr_cfg_config_attributes_dict = {}
        self.vnf_config_attributes_dict = {}
        self.num_vnfs_to_cfg = 0
        self._vnfr_list = []
        self.vnf_cfg_list = []
        self.this_nsr_dir = None
        self.being_deleted = False
        self.dts_obj = self._parent.cmdts_obj

        # Initialize cm-state for this NS
        self.cm_nsr = {}
        self.cm_nsr['cm_vnfr'] = []
        self.cm_nsr['id'] = id
        self.cm_nsr['state'] = self.state_to_string(conmanY.RecordState.INIT)
        self.cm_nsr['state_details'] = None

        self.set_nsr_name('Not Set')

        # Add this NSR cm-state object to global cm-state
        parent.cm_state['cm_nsr'].append(self.cm_nsr)

        # Place holders for NSR & VNFR classes
        self.agent_nsr = None

    @property
    def nsr_opdata_xpath(self):
        ''' Returns full xpath for this NSR cm-state opdata '''
        return self._project.add_project((
            "D,/rw-conman:cm-state/rw-conman:cm-nsr[rw-conman:id={}]"
        ).format(quoted_key(self._nsr_id)))

    @property
    def vnfrs(self):
        return self._vnfr_list

    @property
    def parent(self):
        return self._parent

    @property
    def nsr_id(self):
        return self._nsr_id

    @asyncio.coroutine
    def publish_cm_state(self):
        ''' This function publishes cm_state for this NSR '''

        cm_state = conmanY.YangData_RwProject_Project_CmState()
        cm_state_nsr = cm_state.cm_nsr.add()
        cm_state_nsr.from_dict(self.cm_nsr)
        #with self._dts.transaction() as xact:
        yield from self.dts_obj.update(self.nsr_opdata_xpath, cm_state_nsr)
        self._log.info("Published cm-state with xpath %s and nsr %s",
                       self.nsr_opdata_xpath,
                       cm_state_nsr)

    @asyncio.coroutine
    def delete_cm_nsr(self):
        ''' This function publishes cm_state for this NSR '''

        yield from self.dts_obj.delete(self.nsr_opdata_xpath)
        self._log.info("Deleted cm-nsr with xpath %s",
                       self.nsr_opdata_xpath)

    def set_nsr_name(self, name):
        self.nsr_name = name
        self.cm_nsr['name'] = name

    def ConfigVNF(self, vnfr):

        vnf_cfg = vnfr['vnf_cfg']
        vnf_cm_state = self.find_or_create_vnfr_cm_state(vnf_cfg)

        if (vnf_cm_state['state'] == self.state_to_string(conmanY.RecordState.READY_NO_CFG)
            or
            vnf_cm_state['state'] == self.state_to_string(conmanY.RecordState.READY)):
            self._log.warning("NS/VNF (%s/%s) is already configured! Skipped.", self.nsr_name, vnfr['name'])
            return

        #UPdate VNF state
        vnf_cm_state['state'] = self.state_to_string(conmanY.RecordState.CFG_PROCESS)

        # Now translate the configuration for iP addresses
        try:
            # Add cp_dict members (TAGS) for this VNF
            self._cp_dict['rw_mgmt_ip'] = vnf_cfg['mgmt_ip_address']
            self._cp_dict['rw_username'] = vnf_cfg['username']
            self._cp_dict['rw_password'] = vnf_cfg['password']
        except Exception as e:
            vnf_cm_state['state'] = self.state_to_string(conmanY.RecordState.CFG_PROCESS_FAILED)
            self._log.error("Failed to set tags for VNF: %s with (%s)", log_this_vnf(vnf_cfg), str(e))
            return

        self._log.info("Applying config to VNF: %s = %s!", log_this_vnf(vnf_cfg), vnf_cfg)
        try:
            self._log.debug("Scheduled configuration!")
            vnf_cm_state['state'] = self.state_to_string(conmanY.RecordState.CFG_SCHED)
        except Exception as e:
            self._log.error("Failed apply_vnf_config to VNF: %s as (%s)", log_this_vnf(vnf_cfg), str(e))
            vnf_cm_state['state'] = self.state_to_string(conmanY.RecordState.CFG_PROCESS_FAILED)
            raise

    def add(self, nsr):
        self._log.info("Adding NS Record for id=%s", id)
        self._nsr = nsr

    def sample_cm_state(self):
        return (
            {
                'cm_nsr': [
                    {
                        'cm_vnfr': [
                            {
                                'connection_point': [
                                    {'ip_address': '1.1.1.1', 'name': 'vnf1cp1'},
                                    {'ip_address': '1.1.1.2', 'name': 'vnf1cp2'}
                                ],
                                'id': 'vnfrid1',
                                'mgmt_interface': {'ip_address': '7.1.1.1',
                                                   'port': 1001},
                                'name': 'vnfrname1',
                                'state': 'init'
                            },
                            {
                                'connection_point': [{'ip_address': '2.1.1.1', 'name': 'vnf2cp1'},
                                                     {'ip_address': '2.1.1.2', 'name': 'vnf2cp2'}],
                                'id': 'vnfrid2',
                                'mgmt_interface': {'ip_address': '7.1.1.2',
                                                   'port': 1001},
                                'name': 'vnfrname2',
                                'state': 'init'}
                        ],
                        'id': 'nsrid1',
                        'name': 'nsrname1',
                        'state': 'init'}
                ],
                'states': 'Initialized, '
            })

    def populate_cm_state_from_vnf_cfg(self):
        # Fill in each VNFR from this nsr object
        vnfr_list = self._vnfr_list
        for vnfr in vnfr_list:
            vnf_cfg = vnfr['vnf_cfg']
            vnf_cm_state = self.find_vnfr_cm_state(vnfr['id'])

            if vnf_cm_state:
                # Fill in VNF management interface
                vnf_cm_state['mgmt_interface']['ip_address'] = vnf_cfg['mgmt_ip_address']
                vnf_cm_state['mgmt_interface']['port'] = vnf_cfg['port']

                # Fill in VNF configuration details
                vnf_cm_state['cfg_type'] = vnf_cfg['config_method']

                # Fill in each connection-point for this VNF
                if "connection_point" in vnfr:
                    cp_list = vnfr['connection_point']
                    for cp_item_dict in cp_list:
                        try:
                            vnf_cm_state['connection_point'].append(
                                {
                                    'name' : cp_item_dict['name'],
                                    'ip_address' : cp_item_dict['ip_address'],
                                    'connection_point_id' : cp_item_dict['connection_point_id'],
                                }
                            )
                        except Exception:
                            # Added to make mano_ut work
                            pass

    def state_to_string(self, state):
        state_dict = {
            conmanY.RecordState.INIT : "init",
            conmanY.RecordState.RECEIVED : "received",
            conmanY.RecordState.CFG_PROCESS : "cfg_process",
            conmanY.RecordState.CFG_PROCESS_FAILED : "cfg_process_failed",
            conmanY.RecordState.CFG_SCHED : "cfg_sched",
            conmanY.RecordState.CONNECTING : "connecting",
            conmanY.RecordState.FAILED_CONNECTION : "failed_connection",
            conmanY.RecordState.CFG_SEND : "cfg_send",
            conmanY.RecordState.CFG_FAILED : "cfg_failed",
            conmanY.RecordState.READY_NO_CFG : "ready_no_cfg",
            conmanY.RecordState.READY : "ready",
            conmanY.RecordState.TERMINATE : "terminate",
        }
        return state_dict[state]

    def find_vnfr_cm_state(self, id):
        if self.cm_nsr['cm_vnfr']:
            for vnf_cm_state in self.cm_nsr['cm_vnfr']:
                if vnf_cm_state['id'] == id:
                    return vnf_cm_state
        return None

    def find_or_create_vnfr_cm_state(self, vnf_cfg):
        vnfr = vnf_cfg['vnfr']
        vnf_cm_state = self.find_vnfr_cm_state(vnfr['id'])

        if vnf_cm_state is None:
            # Not found, Create and Initialize this VNF cm-state
            vnf_cm_state = {
                'id' : vnfr['id'],
                'name' : vnfr['name'],
                'state' : self.state_to_string(conmanY.RecordState.RECEIVED),
                'mgmt_interface' :
                {
                    'ip_address' : vnf_cfg['mgmt_ip_address'],
                    'port' : vnf_cfg['port'],
                },
                'connection_point' : [],
                'config_parameter' :
                {
                    'config_parameter_source' : [],
                    'config_parameter_request' : [],
                },
            }
            self.cm_nsr['cm_vnfr'].append(vnf_cm_state)

            # Publish newly created cm-state


        return vnf_cm_state

    @asyncio.coroutine
    def get_vnf_cm_state(self, vnfr):
        if vnfr:
            vnf_cm_state = self.find_vnfr_cm_state(vnfr['id'])
            if vnf_cm_state:
                return vnf_cm_state['state']
        return False

    @asyncio.coroutine
    def update_vnf_cm_state(self, vnfr, state):
        if vnfr:
            vnf_cm_state = self.find_vnfr_cm_state(vnfr['id'])
            if vnf_cm_state is None:
                self._log.error("No opdata found for NS/VNF:%s/%s!",
                                self.nsr_name, vnfr['name'])
                return

            if vnf_cm_state['state'] != self.state_to_string(state):
                old_state = vnf_cm_state['state']
                vnf_cm_state['state'] = self.state_to_string(state)
                # Publish new state
                yield from self.publish_cm_state()
                self._log.info("VNF ({}/{}/{}) state change: {} -> {}"
                               .format(self.nsr_name,
                                       vnfr['name'],
                                       vnfr['member_vnf_index_ref'],
                                       old_state,
                                       vnf_cm_state['state']))

        else:
            self._log.error("No VNFR supplied for state update (NS=%s)!",
                            self.nsr_name)

    @property
    def get_ns_cm_state(self):
        return self.cm_nsr['state']

    @asyncio.coroutine
    def update_ns_cm_state(self, state, state_details=None):
        if self.cm_nsr['state'] != self.state_to_string(state):
            old_state = self.cm_nsr['state']
            self.cm_nsr['state'] = self.state_to_string(state)
            self.cm_nsr['state_details'] = state_details if state_details is not None else None
            self._log.info("NS ({}) state change: {} -> {}"
                           .format(self.nsr_name,
                                   old_state,
                                   self.cm_nsr['state']))
            # Publish new state
            yield from self.publish_cm_state()

    @asyncio.coroutine
    def add_vnfr(self, vnfr, vnfr_msg):

        @asyncio.coroutine
        def populate_subnets_from_vlr(id):
            try:
                # Populate cp_dict with VLR subnet info
                vlr = yield from self.dts_obj.get_vlr(id)
                if vlr is not None and 'assigned_subnet' in vlr:
                    subnet = {vlr.name:vlr.assigned_subnet}
                    self._cp_dict[vnfr['member_vnf_index_ref']].update(subnet)
                    self._cp_dict.update(subnet)
                    self._log.debug("VNF:(%s) Updated assigned subnet = %s",
                                    vnfr['name'], subnet)
            except Exception as e:
                self._log.error("VNF:(%s) VLR Error = %s",
                                vnfr['name'], e)

        if vnfr['id'] not in self._vnfr_dict:
            self._log.info("NSR(%s) : Adding VNF Record for name=%s, id=%s", self._nsr_id, vnfr['name'], vnfr['id'])
            # Add this vnfr to the list for show, or single traversal
            self._vnfr_list.append(vnfr)
        else:
            self._log.warning("NSR(%s) : VNF Record for name=%s, id=%s already exists, overwriting",
                              self._nsr_id, vnfr['name'], vnfr['id'])

        # Make vnfr available by id as well as by name
        unique_name = get_vnf_unique_name(self.nsr_name, vnfr['name'], vnfr['member_vnf_index_ref'])
        self._vnfr_dict[unique_name] = vnfr
        self._vnfr_dict[vnfr['id']] = vnfr

        # Create vnf_cfg dictionary with default values
        vnf_cfg = {
            'nsr_obj' : self,
            'vnfr' : vnfr,
            'agent_vnfr' : self.agent_nsr.add_vnfr(vnfr, vnfr_msg),
            'nsr_name' : self.nsr_name,
            'nsr_id' : self._nsr_id,
            'vnfr_name' : vnfr['name'],
            'member_vnf_index' : vnfr['member_vnf_index_ref'],
            'port' : 0,
            'username' : '@rift',
            'password' : 'rift',
            'config_method' : 'None',
            'protocol' : 'None',
            'mgmt_ip_address' : '0.0.0.0',
            'cfg_file' : 'None',
            'cfg_retries' : 0,
            'script_type' : 'bash',
        }

        ##########################
        # Update the mgmt ip address
        # In case the config method is none, this is not
        # updated later
        try:
            vnf_cfg['mgmt_ip_address'] = vnfr_msg.mgmt_interface.ip_address
            vnf_cfg['port'] = vnfr_msg.mgmt_interface.port
        except Exception as e:
            self._log.warn(
                "VNFR {}({}), unable to retrieve mgmt ip address: {}".
                format(vnfr['name'], vnfr['id'], e))

        vnfr['vnf_cfg'] = vnf_cfg
        self.find_or_create_vnfr_cm_state(vnf_cfg)

        '''
        Build the connection-points list for this VNF (self._cp_dict)
        '''
        # Populate global CP list self._cp_dict from VNFR
        cp_list = []
        if 'connection_point' in vnfr:
            cp_list = vnfr['connection_point']

        self._cp_dict[vnfr['member_vnf_index_ref']] = {}
        if 'vdur' in vnfr:
            for vdur in vnfr['vdur']:
                if 'internal_connection_point' in vdur:
                    cp_list += vdur['internal_connection_point']

                for cp_item_dict in cp_list:
                    if 'ip_address' not in cp_item_dict:
                        self._log.error("connection point {} doesnot have an ip address assigned ".
                                                                        format(cp_item_dict['name']))
                        continue
                    # Populate global dictionary
                    self._cp_dict[
                        cp_item_dict['name']
                    ] = cp_item_dict['ip_address']

                    # Populate unique member specific dictionary
                    self._cp_dict[
                        vnfr['member_vnf_index_ref']
                    ][
                        cp_item_dict['name']
                    ] = cp_item_dict['ip_address']

                    # Fill in the subnets from vlr
                    if 'vlr_ref' in cp_item_dict:
                        ### HACK: Internal connection_point do not have VLR reference
                        yield from populate_subnets_from_vlr(cp_item_dict['vlr_ref'])

        if 'internal_vlr' in vnfr:
            for ivlr in vnfr['internal_vlr']:
                yield from populate_subnets_from_vlr(ivlr['vlr_ref'])

        # Update vnfr
        vnf_cfg['agent_vnfr']._vnfr = vnfr
        return vnf_cfg['agent_vnfr']


class XPaths(object):
    @staticmethod
    def nsr_opdata(k=None):
        return ("D,/nsr:ns-instance-opdata/nsr:nsr" +
                ("[nsr:ns-instance-config-ref={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def nsd_msg(k=None):
        return ("C,/project-nsd:nsd-catalog/project-nsd:nsd" +
                "[project-nsd:id={}]".format(quoted_key(k)) if k is not None else "")

    @staticmethod
    def vnfr_opdata(k=None):
        return ("D,/vnfr:vnfr-catalog/vnfr:vnfr" +
                ("[vnfr:id={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def vnfd_path(k=None):
        return ("C,/vnfd:vnfd-catalog/vnfd:vnfd" +
                ("[vnfd:id={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def config_agent(k=None):
        return ("D,/rw-config-agent:config-agent/rw-config-agent:account" +
                ("[rw-config-agent:name={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def nsr_config(k=None):
        return ("C,/nsr:ns-instance-config/nsr:nsr" +
                ("[nsr:id={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def vlr(k=None):
        return ("D,/vlr:vlr-catalog/vlr:vlr" +
                ("[vlr:id={}]".format(quoted_key(k)) if k is not None else ""))

class ConfigManagerDTS(object):
    ''' This class either reads from DTS or publishes to DTS '''

    def __init__(self, log, loop, parent, dts, project):
        self._log = log
        self._loop = loop
        self._parent = parent
        self._dts = dts
        self._project = project

    @asyncio.coroutine
    def _read_dts(self, path, do_trace=False):
        xpath = self._project.add_project(path)
        self._log.debug("_read_dts path = %s", xpath)
        flags = rwdts.XactFlag.MERGE
        flags += rwdts.XactFlag.TRACE if do_trace else 0
        res_iter = yield from self._dts.query_read(
                xpath, flags=flags
                )

        results = []
        try:
            for i in res_iter:
                result = yield from i
                if result is not None:
                    results.append(result.result)
        except:
            pass

        return results


    @asyncio.coroutine
    def get_xpath(self, xpath):
        self._log.debug("Attempting to get xpath: {}".format(xpath))
        resp = yield from self._read_dts(xpath, False)
        if len(resp) > 0:
            self._log.debug("Got DTS resp: {}".format(resp[0]))
            return resp[0]
        return None

    @asyncio.coroutine
    def get_nsr(self, id):
        self._log.debug("Attempting to get NSR: %s", id)
        nsrl = yield from self._read_dts(XPaths.nsr_opdata(id), False)
        nsr = None
        if len(nsrl) > 0:
            nsr =  nsrl[0].as_dict()
        return nsr

    @asyncio.coroutine
    def get_nsr_config(self, id):
        self._log.debug("Attempting to get config NSR: %s", id)
        nsrl = yield from self._read_dts(XPaths.nsr_config(id), False)
        nsr = None
        if len(nsrl) > 0:
            nsr =  nsrl[0]
        return nsr

    @asyncio.coroutine
    def get_nsd_msg(self, id):
        self._log.debug("Attempting to get NSD: %s", id)
        nsdl = yield from self._read_dts(XPaths.nsd_msg(id), False)
        nsd_msg = None
        if len(nsdl) > 0:
            nsd_msg =  nsdl[0]
        return nsd_msg

    @asyncio.coroutine
    def get_nsd(self, nsr_id):
        self._log.debug("Attempting to get NSD for NSR: %s", id)
        nsr_config = yield from self.get_nsr_config(nsr_id)
        nsd_msg = nsr_config.nsd
        return nsd_msg

    @asyncio.coroutine
    def get_vnfr(self, id):
        self._log.debug("Attempting to get VNFR: %s", id)
        vnfrl = yield from self._read_dts(XPaths.vnfr_opdata(id), do_trace=False)
        vnfr_msg = None
        if len(vnfrl) > 0:
            vnfr_msg = vnfrl[0]
        return vnfr_msg

    @asyncio.coroutine
    def get_vnfd(self, id):
        self._log.debug("Attempting to get VNFD: %s", XPaths.vnfd_path(id))
        vnfdl = yield from self._read_dts(XPaths.vnfd_path(id), do_trace=False)
        vnfd_msg = None
        if len(vnfdl) > 0:
            vnfd_msg = vnfdl[0]
        return vnfd_msg

    @asyncio.coroutine
    def get_vlr(self, id):
        self._log.debug("Attempting to get VLR subnet: %s", id)
        vlrl = yield from self._read_dts(XPaths.vlr(id), do_trace=False)
        vlr_msg = None
        if len(vlrl) > 0:
            vlr_msg = vlrl[0]
        return vlr_msg

    @asyncio.coroutine
    def get_config_agents(self, name):
        self._log.debug("Attempting to get config_agents: %s", name)
        cfgagentl = yield from self._read_dts(XPaths.config_agent(name), False)
        return cfgagentl

    @asyncio.coroutine
    def update(self, xpath, msg, flags=rwdts.XactFlag.REPLACE):
        """
        Update a cm-state (cm-nsr) record in DTS with the path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Updating cm-state %s:%s dts_pub_hdl = %s", path, msg, self.dts_pub_hdl)
        self.dts_pub_hdl.update_element(path, msg, flags)
        self._log.debug("Updated cm-state, %s:%s", path, msg)

    @asyncio.coroutine
    def delete(self, xpath):
        """
        Delete cm-nsr record in DTS with the path only
        """
        path = self._project.add_project(xpath)
        self._log.debug("Deleting cm-nsr %s dts_pub_hdl = %s", path, self.dts_pub_hdl)
        self.dts_pub_hdl.delete_element(path)
        self._log.debug("Deleted cm-nsr, %s", path)

    @asyncio.coroutine
    def register(self):
        yield from self.register_to_publish()
        yield from self.register_for_nsr()

    def deregister(self):
        self._log.debug("De-registering conman config for project {}".
                        format(self._project.name))
        if self.dts_reg_hdl:
            self.dts_reg_hdl.deregister()
            self.dts_reg_hdl = None

        if self.dts_pub_hdl:
            self.dts_pub_hdl.deregister()
            self.dts_pub_hdl = None

    @asyncio.coroutine
    def register_to_publish(self):
        ''' Register to DTS for publishing cm-state opdata '''

        xpath = self._project.add_project("D,/rw-conman:cm-state/rw-conman:cm-nsr")
        self._log.debug("Registering to publish cm-state @ %s", xpath)
        hdl = rift.tasklets.DTS.RegistrationHandler()
        with self._dts.group_create() as group:
            self.dts_pub_hdl = group.register(xpath=xpath,
                                              handler=hdl,
                                              flags=rwdts.Flag.PUBLISHER | rwdts.Flag.NO_PREP_READ)

    @property
    def nsr_xpath(self):
        return self._project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr")

    @asyncio.coroutine
    def register_for_nsr(self):
        """ Register for NSR changes """

        @asyncio.coroutine
        def on_prepare(xact_info, query_action, ks_path, msg):
            """ This NSR is created """
            self._log.debug("Received NSR instantiate on_prepare (%s:%s:%s)",
                            query_action,
                            ks_path,
                            msg)

            if (query_action == rwdts.QueryAction.UPDATE or
                query_action == rwdts.QueryAction.CREATE):
                # Update Each NSR/VNFR state
                if msg.operational_status in ['running', 'terminate']:
                    # Add to the task list
                    self._parent.add_to_pending_tasks({
                        'nsrid' : msg.ns_instance_config_ref,
                        'retries' : 5,
                        'event' : msg.operational_status,
                    })

            elif query_action == rwdts.QueryAction.DELETE:
                nsr_id = msg.ns_instance_config_ref
                self._log.debug("Got terminate for NSR id %s", nsr_id)
                asyncio.ensure_future(self._parent.delete_NSR(nsr_id), loop=self._loop)

            else:
                raise NotImplementedError(
                    "%s action on cm-state not supported",
                    query_action)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        try:
            handler = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare)
            self.dts_reg_hdl = yield from self._dts.register(self.nsr_xpath,
                                                             flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY,
                                                             handler=handler)
        except Exception as e:
            self._log.error("Failed to register for NSR changes as %s", str(e))


