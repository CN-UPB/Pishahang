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

import functools
import json
import logging
import os
import threading
from threading import Event, Thread
from typing import Any, Callable, Dict
from uuid import uuid4

import amqpstorm
import yaml

logging.basicConfig(level=logging.INFO)
logging.getLogger("amqpstorm.channel").setLevel(logging.ERROR)
LOG = logging.getLogger("manobase:messaging")
LOG.setLevel(logging.INFO)

# if we don't find a broker configuration in our ENV, we use this URL as default
RABBITMQ_URL_FALLBACK = "amqp://guest:guest@localhost:5672/%2F"
# if we don't find a broker configuration in our ENV, we use this exchange as default
RABBITMQ_EXCHANGE_FALLBACK = "son-kernel"


class Message:
    """
    Represents a message from the message broker.
    """

    def __init__(
        self,
        topic: str,
        payload: Any = {},
        correlation_id: str = None,
        reply_to=None,
        headers={},
        message_id: str = None,
        channel: amqpstorm.Channel = None,
        app_id: str = None,
    ):
        """
        Note: Unless during unit tests, there's no need to manually create
        message objects.
        """
        self.topic = topic
        self.payload = payload
        self.correlation_id = correlation_id
        self.reply_to = reply_to
        self.headers = headers
        self.message_id = message_id
        self.channel = channel
        self.app_id = app_id

    @staticmethod
    def from_amqpstorm_message(message: amqpstorm.Message):
        """
        Initializes a new `Message` object with data from an AMQPStorm Message
        object (includes deserializing the body)
        """
        assert type(message) == amqpstorm.Message

        # Deserialize payload
        if "yaml" in message.content_type:
            payload = yaml.safe_load(message.body)
        elif "json" in message.content_type:
            payload = json.loads(message.body)
        else:
            LOG.warning(
                'Unsupported content type "%s" in message %r. Skipping deserialization!',
                message.content_type,
                message,
            )
            payload = message.body

        app_id = message.properties.get("app_id", None)
        if app_id == "":
            app_id = None

        headers = (
            {} if "headers" not in message.properties else message.properties["headers"]
        )

        return Message(
            topic=message.method["routing_key"],
            payload=payload,
            correlation_id=message.correlation_id,
            reply_to=None if message.reply_to == "" else message.reply_to,
            headers=headers,
            message_id=message.message_id,
            channel=message.channel,
            app_id=app_id,
        )


