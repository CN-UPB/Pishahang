import pytest
from appcfg import get_config

from manobase.messaging import ManoBrokerRequestResponseConnection
from vim_adaptor.main import VimAdaptor
from mongoengine.connection import connect

config = get_config("vim_adaptor")


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


@pytest.fixture(scope="module")
def mongo_connection():
    """
    A fixture that connects to MongoDB at test setup
    """
    connect(host=config["mongo"])
