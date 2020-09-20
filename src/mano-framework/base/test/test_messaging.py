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
import traceback
from itertools import product
from queue import Empty, Queue
from time import time
from typing import List

import pytest

from manobase.messaging import (
    AsyncioBrokerConnection,
    ManoBrokerConnection,
    ManoBrokerRequestResponseConnection,
    Message,
)

logging.getLogger("manobase.messaging").setLevel(logging.DEBUG)
LOG = logging.Logger(__name__)


@pytest.fixture
def receiver():
    """
    Common helper object fixture that hands out callback functions and allows to
    wait for messages received by them
    """

    class Receiver:
        def __init__(self):
            self._message_queues: List["Queue[Message]"] = [Queue() for _ in range(2)]
            self._exception_message: str = None

        def _check_message(self, message: Message):
            try:
                assert message.app_id is not None
                assert type(message.headers) is dict
            except AssertionError:
                self._exception_message = traceback.format_exc()

        def create_cbf(self, queue=0):
            def simple_subscribe_cbf(message: Message):
                self._check_message(message)
                LOG.debug("Callback function %d: Received %s", queue, message.payload)
                self._message_queues[queue].put(message)

            return simple_subscribe_cbf

        def create_callback_coroutine(self, queue=0):
            async def simple_subscribe_coroutine(message: Message):
                self._check_message(message)
                LOG.debug("Callback coroutine %d: Received %s", queue, message.payload)
                self._message_queues[queue].put(message)

            return simple_subscribe_coroutine

        def echo_cbf(self, message: Message):
            self._check_message(message)
            try:
                assert message.reply_to is not None
                assert message.correlation_id is not None
            except AssertionError:
                self._exception_message = traceback.format_exc()
            LOG.debug("Echo callback function: Received %s", message.payload)
            return message.payload

        async def echo_callback_coroutine(self, message: Message):
            self._check_message(message)
            assert message.reply_to is not None
            assert message.correlation_id is not None
            LOG.debug("Echo callback coroutine: Received %s", message.payload)
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
            try:
                while len(payloads) < number and time() < end_time:
                    payloads.append(
                        queue.get(block=True, timeout=end_time - time()).payload
                    )

                return payloads
            except Empty:
                raise Exception(
                    "Timeout reached, {:d} of {:d} messages received.".format(
                        len(payloads), number
                    )
                )

        def wait_for_particular_messages(self, payload, queue=0, timeout=5):
            """
            Waits until a message with a specified payload is received. Throws an
            exception if the message has not been received within the specified
            time.
            """
            queue = self._message_queues[queue]
            end_time = time() + timeout
            try:
                while time() < end_time:
                    if (
                        queue.get(block=True, timeout=end_time - time()).payload
                        == payload
                    ):
                        return
            except Empty:
                raise Exception(
                    'Timeout reached, message "{}" never found.'.format(payload)
                )

    receiver = Receiver()
    yield receiver
    if receiver._exception_message:
        pytest.fail(msg=receiver._exception_message)


@pytest.fixture
def connection(request):
    connection_class, is_loopback = request.param
    connection = connection_class(connection_class.__name__, is_loopback=is_loopback)
    yield connection
    connection.close()


def connection_classes(*args):
    """
    Sets the classes that the `connection` fixture uses. Each class is used once with
    `is_loopback=False` and once with `is_loopback=True`.
    """

    return pytest.mark.parametrize(
        "connection", product(args, (False, True)), indirect=["connection"]
    )


# Test ManBrokerConnection functions
@connection_classes(
    ManoBrokerConnection, ManoBrokerRequestResponseConnection, AsyncioBrokerConnection
)
def test_connection(connection):
    """
    Test broker connection.
    """
    connection.publish("test.topic1", "testmessage")


@connection_classes(ManoBrokerConnection, AsyncioBrokerConnection)
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