class ManoBrokerConnection:
    """
    This class encapsulates a bare RabbitMQ connection setup.
    It provides helper methods to easily publish/subscribe to a given topic.
    It uses the asynchronous adapter implementation of the amqpstorm library.
    """

    def __init__(self, app_id, **kwargs):
        """
        Initialize broker connection.
        :param app_id: string that identifies application

        """
        self.app_id = app_id
        # fetch configuration
        if "url" in kwargs:
            self.rabbitmq_url = kwargs["url"]
        else:
            self.rabbitmq_url = os.environ.get("broker_host", RABBITMQ_URL_FALLBACK)
        self.rabbitmq_exchange = os.environ.get(
            "broker_exchange", RABBITMQ_EXCHANGE_FALLBACK
        )

        self._connection: amqpstorm.UriConnection = None
        self.setup_connection()

    def __del__(self):
        self.stop_connection()

    def setup_connection(self):
        """
        Connect to rabbit mq using self.rabbitmq_url.
        """
        self._connection = amqpstorm.UriConnection(self.rabbitmq_url)
        return self._connection

    def stop_connection(self):
        """
        Stop all consuming threads and close the connection
        """
        self.stop_threads()
        if self._connection.is_open or self._connection.is_opening:
            self._connection.close()

    def stop_threads(self):
        """
        Deprecated: AMQPStorm stops the threads automatically by closing the channels on
        `stop_connection()`.
        """
        pass

    def publish(
        self,
        topic: str,
        payload,
        app_id: str = None,
        correlation_id: str = None,
        reply_to: str = None,
        headers: Dict[str, str] = {},
    ) -> None:
        """
        This method provides basic topic-based message publishing.

        :param topic: topic the message is published to
        :param payload: the message's payload (serializable object)
        :param app_id: The id of the app publishing the message (defaults to `self.app_id`)
        :return:
        """
        if app_id is None:
            app_id = self.app_id

        # Serialize message as yaml
        body = yaml.dump(payload)

        with self._connection.channel() as channel:  # Create a new channel
            # Declare the exchange to be used
            channel.exchange.declare(self.rabbitmq_exchange, exchange_type="topic")

            # Publish the message
            channel.basic.publish(
                body=body,
                routing_key=topic,
                exchange=self.rabbitmq_exchange,
                properties={
                    "app_id": app_id,
                    "content_type": "application/yaml",
                    "correlation_id": correlation_id
                    if correlation_id is not None
                    else "",
                    "reply_to": reply_to if reply_to is not None else "",
                    "headers": headers,
                },
            )
            LOG.debug("PUBLISHED to %s: %s", topic, payload)

    def subscribe(
        self,
        cbf: Callable[[Message], None],
        topic: str,
        subscription_queue: str = None,
        concurrent=True,
    ) -> str:
        """
        Subscribe to `topic` and invoke `cbf` for each received message. Starts a new
        thread that waits for messages and handles them. If `concurrent` is ``True``,
        each callback function invocation will be executed in a separate thread.
        Otherwise, the subscription thread will also execute the callback function, one
        call after another.

        :param cbf: A callback function that will be invoked with every received message on the specified topic
        :param topic: The topic to subscribe to
        :param subscription_queue: A custom consumer tag for the subscription (will be auto-generated if omitted)
        :param concurrent: Whether or not to spawn a new thread for each callback invocation
        :return: The subscription's consumer tag
        """

        # We create an individual consumer tag ("subscription_queue") for each subscription to allow
        # multiple subscriptions to the same topic.
        if subscription_queue is None:
            subscription_queue = "%s.%s.%s" % ("q", topic, uuid4())

        def _on_message_received(amqpstormMessage: amqpstorm.Message):
            # Create custom message object
            message = Message.from_amqpstorm_message(amqpstormMessage)

            # Call cbf of subscription
            if concurrent:
                Thread(
                    target=cbf, args=(message,), name=subscription_queue + ".callback"
                ).start()
            else:
                cbf(message)

            # Ack the message to let the broker know that message was delivered
            amqpstormMessage.ack()

        consumption_started_event = Event()

        def _subscriber():
            """
            A function that handles messages of the subscription.
            """
            with self._connection.channel() as channel:
                # declare exchange for this channel
                channel.exchange.declare(
                    exchange=self.rabbitmq_exchange, exchange_type="topic"
                )
                # create queue for subscription
                q = channel.queue
                q.declare(subscription_queue)
                # bind queue to given topic
                q.bind(
                    queue=subscription_queue,
                    routing_key=topic,
                    exchange=self.rabbitmq_exchange,
                )
                # recommended qos setting
                channel.basic.qos(100)
                # setup consumer (use queue name as tag)
                channel.basic.consume(
                    _on_message_received,
                    subscription_queue,
                    consumer_tag=subscription_queue,
                )
                try:
                    consumption_started_event.set()
                    # start consuming messages.
                    channel.start_consuming()
                except amqpstorm.exception.AMQPConnectionError:
                    pass
                except Exception:
                    LOG.exception(
                        "Error in subscription thread %s:", subscription_queue
                    )

        # Each subscriber runs in a separate thread
        LOG.debug("Starting new thread to consume %s", subscription_queue)
        Thread(target=_subscriber, name=subscription_queue).start()
        consumption_started_event.wait()

        LOG.debug("SUBSCRIBED to %s", topic)
        return subscription_queue


