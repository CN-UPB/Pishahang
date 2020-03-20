"""
Descriptor-related Mongoengine document definitions
"""

from enum import Enum

from jsonschema.exceptions import ValidationError
from mongoengine import (DynamicEmbeddedDocument, EmbeddedDocumentField,
                         StringField)

from gatekeeper.exceptions import InvalidDescriptorContentsException
from gatekeeper.models.base import TimestampedDocument, UuidDocument
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
    A mongoengine embedded document class to hold a descriptor's contents
    """

    descriptor_version = StringField(required=True)
    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)


class Descriptor(UuidDocument, TimestampedDocument):
    """
    A mongoengine document class for arbitrary descriptors. The `descriptor` embedded document field
    is validated on `save`.
    """

    type = StringField(required=True, choices=[t.value for t in DescriptorType])
    descriptor = EmbeddedDocumentField(DescriptorContents, required=True)

    def save(self, *args, **kwargs):
        """
        Saves a `Descriptor` document, after validating the `descriptor` field against a descriptor
        schema according to the `type` value. If the validation fails, an
        `exceptions.InvalidDescriptorContentsException` is raised.
        """

        descriptorDict = self.descriptor if isinstance(
            self.descriptor, dict) else self.descriptor.to_mongo()
        try:
            if self.type == DescriptorType.SERVICE.value:
                validateServiceDescriptor(descriptorDict)
            else:
                validateFunctionDescriptor(descriptorDict)
        except ValidationError as error:
            raise InvalidDescriptorContentsException(error.message)

        # Convert `descriptor` to `DescriptorContents` if it is a `dict`
        if isinstance(self.descriptor, dict):
            self.descriptor = DescriptorContents(**self.descriptor)

        return super(Descriptor, self).save(*args, **kwargs)
