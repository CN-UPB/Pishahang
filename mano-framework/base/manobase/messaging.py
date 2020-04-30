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

from concurrent import futures as pool
import json
import logging
import os
import threading
import uuid
from threading import Event
from typing import Any, Dict

import amqpstorm
import yaml
from amqpstorm.exception import AMQPConnectionError

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.ERROR)
LOG = logging.getLogger("manobase:messaging")
LOG.setLevel(logging.DEBUG)

# if we don't find a broker configuration in our ENV, we use this URL as default
RABBITMQ_URL_FALLBACK = "amqp://guest:guest@localhost:5672/%2F"
# if we don't find a broker configuration in our ENV, we use this exchange as default
RABBITMQ_EXCHANGE_FALLBACK = "son-kernel"


class Message:
    """
    Represents a message from the message broker.
    """

    def __init__(self, message: amqpstorm.Message):
        """
        Initializes a new `Message` object with data from an AMQPStorm Message object (includes
        deserializing the body)
        """
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
        self.payload: Any = payload

        self.channel: amqpstorm.Channel = message.channel
        self.method = message.method
        self.topic: str = self.method["routing_key"]
        self.correlation_id: str = message.correlation_id
        self.message_id: str = message.message_id
        self.reply_to: str = None if message.reply_to == "" else message.reply_to

        self.properties: Dict = message.properties
        # Convert empty strings in properties to None
        for k, v in self.properties.items():
            self.properties[k] = None if v == "" else v

    @property
    def headers(self):
        return {} if "headers" not in self.properties else self.properties["headers"]


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

        # create additional members
        self._connection: amqpstorm.UriConnection = None
        # trigger connection setup (without blocking)
        # TODO (bjoluc) "without blocking"?
        self.setup_connection()

        # Threading workers
        self.thrd_pool = pool.ThreadPoolExecutor(max_workers=100)
        # Track the workers
        self.tasks = []

    def setup_connection(self):
        """
        Connect to rabbit mq using self.rabbitmq_url.
        """
        self._connection = amqpstorm.UriConnection(self.rabbitmq_url)
        return self._connection

    def stop_connection(self):
        """
        Close the connection
        :return:
        """
        self._connection.close()

    def stop_threads(self):
        """
        Stop all the threads that are consuming messages
        """
        for task in self.tasks:
            task.cancel()

    def publish(
        self,
        topic,
        payload,
        app_id: str = None,
        correlation_id: str = "",
        reply_to: str = "",
        headers: Dict = {},
    ):
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
                    "correlation_id": correlation_id,
                    "reply_to": reply_to,
                    "headers": headers,
                },
            )
            LOG.debug("PUBLISHED to %s: %s", topic, payload)

    def subscribe(self, cbf, topic, subscription_queue=None):
        """
        Implements basic subscribe functionality.
        Starts a new thread for each subscription in which messages are consumed and the callback functions
        are called.

        :param cbf: callback function cbf(message)
        :param topic: topic to subscribe to
        :return:
        """

        def _on_message_received(amqpstormMessage: amqpstorm.Message):
            message = Message(amqpstormMessage)  # Create custom message object
            cbf(message)  # Call cbf of subscription
            amqpstormMessage.ack()  # Ack the message to let the broker know that message was delivered

        consumption_started_event = Event()

        def connection_thread():
            """
            Each subscription consumes messages in its own thread.
            :return:
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
                    # start consuming messages.
                    consumption_started_event.set()
                    channel.start_consuming()
                except AMQPConnectionError:
                    pass
                except BaseException:
                    LOG.exception("Error in subscription thread:")
                    channel.close()

        # Attention: We crate an individual queue for each subscription to allow multiple subscriptions
        # to the same topic.
        if subscription_queue is None:
            queue_uuid = str(uuid.uuid4())
            subscription_queue = "%s.%s.%s" % ("q", topic, queue_uuid)
        # each subscriber is an own thread
        LOG.debug("Starting new thread to consume %s", subscription_queue)
        task = self.thrd_pool.submit(connection_thread)

        self.tasks.append(task)

        # Make sure that consuming has started, before method finishes.
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
        self._async_calls_pending = {}
        self._async_calls_response_topics = {}
        # call superclass to setup the connection
        super(self.__class__, self).__init__(app_id, **kwargs)

    def _execute_async(self, async_finish_cbf, func, message: Message):
        """
        Run `func` and `async_finish_cbf` when it returns.

        :param async_finish_cbf: callback function
        :param func: function to execute
        :param message: The "request" message that triggered this function call
        :return: None
        """
        # TODO (bjoluc) This is not "async". Do we want blocking behavior for
        # subscriptions or not?
        result = func(message)
        if async_finish_cbf is not None:
            async_finish_cbf(message, result)

        LOG.debug("Async execution finished: %r.", func)

    def _on_execute_async_finished(self, request: Message, result):
        """
        Event method that is called when an async. executed function
        has finishes its execution.
        :param request: The request message
        :param result: return value of executed function
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

    def _generate_on_async_request_received_cbf(self, cbf):
        """
        Generates a callback function. Only reacts if reply_to is set.
        CBF is executed asynchronously. Publishes CBF return value to reply to.
        :param cbf: function
        :return:
        """

        def _on_call_async_request_received(message: Message):
            # verify that the message is a request (reply_to != None)
            if message.reply_to is None:
                LOG.debug(
                    'Async request received: Message on topic "%s" does not specify reply_to.'
                    + " Assuming it's not a request and dropping the message.",
                    message.topic,
                )
                return
            LOG.debug("Async request on topic %s received.", message.topic)
            # call the user defined callback function (in a new thread to be async.
            self._execute_async(
                self._on_execute_async_finished,  # function called after execution of cbf
                cbf,  # function to be executed
                message,
            )

        return _on_call_async_request_received

    def _generate_on_notification_received_cbf(self, cbf):
        """
        Generates a callback function. Only reacts if reply_to is None.
        CBF is executed asynchronously.
        :param cbf: function
        :return:
        """

        def _on_notification_received(message: Message):
            # verify that the message is a notification (reply_to == None)
            if message.reply_to is not None:
                LOG.debug("Notification cbf: reply_to is not None. Drop!")
                return
            LOG.debug("Notification on topic %r received.", message.topic)
            # call the user defined callback function (in a new thread to be async.
            self._execute_async(None, cbf, message)

        return _on_notification_received

    def _on_call_async_response_received(self, message: Message):
        """
        Event method that is called on caller side when a response for an previously
        issued request is received. Might be called multiple times if more than one callee
        are subscribed to the used topic.
        :param message: Received message
        :return: None
        """
        # check if we really have a response, not a request
        if message.reply_to is not None:
            LOG.info(
                "Message with non-empty reply_to field received at response endpoint. "
                + "Dropping it, as it does not seem to be a response."
            )
            return
        if message.correlation_id in self._async_calls_pending.keys():
            LOG.debug(
                "Async response received. Matches to corr_id: %r",
                message.correlation_id,
            )
            # call callback (in new thread)
            self._execute_async(
                None, self._async_calls_pending[message.correlation_id]["cbf"], message
            )
            # if no other call_async is using this queue, remove the queue
            queue_tag = self._async_calls_pending[message.correlation_id]["queue"]
            queue_empty = True
            for corr_id in self._async_calls_pending.keys():
                if corr_id != message.correlation_id:
                    if self._async_calls_pending[corr_id]["queue"] == queue_tag:
                        queue_empty = False
                        break
            if queue_empty:
                LOG.debug("Removing queue, as it is no longer used by any async call")
                message.channel.queue.delete()
                del self._async_calls_response_topics[
                    self._async_calls_pending[message.correlation_id]["topic"]
                ]

            # remove from pending calls
            del self._async_calls_pending[message.correlation_id]

        else:
            LOG.debug("Received unmatched call response. Ignore it.")

    def call_async(
        self, cbf, topic, payload={}, key="default", correlation_id=None, headers={},
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
        :return:
        """
        if cbf is None:
            raise BaseException(
                "No callback function (cbf) given to call_async. Use notify if you want one-way communication."
            )
        # generate uuid to match requests and responses
        correlation_id = str(uuid.uuid4()) if correlation_id is None else correlation_id
        # initialize response subscription if a callback function was defined
        if topic not in self._async_calls_response_topics.keys():
            queue_uuid = str(uuid.uuid4())
            subscription_queue = "%s.%s.%s" % ("q", topic, queue_uuid)

            self.subscribe(
                self._on_call_async_response_received, topic, subscription_queue
            )
            # keep track of request
            self._async_calls_response_topics[topic] = subscription_queue
        else:
            # find the queue related to this topic
            subscription_queue = self._async_calls_response_topics[topic]

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

    def register_async_endpoint(self, cbf, topic):
        """
        Executed by callees that want to expose the functionality implemented in cbf
        to callers that are connected to the broker.
        :param cbf: function to be called when requests with the given topic and key are received
        :param topic: topic for requests and responses
        :return: None
        """
        self.subscribe(self._generate_on_async_request_received_cbf(cbf), topic)
        LOG.debug("Registered async endpoint: topic: %r cbf: %r", topic, cbf)

    def notify(
        self,
        topic,
        payload={},
        key="default",
        correlation_id=None,
        headers={},
        reply_to=None,
    ):
        """
        Sends a simple one-way notification that does not expect a reply.
        :param topic: topic for communication (callee has to be described to it)
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param msg: actual message
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :param reply_to: (normally not used)
        :return: None
        """
        # Set header defaults
        headers.setdefault("key", key)
        headers.setdefault("type", "notification")

        # publish request message
        self.publish(
            topic,
            payload,
            correlation_id=correlation_id,
            reply_to=reply_to,
            headers=headers,
        )

    def register_notification_endpoint(self, cbf, topic, key="default"):
        """
        Wrapper for register_async_endpoint that allows to register
        notification endpoints that do not send responses after executing
        the callback function.
        :param cbf: function to be called when requests with the given topic and key are received
        :param topic: topic for requests and responses
        :param key:  optional identifier for endpoints (enables more than 1 endpoint per topic)
        :return: None
        """
        # TODO (bjoluc) The key is not used here! Also, there's no unit test for keys.
        return self.subscribe(self._generate_on_notification_received_cbf(cbf), topic)

    def call_sync(
        self,
        topic,
        payload={},
        key="default",
        correlation_id=None,
        headers={},
        timeout=20,  # a sync. request has a timeout
    ) -> Message:
        """
        Client method to sync. call an endpoint registered and bound to the given topic by any
        other component connected to the broker. The method waits for a response and returns it
        as a tuple containing message properties and content.

        :param topic: topic for communication (callee has to be described to it)
        :param payload: The message payload (serializable object)
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :param timeout: time in s to wait for a response
        :return: message
        """
        # we use this lock to wait for the response
        lock = threading.Event()
        response = None

        def result_cbf(message):
            """
            define a local callback method which receives the response
            """
            nonlocal response
            response = message
            # release lock
            lock.set()

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
        lock.clear()
        lock.wait(timeout)
        # return received response
        return response


def callback_print(self, message: Message):
    """
    Helper callback that prints the received message.
    """
    LOG.debug("RECEIVED from %r on %r: %s", message.app_id, message.topic, message)
