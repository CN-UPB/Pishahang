from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from manobase.messaging import ManoBrokerRequestResponseConnection
from vim_adaptor.main import VimAdaptor

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_fs(fs: FakeFilesystem):
    fs.add_real_directory(FIXTURE_DIR)
    fs.fixture_dir = FIXTURE_DIR
    yield fs


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
