from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet

from gatekeeper.mongoengine_custom_json import to_custom_json


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A flask JSONEncoder which provides serialization of MongoEngine documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, (BaseDocument, QuerySet)):
            return to_custom_json(obj)
        return super().default(obj)
