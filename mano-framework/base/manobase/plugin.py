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
import os
import time
from threading import Event, Thread
from uuid import uuid4

from amqpstorm import AMQPConnectionError

from manobase.messaging import AsyncioBrokerConnection, Message

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("manobase:plugin")


class ManoBasePlugin:
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
        use_loopback_connection=False,
        fake_registration=False,
    ):
        """
        Performs plugin initialization steps, e.g., connection setup
        :param name: Plugin name prefix
        :param version: Plugin version
        :param description: A description string
        :param auto_register: Automatically register on init
        :param wait_for_registration: Wait for registration before returning from init
        :param auto_heartbeat_rate: rate of automatic heartbeat notifications 1/n seconds. 0=deactivated
        :param use_loopback_connection: For unit testing: Whether to set up the connection with `is_loopback=True`
        :param fake_registration: For unit testing: Whether to fake the registration process without a real PluginManager instance involved
        """
        self.name = "%s.%s" % (name, self.__class__.__name__)
        self.version = version
        self.description = description
        self.uuid: str = None  # uuid given by plugin manager on registration
        self.state: str = None  # the state of this plugin READY/RUNNING/PAUSED/FAILED
        self._fake_registration = fake_registration

        self._registered_event = Event()

        LOG.info("Starting MANO Plugin: %s ...", self.name)

        # Initialize broker connection
        while True:
            try:
                self.conn = AsyncioBrokerConnection(
                    self.name, is_loopback=use_loopback_connection
                )
                break
            except AMQPConnectionError:
                time.sleep(5)
        self.manoconn = self.conn  # For backwards compatibility

        LOG.info("Plugin connected to broker.")

        self.declare_subscriptions()

        # Register at plugin manager
        if auto_register:
            self.register()
            if wait_for_registration:
                self._wait_for_registration()

        # Start hearbeat mechanism
        self._start_heartbeats(auto_heartbeat_rate)

        if start_running:
            self.run()

    def __del__(self):
        """
        Actions done when plugin is destroyed.
        :return:
        """
        # de-register this plugin
        self.deregister()
        self.conn.close()

    def _start_heartbeats(self, rate):
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

        Thread(target=run, daemon=True).start()

    def _send_heartbeat(self):
        self.conn.notify(
            "platform.management.plugin.%s.heartbeat" % str(self.uuid),
            {"uuid": self.uuid, "state": str(self.state)},
        )

    def declare_subscriptions(self):
        """
        Can be overwritten by subclass.
        But: The this superclass method should be called in any case.
        """
        # plugin status update subscription
        self.conn.register_notification_endpoint(
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

    def on_lifecycle_start(self, message: Message):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received lifecycle.start event.")
        self.state = "RUNNING"

    def on_lifecycle_pause(self, message: Message):
        """
        To be overwritten by subclass
        """
        LOG.debug("Received lifecycle.pause event.")
        self.state = "PAUSED"

    def on_lifecycle_stop(self, message: Message):
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

    def on_plugin_status_update(self, message: Message):
        """
        To be overwritten by subclass.
        Called when a plugin list status update
        is received from the plugin manager.
        """
        LOG.debug("Received plugin status update %s.", message.payload)

    def register(self):
        """
        Register this plugin at the plugin manager.
        """
        self.conn.run_coroutine(self._register())

    async def _register(self):
        if self._fake_registration:
            self.uuid = str(uuid4())
        else:
            response = (
                await self.conn.call(
                    "platform.management.plugin.register",
                    {
                        "name": self.name,
                        "version": self.version,
                        "description": self.description,
                    },
                )
            ).payload

            if response["status"] != "OK":
                LOG.debug("Response %r", response)
                LOG.error("Plugin registration failed. Exit.")
                exit(1)

            self.uuid = response["uuid"]

        self.state = "READY"

        LOG.info("Plugin registered with UUID: %s", self.uuid)
        self.on_registration_ok()

        self._register_lifecycle_endpoints()
        self._registered_event.set()

    def deregister(self):
        """
        De-registers the plugin at the plugin manager.
        """
        self.conn.run_coroutine(self._deregister())

    async def _deregister(self):
        LOG.info("De-registering plugin...")

        response = await self.conn.call(
            "platform.management.plugin.deregister", {"uuid": self.uuid},
        )

        if response.payload["status"] != "OK":
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
            base_topic = "platform.management.plugin.%s.lifecycle." % str(self.uuid)

            # lifecycle.start
            self.conn.register_notification_endpoint(
                self.on_lifecycle_start, base_topic + "start",
            )
            # lifecycle.pause
            self.conn.register_notification_endpoint(
                self.on_lifecycle_pause, base_topic + "pause",
            )
            # lifecycle.stop
            self.conn.register_notification_endpoint(
                self.on_lifecycle_stop, base_topic + "stop",
            )
