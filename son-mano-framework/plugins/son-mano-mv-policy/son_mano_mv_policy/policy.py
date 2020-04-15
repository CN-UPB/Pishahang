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

from pymongo import MongoClient

# import psutil
from son_mano_mv_policy import policy_helpers

from sonmanobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:mv-policy")
LOG.setLevel(logging.INFO)


class PolicyPlugin(ManoBasePlugin):
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
        # broker and register the Policy plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the Policy plugin"

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy Policy plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that Policy Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.policy_topic = 'mano.service.policy'
        self.manoconn.subscribe(self.policy_request, self.policy_topic)

        LOG.info("Subscribed to topic: " + str(self.policy_topic))

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
        LOG.info("Policy plugin started and operational.")
        # TEST: here

        import requests
        import yaml
        r = requests.get('https://raw.githubusercontent.com/CN-UPB/Pishahang/mvp-thesis/pish-examples/pwm-scripts/descriptors/multiversion/cirros1_mv_policy.yml')
        # print(r.text)
        PD = yaml.load(r.text, Loader=yaml.FullLoader)

        weights = [-4, -3, -4, 2, 3]
        prediction = { "mean": 400, "std": 100, "min": 800, "max": 1800 }
        meta = { "current_version": "cirros-image-1-gpu" }
        self.policy_decision(descriptor=PD, prediction=prediction, meta=meta)

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering Policy plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the Policy plugin
        is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.debug("Received registration ok event.")

##########################
# Policy
##########################

    def get_policy(self, service_name):
        client = MongoClient('mongodb://son-mongo:27017')
        db = client['son-catalogue-repository']
        pd = db['pd']
        _query = { "name": service_name  }

        policy_desp = pd.find_one(_query, {'_id': 0})
        if policy_desp is not None:
            LOG.info(policy_desp)

            return policy_desp
        else:
            LOG.info("Policy not found")
            return None

    def policy_request(self, ch, method, prop, payload):
        """
        This method handles a policy request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        LOG.info("Policy request for service: " + content['serv_id'])

        if content['request_type'] == 'get_policy':
            _policy = self.get_policy(content['service_name'])
            response = {}

            response['policy'] = _policy

            self.manoconn.notify(self.policy_topic,
                                yaml.dump(response),
                                correlation_id=prop.correlation_id)

            LOG.info("Policy response sent for service: " + content['serv_id'])
            LOG.info(response)

        elif content['request_type'] == 'get_policy_version':
            pass

        # Test 1
        # WEIGHTS --> [cost, over_provision, overhead, support_deviation, same_version]
        # WEIGHTS = [-4, -3, -4, 2, 3]
        # weights = descriptor["weights"]
        # prediction = { "mean": 800, "std": 100, "min": 800, "max": 1800 }
        # meta = { "current_version": "cirros-image-1-gpu" }

        # topology = content['topology']
        # descriptor = content['nsd'] if 'nsd' in content else content['cosd']
        # functions = content['functions'] if 'functions' in content else []
        # cloud_services = content['cloud_services'] if 'cloud_services' in content else []

        # policy = self.policy(descriptor, functions, cloud_services, topology)

        # response = {'mapping': policy}
        # topic = 'mano.service.place'

        # self.manoconn.notify(topic,
        #                      yaml.dump(response),
        #                      correlation_id=prop.correlation_id)

        # LOG.info("Policy response sent for service: " + content['serv_id'])
        # LOG.info(response)

    def policy_decision(self, descriptor, prediction, meta):
        """
        This is the default policy algorithm that is used if the SLM
        is responsible to perform the policy
        """
        supported_versions = policy_helpers.get_supported_versions(prediction=prediction, versions=descriptor["versions"])
        decision_matrix_df = policy_helpers.build_decision_matrix(prediction=prediction, meta=meta, versions=supported_versions)

        selected_type, selected_version = policy_helpers.get_policy_decision(decision_matrix_df, descriptor["weights"])

        LOG.info(decision_matrix_df)
        LOG.info("\nSelected version to deploy - {} - {}".format(selected_type, selected_version))
    
        # print("\nSelected version to deploy - ", selected_type, " : ", selected_version, "\n")


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
    policy = PolicyPlugin()

if __name__ == '__main__':
    main()
