"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.
This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).a
"""

import logging
import yaml
import os
from sonmanobase.plugin import ManoBasePlugin
from sonmanobase import messaging

import zmq
from time import sleep
import json
import hashlib

SDN_CONTROLLER_ADDRESS = "localhost"

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("son-mano-sdn")
LOG.setLevel(logging.DEBUG)
logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://{}:50165".format(SDN_CONTROLLER_ADDRESS))

class SDN(ManoBasePlugin):
    """
    This class implements the SDN plugin.
    """

    def __init__(self):

        # call super class (will automatically connect to
        # broker and register the SDN plugin to the plugin manger)
        self.version = "0.1"
        self.description = "SDN plugin"
        self.vlan = {}

        LOG.info("son-plugin.SDN initializing.")
        # register in the plugin manager
        super(self.__class__, self).__init__(version=self.version,
                                             description=self.description)

    def __del__(self):
        """
        Destroy SDN plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics to which we want to listen and define callback methods.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        self.manoconn.subscribe(self.on_sdn_chain_dploy, "chain.dploy.sdnplugin")
        LOG.info("son-plugin.SDN subscribing to topic chain.dploy.sdnplugin")


    def on_sdn_chain_dploy(self, ch, method, properties, payload):
        """
        Send IPs involved in chain to RYU controller via ZeroMQ.
        """
        LOG.info("son-plugin.SDN received chain chain.dploy.sdnplugin message")
        message = yaml.load(payload)

        # generate VLAN ID
        # use hashing to assign same VLAN ID for the same chain
        hash_val = hashlib.sha224(str(message)).hexdigest()
        try:
            vlan_id = max(vlan.values()) + 1
        except:
            vlan_id = 1
        vlan[hash_val] = vlan_id

        # build message to send to SDN controller
        # the following format is used
        # [
        #     { 'vlan': 42 },
        #     { 'ip': 10.0.0.1 },
        #     { 'ip': 10.0.0.2 },
        #     { 'ip': 10.0.0.3 },
        #     { 'ip': 10.0.0.4 }
        # ] 
        forwarding_graph = []
        forwarding_graph.append({'vlan': vlan_id})
        for ip in message:
            forwarding_graph.append({'ip': ip})

        socket.send_json({"forwarding_graph": message})
        LOG.debug("Received " + socket.recv_json()["reply"] + " event.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering SLM with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        LOG.info("son-plugin.SDN deregistered")
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the SLM is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.info("son-plugin.SDN registration ok event.")

def main():
    """
    Entry point to start plugin.
    :return:
    """
    # reduce messaging log level to have a nicer output for this plugin
    logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)
    logging.getLogger("son-mano-base:plugin").setLevel(logging.INFO)
#    logging.getLogger("amqp-storm").setLevel(logging.DEBUG)
    # create our service lifecycle manager
    LOG.info("son-plugin.SDN starting...")
    sdn = SDN()

if __name__ == '__main__':
    main()
