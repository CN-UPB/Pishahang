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
# import concurrent.futures as pool

# DL
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
# import seaborn as sns
from pylab import rcParams
import matplotlib.pyplot as plt
from matplotlib import rc


from sonmanobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:tfp")
LOG.setLevel(logging.INFO)


class TFPlugin(ManoBasePlugin):
    """
    This class implements the Traffic Forecasting Plugin.
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
        # broker and register the Traffic Forecasting plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the Traffic Forecasting plugin"

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy Traffic Forecasting plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that Traffic Forecasting Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        topic = 'mano.service.tfp'
        self.manoconn.subscribe(self.tfp_request, topic)

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
        LOG.info("Traffic Forecasting plugin started and operational.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering Traffic Forecasting plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the Traffic Forecasting plugin
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
# TFP
##########################

    def tfp_request(self, ch, method, prop, payload):
        """
        This method handles a placement request
        """

        if prop.app_id == self.name:
            return

        content = yaml.load(payload)


def main():
    """
    Entry point to start plugin.
    :return:
    """
    # reduce messaging log level to have a nicer output for this plugin
    logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)
    logging.getLogger("son-mano-base:plugin").setLevel(logging.INFO)
    tfp = TFPlugin()

if __name__ == '__main__':
    main()
