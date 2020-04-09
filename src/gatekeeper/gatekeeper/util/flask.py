from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet

from gatekeeper.util.mongoengine_custom_json import to_custom_dict


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A flask JSONEncoder which provides serialization of MongoEngine documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, (BaseDocument, QuerySet)):
            return to_custom_dict(obj)
        return super().default(obj)
