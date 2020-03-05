import json

from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A JSONEncoder which provides serialization of MongoEngine
    documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, BaseDocument):
            serializeableDict: dict = json.loads(obj.to_json())
            if "_cls" in serializeableDict: # Remove Mongoengine class field if it exists
                serializeableDict.pop("_cls")
            return serializeableDict
        if isinstance(obj, QuerySet):
            return [self.default(entry) for entry in obj]

        return super().default(obj)

def makeErrorDict(status: int, detail: str):
    """
    Given a `detail` string with a message and a `status` integer, returns a dictionary containing
    those two items.
    """
    return {"detail": detail, "status": status}

def makeErrorResponse(status: int, detail: str):
    """
    Given a `detail` string and a `status` integer, returns a tuple containing the result of
    `makeErrorDict()` and the `status` code. This can be returned from flask route handlers.
    """
    return makeErrorDict(status, detail), status
