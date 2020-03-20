import os

import pytest
import yaml
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.datastructures import Headers

from gatekeeper.app import app
from gatekeeper.models.users import User

from config2.config import config  # Has to be imported after app to get the right config path


class AuthorizedFlaskClient(FlaskClient):

    accessToken: str

    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", Headers())
        headers.extend(Headers({
            "Authorization": "Bearer " + AuthorizedFlaskClient.accessToken
        }))
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


# User and auth fixtures

@pytest.fixture(scope="session")
def adminUser():
    return User.objects(username=config.initialUserData.username).get()


@pytest.fixture(scope="session")
def adminPassword():
    return config.initialUserData.password


@pytest.fixture(scope="session")
def accessToken(adminUser):
    with app.app.app_context():
        return create_access_token(adminUser)


@pytest.fixture(scope="session")
def refreshToken(adminUser):
    with app.app.app_context():
        return create_refresh_token(adminUser)


# Api fixtures

@pytest.fixture(scope="module")
def api():
    app.app.test_client_class = FlaskClient
    with app.app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def authorizedApi(accessToken):
    AuthorizedFlaskClient.accessToken = accessToken
    app.app.test_client_class = AuthorizedFlaskClient
    with app.app.test_client() as c:
        yield c


# Data fixtures

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures/')


@pytest.fixture(scope="session")
def exampleCsd():
    with open(FIXTURE_DIR + "/example-csd.yml") as descriptor:
        return yaml.safe_load(descriptor)


@pytest.fixture(scope="session")
def exampleVnfd():
    with open(FIXTURE_DIR + "/example-vnfd.yml") as descriptor:
        return yaml.safe_load(descriptor)
