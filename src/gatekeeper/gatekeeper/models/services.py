"""
Service-related Mongoengine document definitions
"""

import mongoengine
from mongoengine import (
    EmbeddedDocumentListField,
    ListField,
    ReferenceField,
    StringField,
    UUIDField,
)

from gatekeeper.models.base import TimestampsDocument, UuidDocument
from gatekeeper.models.descriptors import DescriptorSnapshot
from gatekeeper.util.mongoengine_custom_json import CustomJsonRules


class ServiceInstance(UuidDocument, TimestampsDocument):
    status = StringField(required=True)
    message = StringField()

    correlationId = UUIDField(required=True, custom_json=CustomJsonRules.HIDDEN)
    internalId = UUIDField(custom_json=CustomJsonRules.HIDDEN)


class Service(UuidDocument, TimestampsDocument):
    """
    Document class for services. A `Service` contains snapshots of all descriptors
    required to instantiate it, as well as information on its service instances.
    """

    descriptorSnapshots = EmbeddedDocumentListField(DescriptorSnapshot, required=True)
    rootDescriptorId = UUIDField(required=True, custom_json=str)

    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)

    instances = ListField(
        ReferenceField(ServiceInstance, reverse_delete_rule=mongoengine.PULL),
        custom_json=CustomJsonRules.HIDDEN,
    )
