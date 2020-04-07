"""
Service-related Mongoengine document definitions
"""

from mongoengine import EmbeddedDocumentListField, StringField, UUIDField

from gatekeeper.models.base import TimestampsDocument, UuidDocument
from gatekeeper.models.descriptors import DescriptorSnapshot


class Service(UuidDocument, TimestampsDocument):
    """
    Document class for services. A `Service` contains snapshots of all descriptors required to
    instantiate it, as well as information on its service instances.
    """

    descriptorSnapshots = EmbeddedDocumentListField(DescriptorSnapshot, required=True)
    rootDescriptorId = UUIDField(required=True, custom_json=str)

    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)