# Test ManoBrokerRequestResponseConnection functions (which AsyncioBrokerConnection
# should support as well)
@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
def test_request_response(connection, receiver):
    """
    Test request/response messaging pattern.
    """

    def endpoint_callback(message):
        return message.payload + "-pong"

    connection.register_async_endpoint(endpoint_callback, "test.request")
    connection.call_async(receiver.create_cbf(), "test.request", "ping")

    assert ["ping-pong"] == receiver.wait_for_messages()


@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
def test_request_response_sync(connection, receiver):
    """
    Test request/response messaging pattern (synchronous).
    """
    connection.register_async_endpoint(receiver.echo_cbf, "test.request.sync")
    response = connection.call_sync("test.request.sync", "ping-pong", timeout=5)
    assert type(response) is Message
    assert "ping-pong" == response.payload


@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
def test_notification(connection, receiver):
    """
    Test notification messaging pattern.
    """
    connection.register_notification_endpoint(
        receiver.create_cbf(), "test.notification"
    )
    connection.notify("test.notification", "my-notification")
    receiver.wait_for_particular_messages("my-notification")


@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
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


@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
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


@connection_classes(ManoBrokerRequestResponseConnection, AsyncioBrokerConnection)
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


# Test AsyncioBrokerConnection
@connection_classes(AsyncioBrokerConnection)
def test_asyncio_publishsubscribe(connection, receiver):
    """
    Test publish / subscribe messaging.
    """
    connection.subscribe(receiver.create_callback_coroutine(), "test.asyncio.topic1")
    connection.publish("test.asyncio.topic1", "my-message")
    assert ["my-message"] == receiver.wait_for_messages()


@connection_classes(AsyncioBrokerConnection)
def test_asyncio_request_response(connection, receiver):
    """
    Test request/response messaging pattern with coroutine callbacks
    """

    async def endpoint_handler(message):
        return message.payload + "-pong"

    connection.register_async_endpoint(endpoint_handler, "test.asyncio.request")
    connection.call_async(
        receiver.create_callback_coroutine(), "test.asyncio.request", "ping"
    )

    assert ["ping-pong"] == receiver.wait_for_messages()


@connection_classes(AsyncioBrokerConnection)
def test_asyncio_notification(connection, receiver):
    """
    Test notification messaging pattern with coroutine callbacks
    """
    connection.register_notification_endpoint(
        receiver.create_callback_coroutine(), "test.asyncio.notification"
    )
    connection.notify("test.asyncio.notification", "my-notification")
    receiver.wait_for_particular_messages("my-notification")


@connection_classes(AsyncioBrokerConnection)
def test_asyncio_future_functions(connection: AsyncioBrokerConnection, receiver):
    """
    Test the `call()`, `subscribe_awaitable()`, `await_message()`, and
    `await_notification()` functions (implicitly tests `await_generic()`)
    """

    connection.subscribe_awaitable("test.await_message_1")
    connection.subscribe_awaitable("test.await_notification")

    async def handler(message: Message):
        # Test `call()`
        response_future = connection.call("test.call", "my-message")
        assert "my-message" == (await response_future).payload

        # Test `await_message()` with initial call to `subscribe_awaitable()`
        message_future = connection.await_message("test.await_message_1")
        connection.publish("test.await_message_1", "message-1")
        assert "message-1" == (await message_future).payload

        # Test `await_message()` with on-demand call to `subscribe_awaitable()`
        connection.subscribe_awaitable("test.await_message_2")
        message_future = connection.await_message("test.await_message_2")
        connection.publish("test.await_message_2", "message-2")
        assert "message-2" == (await message_future).payload

        # Test `await_notification()`
        message_future = connection.await_notification("test.await_notification")
        # Request with empty payload, should be ignored:
        connection.call_async(
            lambda message: None, "test.await_notification", "not-a-notification"
        )
        connection.notify("test.await_notification", "notification")
        assert "notification" == (await message_future).payload

        return "response-message"

    connection.register_async_endpoint(handler, "test.handler")
    connection.register_async_endpoint(receiver.echo_callback_coroutine, "test.call")

    connection.call_async(receiver.create_callback_coroutine(), "test.handler", "ping")
    assert ["response-message"] == receiver.wait_for_messages()
