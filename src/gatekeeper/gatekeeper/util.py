from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet

import json


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A JSONEncoder which provides serialization of MongoEngine
    documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, BaseDocument) or isinstance(obj, QuerySet):
            return json.loads(obj.to_json()) # TODO Replacement for the json.loads cheat?
        return super().default(obj)


