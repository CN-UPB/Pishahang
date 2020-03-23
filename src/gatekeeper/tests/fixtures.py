import os

import pytest
import yaml
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.datastructures import Headers

from gatekeeper.app import app, mongoDb
from gatekeeper.models.users import User

from config2.config import config  # Has to be imported after app to get the right config path

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures/')
MONGO_DATABASE_NAME = os.path.basename(config.databases.mongo)


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


# Database-related fixtures

@pytest.fixture(scope="function")
def dropMongoDb():
    """
    Drops the MongoDB database after each test function
    """
    yield
    mongoDb.connection.drop_database(MONGO_DATABASE_NAME)


# Data fixtures

@pytest.fixture(scope="session")
def getDescriptorFixture():
    def _getDescriptorFileContents(filename):
        with open(FIXTURE_DIR + "/" + filename) as descriptor:
            return yaml.safe_load(descriptor)

    return _getDescriptorFileContents


@pytest.fixture(scope="session")
def exampleCsd(getDescriptorFixture):
    return getDescriptorFixture("example-csd.yml")


@pytest.fixture(scope="session")
def exampleVnfd(getDescriptorFixture):
    return getDescriptorFixture("example-vnfd.yml")
