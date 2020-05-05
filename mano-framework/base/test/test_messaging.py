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
from queue import Queue
from time import time
from typing import List

import pytest

from manobase.messaging import (
    ManoBrokerConnection,
    ManoBrokerRequestResponseConnection,
    Message,
)

logging.getLogger("manobase:messaging").setLevel(logging.DEBUG)
LOG = logging.Logger("manobase:messaging:test")


@pytest.fixture
def receiver():
    """
    Common helper object fixture that hands out callback functions and allows to
    wait for messages received by them
    """

    class Receiver:
        def __init__(self):
            self._message_queues: List["Queue[Message]"] = [Queue() for _ in range(2)]

        def create_cbf(self, queue=0):
            def simple_subscribe_cbf(message: Message):
                assert message.app_id is not None
                assert type(message.headers) is dict
                LOG.debug("SUBSCRIBE CBF %d: Received %s", queue, message.payload)
                self._message_queues[queue].put(message)

            return simple_subscribe_cbf

        def echo_cbf(self, message: Message):
            assert message.app_id is not None
            assert message.reply_to is not None
            assert message.correlation_id is not None
            assert type(message.headers) is dict
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
                payloads.append(
                    queue.get(block=True, timeout=end_time - time()).payload
                )

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

    return Receiver()


@pytest.fixture
def connection(request):
    connection_class = request.param
    print(connection_class.__name__)
    connection = connection_class(connection_class.__name__)
    yield connection
    connection.close()


def connection_classes(*args):
    """
    Sets the classes that the `connection` fixture uses
    """
    return pytest.mark.parametrize("connection", args, indirect=["connection"])


# Test ManBrokerConnection functions
@connection_classes(ManoBrokerConnection, ManoBrokerRequestResponseConnection)
def test_connection(connection):
    """
    Test broker connection.
    """
    connection.publish("test.topic1", "testmessage")


@connection_classes(ManoBrokerConnection)
def test_bare_publishsubscribe(connection, receiver):
    """
    Test publish / subscribe messaging.
    """
    connection.subscribe(receiver.create_cbf(), "test.topic2")
    connection.publish("test.topic2", "testmsg")
    assert ["testmsg"] == receiver.wait_for_messages()


@connection_classes(ManoBrokerConnection)
def test_multi_publish(connection, receiver):
    """
    Test publish / subscribe messaging.
    """
    connection.subscribe(receiver.create_cbf(), "test.topic3")
    for i in range(5):
        connection.publish("test.topic3", str(i))
    assert [str(i) for i in range(5)] == receiver.wait_for_messages(0, 5)


@connection_classes(ManoBrokerConnection)
def test_doulbe_subscription(connection, receiver):
    """
    Test publish / subscribe messaging.
    """
    for queue in range(2):
        connection.subscribe(receiver.create_cbf(queue), "test.topic4")

    for i in range(5):
        connection.publish("test.topic4", str(i))

    for queue in range(2):
        assert [str(i) for i in range(5)] == receiver.wait_for_messages(queue, 5)


# Test ManoBrokerRequestResponseConnection functions
@connection_classes(ManoBrokerRequestResponseConnection)
def test_request_response(connection, receiver):
    """
    Test request/response messaging pattern.
    """

    def endpoint_callback(message):
        return message.payload + "-pong"

    connection.register_async_endpoint(endpoint_callback, "test.request")
    connection.call_async(receiver.create_cbf(), "test.request", "ping")

    assert ["ping-pong"] == receiver.wait_for_messages()


@connection_classes(ManoBrokerRequestResponseConnection)
def test_request_response_sync(connection, receiver):
    """
    Test request/response messaging pattern (synchronous).
    """
    connection.register_async_endpoint(receiver.echo_cbf, "test.request.sync")
    response = connection.call_sync("test.request.sync", "ping-pong", timeout=5)
    assert type(response) is Message
    assert "ping-pong" == response.payload


@connection_classes(ManoBrokerRequestResponseConnection)
def test_notification(connection, receiver):
    """
    Test notification messaging pattern.
    """
    connection.register_notification_endpoint(
        receiver.create_cbf(), "test.notification"
    )
    connection.notify("test.notification", "my-notification")
    receiver.wait_for_particular_messages("my-notification")


@connection_classes(ManoBrokerRequestResponseConnection)
def test_notification_pub_sub_mix(connection, receiver):
    """
    Test notification messaging pattern mixed with basic pub/sub calls.
    """
    connection.register_notification_endpoint(
        receiver.create_cbf(0), "test.notification1"
    )
    connection.subscribe(receiver.create_cbf(0), "test.notification2")

    # Publish regular message to notification endpoint
    connection.publish("test.notification1", "n1")
    assert ["n1"] == receiver.wait_for_messages()

    # Publish notification to regular endpoint
    connection.notify("test.notification2", "n2")
    assert ["n2"] == receiver.wait_for_messages()


@connection_classes(ManoBrokerRequestResponseConnection)
def test_double_subscriptions(connection, receiver):
    """
    Ensure that messages are delivered to all subscriptions of a topic.
    (e.g. identifies queue setup problems)
    """
    for queue in range(2):
        connection.subscribe(receiver.create_cbf(queue), "test.double")

    # Publish a message
    connection.publish("test.double", "my-message")

    # enusre that it is received by each subscription
    for queue in range(2):
        receiver.wait_for_particular_messages("my-message", queue=queue)


@connection_classes(ManoBrokerRequestResponseConnection)
def test_interleaved_subscriptions(connection, receiver):
    """
    Ensure that interleaved subscriptions to the same topic do not lead to problems.
    """
    connection.subscribe(receiver.create_cbf(0), "test.interleave")

    # Do an async call on the same topic
    connection.register_async_endpoint(receiver.echo_cbf, "test.interleave")
    connection.call_async(receiver.create_cbf(1), "test.interleave", "ping-pong")
    assert ["ping-pong"] == receiver.wait_for_messages(queue=1)

    # Publish a message
    connection.publish("test.interleave", "my-message")

    # Ensure that the subscriber gets the message (and sees the ones from async_call)
    assert ["ping-pong", "ping-pong", "my-message"] == receiver.wait_for_messages(
        queue=0, number=3
    )
