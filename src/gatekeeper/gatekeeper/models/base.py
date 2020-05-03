"""
Common abstract Mongoengine document definitions
"""

from datetime import datetime
from uuid import uuid4

from mongoengine import DateTimeField, Document, UUIDField

from gatekeeper.util.mongoengine_custom_json import makeHttpDatetime


class CreatedAtMixin:
    """
    Document mixin that defines an auto-generated `createdAt` field
    """

    createdAt = DateTimeField(default=datetime.utcnow, custom_json=makeHttpDatetime)


class UpdatedAtMixin:
    """
    Document mixin that defines an auto-generated `updatedAt` field
    """
    updatedAt = DateTimeField(custom_json=makeHttpDatetime)

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.utcnow()
        return super(UpdatedAtMixin, self).save(*args, **kwargs)


class TimestampsMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Document mixin that defines an auto-generated `updatedAt` field
    """
    pass


class TimestampsDocument(TimestampsMixin, Document):
    """
    Abstract `Document` subclass that defines and manages a `createdAt` and an `updatedAt` field
    """
    meta = {'abstract': True}


class UuidMixin:
    """
    Document mixin that defines a primary-key `id` field containing an auto-generated UUID
    """
    id = UUIDField(default=uuid4, primary_key=True, custom_json=("id", str))


class UuidDocument(UuidMixin, Document):
    """
    Abstract `Document` subclass that defines a primary-key `id` field containing an auto-generated
    UUID
    """
    meta = {'abstract': True}
