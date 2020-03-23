"""
Common abstract Mongoengine document definitions
"""

from datetime import datetime
from uuid import uuid4

from mongoengine import DateTimeField, Document, UUIDField

from gatekeeper.mongoengine_custom_json import makeHttpDatetime


class TimestampedDocument(Document):
    """
    Abstract Mongoengine `Document` subclass that defines and manages a `createdAt` and an
    `updatedAt` field
    """

    meta = {'abstract': True}
    createdAt = DateTimeField(default=datetime.utcnow, custom_json=makeHttpDatetime)
    updatedAt = DateTimeField(custom_json=makeHttpDatetime)

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.utcnow()
        return super(TimestampedDocument, self).save(*args, **kwargs)


class UuidDocument(Document):
    """
    Abstract Mongoengine `Document` subclass that defines an `id` field containing an auto-generated
    UUID primary key
    """

    meta = {'abstract': True}
    id = UUIDField(default=uuid4, primary_key=True, custom_json=("id", str))
