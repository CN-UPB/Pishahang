from pathlib import Path

import pytest
import yaml
from appcfg import get_config
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, create_refresh_token
from manobase.messaging.request_response import ManoBrokerRequestResponseConnection
from werkzeug.datastructures import Headers

from gatekeeper.app import app
from gatekeeper.models.descriptors import Descriptor, DescriptorType
from gatekeeper.models.services import Service
from gatekeeper.models.users import User

FIXTURE_DIR = Path(__file__).parent / "fixtures"

config = get_config("gatekeeper")


class AuthorizedFlaskClient(FlaskClient):

    accessToken: str

    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", Headers())
        headers.extend(
            Headers({"Authorization": "Bearer " + AuthorizedFlaskClient.accessToken})
        )
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


# User and auth fixtures


@pytest.fixture(scope="session")
def adminUser():
    return User.objects(username=config["initialUserData"]["username"]).get()


@pytest.fixture(scope="session")
def adminPassword():
    return config["initialUserData"]["password"]


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
def unauthorizedApi():
    app.app.test_client_class = FlaskClient
    with app.app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def api(accessToken):
    AuthorizedFlaskClient.accessToken = accessToken
    app.app.test_client_class = AuthorizedFlaskClient
    with app.app.test_client() as c:
        yield c


# Database-related fixtures


@pytest.fixture(scope="function", autouse=True)
def dropMongoDbCollections():
    """
    Empties a number of MongoDB collections after each test function
    """
    yield
    with app.app.app_context():
        Descriptor.objects.delete()
        Service.objects.delete()


# Data fixtures


@pytest.fixture(scope="session")
def getDescriptorFixture():
    def _getDescriptorFileContents(filename):
        with (FIXTURE_DIR / filename).open() as descriptor:
            return yaml.safe_load(descriptor)

    return _getDescriptorFileContents


@pytest.fixture(scope="session")
def exampleServiceDescriptor(getDescriptorFixture):
    return getDescriptorFixture("service-descriptor.yml")


@pytest.fixture(scope="session")
def exampleOpenStackDescriptor(getDescriptorFixture):
    return getDescriptorFixture("openstack-descriptor.yml")


@pytest.fixture(scope="function")
def exampleService(api, getDescriptorFixture):
    def uploadDescriptor(type: DescriptorType, content):
        response = api.post(
            "/api/v3/descriptors", json={"type": type.value, "content": content}
        )
        print(response.get_json())
        assert 201 == response.status_code
        return response.get_json()

    serviceDescriptor = uploadDescriptor(
        DescriptorType.SERVICE, getDescriptorFixture("onboarding/root-service.yml")
    )

    for i in range(1, 3):
        uploadDescriptor(
            DescriptorType.OPENSTACK,
            getDescriptorFixture("onboarding/vnf-{}.yml".format(i)),
        )

    response = api.post("/api/v3/services", json={"id": serviceDescriptor["id"]})
    assert 201 == response.status_code
    return response.get_json()


# Messaging-related fixtures


@pytest.fixture(scope="module")
def broker():
    """
    A loopback broker connection
    """
    connection = ManoBrokerRequestResponseConnection(
        "test-connection", is_loopback=True
    )
    yield connection
    connection.close()
