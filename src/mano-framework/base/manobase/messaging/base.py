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

import json
import logging
import os
from collections import defaultdict
from copy import deepcopy
from queue import Queue
from threading import Event, Lock, Thread
from typing import Any, Callable, Dict, Set
from uuid import uuid4

import amqpstorm
import yaml
from amqpstorm.exception import AMQPConnectionError

logging.getLogger("amqpstorm.channel").setLevel(logging.ERROR)
LOG = logging.getLogger("manobase:messaging:base")

# if we don't find a broker configuration in our ENV, we use this URL as default
RABBITMQ_URL_FALLBACK = "amqp://guest:guest@localhost:5672/%2F"
# if we don't find a broker configuration in our ENV, we use this exchange as default
RABBITMQ_EXCHANGE_FALLBACK = "son-kernel"

# For connections with is_loopback=True:

# Map topics to tags of local queues
_loopback_queue_tags_by_topic: Dict[str, Set[str]] = defaultdict(set)

# Map queue tags to local queues
_loopback_queue_by_tag: Dict[str, "Queue[Message]"] = defaultdict(Queue)

# Map queue tags to topics
_loopback_topic_by_tag: Dict[str, str] = {}

# A lock to coordinate creation and deletion of loopback queues
_loopback_queue_lock = Lock()


def _publish_to_loopback_queues(topic: str, message: "Message"):
    """
    Publish a copy of `message` on all local loopback queues that belong to `topic`
    """
    with _loopback_queue_lock:
        LOG.debug(
            "Locally publishing message on topic %s to %d queues",
            topic,
            len(_loopback_queue_tags_by_topic[topic]),
        )

        for queue in [
            _loopback_queue_by_tag[tag] for tag in _loopback_queue_tags_by_topic[topic]
        ]:
            queue.put(deepcopy(message))


def _get_loopback_queue(topic: str, tag: str):
    with _loopback_queue_lock:
        if tag in _loopback_queue_tags_by_topic[topic]:
            return _loopback_queue_by_tag[_loopback_queue_tags_by_topic[topic]]

        # Create new queue
        _loopback_queue_tags_by_topic[topic].add(tag)
        _loopback_topic_by_tag[tag] = topic
        return _loopback_queue_by_tag[tag]


def _delete_loopback_queue(tag: str):
    with _loopback_queue_lock:
        if tag in _loopback_queue_by_tag:
            queue = _loopback_queue_by_tag.pop(tag)
            queue.put("STOP")  # Stop subscriber thread

            topic = _loopback_topic_by_tag.pop(tag)
            _loopback_queue_tags_by_topic[topic].discard(tag)


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
            app_id=app_id,
        )


