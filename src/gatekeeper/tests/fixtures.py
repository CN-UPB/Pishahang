import pytest

from gatekeeper.app import app


@pytest.fixture(scope='module')
def api():
    with app.app.test_client() as c:
        yield c
