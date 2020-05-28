"""
Copyright (c) 2017 Pishahang
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

Neither the name of Pishahang, nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.
"""

import asyncio
import functools
import inspect
import logging
from collections import defaultdict
from concurrent.futures import Future
from threading import Thread
from typing import Any, Callable, Coroutine, Dict, Set, Tuple, Union

from .base import Message
from .request_response import ManoBrokerRequestResponseConnection

LOG = logging.getLogger("manobase:messaging:asyncio")
LOG.setLevel(logging.INFO)


class AsyncioBrokerConnection(ManoBrokerRequestResponseConnection):
    """
    A subclass of `ManoBrokerRequestResponseConnection` that adds support for
    asynchronous callback routines using `asyncio`. All callback routines are run in a
    single eventloop that runs in a separate thread. In addition to that, this class
    provides the following awaitable functions for usage in coroutines:

    - `call()`
    - `await_message()`
    - `await_notification()`
    - `await_generic()`
    """

    def __init__(self, app_id, **kwargs):
        super(AsyncioBrokerConnection, self).__init__(app_id, **kwargs)

        self._resolve_callbacks_by_topic: Dict[
            str, Set[Callable[[Message], Any]]
        ] = defaultdict(set)
        self._awaitable_topics: Set[str] = set()

        # Create and run event loop
        def run_loop(loop: asyncio.AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(target=run_loop, args=(self._loop,), daemon=True)
        self._loop_thread.start()

    def run_coroutine(self, coroutine) -> Future:
        """
        Schedules a coroutine to run in the event loop and logs any exception that the
        coroutine may rise.
        """
        future: Future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)

        def done(future: Future):
            exception = future.exception()
            if exception is not None:
                LOG.exception(
                    "Exception in coroutine %r", coroutine, exc_info=exception
                )

        future.add_done_callback(done)
        return future

    def _replace_coroutine_with_runner(
        self, function: Union[Callable, Coroutine]
    ) -> Callable:
        """
        Given a function, returns that function. Given a coroutine, returns a function
        that triggers the execution of the coroutine using `_run_coroutine()`.
        """
        if inspect.iscoroutinefunction(function):

            def runner(*args, **kwargs):
                self.run_coroutine(function(*args, **kwargs))

            return runner

        return function

    @staticmethod
    def _make_future() -> Tuple[Future, Callable[[Any], None]]:
        """
        Returns a new future object (for the event loop of the thread `_make_future()`
        is called in), and a callback to resolve it.
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def callback(result):
            # Because futures are not thread-safe
            loop.call_soon_threadsafe(future.set_result, result)

        return future, callback

    def subscribe(self, cbf, topic, subscription_queue=None, concurrent=True):
        if inspect.iscoroutinefunction(cbf):
            # No need to invoke on_message_received in a separate thread, as it only
            # schedules a task to be executed in the event loop:
            concurrent = False

        return super().subscribe(
            self._replace_coroutine_with_runner(cbf),
            topic,
            subscription_queue=subscription_queue,
            concurrent=concurrent,
        )

    def _run_endpoint_handler_coroutine(
        self,
        coroutine: Coroutine[Message, Any, Any],
        message: Message,
        on_finish: Callable,
    ):
        """
        Run `coroutine` with `message` and run `on_finish` with its return value.

        :param coroutine: The coroutine to be executed
        :param message: The "request" message that triggered the execution
        :param on_finish: Callback function that is executed when `handler` returns
        :return: None
        """

        async def runner():
            try:
                result = await coroutine(message)
            except Exception:
                LOG.exception("Exception in coroutine %r", coroutine)
            on_finish(message, result)

        self.run_coroutine(runner())

    def register_async_endpoint(self, endpoint_handler, topic):
        if not inspect.iscoroutinefunction(endpoint_handler):
            return super().register_async_endpoint(endpoint_handler, topic)

        self.subscribe(
            functools.partial(
                self._on_request_received,
                self._run_endpoint_handler_coroutine,
                endpoint_handler,
                self._on_request_endpoint_handler_finished,
            ),
            topic,
            concurrent=False,
        )

    def register_notification_endpoint(self, endpoint_handler, topic, key="default"):
        return super().register_notification_endpoint(
            self._replace_coroutine_with_runner(endpoint_handler), topic, key=key
        )

    def call_async(
        self, cbf, topic, payload={}, key="default", correlation_id=None, headers={}
    ) -> str:
        return super().call_async(
            self._replace_coroutine_with_runner(cbf),
            topic,
            payload=payload,
            key=key,
            correlation_id=correlation_id,
            headers=headers,
        )

    def call(
        self, topic, payload={}, key="default", correlation_id=None, headers={}
    ) -> "Future[Message]":
        """
        Sends a request message to a topic and returns a future that is resolved with a
        reply message, once received.

        :param topic: Topic for this call.
        :param payload: The message payload (serializable object)
        :param key: additional header field
        :param correlation_id: used to match requests to replies. If correlation_id is not given, a new one is generated.
        :param headers: Dictionary with additional header fields.
        :return: A future that is resolved with a reply message, once received
        """

        future, resolve = AsyncioBrokerConnection._make_future()
        super().call_async(
            resolve,
            topic,
            payload=payload,
            key=key,
            correlation_id=correlation_id,
            headers=headers,
        )
        return future

    def subscribe_awaitable(self, topic):
        """
        Subscribe to a topic so that messages on that topic can be awaited with the
        `await_...()` methods. Note: This method only has to be called once per topic
        that should be available.

        :param topic: The topic to subscribe to
        :return: The subscription's consumer tag or None if no new subscription has been made
        """

        if topic in self._awaitable_topics:
            return

        def callback(message: Message):
            LOG.debug(
                "Calling the callbacks subscibed via subscribe_awaitable() for topic %s",
                topic,
            )
            for cb in list(self._resolve_callbacks_by_topic[topic]):
                cb(message)

        self._awaitable_topics.add(topic)

        return super().subscribe(callback, topic, concurrent=False)

    def await_generic(
        self, topic: str, filter: Callable[[Message], bool],
    ) -> "Future[Message]":
        """
        Returns a future that is resolved with the next received message on `topic` for
        which `filter(message)` returns ``True``.

        Note: `subscribe_awaitable()` has to be called once for every topic that this
        method is used with.

        :param topic: The topic to expect the message on. :param filter: A callable
        that, provided with a message object, returns `True` if the message should
        resolve the future, or `False` otherwise :return: A future that is resolved when
        a message with `filter(message) == True` is received
        """
        if topic not in self._awaitable_topics:
            LOG.warning(
                'Calling `await_...("{topic}")` requires a preceding call to '
                + 'subscribe_awaitable("{topic}") in order to work!'.format(topic=topic)
            )

        future, resolve = AsyncioBrokerConnection._make_future()

        def callback(message: Message):
            if filter(message):
                resolve(message)
                self._resolve_callbacks_by_topic[topic].discard(callback)

        self._resolve_callbacks_by_topic[topic].add(callback)

        return future

    def await_message(self, topic, correlation_id=None) -> "Future[Message]":
        """
        Returns a future that is resolved with the next message that is received on
        `topic`, matching `correlation_id` (if provided).

        Note: `subscribe_awaitable()` has to be called once for every topic that this
        method is used with.

        :param topic: The topic to expect the message on.
        :param correlation_id: An optional correlation_id that a message must have to resolve the future
        :return: A future that is resolved when a message with the specified criteria is received
        """
        return self.await_generic(
            topic,
            lambda message: (
                correlation_id is None or message.correlation_id == correlation_id
            ),
        )

    def await_notification(self, topic, correlation_id=None) -> "Future[Message]":
        """
        Returns a future that is resolved with the next notification that is received on
        `topic`, matching `correlation_id` (if provided).

        Note: `subscribe_awaitable()` has to be called once for every topic that this
        method is used with.

        :param topic: The topic to expect the notification on.
        :param correlation_id: An optional correlation_id that a message must have to resolve the future
        :return: A future that is resolved when a notification with the specified criteria is received
        """
        return self.await_generic(
            topic,
            lambda message: (
                ManoBrokerRequestResponseConnection.is_notification(message)
                and (correlation_id is None or message.correlation_id == correlation_id)
            ),
        )
