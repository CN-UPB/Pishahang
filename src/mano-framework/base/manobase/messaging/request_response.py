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

import functools
import logging
import threading
from collections import defaultdict
from typing import Any, Callable, Dict
from uuid import uuid4

from .base import ManoBrokerConnection, Message

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


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
        self._async_calls_pending_by_corr_id: Dict[str, Dict] = {}
        self._async_calls_response_queue_by_topic: Dict[str, str] = {}
        self._async_calls_count_by_topic: Dict[str, int] = defaultdict(int)

    @staticmethod
    def is_request(message: Message) -> bool:
        """
        Check whether a given message is a request
        """
        return message.reply_to is not None

    @staticmethod
    def is_response(message: Message) -> bool:
        """
        Check whether a given message is a response
        """
        return message.reply_to is None

    @staticmethod
    def is_notification(message: Message) -> bool:
        """
        Check whether a given message is a notification
        """
        return message.reply_to is None

    def _execute_endpoint_handler(
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

    def _on_request_endpoint_handler_finished(self, request: Message, result):
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

    def _on_request_received(
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
        # verify that the message is a request
        if not ManoBrokerRequestResponseConnection.is_request(message):
            LOG.debug(
                'Message on topic "%s" is not a request, ignoring it.', message.topic,
            )
            return

        LOG.debug("Request on topic %s received.", message.topic)
        endpoint_executor(
            endpoint_handler, message, on_handler_finished,
        )

    def _on_notification_received(self, callback_function, message: Message):
        """
        Callback function that handles notifications by calling `callback_function` with
        `message`
        """
        # verify that the message is a notification
        if not ManoBrokerRequestResponseConnection.is_notification(message):
            LOG.debug(
                "Notification endpoint received request message on topic %s. Dropping it.",
                message.reply_to,
            )
            return

        LOG.debug("Notification on topic %r received.", message.topic)
        callback_function(message)

    def _on_response_received(self, message: Message):
        """
        Callback function that handles the response of a remote function call.

        :param message: The response message that has been received
        :return: None
        """
        # check if we really have a response, not a request
        if not ManoBrokerRequestResponseConnection.is_response(message):
            LOG.debug(
                "Non-response message on topic %s received at response endpoint. Ignoring it.",
                message.reply_to,
            )
            return

        corr_id = message.correlation_id
        if corr_id not in self._async_calls_pending_by_corr_id:
            LOG.debug(
                "Received unmatched call response on topic %s. Ignoring it.",
                message.topic,
            )
            return

        LOG.debug("Async response received. Matches via corr_id %r", corr_id)
        call_details = self._async_calls_pending_by_corr_id.pop(corr_id)

        # Call callback function
        call_details["cbf"](message)

        queue_tag = call_details["queue"]
        topic = call_details["topic"]
        self._async_calls_count_by_topic[topic] -= 1

        # If no other call_async is using this queue, remove the queue
        if self._async_calls_count_by_topic[topic] == 0:
            LOG.debug(
                "Unsubscribing from queue %s, as it is no longer used by any async call",
                queue_tag,
            )
            self._async_calls_response_queue_by_topic.pop(topic)
            self.unsubscribe(queue_tag)

    def call_async(
        self,
        cbf,
        topic: str,
        payload={},
        key="default",
        correlation_id: str = None,
        headers: Dict[str, str] = {},
    ) -> str:
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

        self._async_calls_count_by_topic[topic] += 1

        # Generate correlation_id to match requests and responses
        correlation_id = str(uuid4()) if correlation_id is None else correlation_id

        # initialize response subscription

        subscription_queue = self.subscribe(
            self._on_response_received,
            topic,
            subscription_queue=self._async_calls_response_queue_by_topic.get(
                topic, None
            ),
        )
        self._async_calls_response_queue_by_topic[topic] = subscription_queue

        self._async_calls_pending_by_corr_id[correlation_id] = {
            "cbf": cbf,
            "topic": topic,
            "queue": subscription_queue,
        }

        # Set header defaults
        headers.setdefault("key", key)
        headers.setdefault("type", "request")

        # publish request message
        self.publish(
            topic,
            payload,
            reply_to=topic,
            correlation_id=correlation_id,
            headers=headers,
        )
        LOG.debug(
            "Async request made on %s, with correlation_id %s", topic, correlation_id
        )
        return correlation_id

    def register_async_endpoint(self, endpoint_handler, topic):
        """
        Exposes the functionality implemented in `endpoint_handler` to callers that are
        connected to the broker.

        :param endpoint_handler: Function to be called when requests with the given topic and key are received
        :param topic: Topic for requests and responses
        :return: The endpoint subscription's consumer tag
        """
        subscription_queue = self.subscribe(
            functools.partial(
                self._on_request_received,
                self._execute_endpoint_handler,
                endpoint_handler,
                self._on_request_endpoint_handler_finished,
            ),
            topic,
        )
        LOG.debug(
            "Registered async endpoint: topic: %r handler: %r", topic, endpoint_handler
        )
        return subscription_queue

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
        :param payload: The message payload (serializable object)
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :return: None
        """
        # Set header defaults
        headers.setdefault("key", key)
        headers.setdefault("type", "notification")

        self.publish(topic, payload, correlation_id=correlation_id, headers=headers)

    def register_notification_endpoint(self, endpoint_handler, topic, key="default"):
        """
        Registers `endpoint_handler` to be called when a notification on `topic` is
        received.

        :param endpoint_handler: Function to be called when requests with the given topic and key are received
        :param topic: Topic to subscribe the endpoint to
        :param key:  optional identifier for endpoints (enables more than 1 endpoint per topic)
        :return: The endpoint subscription's consumer tag
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

        :param topic: topic for communication (callee needs to have a subscription to it)
        :param payload: The message payload (serializable object)
        :param key: optional identifier for endpoints (enables more than 1 endpoint per topic)
        :param correlation_id: allow to set individual correlation ids
        :param headers: header dict
        :param timeout: time in s to wait for a response
        :return: message
        """
        response_received_event = threading.Event()
        response = None

        def on_response_received(message):
            nonlocal response
            response = message
            # release lock
            response_received_event.set()

        self.call_async(
            on_response_received,
            topic=topic,
            payload=payload,
            key=key,
            correlation_id=correlation_id,
            headers=headers,
        )

        response_received_event.wait(timeout)
        return response
