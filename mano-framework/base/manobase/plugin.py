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
import os
import threading
import time

import amqpstorm

from manobase import messaging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("manobase:plugin")
LOG.setLevel(logging.DEBUG)


class ManoBasePlugin(object):
    """
    Abstract class that should be inherited by other MANO plugins.
    This class provides basic mechanisms to
    - connect to the broker
    - send/receive async/sync request/response calls
    - send/receive notifications
    - register / de-register plugin to plugin manager

    It also implements an automatic heartbeat mechanism that periodically sends
    heartbeat notifications.
    """

    def __init__(
        self,
        name="son-plugin",
        version=None,
        description=None,
        auto_register=True,
        wait_for_registration=True,
        start_running=True,
        auto_heartbeat_rate=0.5,
    ):
        """
        Performs plugin initialization steps, e.g., connection setup
        :param name: Plugin name prefix
        :param version: Plugin version
        :param description: A description string
        :param auto_register: Automatically register on init
        :param wait_for_registration: Wait for registration before returning from init
        :param auto_heartbeat_rate: rate of automatic heartbeat notifications 1/n seconds. 0=deactivated
        :return:
        """
        self.name = "%s.%s" % (name, self.__class__.__name__)
        self.version = version
        self.description = description
        self.uuid = None  # uuid given by plugin manager on registration
        self.state = None  # the state of this plugin READY/RUNNING/PAUSED/FAILED

        self._registered_event = threading.Event()

        LOG.info("Starting MANO Plugin: %s ...", self.name)
        # create and initialize broker connection
        while True:
            try:
                self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)
                break
            except amqpstorm.AMQPConnectionError:
                time.sleep(5)
        # register subscriptions
        LOG.info("Plugin connected to broker.")

        self.declare_subscriptions()
        # register to plugin manager
        if auto_register:
            while self.uuid is None:
                self.register()
                if wait_for_registration:
                    self._wait_for_registration()
        # kick-off automatic heartbeat mechanism
        self._auto_heartbeat(auto_heartbeat_rate)
        # jump to run
        if start_running:
            self.run()

    def __del__(self):
        """
        Actions done when plugin is destroyed.
        :return:
        """
        # de-register this plugin
        self.deregister()
        self.manoconn.stop_connection()
        self.manoconn.stop_threads()
        del self.manoconn

    def _auto_heartbeat(self, rate):
        """
        A simple periodic heartbeat mechanism.
        (much room for improvements here)
        :param rate: rate of heartbeat notifications
        :return:
        """
        if rate <= 0:
            return

        def run():
            while True:
                if self.uuid is not None:
                    self._send_heartbeat()
                time.sleep(1 / rate)

        # run heartbeats in separated thread
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def _send_heartbeat(self):
        self.manoconn.notify(
            "platform.management.plugin.%s.heartbeat" % str(self.uuid),
            {"uuid": self.uuid, "state": str(self.state)},
        )

    def declare_subscriptions(self):
        """
        Can be overwritten by subclass.
        But: The this superclass method should be called in any case.
        """
        # plugin status update subscription
        self.manoconn.register_notification_endpoint(
            self.on_plugin_status_update,  # call back method
            "platform.management.plugin.status",
        )

    def run(self):
        """
        To be overwritten by subclass
        """
        # go into infinity loop (we could do anything here)
        while True:
            time.sleep(1)

    def on_lifecycle_start(self, message: messaging.Message):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received lifecycle.start event.")
        self.state = "RUNNING"

    def on_lifecycle_pause(self, message: messaging.Message):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received lifecycle.pause event.")
        self.state = "PAUSED"

    def on_lifecycle_stop(self, message: messaging.Message):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received lifecycle.stop event.")
        self.deregister()
        os._exit(0)

    def on_registration_ok(self):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received registration ok event.")
        pass

    def on_plugin_status_update(self, message: messaging.Message):
        """
        To be overwritten by subclass.
        Called when a plugin list status update
        is received from the plugin manager.
        """
        LOG.debug("Received plugin status update %s.", message.payload)

    def register(self):
        """
        Send a register request to the plugin manager component to announce this plugin.
        """
        self.manoconn.call_async(
            self._on_register_response,
            "platform.management.plugin.register",
            {
                "name": self.name,
                "version": self.version,
                "description": self.description,
            },
        )

    def _on_register_response(self, message: messaging.Message):
        """
        Event triggered when register response is received.
        :param props: response properties
        :param response: response body
        :return: None
        """
        response = message.payload
        if response["status"] != "OK":
            LOG.debug("Response %r", response)
            LOG.error("Plugin registration failed. Exit.")
            exit(1)
        self.uuid = response["uuid"]
        # mark this plugin to be ready to be started
        self.state = "READY"
        LOG.info("Plugin registered with UUID: %s", response["uuid"])
        # jump to on_registration_ok()
        self.on_registration_ok()
        # subscribe to start topic
        self._register_lifecycle_endpoints()
        self._registered_event.set()

    def deregister(self):
        """
        Send a deregister event to the plugin manager component.
        """
        LOG.info("De-registering plugin...")
        self.manoconn.call_async(
            self._on_deregister_response,
            "platform.management.plugin.deregister",
            {"uuid": self.uuid},
        )

    def _on_deregister_response(self, message: messaging.Message):
        """
        Event triggered when de-register response is received.
        :param props: response properties
        :param response: response body
        :return: None
        """
        if message.payload["status"] != "OK":
            LOG.error("Plugin de-registration failed. Exit.")
            exit(1)
        self.uuid = None
        self._registered_event.clear()
        LOG.info("Plugin de-registered.")

    def _wait_for_registration(self, timeout=5):
        """
        Method to block until the registration is completed or a timeout reached.
        :param timeout: Timeout in seconds
        :return: None
        """
        LOG.debug("Waiting for registration (timeout=%d) ...", timeout)
        self._registered_event.wait(timeout)

    def _register_lifecycle_endpoints(self):
        if self.uuid is not None:
            # lifecycle.start
            self.manoconn.register_notification_endpoint(
                self.on_lifecycle_start,  # call back method
                "platform.management.plugin.%s.lifecycle.start" % str(self.uuid),
            )
            # lifecycle.pause
            self.manoconn.register_notification_endpoint(
                self.on_lifecycle_pause,  # call back method
                "platform.management.plugin.%s.lifecycle.pause" % str(self.uuid),
            )
            # lifecycle.stop
            self.manoconn.register_notification_endpoint(
                self.on_lifecycle_stop,  # call back method
                "platform.management.plugin.%s.lifecycle.stop" % str(self.uuid),
            )
