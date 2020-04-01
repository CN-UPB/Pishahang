"""
Service-related Mongoengine document definitions
"""

from mongoengine import EmbeddedDocumentListField, StringField, UUIDField

from gatekeeper.models.base import TimestampedDocument, UuidDocument
from gatekeeper.models.descriptors import DescriptorSnapshot


class Service(UuidDocument, TimestampedDocument):
    """
    Document class for services. A `Service` contains snapshots of all descriptors required to
    instantiate it, as well as references to its service instances.
    """

    descriptorSnapshots = EmbeddedDocumentListField(DescriptorSnapshot, required=True)
    rootDescriptorId = UUIDField(required=True, custom_json=str)

    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)
