import pytest

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
    return create_access_token(adminUser)


@pytest.fixture(scope="session")
def refreshToken(adminUser):
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
