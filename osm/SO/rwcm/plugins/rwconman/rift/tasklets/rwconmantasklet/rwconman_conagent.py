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
import rift.tasklets

from gi.repository import (
    RwConfigAgentYang as rwcfg_agent,
)

from .riftcm_config_plugin import DEFAULT_CAP_TYPE
from . import RiftCA
from . import jujuconf
import rift.mano.config_agent


class ConfigAgentError(Exception):
    pass


class ConfigAgentExistsError(ConfigAgentError):
    pass


class UnknownAgentTypeError(Exception):
    pass


class ConfigAgentVnfrAddError(Exception):
    pass


class ConfigAgentVnfrTypeError(Exception):
    pass


class ConfigAccountHandler(object):
    def __init__(self, dts, log, loop, project, on_add_config_agent, on_delete_config_agent):
        self._log = log
        self._dts = dts
        self._loop = loop
        self._project = project
        self._on_add_config_agent = on_add_config_agent
        self._on_delete_config_agent = on_delete_config_agent

        self._log.debug("creating config account handler")
        self.cloud_cfg_handler = rift.mano.config_agent.ConfigAgentSubscriber(
            self._dts, self._log, self._project,
            rift.mano.config_agent.ConfigAgentCallbacks(
                on_add_apply=self.on_config_account_added,
                on_delete_apply=self.on_config_account_deleted,
            )
        )

    def on_config_account_deleted(self, account):
        self._log.debug("config account deleted: %s", account.name)
        self._on_delete_config_agent(account)

    def on_config_account_added(self, account):
        self._log.debug("config account added")
        self._log.debug(account.as_dict())
        self._on_add_config_agent(account)

    @asyncio.coroutine
    def register(self):
        self.cloud_cfg_handler.register()

    def deregister(self):
        self.cloud_cfg_handler.deregister()


class RiftCMConfigPlugins(object):
    """ NSM Config Agent Plugins """
    def __init__(self):
        self._plugin_classes = {
            "juju": jujuconf.JujuConfigPlugin,
            "riftca": RiftCA.RiftCAConfigPlugin,
        }

    @property
    def plugins(self):
        """ Plugin info """
        return self._plugin_classes

    def __getitem__(self, name):
        """ Get item """
        return self._plugin_classes[name]

    def register(self, plugin_name, plugin_class, *args):
        """ Register a plugin to this Nsm"""
        self._plugin_classes[plugin_name] = plugin_class

    def deregister(self, plugin_name, plugin_class, *args):
        """ Deregister a plugin to this Nsm"""
        if plugin_name in self._plugin_classes:
            del self._plugin_classes[plugin_name]

    def class_by_plugin_name(self, name):
        """ Get class by plugin name """
        return self._plugin_classes[name]


