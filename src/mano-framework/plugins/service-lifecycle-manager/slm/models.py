from datetime import datetime
from uuid import uuid4

from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    DateTimeField,
    DictField,
    EmbeddedDocumentListField,
    StringField,
    UUIDField,
)


class Function(EmbeddedDocument):
    """
    Represents a function instance.
    """

    id = UUIDField(required=True)
    descriptor = DictField(required=True)
    vim = UUIDField()
    record = DictField()


class Service(Document):
    """
    Represents a service instance.
    """

    id = UUIDField(primary_key=True, default=uuid4)
    created_at = DateTimeField(default=datetime.utcnow)

    status = StringField()

    descriptor = DictField(required=True)
    functions = EmbeddedDocumentListField(Function, required=True)

    placement = DictField()
