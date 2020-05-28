import pytest

from manobase.messaging import ManoBrokerRequestResponseConnection
from slm.slm import ServiceLifecycleManager


@pytest.fixture(scope="module")
def slm():
    """
    A running SLM instance that uses a loopback broker connection
    """
    adaptor = ServiceLifecycleManager(
        use_loopback_connection=True, fake_registration=True, start_running=False
    )
    yield adaptor
    adaptor.conn.close()


@pytest.fixture(scope="module")
def connection():
    """
    A loopback broker connection
    """
    connection = ManoBrokerRequestResponseConnection(
        "test-connection", is_loopback=True
    )
    yield connection
    connection.close()