class RiftCMConfigAgent(object):
    def __init__(self, dts, log, loop, parent):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._ConfigManagerConfig = parent

        self._config_plugins = RiftCMConfigPlugins()
        self._config_handler = ConfigAccountHandler(
            self._dts, self._log, self._loop, parent._project,
            self._on_config_agent, self._on_config_agent_delete)
        self._plugin_instances = {}
        self._default_account_added = False

    @asyncio.coroutine
    def invoke_config_agent_plugins(self, method, nsr, vnfr, *args):
        # Invoke the methods on all config agent plugins registered
        rc = True
        
        for agent in self._plugin_instances.values():
            if not agent.is_vnfr_managed(vnfr.id):
                continue
            try:
                self._log.debug("Invoke {} on {}".format(method, agent.name))
                rc = yield from agent.invoke(method, nsr, vnfr, *args)
                break
            except Exception as e:
                self._log.exception("Error invoking {} on {} : {}".
                                    format(method, agent.name, e))
                raise e

        self._log.info("vnfr({}), method={}, return rc={}"
                       .format(vnfr.name, method, rc))
        return rc

    def get_vnfr_config_agent(self, vnfr):
        for agent in self._plugin_instances.values():
            try:
                if agent.is_vnfr_managed(vnfr.id):
                    return agent
            except Exception as e:
                self._log.debug("Check if VNFR {} is config agent managed: {}".
                                format(vnfr.name, e))

    def is_vnfr_config_agent_managed(self, vnfr):
        if self.get_vnfr_config_agent(vnfr):
            return True
        return False

    def _on_config_agent(self, config_agent):
        self._log.debug("Got nsm plugin config agent account: %s", config_agent)
        try:
            cap_name = config_agent.name
            cap_inst = self._config_plugins.class_by_plugin_name(
                config_agent.account_type)
        except KeyError as e:
            msg = "Config agent nsm plugin type not found: {}". \
                format(config_agent.account_type)
            self._log.error(msg)
            raise UnknownAgentTypeError(msg)

        # Check to see if the plugin was already instantiated
        if cap_name in self._plugin_instances:
            self._log.debug("Config agent nsm plugin {} already instantiated. " \
                            "Using existing.". format(cap_name))
        else:
            # Otherwise, instantiate a new plugin using the config agent account
            self._log.debug("Instantiting new config agent using class: %s", cap_inst)
            new_instance = cap_inst(self._dts, self._log, self._loop,
                                    self._ConfigManagerConfig._project, config_agent)
            self._plugin_instances[cap_name] = new_instance

        # TODO (pjoseph): See why this was added, as this deletes the
        # Rift plugin account when Juju account is added
        # if self._default_account_added:
        #     # If the user has provided a config account, chuck the default one.
        #     if self.DEFAULT_CAP_TYPE in self._plugin_instances:
        #         del self._plugin_instances[self.DEFAULT_CAP_TYPE]

    def _on_config_agent_delete(self, config_agent):
        self._log.debug("Got nsm plugin config agent delete, account: %s, type: %s",
                config_agent.name, config_agent.account_type)
        cap_name = config_agent.name
        if cap_name in self._plugin_instances:
            self._log.debug("Config agent nsm plugin exists, deleting it.")
            del self._plugin_instances[cap_name]
        else:
            self._log.error("Error deleting - Config Agent nsm plugin %s does not exist.", cap_name)


    @asyncio.coroutine
    def register(self):
        self._log.debug("Registering for config agent nsm plugin manager")
        yield from self._config_handler.register()
                            
        account = rwcfg_agent.YangData_RwProject_Project_ConfigAgent_Account()
        account.account_type = DEFAULT_CAP_TYPE
        account.name = "RiftCA"
        self._on_config_agent(account)
        self._default_account_added = True

        # Also grab any account already configured
        config_agents = yield from self._ConfigManagerConfig.cmdts_obj.get_config_agents(name=None)
        for account in config_agents:
            self._on_config_agent(account)

    def deregister(self):
        self._log.debug("De-registering config agent nsm plugin manager".
                        format(self._ConfigManagerConfig._project))
        self._config_handler.deregister()

    def set_config_agent(self, nsr, vnfr, method):
        if method == 'juju':
            agent_type = 'juju'
        elif method in ['script']:
            agent_type = DEFAULT_CAP_TYPE
        else:
            msg = "Unsupported configuration method ({}) for VNF:{}/{}". \
                  format(method, nsr.name, vnfr.name)
            self._log.error(msg)
            raise UnknownAgentTypeError(msg)

        try:
            acc_map = nsr.nsr_cfg_msg.vnf_cloud_account_map
        except AttributeError:
            self._log.debug("Did not find cloud account map for NS {}".
                            format(nsr.name))
            acc_map = []

        for vnfd in acc_map:
            if vnfd.config_agent_account is not None:
                if vnfd.member_vnf_index_ref == vnfr.vnfr_msg.member_index:
                    for agent in self._plugin_instances:
                        # Find the plugin with the same name
                        if agent == vnfd.config_agent_account:
                            # Check if the types are same
                            if  self._plugin_instances[agent].agent_type != agent_type:
                                msg = "VNF {} specified config agent {} is not of type {}". \
                                      format(vnfr.name, agent, agent_type)
                                self._log.error(msg)
                                raise ConfigAgentVnfrTypeError(msg)

                            self._plugin_instances[agent].add_vnfr_managed(vnfr)
                            self._log.debug("Added vnfr {} as config plugin {} managed".
                                            format(vnfr.name, agent))
                            return

        # If no config agent specified for the VNF, use the
        # first available of the same type
        for agent in self._plugin_instances:
            if self._plugin_instances[agent].agent_type == agent_type:
                self._plugin_instances[agent].add_vnfr_managed(vnfr)
                self._log.debug("Added vnfr from {} from default CAs as config plugin {} managed".
                                format(vnfr.name, agent))
                return

        msg = "Error finding config agent of type {} for VNF {}". \
              format(agent_type, vnfr.name)
        self._log.error(msg)
        raise ConfigAgentVnfrAddError(msg)
