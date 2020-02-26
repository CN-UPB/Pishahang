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
import concurrent.futures as pool
# import psutil

from sonmanobase.plugin import ManoBasePlugin

try:
    from son_mano_dummy_api import dummy_topics as t
except:
    import dummy_topics as t


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:dummy")
LOG.setLevel(logging.INFO)


class DummyPlugin(ManoBasePlugin):
    """
    This class implements the Function lifecycle manager.
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
        # broker and register the dummy plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the dummy plugin"

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy dummy plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that dummy Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        topic = 'mano.service.dummy'
        self.manoconn.subscribe(self.dummy_request, topic)
        self.manoconn.subscribe(self.dummy_resp_prepare_IA_mapping, t.DUMMY_IA_PREPARE)
        self.manoconn.subscribe(self.dummy_resp_vnf_depl_vnf_deploy, t.DUMMY_MANO_DEPLOY)
        self.manoconn.subscribe(self.dummy_resp_vnfs_csss_vnfs_csss, t.DUMMY_MANO_START)

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
        LOG.info("dummy plugin started and operational.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering dummy plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the dummy plugin
        is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.debug("Received registration ok event.")

##########################
# dummy
##########################

    def dummy_request(self, ch, method, prop, payload):
        """
        This method handles a dummy request
        """

        if prop.app_id == self.name:
            return


        content = yaml.load(payload)
        LOG.info("dummy request for service: " + content['serv_id'])
        topology = content['topology']
        descriptor = content['nsd'] if 'nsd' in content else content['cosd']
        functions = content['functions'] if 'functions' in content else []
        cloud_services = content['cloud_services'] if 'cloud_services' in content else []

        response = {'mapping': dummy}
        topic = 'mano.service.place'

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        LOG.info("dummy response sent for service: " + content['serv_id'])
        LOG.info(response)

    def dummy_resp_prepare_IA_mapping(self, ch, method, prop, payload):
        """
        This method handles a IA_mapping request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        LOG.info("dummy IA_mapping request for service: " + content['instance_id'])

        response = t.dummy_resp_prepare_IA_mapping_data

        topic = t.DUMMY_IA_PREPARE

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        LOG.info("dummy response sent for service: " + content['instance_id'])
        LOG.info(response)

#
    def dummy_resp_vnf_depl_vnf_deploy(self, ch, method, prop, payload):
        """
        This method handles a vnf_deploy request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        LOG.info("dummy vnf_deploy request for service: " + content['service_instance_id'])
        # LOG.info(content)

        # response = t.dummy_resp_vnf_depl_vnf_deploy_data

        response = {'instanceName': 'SonataService-{}'.format(content['service_instance_id']), 'instanceVimUuid': '101a4acd-2f8d-43a7-83f3-fb64bfd543dd', 'message': '', 'vimUuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'vnfr': {'status': 'offline', 'descriptor_reference': '81ff5d93-339d-4274-856a-6575940e7023', 'descriptor_version': 'vnfr-schema-01', 'id': content['vnfd']['instance_uuid'], 'virtual_deployment_units': [{'id': 'cirros-image-1', 'number_of_instances': 1, 'vdu_reference': 'cirros-image-1:cirros-image-1', 'vm_image': 'cirros-image-1', 'vnfc_instance': [{'id': '0', 'connection_points': [{'id': 'eth0', 'type': 'internal', 'interface': {'address': '10.0.5.69', 'hardware_address': 'fa:16:3e:9d:99:d8', 'netmask': '255.255.255.248'}}], 'vc_id': '08e5693a-2590-44ad-985a-0d5cea1d398b', 'vim_id': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06'}]}]}, 'request_status': 'COMPLETED'}

        topic = t.DUMMY_MANO_DEPLOY

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        LOG.info("dummy response sent for service: " + content['service_instance_id'])
        LOG.info(response)

    def dummy_resp_vnfs_csss_vnfs_csss(self, ch, method, prop, payload):
        """
        This method handles a vnfs_csss request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        LOG.info("dummy vnfs_csss request for service: " + content['serv_id'])

        # response = t.dummy_resp_vnfs_csss_vnfs_csss_data

        response = {'error': None, 'message': ': No start FSM provided, start event ignored.', 'status': 'COMPLETED', 'timestamp': time.time(), 'vnf_id': content['vnf_id']}

        topic = t.DUMMY_MANO_START

        self.manoconn.notify(topic,
                             yaml.dump(response),
                             correlation_id=prop.correlation_id)

        LOG.info("dummy response sent for service: " + content['serv_id'])
        LOG.info(response)

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
    dummy = DummyPlugin()

if __name__ == '__main__':
    main()
