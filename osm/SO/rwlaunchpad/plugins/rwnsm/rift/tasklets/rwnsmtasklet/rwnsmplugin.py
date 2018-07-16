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

from . import nsmpluginbase
from . import openmano_nsm
import asyncio

class RwNsPlugin(nsmpluginbase.NsmPluginBase):
    """
        RW Implentation of the NsmPluginBase
    """
    def __init__(self, dts, log, loop, publisher, ro_account, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

    def set_state(self, nsr_id, state):
        pass

    def create_nsr(self, nsr_msg, nsd, key_pairs=None, ssh_key=None):
        """
        Create Network service record
        """
        pass

    @asyncio.coroutine
    def deploy(self, nsr):
        pass

    @asyncio.coroutine
    def instantiate_ns(self, nsr, config_xact):
        """
        Instantiate NSR with the passed nsr id
        """
        yield from nsr.instantiate(config_xact)

    @asyncio.coroutine
    def instantiate_vnf(self, nsr, vnfr, scaleout=False):
        """
        Instantiate NSR with the passed nsr id
        """
        yield from vnfr.instantiate(nsr)

    @asyncio.coroutine
    def instantiate_vl(self, nsr, vlr):
        """
        Instantiate NSR with the passed nsr id
        """
        yield from vlr.instantiate()

    @asyncio.coroutine
    def terminate_ns(self, nsr):
        """
        Terminate the network service
        """
        pass

    @asyncio.coroutine
    def terminate_vnf(self, nsr, vnfr, scalein=False):
        """
        Terminate the VNF
        """
        yield from vnfr.terminate()

    @asyncio.coroutine
    def terminate_vl(self, vlr):
        """
        Terminate the virtual link
        """
        yield from vlr.terminate()

    @asyncio.coroutine
    def update_vnfr(self, vnfr):
        """ Update the virtual network function record """
        yield from vnfr.update_vnfm()

class NsmPlugins(object):
    """ NSM Plugins """
    def __init__(self):
        self._plugin_classes = {
                "openmano": openmano_nsm.OpenmanoNsPlugin,
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
