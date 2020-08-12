import json
from datetime import datetime, timezone
from enum import IntEnum
from typing import Union

from bson import json_util
from mongoengine.base import BaseDocument
from mongoengine.fields import EmbeddedDocumentField, ListField, ReferenceField
from mongoengine.queryset import QuerySet


class CustomJsonRules(IntEnum):
    HIDDEN = 1


def to_custom_dict(obj: Union[BaseDocument, QuerySet]):
    """
    Converts a Mongoengine document (anything inheriting from
    `mongoengine.base.BaseDocument`) or a Mongoengine QuerySet to a Python `dict`,
    considering fields' `custom_json` attributes (if any).
    """
    if isinstance(obj, QuerySet):
        return [to_custom_dict(entry) for entry in obj]

    if isinstance(obj, BaseDocument):
        doc: dict = obj.to_mongo()

        # Iterate over Mongoengine document fields and handle them accordingly
        for field in obj._fields.values():
            rule = getattr(field, "custom_json", None)
            fieldName = field.name

            if rule is CustomJsonRules.HIDDEN:
                try:
                    doc.pop(fieldName)
                except KeyError:
                    # TODO Is the field always stored in "_id" in this case?
                    # doc.pop(
                    #     "_id"
                    # )
                    pass
            else:
                # Check for recursive document fields and process them recursively
                if isinstance(field, (ReferenceField, EmbeddedDocumentField)):
                    doc[fieldName] = to_custom_dict(obj[fieldName])
                    continue
                elif isinstance(field, ListField):
                    doc[fieldName] = [to_custom_dict(x) for x in obj[fieldName]]
                    continue

            if rule is None:
                continue

            # Extract alternative name and / or conversion function
            if isinstance(rule, tuple):
                altName, conversionFunc = rule
            elif isinstance(rule, str):
                altName = rule

                def conversionFunc(x):
                    return x

            elif callable(rule):
                altName = None
                conversionFunc = rule
            else:
                continue

            if fieldName not in doc and "_id" in doc:
                # Assuming that the field is stored in _id
                # TODO Does this always apply?
                fieldName = "_id"

            # Handle field according to altName and conversionFunc
            doc[fieldName if altName is None else altName] = conversionFunc(
                doc.pop(fieldName)
            )

        # Remove Mongoengine class field if it exists
        # TODO Find alternative solution that does not hardcode this
        if "_cls" in doc:
            doc.pop("_cls")

        return doc


def to_custom_json(obj: Union[BaseDocument, QuerySet]):
    return json.dumps(json_util._json_convert(to_custom_dict(obj)))


# Common handler functions


def makeHttpDatetime(value: datetime):
    return value.replace(tzinfo=timezone.utc, microsecond=0).isoformat()
