from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet

from gatekeeper.mongoengine_custom_json import to_custom_json


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A JSONEncoder which provides serialization of MongoEngine
    documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, (BaseDocument, QuerySet)):
            return to_custom_json(obj)
        return super().default(obj)


def makeMessageDict(status: int, detail: str):
    """
    Given a `detail` string with a message and a `status` integer, returns a dictionary containing
    those two items.
    """
    return {"detail": detail, "status": status}


def makeMessageResponse(status: int, detail: str):
    """
    Given a `detail` string and a `status` integer, returns a tuple containing the result of
    `makeErrorDict()` and the `status` code. This can be returned from flask route handlers.
    """
    return makeMessageDict(status, detail), status
