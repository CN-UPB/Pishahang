from contextlib import contextmanager
from typing import Any, Callable

from manobase.messaging import AsyncioBrokerConnection as Connection
from manobase.messaging import Message


@contextmanager
def async_endpoint(
    connection: Connection, topic, endpoint_handler: Callable[[Message], Any]
):
    """
    Context manager that registers an endpoint with `endpoint_handler` on `topic` at
    `connection`. The endpoint handler is unsubscribed again when the context manager is
    exited.
    """
    subscription_id = connection.register_async_endpoint(endpoint_handler, topic)
    try:
        yield
    finally:
        connection.unsubscribe(subscription_id)


@contextmanager
def simple_async_endpoint(connection: Connection, topic, response):
    """
    Context manager that registers an endpoint on `topic` at `connection` that returns
    the given response payload. The endpoint handler is unsubscribed again when the
    context manager is exited.
    """

    def endpoint_handler(message: Message):
        return response

    with async_endpoint(connection, topic, endpoint_handler):
        yield
