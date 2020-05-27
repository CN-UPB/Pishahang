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
partner consortium (www.sonata-nfv.eu).
"""

import logging

import yaml

from manobase import messaging
from manobase.messaging import Message

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("fakeslm")

LOG.setLevel(logging.DEBUG)


class fakeslm_onboarding:
    def __init__(self):

        self.name = "fake-slm"
        self.version = "0.1-dev"
        self.description = "description"

        LOG.info("Starting fake SLM:...")

        # create and initialize broker connection
        self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)

        self.publish_nsd()

    def publish_nsd(self):
        LOG.info("Sending forwarding graph")
        with open("payload.yml", "r") as forwarding_graph:
            message = yaml.safe_load(forwarding_graph)
        self.manoconn.call_async(
            self._on_publish_nsd_response, "chain.dploy.sdnplugin", message
        )

    def _on_publish_nsd_response(self, message: Message):
        if type(message.payload) == dict:
            print(message.payload)
        self.manoconn.close()


def main():
    fakeslm_onboarding()


if __name__ == "__main__":
    main()
