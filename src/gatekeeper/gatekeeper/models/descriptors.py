"""
Descriptor-related Mongoengine document definitions
"""

from enum import Enum

from jsonschema.exceptions import ValidationError
from mongoengine import (DateTimeField, DynamicEmbeddedDocument,
                         EmbeddedDocument, EmbeddedDocumentField, StringField,
                         UUIDField)

from gatekeeper.exceptions import InvalidDescriptorContentError
from gatekeeper.models.base import TimestampedDocument, UuidDocument
from gatekeeper.mongoengine_custom_json import makeHttpDatetime
from gatekeeper.validation import (validateFunctionDescriptor,
                                   validateServiceDescriptor)


class DescriptorType(Enum):
    """
    An enumeration of valid `type` values for descriptors
    """

    SERVICE = "service"
    VM = "vm"
    CN = "cn"
    FPGA = "fpga"


class DescriptorContents(DynamicEmbeddedDocument):
    """
    Embedded document class to hold a descriptor's content
    """

    descriptor_version = StringField(required=True)
    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)

    def __str__(self):
        return 'Descriptor(vendor="{}", name="{}", version="{}")'.format(
            self.vendor, self.name, self.version)


class BaseDescriptor:
    """
    Document mixin for descriptors.
    """

    type = StringField(required=True, choices=[t.value for t in DescriptorType])
    descriptor = EmbeddedDocumentField(DescriptorContents, required=True)


class Descriptor(UuidDocument, TimestampedDocument, BaseDescriptor):
    """
    Document class for descriptors. The `descriptor` embedded document field is validated on `save`.
    """

    meta = {
        "indexes": [
            {
                "fields": ("descriptor.vendor", "descriptor.name", "descriptor.version"),
                "unique": True
            }
        ]
    }

    def save(self, *args, **kwargs):
        """
        Saves a `Descriptor` document, after validating the `descriptor` field against a descriptor
        schema according to the `type` value. If the validation fails, an
        `exceptions.InvalidDescriptorContentError` is raised.
        """

        descriptorDict = self.descriptor if isinstance(
            self.descriptor, dict) else self.descriptor.to_mongo()
        try:
            if self.type == DescriptorType.SERVICE.value:
                validateServiceDescriptor(descriptorDict)
            else:
                validateFunctionDescriptor(descriptorDict)
        except ValidationError as error:
            raise InvalidDescriptorContentError(error.message)

        # Convert `descriptor` to `DescriptorContents` if it is a `dict`
        if isinstance(self.descriptor, dict):
            self.descriptor = DescriptorContents(**self.descriptor)

        return super(Descriptor, self).save(*args, **kwargs)


class DescriptorSnapshot(EmbeddedDocument, BaseDescriptor):
    """
    Embedded descriptor document that is not meant to be updated after its creation. It can be used
    to embed a static copy of a `Descriptor` document in another document.
    """

    id = UUIDField(required=True, primary_key=True, custom_json=("id", str))
    createdAt = DateTimeField(required=True, custom_json=makeHttpDatetime)
    updatedAt = DateTimeField(required=True, custom_json=makeHttpDatetime)
