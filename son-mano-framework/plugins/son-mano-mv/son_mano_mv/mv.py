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
import time
import os
import requests
import copy
import uuid
import json
import threading
import sys
import csv
import concurrent.futures as pool
# from multi_version import CreateTemplate
from son_mano_mv.multi_version import CreateTemplate

# import psutil

from sonmanobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:mv")
LOG.setLevel(logging.INFO)


class MVPlugin(ManoBasePlugin):
    """
    This class implements the Multiversion Plugin.
    """

    def __init__(self,
                 auto_register=True,
                 wait_for_registration=True,
                 start_running=True):
        """
        Initialize class and son-mano-base.plugin.BasePlugin class.
        This will automatically connect to the broker, contact the
        plugin manager, and self-register this plugin to the plugin
        manager.

        After the connection and registration procedures are done, the
        'on_lifecycle_start' method is called.
        :return:
        """

        # call super class (will automatically connect to
        # broker and register the Placement plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the Multiversion plugin"

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy Placement plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that Placement Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        topic = 'mano.service.place'
        self.manoconn.subscribe(self.placement_request, topic)

        LOG.info("Subscribed to topic: " + str(topic))

    def on_lifecycle_start(self, ch, mthd, prop, msg):
        """
        This event is called when the plugin has successfully registered itself
        to the plugin manager and received its lifecycle.start event from the
        plugin manager. The plugin is expected to do its work after this event.

        :param ch: RabbitMQ channel
        :param method: RabbitMQ method
        :param properties: RabbitMQ properties
        :param message: RabbitMQ message content
        :return:
        """
        super(self.__class__, self).on_lifecycle_start(ch, mthd, prop, msg)
        LOG.info("Placement plugin started and operational.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering Placement plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the Placement plugin
        is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.debug("Received registration ok event.")

    def remove_empty_values(self, line):
        """
        remove empty values (from multiple delimiters in a row)
        :param line: Receives the Line
        :return: sends back after removing the empty value
        """
        result = []
        for i in range(len(line)):
            if line[i] != "":
                result.append(line[i])
        return result

    def get_components_as(self, result_file):
        """
        This method processes the generated result file and pulls out as_vm, as_container and as_accelerated component
        from the file. To extract the components mentioned above, this method extracts all lines between #as_vm and an
        empty line. Similarly for #as_container and #as_accelerated.
        :param result_file: path of the result file generated.
        :return: returns as_vm, as_container and as_accelerated arrays with function_id as element.
        """
        as_vm = []
        as_container = []
        as_accelerated = []
        with open(result_file, "r") as result:
            with open(result_file, "r") as temp:
                reader = csv.reader(result, delimiter=" ")
                data = [row for row in temp]
                i = 0
                for row in reader:
                    i = i + 1
                    if len(row) is not 0 and row[0] == '#':
                        row = self.remove_empty_values(row)  # deal with multiple spaces in a row leading to empty values
                        if row[1] == 'as_vm:':
                            vm_i = i
                            while True:
                                if data[vm_i] == "" or data[vm_i] == '\n':
                                    # print("breaking out of loop")
                                    break
                                if data[vm_i] != "":
                                    as_vm.append(data[vm_i])
                                vm_i += 1

                        if row[1] == 'as_container:':
                            container_i = i
                            while True:
                                if data[container_i] == "" or data[container_i] == '\n':
                                    break
                                if data[container_i] != "":
                                    as_container.append(data[container_i])
                                container_i += 1
                        if row[1] == 'as_accelerated:':
                            accelerated_i = i
                            while True:
                                if data[accelerated_i] == "" or data[accelerated_i] == '\n':
                                    # print("breaking out of loop")
                                    break
                                if data[accelerated_i] != "":
                                    as_accelerated.append(data[accelerated_i])
                                accelerated_i += 1
        return as_vm, as_container, as_accelerated

##########################
# Placement
##########################

    def placement_request(self, ch, method, prop, payload):
        """
        This method handles a placement request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        #  calls create_template to create the template from the payload and returns created result file.
        result_file = CreateTemplate.create_template(content)

        LOG.info("MV request for service: " + content['serv_id'])
        topology = content['topology']
        descriptor = content['nsd'] if 'nsd' in content else content['cosd']
        functions = content['functions'] if 'functions' in content else []
        cloud_services = content['cloud_services'] if 'cloud_services' in content else []

        placement = self.placement(descriptor, functions, cloud_services, topology, result_file)

        response = {'mapping': placement}
        topic = 'mano.service.place'

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        LOG.info("MV response sent for service: " + content['serv_id'])
        LOG.info(response)

    def placement(self, descriptor, functions, cloud_services, topology, result_file):
        """
        This is the default placement algorithm that is used if the SLM
        is responsible to perform the placement
        """
        LOG.info("MV Embedding started on following topology: " + str(topology))

        as_vm, as_container, as_accelerated = self.get_components_as(result_file)
        vnf_name_id_mapping = CreateTemplate.get_name_id_mapping(descriptor)

        mapping = {}

        for function in functions:
            vnfd = function['vnfd']
            vdu = vnfd['virtual_deployment_units']
            vnf_id = CreateTemplate.get_function_id(vnfd['name'], vnf_name_id_mapping)
            needed_cpu = vdu[0]['resource_requirements']['cpu']['vcpus']
            needed_mem = vdu[0]['resource_requirements']['memory']['size']
            needed_sto = vdu[0]['resource_requirements']['storage']['size']

            for vim in topology:
                if vim['vim_type'] == 'Kubernetes':
                    for as_container_function in as_container:
                        if vnf_id in as_container_function:
                            cpu_req = needed_cpu <= (vim['core_total'] - vim['core_used'])
                            mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                            if cpu_req and mem_req:
                                mapping[function['id']] = {}
                                mapping[function['id']]['vim'] = vim['vim_uuid']
                                vim['core_used'] = vim['core_used'] + needed_cpu
                                vim['memory_used'] = vim['memory_used'] + needed_mem
                                break
                if vim['vim_type'] == 'Heat':
                    for as_vm_function in as_vm:
                        if vnf_id in as_vm_function:
                            cpu_req = needed_cpu <= (vim['core_total'] - vim['core_used'])
                            mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                            if cpu_req and mem_req:
                                mapping[function['id']] = {}
                                mapping[function['id']]['vim'] = vim['vim_uuid']
                                vim['core_used'] = vim['core_used'] + needed_cpu
                                vim['memory_used'] = vim['memory_used'] + needed_mem
                                break

                if vim['vim_type'] == 'Accelerated':
                    for as_accelerated_function in as_accelerated:
                        if vnf_id in as_accelerated_function:
                            cpu_req = needed_cpu <= (vim['core_total'] - vim['core_used'])
                            mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                            if cpu_req and mem_req:
                                mapping[function['id']] = {}
                                mapping[function['id']]['vim'] = vim['vim_uuid']
                                vim['core_used'] = vim['core_used'] + needed_cpu
                                vim['memory_used'] = vim['memory_used'] + needed_mem
                                break

        for cloud_service in cloud_services:
            csd = cloud_service['csd']
            vdu = csd['virtual_deployment_units']
            needed_mem = 0
            if 'resource_requirements' in vdu[0] and 'memory' in vdu[0]['resource_requirements']:
                needed_mem = vdu[0]['resource_requirements']['memory']['size']

            for vim in topology:
                if vim['vim_type'] != 'Kubernetes':
                    continue
                mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                if mem_req:
                    mapping[cloud_service['id']] = {}
                    mapping[cloud_service['id']]['vim'] = vim['vim_uuid']
                    vim['memory_used'] = vim['memory_used'] + needed_mem
                    break

        # Check if all VNFs and CSs have been mapped
        if len(mapping.keys()) == len(functions) + len(cloud_services):
            return mapping
        else:
            LOG.info("Placement was not possible")
            return None


def main():
    """
    Entry point to start plugin.
    :return:
    """
    # reduce messaging log level to have a nicer output for this plugin
    logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)
    logging.getLogger("son-mano-base:plugin").setLevel(logging.INFO)
#    logging.getLogger("amqp-storm").setLevel(logging.DEBUG)
    # create our function lifecycle manager
    placement = MVPlugin()

if __name__ == '__main__':
    main()
