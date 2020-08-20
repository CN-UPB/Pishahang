from contextlib import contextmanager
from test.util import async_endpoint

import pytest
from appcfg import get_config
from mongoengine.connection import connect

from manobase.messaging import AsyncioBrokerConnection, Message
from slm.slm import ServiceLifecycleManager

config = get_config("slm")


@pytest.fixture(scope="module")
def slm_plugin():
    """
    A running SLM plugin instance that uses a loopback broker connection
    """
    adaptor = ServiceLifecycleManager(
        use_loopback_connection=True, fake_registration=True
    )
    yield adaptor
    adaptor.conn.close()


@pytest.fixture(scope="function")  # to reset subscriptions after each test case
def connection():
    """
    A loopback broker connection
    """
    connection = AsyncioBrokerConnection("test-connection", is_loopback=True)
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def mongo_connection():
    """
    A fixture that connects to MongoDB at test setup
    """
    connect(host=config["mongo"])


@pytest.fixture
def snapshot_endpoint(connection: AsyncioBrokerConnection, snapshot, reraise):
    """
    Returns a context manager that registers an endpoint that snapshot-tests the payload
    of any received message on a given `topic` and returns a provided `response`
    payload. The context manager also accepts an optional `matcher` parameter that may
    be used to provide a custom syrupy matcher function.
    """

    @contextmanager
    def snapshot_async_endpoint(topic: str, response: dict, matcher=None):
        def endpoint_handler(message: Message):
            with reraise(catch=True):
                assert message.payload == snapshot(matcher=matcher)

            return response

        with async_endpoint(connection, topic, endpoint_handler):
            yield

    return snapshot_async_endpoint
