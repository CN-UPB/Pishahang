import importlib

import mongomock
import pymongo
import pytest
from appcfg import get_config
from pytest_voluptuous import S
from voluptuous.validators import All, Contains
from werkzeug.test import Client


config = get_config("repository")

RESOURCES = {
    "entries": {
        "type": "object",
        "required": ["a"],
        "properties": {
            "a": {"type": "string"},
            "b": {
                "type": "object",
                "required": ["c"],
                "properties": {"c": {"type": "number"}},
            },
        },
    }
}


@pytest.fixture
def api(mocker):

    with mongomock.patch():
        import repository.app as app

        mocker.patch("repository.resources.resources", new=RESOURCES)
        importlib.reload(app)

        with app.app.test_client() as client:
            yield client

        # Drop the MongoMock database
        uri: str = config["mongo_uri"]
        pymongo.MongoClient(host=uri).drop_database(uri[uri.rfind("/") + 1 :])


def test_fields(api: Client):
    def get_items():
        return api.get("/entries").get_json()["_items"]

    # Add a valid entry
    assert 201 == api.post("/entries", json={"a": "foo"}).status_code

    items = get_items()
    assert len(items) == 1
    item = items[0]
    assert S({"a": "foo", "id": str, "created_at": str, "updated_at": str}) == item

    # Retrieve the single item and check that it is identical
    response = api.get("/entries/{}".format(item["id"]))
    assert 200 == response.status_code
    assert item == response.get_json()


def test_json_schema_validation(api: Client):
    def post(json: dict):
        return api.post("/entries", json=json)

    # a is required but not provided
    response = post({"b": "bar"})
    assert 422 == response.status_code
    assert S({"_issues": {".": str}}) <= response.get_json()

    # b does not contain c
    response = post({"a": "foo", "b": {}})
    assert 422 == response.status_code
    assert (
        S({"_issues": {"b": All(str, Contains("c"), Contains("required"))}})
        <= response.get_json()
    )

    # c is not a number
    response = post({"a": "foo", "b": {"c": "bar"}})
    assert 422 == response.status_code
    assert (
        S({"_issues": {"b.c": All(str, Contains("bar"), Contains("number"))}})
        <= response.get_json()
    )