class ManoBrokerRequestResponseConnection(ManoBrokerConnection):
    """
    This class extends the ManoBrokerConnection class and adds functionality
    for a simple request/response messaging pattern on top of the topic-based
    publish/subscribe transport.

    The request/response implementation is strictly asynchronous on both sides:
    - the caller does not block and has to specify a callback function to
      receive a result (its even possible to receive multiple results because of
      the underlying publish/subscribe terminology).
    - the callee provides an RPC like endpoint specified by its topic and executes
      each request in an independent thread.
    """

    def __init__(self, app_id, **kwargs):
        super(ManoBrokerRequestResponseConnection, self).__init__(app_id, **kwargs)
        self._async_calls_pending: Dict[str, Dict] = {}
        self._async_calls_response_queues: Dict[str, str] = {}

    def _execute_async_endpoint_handler(
        self, handler: Callable[[Message], Any], message: Message, on_finish: Callable
    ):
        """
        Run `handler` with `message` and run `on_finish` with its return value.

        :param handler: The endpoint handler function to be executed
        :param message: The "request" message that triggered the execution
        :param on_finish: Callback function that is executed when `handler` returns
        :return: None
        """
        result = handler(message)
        on_finish(message, result)

    def _on_async_endpoint_handler_finished(self, request: Message, result):
        """
        Event method that is called when an async endpoint handler has returned.

        :param request: The request message
        :param result: The return value of the async handler
        :return: None
        """
        LOG.debug("Async execution finished.")
        # check if we have a reply destination
        if request.reply_to is None or request.reply_to == "NO_RESPONSE":
            return  # do not send a reply

        result = {} if result is None else result

        # Specify headers
        reply_headers = request.headers
        reply_headers.setdefault("key", None)
        reply_headers["type"] = "response"

        # Publish the reply with the result
        self.publish(
            request.reply_to,
            result,
            correlation_id=request.correlation_id,
            headers=reply_headers,
        )

    def _on_async_request_received(
        self,
        endpoint_executor: Callable[
            [Callable[[Message], Any], Message, Callable], None
        ],
        endpoint_handler: Callable[[Message], Any],
        on_handler_finished: Callable,
        message: Message,
    ):
        """
        Callback function that handles async requests by calling `endpoint_executor`
        with `endpoint_handler`, `message`, and `on_handler_finished`
        """
        # verify that the message is a request (reply_to != None)
        if message.reply_to is None:
            LOG.debug(
                'Async request received: Message on topic "%s" does not specify reply_to.'
                + " Assuming it's not a request and dropping the message.",
                message.topic,
            )
            return
        LOG.debug("Async request on topic %s received.", message.topic)
        endpoint_executor(
            endpoint_handler, message, on_handler_finished,
        )

    def _on_notification_received(self, callback_function, message: Message):
        """
        Callback function that handles notifications by calling `callback_function` with
        `message`
        """
        # verify that the message is a notification (reply_to == None)
        if message.reply_to is not None:
            LOG.debug("Notification cbf: reply_to is not None. Drop!")
            return
        LOG.debug("Notification on topic %r received.", message.topic)
        callback_function(message)

    def _on_async_response_received(self, message: Message):
        """
        Callback function that handles the response of a remote function call.

        :param message: The response message that has been received
        :return: None
        """
        # check if we really have a response, not a request
        if message.reply_to is not None:
            LOG.info(
                "Message with non-empty reply_to field (%s) received at response endpoint. "
                + "Dropping it, as it does not seem to be a response.",
                message.reply_to,
            )
            return

        corr_id = message.correlation_id
        if corr_id not in self._async_calls_pending:
            LOG.info(
                "Received unmatched call response on topic %s. Ignoring it.",
                message.topic,
            )
            return

        LOG.debug("Async response received. Matches via corr_id %r", corr_id)
        call_details = self._async_calls_pending.pop(corr_id)

        # Call callback function
        call_details["cbf"](message)

        # If no other call_async is using this queue, remove the queue
        queue_tag = call_details["queue"]
        queue_empty = True
        for other_call_details in self._async_calls_pending.values():
            if other_call_details["queue"] == queue_tag:
                queue_empty = False
                break
        if queue_empty:
            LOG.debug("Removing queue, as it is no longer used by any async call")
            try:
                message.channel.queue.delete()
            except amqpstorm.exception.AMQPConnectionError:
                pass
            self._async_calls_response_queues.pop(call_details["topic"])

    def call_async(
        self,
        cbf,
        topic: str,
        payload={},
        key="default",
        correlation_id: str = None,
        headers: Dict[str, str] = {},
    ):
        """
        Sends a request message to a topic. If a "register_async_endpoint" is listening to this topic,
        it will execute the request and reply. This method sets up the subscriber for this reply and calls it
        when the reply is received.

        :param cbf: Function that is called when reply is received.
        :param topic: Topic for this call.
        :param payload: The message payload (serializable object)
        :param key: additional header field
        :param correlation_id: used to match requests to replies. If correlation_id is not given, a new one is generated.
        :param headers: Dictionary with additional header fields.
        :return: The correlation_id used for the request message
        """
        if cbf is None:
            raise BaseException(
                "No callback function (cbf) given to call_async. Use notify if you want one-way communication."
            )
        # generate uuid to match requests and responses
        correlation_id = str(uuid4()) if correlation_id is None else correlation_id
        # initialize response subscription
        if topic not in self._async_calls_response_queues:
            subscription_queue = "%s.%s.%s" % ("q", topic, str(uuid4()))

            self.subscribe(self._on_async_response_received, topic, subscription_queue)
            # keep track of request
            self._async_calls_response_queues[topic] = subscription_queue
        else:
            # find the queue related to this topic
            subscription_queue = self._async_calls_response_queues[topic]

        self._async_calls_pending[correlation_id] = {
            "cbf": cbf,
            "topic": topic,
            "queue": subscription_queue,
        }

        # Set header defaults
        headers.setdefault("key", key)
        headers.setdefault("type", "request")

        # publish request message
        LOG.debug(
            "Async request made on %s, with correlation_id %s", topic, correlation_id
        )
        self.publish(
            topic,
            payload,
            reply_to=topic,
            correlation_id=correlation_id,
            headers=headers,
        )
        return correlation_id

    def register_async_endpoint(self, endpoint_handler, topic):
        """
        Executed by callees that want to expose the functionality implemented in cbf
        to callers that are connected to the broker.

        :param endpoint_handler: Function to be called when requests with the given topic and key are received
        :param topic: Topic for requests and responses
        :return: None
        """
        self.subscribe(
            functools.partial(
                self._on_async_request_received,
                self._execute_async_endpoint_handler,
                endpoint_handler,
                self._on_async_endpoint_handler_finished,
            ),
            topic,
        )
        LOG.debug(
            "Registered async endpoint: topic: %r handler: %r", topic, endpoint_handler
        )

    def notify(
        self,
        topic: str,
        payload={},
        key="default",
        correlation_id: str = None,
        headers: Dict[str, str] = {},
    ):
        """
        Sends a simple one-way notification that does not expect a reply.

        :param topic: topic for communication (callee needs to have a subscription to it)
        :param payload: actual message
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :return: None
        """
        # Set header defaults
        headers.setdefault("key", key)
        headers.setdefault("type", "notification")

        # publish request message
        self.publish(topic, payload, correlation_id=correlation_id, headers=headers)

    def register_notification_endpoint(self, endpoint_handler, topic, key="default"):
        """
        Wrapper for register_async_endpoint that allows to register
        notification endpoints that do not send responses after executing
        the callback function.

        :param endpoint_handler: function to be called when requests with the given topic and key are received
        :param topic: topic for requests and responses
        :param key:  optional identifier for endpoints (enables more than 1 endpoint per topic)
        :return: None
        """
        # TODO (bjoluc) The key is not used here! Also, there's no unit test for keys.
        return self.subscribe(
            functools.partial(self._on_notification_received, endpoint_handler), topic,
        )

    def call_sync(
        self,
        topic: str,
        payload={},
        key="default",
        correlation_id: str = None,
        headers: Dict[str, str] = {},
        timeout=20,  # a sync. request has a timeout
    ) -> Message:
        """
        Client method to sync. call an endpoint registered and bound to the given topic by any
        other component connected to the broker. The method waits for a response and returns it
        as a `manobase.messaging.Message` object.

        :param topic: topic for communication (callee has to be described to it)
        :param payload: The message payload (serializable object)
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :param timeout: time in s to wait for a response
        :return: message
        """
        # we use this event to wait for the response
        response_received_event = threading.Event()
        response = None

        def result_cbf(message):
            """
            define a local callback method which receives the response
            """
            nonlocal response
            response = message
            # release lock
            response_received_event.set()

        # do a normal async call
        self.call_async(
            result_cbf,
            topic=topic,
            payload=payload,
            key=key,
            correlation_id=correlation_id,
            headers=headers,
        )
        # block until we get our response
        response_received_event.wait(timeout)
        # return received response
        return response
