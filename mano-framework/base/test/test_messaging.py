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
import unittest
from queue import Queue
from time import time
from typing import List

from manobase.messaging import (
    ManoBrokerConnection,
    ManoBrokerRequestResponseConnection,
    Message,
)

logging.getLogger("manobase:messaging").setLevel(logging.DEBUG)
LOG = logging.Logger("manobase:messaging:test")


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self._message_queues: List["Queue[Message]"] = [Queue() for _ in range(2)]
        self.m: ManoBrokerConnection = None

    def tearDown(self):
        self.m.stop_connection()

    def create_cbf(self, queue=0):
        def simple_subscribe_cbf(message: Message):
            self.assertIsNotNone(message.app_id)
            self.assertIsNotNone(message.headers)
            LOG.debug("SUBSCRIBE CBF %d: Received %s", queue, message.payload)
            self._message_queues[queue].put(message)

        return simple_subscribe_cbf

    def echo_cbf(self, message: Message):
        self.assertIsNotNone(message.app_id)
        self.assertIsNotNone(message.reply_to)
        self.assertIsNotNone(message.correlation_id)
        self.assertIsNotNone(message.headers)
        LOG.debug("REQUEST ECHO CBF: %s", message.payload)
        return message.payload

    def wait_for_messages(self, queue=0, number=1, timeout=5):
        """
        Waits until `number` messages are added to the specified message queue
        or until a timeout is reached. Returns a list of received message
        payloads.
        """
        queue = self._message_queues[queue]
        payloads = []
        end_time = time() + timeout
        while len(payloads) < number and time() < end_time:
            payloads.append(queue.get(block=True, timeout=end_time - time()).payload)

        return payloads

    def wait_for_particular_messages(self, payload, queue=0, timeout=5):
        """
        Waits until a message with a specified payload is received. Throws an
        exception if the message has not been received within the specified
        time.
        """
        queue = self._message_queues[queue]
        end_time = time() + timeout
        while time() < end_time:
            if queue.get(block=True, timeout=end_time - time()).payload == payload:
                return
        raise Exception(
            'Message "%s" never found. Subscription timeout reached.', payload
        )


class TestManoBrokerConnection(BaseTestCase):
    """
    Test basic broker interactions.
    """

    def setUp(self):
        super().setUp()
        self.m = ManoBrokerConnection("test-basic-broker-connection")

    def test_broker_connection(self):
        """
        Test broker connection.
        """
        self.m.publish("test.topic1", "testmessage")

    def test_broker_bare_publishsubscribe(self):
        """
        Test publish / subscribe messaging.
        """
        self.m.subscribe(self.create_cbf(), "test.topic2")
        self.m.publish("test.topic2", "testmsg")
        assert ["testmsg"] == self.wait_for_messages()

    def test_broker_multi_publish(self):
        """
        Test publish / subscribe messaging.
        """
        self.m.subscribe(self.create_cbf(), "test.topic3")
        for i in range(5):
            self.m.publish("test.topic3", str(i))
        assert [str(i) for i in range(5)] == self.wait_for_messages(0, 5)

    def test_broker_doulbe_subscription(self):
        """
        Test publish / subscribe messaging.
        """
        for queue in range(2):
            self.m.subscribe(self.create_cbf(queue), "test.topic4")

        for i in range(5):
            self.m.publish("test.topic4", str(i))

        for queue in range(2):
            assert [str(i) for i in range(5)] == self.wait_for_messages(queue, 5)


class TestManoBrokerRequestResponseConnection(BaseTestCase):
    """
    Test async. request/response and notification functionality.
    """

    def setUp(self):
        super().setUp()
        self.m = ManoBrokerRequestResponseConnection(
            "test-request-response-broker-connection"
        )

    def test_broker_connection(self):
        """
        Test broker connection.
        """
        self.m.notify("test.topic5", "simplemessage")

    def test_request_response(self):
        """
        Test request/response messaging pattern.
        """

        def endpoint_callback(message):
            return message.payload + "-pong"

        self.m.register_async_endpoint(endpoint_callback, "test.request")
        self.m.call_async(self.create_cbf(), "test.request", "ping")

        assert ["ping-pong"] == self.wait_for_messages()

    def test_request_response_sync(self):
        """
        Test request/response messaging pattern (synchronous).
        """
        self.m.register_async_endpoint(self.echo_cbf, "test.request.sync")
        response = self.m.call_sync("test.request.sync", "ping-pong", timeout=5)
        assert type(response) is Message
        assert "ping-pong" == response.payload

    def test_notification(self):
        """
        Test notification messaging pattern.
        """
        self.m.register_notification_endpoint(self.create_cbf(), "test.notification")
        self.m.notify("test.notification", "my-notification")
        self.wait_for_particular_messages("my-notification")

    def test_notification_pub_sub_mix(self):
        """
        Test notification messaging pattern mixed with basic pub/sub calls.
        """
        self.m.register_notification_endpoint(self.create_cbf(0), "test.notification1")
        self.m.subscribe(self.create_cbf(0), "test.notification2")

        # Publish regular message to notification endpoint
        self.m.publish("test.notification1", "n1")
        assert ["n1"] == self.wait_for_messages()

        # Publish notification to regular endpoint
        self.m.notify("test.notification2", "n2")
        assert ["n2"] == self.wait_for_messages()

    def test_double_subscriptions(self):
        """
        Ensure that messages are delivered to all subscriptions of a topic.
        (e.g. identifies queue setup problems)
        """
        for queue in range(2):
            self.m.subscribe(self.create_cbf(queue), "test.double")

        # Publish a message
        self.m.publish("test.double", "my-message")

        # enusre that it is received by each subscription
        for queue in range(2):
            self.wait_for_particular_messages("my-message", queue=queue)

    def test_interleaved_subscriptions(self):
        """
        Ensure that interleaved subscriptions to the same topic do not lead to problems.
        """
        self.m.subscribe(self.create_cbf(0), "test.interleave")

        # Do an async call on the same topic
        self.m.register_async_endpoint(self.echo_cbf, "test.interleave")
        self.m.call_async(self.create_cbf(1), "test.interleave", "ping-pong")
        assert ["ping-pong"] == self.wait_for_messages(queue=1)

        # Publish a message
        self.m.publish("test.interleave", "my-message")

        # Ensure that the subscriber gets the message (and sees the ones from async_call)
        assert ["ping-pong", "ping-pong", "my-message"] == self.wait_for_messages(
            queue=0, number=3
        )
