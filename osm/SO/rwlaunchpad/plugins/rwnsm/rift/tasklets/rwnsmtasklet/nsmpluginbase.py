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
import abc

class NsmPluginBase(object):
    """
        Abstract base class for the NSM plugin.
        There will be single instance of this plugin for each plugin type.
    """

    def __init__(self, dts, log, loop, nsm, plugin_name, dts_publisher):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._nsm = nsm
        self._plugin_name = plugin_name
        self._dts_publisher = dts_publisher

    @property
    def dts(self):
        return self._dts

    @property
    def log(self):
        return self._log

    @property
    def loop(self):
        return self._loop

    @property
    def nsm(self):
        return self._nsm

    @abc.abstractmethod
    def set_state(self, nsr_id, state):
        pass

    @abc.abstractmethod
    def create_nsr(self, nsr, nsd, key_pairs=None, ssh_key=None):
        """ Create an NSR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def deploy(self, nsr_msg):
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def instantiate_ns(self, nsr, xact):
        """ Instantiate the network service """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def instantiate_vnf(self, nsr, vnfr, scaleout=False):
        """ Instantiate the virtual network function """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def instantiate_vl(self, nsr, vl):
        """ Instantiate the virtual link"""
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def update_vnfr(self, vnfr):
        """ Update the virtual network function record """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def get_nsr(self, nsr_path):
        """ Get the NSR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def get_vnfr(self, vnfr_path):
        """ Get the VNFR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def get_vlr(self, vlr_path):
        """ Get the VLR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def terminate_ns(self, nsr):
        """Terminate the network service """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def terminate_vnf(self, nsr, vnfr, scalein=False):
        """Terminate the VNF """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def terminate_vl(self, vlr):
        """Terminate the Virtual Link Record"""
        pass
