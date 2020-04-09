"""
Service-related Mongoengine document definitions
"""

from mongoengine import (EmbeddedDocument, EmbeddedDocumentListField,
                         StringField, UUIDField)

from gatekeeper.models.base import (TimestampsDocument, TimestampsMixin,
                                    UuidDocument, UuidMixin)
from gatekeeper.models.descriptors import DescriptorSnapshot
from gatekeeper.util.mongoengine_custom_json import CustomJsonRules


class ServiceInstance(UuidMixin, TimestampsMixin, EmbeddedDocument):
    status = StringField(required=True)


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

    instances = EmbeddedDocumentListField(ServiceInstance, custom_json=CustomJsonRules.HIDDEN)
