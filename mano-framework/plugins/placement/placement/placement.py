"""
Copyright (c) 2015 SONATA-NFV, 2017 Pishahang
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

Neither the name of the SONATA-NFV, Pishahang,
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

Parts of this work have been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

import logging

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:placement")
LOG.setLevel(logging.INFO)


class PlacementPlugin(ManoBasePlugin):
    def __init__(self, **kwargs):
        """
        Initialize class and manobase.plugin.BasePlugin class.
        This will automatically connect to the broker, contact the
        plugin manager, and self-register this plugin to the plugin
        manager.

        After the connection and registration procedures are done, the
        'on_lifecycle_start' method is called.
        """

        super().__init__(
            version="0.1-dev", description="This is the Placement plugin", **kwargs
        )

    def declare_subscriptions(self):
        """
        Declare topics that Placement Plugin subscribes on.
        """
        super().declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.manoconn.subscribe(self.placement_request, "mano.service.place")

    def on_lifecycle_start(self, message: Message):
        """
        This event is called when the plugin has successfully registered itself
        to the plugin manager and received its lifecycle.start event from the
        plugin manager. The plugin is expected to do its work after this event.

        :return:
        """
        super().on_lifecycle_start(message)
        LOG.info("Placement plugin started and operational.")

    ##########################
    # Placement
    ##########################

    def placement_request(self, message: Message):
        """
        This method handles a placement request
        """

        if message.app_id == self.name:
            return

        payload = message.payload
        LOG.info("Placement request for service: %s", payload["serv_id"])
        topology = payload["topology"]
        descriptor = payload["nsd"] if "nsd" in payload else payload["cosd"]
        functions = payload["functions"] if "functions" in payload else []
        cloud_services = (
            payload["cloud_services"] if "cloud_services" in payload else []
        )

        placement = self.placement(descriptor, functions, cloud_services, topology)

        response = {"mapping": placement}
        self.manoconn.notify(
            "mano.service.place", response, correlation_id=message.correlation_id,
        )

        LOG.info("Placement response sent for service: %s", payload["serv_id"])
        LOG.info(response)

    def placement(self, descriptor, functions, cloud_services, topology):
        """
        This is the default placement algorithm that is used if the SLM
        is responsible to perform the placement
        """
        LOG.info("Embedding started on following topology: %s", topology)

        mapping = {}

        for function in functions:
            vnfd = function["vnfd"]
            vdu = vnfd["virtual_deployment_units"]
            needed_cpu = vdu[0]["resource_requirements"]["cpu"]["vcpus"]
            needed_mem = vdu[0]["resource_requirements"]["memory"]["size"]
            needed_sto = vdu[0]["resource_requirements"]["storage"]["size"]

            for vim in topology:
                if vim["vim_type"] == "Kubernetes":
                    continue
                cpu_req = needed_cpu <= (vim["core_total"] - vim["core_used"])
                mem_req = needed_mem <= (vim["memory_total"] - vim["memory_used"])

                if cpu_req and mem_req:
                    mapping[function["id"]] = {}
                    mapping[function["id"]]["vim"] = vim["vim_uuid"]
                    vim["core_used"] = vim["core_used"] + needed_cpu
                    vim["memory_used"] = vim["memory_used"] + needed_mem
                    break

        for cloud_service in cloud_services:
            csd = cloud_service["csd"]
            vdu = csd["virtual_deployment_units"]
            needed_mem = 0
            if (
                "resource_requirements" in vdu[0]
                and "memory" in vdu[0]["resource_requirements"]
            ):
                needed_mem = vdu[0]["resource_requirements"]["memory"]["size"]

            for vim in topology:
                if vim["vim_type"] != "Kubernetes":
                    continue
                mem_req = needed_mem <= (vim["memory_total"] - vim["memory_used"])

                if mem_req:
                    mapping[cloud_service["id"]] = {}
                    mapping[cloud_service["id"]]["vim"] = vim["vim_uuid"]
                    vim["memory_used"] = vim["memory_used"] + needed_mem
                    break

        # Check if all VNFs and CSs have been mapped
        if len(mapping.keys()) == len(functions) + len(cloud_services):
            return mapping
        else:
            LOG.info("Placement was not possible")
            return None


def main():
    PlacementPlugin()


if __name__ == "__main__":
    main()
