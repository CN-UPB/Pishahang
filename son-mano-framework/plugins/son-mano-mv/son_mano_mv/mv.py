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

# import psutil
try:
    from son_mano_mv import mv_helpers as tools
except:
    import mv_helpers as tools

from sonmanobase.plugin import ManoBasePlugin

CLASSIFIER_IP="IP"
SWITCH_DEBUG = False
SWITCH_DEBUG_IMAGE_VM = "cirros-image-1-vm"
SWITCH_DEBUG_IMAGE_ACC = "cirros-image-1-acc"
SWITCH_DEBUG_IMAGE_CON = "cirros-image-1-con"

with open("MV-Logs.log", "w") as f:  
    f.truncate()

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:mv")
LOG.setLevel(logging.INFO)

fh = logging.FileHandler('MV-Logs.log')
fh.setLevel(logging.DEBUG)
LOG.addHandler(fh)

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
        # broker and register the Multi-version plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the Multiversion plugin"

        self.mon_metrics = {}
        # TODO: Make is consistant
        self.active_services = {}
        # self.EXP_REQ_TIME = 0

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy Multi-version plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that Multi-version Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        topic = 'mano.service.place'
        mv_mon_topic = 'mano.service.mv_mon'
        self.manoconn.subscribe(self.mon_policy_request, mv_mon_topic)
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
        LOG.info("Multi-version plugin started and operational.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering Multi-version plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the Multi-version plugin
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


##########################
# Placement
##########################

    def mon_policy_request(self, ch, method, prop, payload):
        """
        This method handles a MV Monitoringrequest
        """
        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        serv_id = content['serv_id']

        LOG.info("MV MON request for service: " + serv_id)
        # LOG.info(content)

        if content['request_type'] == "START":
            # LOG.info("EXP: Switch Time - {}".format(time.time() - self.EXP_REQ_TIME))
            is_nsd = content['is_nsd']
            version_image = content['version_image']
            self.active_services[serv_id] = {}
            self.active_services[serv_id]['charts'] = []
            self.active_services[serv_id]['vim_endpoint'] = ""
            self.active_services[serv_id]['function_versions'] = content['function_versions']
            self.active_services[serv_id]['version_changed'] = False
            self.active_services[serv_id]['version_image'] = version_image
            self.active_services[serv_id]['policy'] = content['policy']

            topology = content['topology']
            functions = content['functions'] if 'functions' in content else []
            cloud_services = content['cloud_services'] if 'cloud_services' in content else []
           
            if is_nsd:
                for _function in functions:
                    for _vdu in _function['vnfr']['virtual_deployment_units']:
                        for _vnfi in _vdu['vnfc_instance']:
                            # LOG.info(_vnfi)
                            for _t in topology:
                                # LOG.info(_t)
                                if _t['vim_uuid'] == _vnfi['vim_id']:
                                    _instance_id = tools.get_nova_server_info(serv_id, _t)
                                    _charts = tools.get_netdata_charts(_instance_id, _t, _function['vnfd'][version_image][0]['monitoring_parameters'])
                                    # LOG.info("Mon?")
                                    # LOG.info(_vdu['monitoring_parameters'])
                                    self.active_services[serv_id]['charts'] = _charts
                                    self.active_services[serv_id]['vim_endpoint'] = _t['vim_endpoint']
                                    self.active_services[serv_id]['metadata'] = content
                                    self.active_services[serv_id]['is_nsd'] = is_nsd                                                                        
                                    self.active_services[serv_id]['network'] = {
                                        "ip": _vnfi["connection_points"][0]["interface"]["address"],
                                        "port": 80
                                    }
                                    self.active_services[serv_id]['monitoring_parameters'] = _function['vnfd'][version_image][0]['monitoring_parameters']
                                    # self.active_services[serv_id]['monitoring_rules'] = _function['vnfd'][version_image][0]['monitoring_rules']
                                    # self.active_services[serv_id]['monitoring_config'] = _function['vnfd']['monitoring_config']
                                    self.active_services[serv_id]['deployed_version'] = content['deployed_version']

                                    # Start monitoring thread
                                    self.monitoring_policy_thread(serv_id)

                                    # Start Forecasting thread
                                    self.request_forecast_thread_start(serv_id)

                                    # tools.switch_classifier(
                                    #     classifier_ip=CLASSIFIER_IP,
                                    #     vnf_ip=self.active_services[serv_id]['network']['ip'],
                                    #     vnf_port=self.active_services[serv_id]['network']['port'])
            else:
                # LOG.info("Not OpenStack monitoting")
                for _function in cloud_services:
                    for _vdu in _function['csr']['virtual_deployment_units']:
                        # LOG.info(_vnfi)
                        for _t in topology:
                            # LOG.info(_t)
                            if _t['vim_uuid'] == _vdu['vim_id']:
                                # LOG.info("VNF is on")
                                # LOG.info(_vdu['vim_id'])
                                # LOG.info(_t['vim_endpoint'])
                                # FIXME: Timer for creation delay (Add a loop?)
                                time.sleep(10)
                                # _instance_timings = tools.get_k8_pod_times(serv_id, _t)
                                # LOG.info("EXP: K8 VIM Time - {}\n".format(
                                #         _instance_timings["vim_time"]
                                #         ))
                                # LOG.info("CSD scene")
                                # LOG.info(_function['csd'])
                                # FIXME: _function['csd'][version_image][0]['monitoring_parameters'] need to change this bs!                                
                                _instance_meta = tools.get_k8_pod_info(serv_id, _t)
                                _charts = tools.get_netdata_charts(_instance_meta['uid'], _t, _function['csd'][version_image][0]['monitoring_parameters'])
                                # LOG.info("K8 UUID")
                                # LOG.info(_instance_meta)
                                # LOG.info(_charts)
                                self.active_services[serv_id]['charts'] = _charts
                                self.active_services[serv_id]['vim_endpoint'] = _t['vim_endpoint']
                                self.active_services[serv_id]['metadata'] = content
                                self.active_services[serv_id]['is_nsd'] = is_nsd
                                self.active_services[serv_id]['ports'] = _instance_meta
                                self.active_services[serv_id]['monitoring_parameters'] = _function['csd'][version_image][0]['monitoring_parameters']
                                # self.active_services[serv_id]['monitoring_rules'] = _function['csd'][version_image][0]['monitoring_rules']
                                # self.active_services[serv_id]['monitoring_config'] = _function['csd']['monitoring_config']
                                self.active_services[serv_id]['deployed_version'] = content['deployed_version']
                                
                                # Start monitoring thread
                                self.monitoring_policy_thread(serv_id)

                                # Start Forecasting thread
                                self.request_forecast_thread_start(serv_id)

                                # tools.switch_classifier(
                                #     classifier_ip=CLASSIFIER_IP, 
                                #     vnf_ip=_instance_meta['ip'], 
                                #     vnf_port=_instance_meta['port'])

        elif content['request_type'] == "STOP":
            self.active_services.pop(serv_id, None)
            LOG.info("Monitoring stopped")

        else:
            LOG.info("Request type not suppoted")


    @tools.run_async
    def monitoring_policy_thread(self, serv_id):
        LOG.info("### Setting up monitoring thread: " + serv_id)
        self.active_services[serv_id]['fetching_version'] = False
        time.sleep(self.active_services[serv_id]['policy']['initial_observation_period'])
        while(serv_id in self.active_services):
            try:
                LOG.info("Monitoring Thread " + serv_id)
                _service_meta = self.active_services[serv_id]

                # _metrics = tools.get_netdata_charts_instance(_service_meta['charts'],
                #                                              _service_meta['vim_endpoint'],
                #                                              avg_sec=mon_config['average_range'])

                # LOG.info(json.dumps(_metrics, indent=4, sort_keys=True))

                # LOG.info("### CPU ###")
                # LOG.info(_metrics["cpu"])
                # LOG.info("### net ###")
                # LOG.info(_metrics["net"])

                # TODO: Add static switching flags

                if not self.active_services[serv_id]['version_changed']:
                    if self.active_services[serv_id]['is_nsd']:
                        # VM Monitoring
                        if SWITCH_DEBUG:
                            with open("/plugins/son-mano-mv/SWITCH_VNF") as f:  
                                data = f.read().rstrip()
                                # LOG.info("SWITCH_DEBUG:VM: " + data)
                                if data == "GPU":
                                    self.active_services[serv_id]['version_changed'] = True
                                    self.request_version_change(serv_id, switch_type="GPU", version_image=SWITCH_DEBUG_IMAGE_ACC)
                                if data == "CON":
                                    self.active_services[serv_id]['version_changed'] = True
                                    self.request_version_change(serv_id, switch_type="CON", version_image=SWITCH_DEBUG_IMAGE_CON)
                        else:
                            LOG.info("VM Monitoring")

                    else:
                        # GPU Monitoring
                        if SWITCH_DEBUG:
                            with open("/plugins/son-mano-mv/SWITCH_VNF") as f:  
                                data = f.read().rstrip()
                                # LOG.info("SWITCH_DEBUG:GPU: " + data)
                                if self.active_services[serv_id]['deployed_version'] == "CON":
                                    if data == "GPU":
                                        self.active_services[serv_id]['version_changed'] = True
                                        self.request_version_change(serv_id, switch_type="GPU", version_image=SWITCH_DEBUG_IMAGE_ACC)
                                    if data == "VM":
                                        self.active_services[serv_id]['version_changed'] = True
                                        self.request_version_change(serv_id, switch_type="VM", version_image=SWITCH_DEBUG_IMAGE_VM)
                                if self.active_services[serv_id]['deployed_version'] == "GPU":
                                    if data == "CON":
                                        self.active_services[serv_id]['version_changed'] = True
                                        self.request_version_change(serv_id, switch_type="CON", version_image=SWITCH_DEBUG_IMAGE_CON)
                                    if data == "VM":
                                        self.active_services[serv_id]['version_changed'] = True
                                        self.request_version_change(serv_id, switch_type="VM", version_image=SWITCH_DEBUG_IMAGE_VM)
                        else:
                            LOG.info("GPU/CON Monitoring")
                            # Get best version
                            if not self.active_services[serv_id]['fetching_version']:
                                self.active_services[serv_id]['fetching_version'] = True
                                self.request_policy_version(serv_id)

                            # FIXME: Better way to switch back
                            time.sleep(10)
                            if self.active_services[serv_id]['fetching_version']:
                                self.active_services[serv_id]['fetching_version'] = False


            except Exception as e:
                LOG.error("Error")
                LOG.error(e)

            if SWITCH_DEBUG:
                time.sleep(2)
            else:
                # TODO: Policy data
                time.sleep(self.active_services[serv_id]['policy']['monitoring_config']['fetch_frequency'])

        LOG.info("### Stopping monitoring thread for: " + serv_id)

    def request_forecast_thread_start(self, serv_id):
        MANO_FORECAST = "mano.service.forecast"

        content = self.active_services[serv_id]
        content['serv_id'] = serv_id
        content['request_type'] = "start_forecast_thread"

        # self.EXP_REQ_TIME = time.time()
        # LOG.info("EXP: Req Time - {}".format(self.EXP_REQ_TIME))
        self.manoconn.call_async(self.resp_forecast_thread_start,
                                MANO_FORECAST,
                                yaml.dump(content))

    def resp_forecast_thread_start(self):
        LOG.info("MV Handle Forecast Response ")

    def request_policy_version(self, serv_id):
        corr_id = str(uuid.uuid4())
        # self.services[serv_id]['act_corr_id'] = corr_id

        MV_POLICY = "mano.service.policy"
        content = {}
        content['serv_id'] = serv_id
        content['policy'] = self.active_services[serv_id]['policy']

        _meta = {
            "current_version": self.active_services[serv_id]['deployed_version']
        }

        content['meta'] = _meta
        content['request_type'] = 'get_policy_version'   
        
        # 
        # self.EXP_REQ_TIME = time.time()
        # LOG.info("EXP: Req Time - {}".format(self.EXP_REQ_TIME))
        self.manoconn.call_async(self.handle_resp_policy_version,
                                MV_POLICY,
                                yaml.dump(content),
                                correlation_id=corr_id)


    def handle_resp_policy_version(self, ch, method, prop, payload):
        LOG.info("MV Policy Version Response")
        content = yaml.load(payload)
        deployment = content["deployment"]
        serv_id = content["serv_id"]

        if deployment is None:
            LOG.info("Prediction not ready or failed")
        else:
            LOG.info(deployment)

        self.active_services[serv_id]['fetching_version'] = False


    def request_version_change(self, serv_id, switch_type, version_image):
        MV_CHANGE_VERSION = "mano.instances.change"
        content = self.active_services[serv_id]['metadata']
        content['function_versions'] = self.active_services[serv_id]['function_versions']

        if switch_type == "VM":
            LOG.info("Switch to VM")
            as_vm = True
            as_container = False
            as_accelerated = False
        elif switch_type == "GPU":
            LOG.info("Switch to GPU")
            as_vm = False
            as_container = False
            as_accelerated = True
        elif switch_type == "CON":
            LOG.info("Switch to CON")
            as_vm = False
            as_container = True
            as_accelerated = False

        content['as_vm'] = as_vm
        content['as_container'] = as_container
        content['as_accelerated'] = as_accelerated
        content['version_image'] = version_image        

        # self.EXP_REQ_TIME = time.time()
        # LOG.info("EXP: Req Time - {}".format(self.EXP_REQ_TIME))
        self.manoconn.call_async(self.handle_resp_change,
                                MV_CHANGE_VERSION,
                                yaml.dump(content))

    def handle_resp_change(self):
        LOG.info("MV Handle Change Request ")

    def placement_request(self, ch, method, prop, payload):
        """
        This method handles a placement request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        LOG.info("MV placement request for service: " + content['serv_id'])
        LOG.info(content)

        as_vm, as_container, as_accelerated = False, False, False
        
        if content['as_vm']:
            as_vm = True
        elif content['as_container']:
            as_container = True
        elif content['as_accelerated']:
            as_accelerated = True

        result_data = {
            "as_vm": as_vm,
            "as_container": as_container,
            "as_accelerated": as_accelerated,
            "version_image": content['version_image']
        }

        LOG.info("MV request for service: " + content['serv_id'])
        topology = content['topology']
        descriptor = content['nsd']
        functions = content['functions']

        placement = self.placement(descriptor, functions, topology, result_data)

        response = {'mapping': placement}
        topic = 'mano.service.place'

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        # LOG.info("MV response sent for service: " + content['serv_id'])
        # LOG.info(response)

    def placement(self, descriptor, functions, topology, result_data):
        """
        This is the default placement algorithm that is used if the SLM
        is responsible to perform the placement
        """
        LOG.info("MV Embedding started on following topology: " + str(topology))

        as_vm, as_container, as_accelerated = result_data["as_vm"], result_data["as_container"], result_data["as_accelerated"]
        version_image = result_data['version_image']
        # LOG.info("\n\nas_vm: ", str(as_vm), "\n\nas_container: ", str(as_container), "\n\nas_accelerated: ", str(as_accelerated))

        # LOG.info("as_vm")
        # LOG.info(as_vm)
        # LOG.info("as_container")
        # LOG.info(as_container)
        # LOG.info("as_accelerated")
        # LOG.info(as_accelerated)

        mapping = {}
        mapping_counter = 0
        # FIXME: designed only for 1
        is_nsd = True

        if as_vm:
            # FIXME: should support multiple VDU?
            cloud_services = []
            # LOG.info("VM Mapping")
            for function in functions:

                function['vnfd']['virtual_deployment_units'] = function['vnfd'][version_image]
                vnfd = function['vnfd']
                vdu = vnfd['virtual_deployment_units']
                needed_cpu = vdu[0]['resource_requirements']['cpu']['vcpus']
                needed_mem = vdu[0]['resource_requirements']['memory']['size']
                needed_sto = vdu[0]['resource_requirements']['storage']['size']

                for vim in topology:
                    if vim['vim_type'] == 'Heat':
                        cpu_req = needed_cpu <= (vim['core_total'] - vim['core_used'])
                        mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                        if cpu_req and mem_req:
                            function["vim_uuid"] = vim['vim_uuid']
                            vim['core_used'] = vim['core_used'] + needed_cpu
                            vim['memory_used'] = vim['memory_used'] + needed_mem
                            mapping_counter += 1
                            break

        elif as_accelerated:
            # FIXME: should support multiple VDU?
            # LOG.info("Accelerated Mapping")
            cloud_services = functions
            functions = []

            for cloud_service in cloud_services:
                cloud_service['csd'] = cloud_service['vnfd']
                cloud_service['csd']['virtual_deployment_units'] = cloud_service['vnfd'][version_image]
                csd = cloud_service['csd']

                vdu = csd['virtual_deployment_units']
                needed_mem = 0
                if 'resource_requirements' in vdu[0] and 'memory' in vdu[0]['resource_requirements']:
                    needed_mem = vdu[0]['resource_requirements']['memory']['size']

                for vim in topology:

                    # For our use case, we use kubernetes for accelerated images
                    if vim['vim_type'] != 'Kubernetes':
                        continue
                    mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                    if mem_req:
                        cloud_service["vim_uuid"] = vim['vim_uuid']
                        vim['memory_used'] = vim['memory_used'] + needed_mem
                        mapping_counter += 1
                        is_nsd = False
                        break

        elif as_container:
            # FIXME: should support multiple VDU?
            cloud_services = functions
            functions = []

            for cloud_service in cloud_services:
                LOG.info("VM Mapping")

                cloud_service['csd'] = cloud_service['vnfd']
                cloud_service['csd']['virtual_deployment_units'] = cloud_service['vnfd'][version_image]
                csd = cloud_service['csd']

                vdu = csd['virtual_deployment_units']
                needed_mem = 0
                if 'resource_requirements' in vdu[0] and 'memory' in vdu[0]['resource_requirements']:
                    needed_mem = vdu[0]['resource_requirements']['memory']['size']

                for vim in topology:

                    # For our use case, we use kubernetes for accelerated images
                    if vim['vim_type'] != 'Kubernetes':
                        continue
                    mem_req = needed_mem <= (vim['memory_total'] - vim['memory_used'])

                    if mem_req:
                        cloud_service["vim_uuid"] = vim['vim_uuid']
                        vim['memory_used'] = vim['memory_used'] + needed_mem
                        mapping_counter += 1
                        is_nsd = False
                        break

        mapping["functions"] = functions
        mapping["cloud_services"] = cloud_services
        mapping["is_nsd"] = is_nsd

        # LOG.info("Functions \n\n\n")
        # LOG.info(functions)

        # LOG.info("Cloud_services \n\n\n")
        # LOG.info(cloud_services)

        # LOG.info("Mapping \n\n\n")
        # LOG.info(mapping)

        # Check if all VNFs and CSs have been mapped
        if mapping_counter == len(functions) + len(cloud_services):
            return mapping
        else:
            LOG.info("Placement was not possible")
            return None

        return mapping


    # def run(self):
    #     while(True):
            # time.sleep(10)


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