class ManoBrokerConnection:
    """
    This class encapsulates a bare RabbitMQ connection setup.
    It provides helper methods to easily publish/subscribe to a given topic.
    It uses the asynchronous adapter implementation of the amqpstorm library.
    """

    def __init__(self, app_id, url=None, exchange=None, is_loopback=False):
        """
        Initialize broker connection.

        :param app_id: A string that identifies the application of the connection
        :param url: The RabbitMQ URL to use for the connection
        :param exchange: The RabbitMQ exchange to be used
        :param loopback: Useful for unit testing: If set to True, no broker connection
        will be made, but messages will directly be delivered to all
        `ManoBrokerConnection` objects with ``loopback=True`` within the running python
        application.
        """
        self.app_id = app_id
        self.rabbitmq_url = (
            url
            if url is not None
            else os.environ.get("broker_host", RABBITMQ_URL_FALLBACK)
        )
        self.rabbitmq_exchange = (
            exchange
            if exchange is not None
            else os.environ.get("broker_exchange", RABBITMQ_EXCHANGE_FALLBACK)
        )
        self._is_loopback = is_loopback

        self._subscription_queue_by_tag: Dict[str, amqpstorm.queue.Queue] = {}
        self._connection: amqpstorm.UriConnection = None

        if not self._is_loopback:
            self.connect()

    def __del__(self):
        self.close()

    def connect(self):
        """
        Connect to RabbitMQ using `self.rabbitmq_url`. You usually do not have to call
        this yourself, as it is already done by the constructor.
        """
        self._connection = amqpstorm.UriConnection(self.rabbitmq_url)
        return self._connection

    def close(self):
        """
        Close the connection, stopping all consuming threads
        """
        if self._is_loopback:
            for tag in self._subscription_queue_by_tag:
                _delete_loopback_queue(tag)
        else:
            if self._connection is not None and (
                self._connection.is_open or self._connection.is_opening
            ):
                self._connection.close()

    def setup_connection(self):
        """
        Deprecated: Use `connect()` instead.
        """
        return self.connect()

    def stop_connection(self):
        """
        Deprecated: Use `close()` instead.
        """
        self.close()

    def stop_threads(self):
        """
        Deprecated: AMQPStorm terminates the threads automatically by closing the
        channels when the connection is closed.
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

        # Serialize message as JSON
        body = json.dumps(payload)

        if self._is_loopback:
            _publish_to_loopback_queues(
                topic,
                Message(
                    topic=topic,
                    payload=payload,
                    correlation_id=correlation_id,
                    reply_to=reply_to,
                    headers=headers,
                    message_id=uuid4(),
                    app_id=app_id,
                ),
            )
        else:
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
                        "content_type": "application/json",
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

        def on_message_received(message: Message):
            # Call cbf of subscription
            if concurrent:
                Thread(
                    target=cbf, args=(message,), name=subscription_queue + ".callback"
                ).start()
            else:
                cbf(message)

        def on_amqpstorm_message_received(amqpstormMessage: amqpstorm.Message):
            # Create custom message object and call cbf of subscription
            on_message_received(Message.from_amqpstorm_message(amqpstormMessage))

            # Acknowledge the message
            amqpstormMessage.ack()

        consumption_started_event = Event()

        def amqpstorm_subscriber():
            """
            A function that handles messages of the subscription.
            """
            with self._connection.channel() as channel:
                # declare exchange for this channel
                channel.exchange.declare(
                    exchange=self.rabbitmq_exchange, exchange_type="topic"
                )
                # create queue for subscription
                queue = channel.queue
                queue.declare(subscription_queue)
                # bind queue to given topic
                queue.bind(
                    queue=subscription_queue,
                    routing_key=topic,
                    exchange=self.rabbitmq_exchange,
                )

                # Store a reference to the queue (used for unsubscribing)
                self._subscription_queue_by_tag[subscription_queue] = queue

                # recommended qos setting
                channel.basic.qos(100)
                # setup consumer (use queue name as tag)
                channel.basic.consume(
                    on_amqpstorm_message_received,
                    subscription_queue,
                    consumer_tag=subscription_queue,
                )
                try:
                    consumption_started_event.set()
                    # start consuming messages.
                    channel.start_consuming()
                except AMQPConnectionError:
                    pass
                except Exception:
                    LOG.exception(
                        "Error in subscription thread %s:", subscription_queue
                    )
                finally:
                    try:
                        self._subscription_queue_by_tag.pop(subscription_queue, None)
                    except AMQPConnectionError:
                        pass

        def loopback_subscriber():
            """
            Like amqpstorm_subscriber, but using a local loopback queue
            """
            consumption_started_event.set()
            queue: Queue = _get_loopback_queue(topic, subscription_queue)

            # Store queue tag for unsubscribing (None, as no AMQPStorm queue is present)
            self._subscription_queue_by_tag[subscription_queue] = None

            while True:
                message = queue.get()
                if message == "STOP":
                    break
                else:
                    on_message_received(message)

        # Each subscriber runs in a separate thread
        LOG.debug("Starting new thread to consume %s", subscription_queue)
        Thread(
            target=amqpstorm_subscriber
            if not self._is_loopback
            else loopback_subscriber,
            name=subscription_queue,
        ).start()
        consumption_started_event.wait()

        LOG.debug("SUBSCRIBED to %s", topic)
        return subscription_queue

    def unsubscribe(self, subscription_queue):
        """
        Unsubscribe from `subscription_queue` if a subscription was made to it with
        `subscribe()` before.

        :param subscription_queue: The consumer tag that was used for the subscription, as handed out by `subscribe()`
        :return: None
        """
        if self._is_loopback:
            _delete_loopback_queue(subscription_queue)
        else:
            try:
                self._subscription_queue_by_tag.pop(subscription_queue).delete()
                LOG.debug(
                    "unsubscribe(): Successfully deleted subscription queue %s.",
                    subscription_queue,
                )
            except KeyError:
                LOG.debug(
                    "unsubscribe(): Deletion of subscription queue %s failed: Queue not found.",
                    subscription_queue,
                )
            except AMQPConnectionError:
                pass
