import pytest

from flm_base.plugin import FunctionLifecycleManagerBasePlugin
from manobase.messaging import AsyncioBrokerConnection


@pytest.fixture(scope="module")
def instance():
    """
    A running plugin instance that uses a loopback broker connection
    """
    instance = FunctionLifecycleManagerBasePlugin(
        version="1.0.0",
        description="",
        use_loopback_connection=True,
        fake_registration=True,
    )
    yield instance
    instance.conn.close()


@pytest.fixture(scope="module")
def connection():
    """
    A loopback broker connection
    """
    connection = AsyncioBrokerConnection("test-connection", is_loopback=True)
    yield connection
    connection.close()
