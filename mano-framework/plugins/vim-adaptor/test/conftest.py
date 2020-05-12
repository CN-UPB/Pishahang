import pytest
from vim_adaptor.main import VimAdaptor
from manobase.messaging import ManoBrokerRequestResponseConnection


@pytest.fixture(scope="module")
def adaptor():
    """
    A running VimAdaptor instance that uses a loopback broker connection
    """
    adaptor = VimAdaptor(use_loopback_connection=True, fake_registration=True)
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
