"""
Descriptor-related Mongoengine document definitions
"""

from enum import Enum

from jsonschema.exceptions import ValidationError
from mongoengine import (
    DateTimeField,
    DynamicEmbeddedDocument,
    EmbeddedDocument,
    EmbeddedDocumentField,
    StringField,
)

from gatekeeper.exceptions import InvalidDescriptorContentError
from gatekeeper.models.base import (
    TimestampsDocument,
    UserIdMixin,
    UuidDocument,
    UuidMixin,
)
from gatekeeper.util.mongoengine_custom_json import makeHttpDatetime


class DescriptorType(Enum):
    """
    An enumeration of valid `type` values for descriptors
    """

    SERVICE = "service"
    OPENSTACK = "openStack"
    KUBERNETES = "kubernetes"
    AWS = "aws"


class DescriptorContent(DynamicEmbeddedDocument):
    """
    Embedded document class to hold a descriptor's content
    """

    descriptor_type = StringField(required=True)
    descriptor_version = StringField(required=True)
    vendor = StringField(required=True)
    name = StringField(required=True)
    version = StringField(required=True)

    def __str__(self):
        return (
            f'Descriptor(descriptor_type="{self.descriptor_type}", '
            f'vendor="{self.vendor}", name="{self.name}", version="{self.version}")'
        )


class BaseDescriptorMixin(UserIdMixin):
    """
    Document mixin for descriptors.
    """

    type = StringField(required=True, choices=[t.value for t in DescriptorType])
    content = EmbeddedDocumentField(DescriptorContent, required=True)
    contentString = StringField(default="")


class Descriptor(BaseDescriptorMixin, UuidDocument, TimestampsDocument):
    """
    Document class for descriptors. The `descriptor` embedded document field is
    validated on `save`.
    """

    meta = {
        "indexes": [
            {
                "fields": (
                    "userId",
                    "content.descriptor_type",
                    "content.vendor",
                    "content.name",
                    "content.version",
                ),
                "unique": True,
            }
        ]
    }

    def save(self, *args, **kwargs):
        """
        Saves a `Descriptor` document, after validating the `content` field against a
        descriptor schema according to the `type` value. If the validation fails, an
        `exceptions.InvalidDescriptorContentError` is raised.
        """

        descriptorDict = (
            self.content if isinstance(self.content, dict) else self.content.to_mongo()
        )
        try:
            # Import not at top level to prevent circular imports
            from gatekeeper.util.validation import validateDescriptor

            validateDescriptor(self.type, descriptorDict)
        except ValidationError as error:
            raise InvalidDescriptorContentError(error.message)

        # Convert `content` to `DescriptorContents` if it is a `dict`
        if isinstance(self.content, dict):
            self.content = DescriptorContent(**self.content)

        return super(Descriptor, self).save(*args, **kwargs)


class DescriptorSnapshot(UuidMixin, BaseDescriptorMixin, EmbeddedDocument):
    """
    Embedded descriptor document that is not meant to be updated after its creation. It
    can be used to embed a static copy of a `Descriptor` document in another document.
    """

    # Not inheriting from TimestampsDocument, as we want the timestamps to be static
    createdAt = DateTimeField(required=True, custom_json=makeHttpDatetime)
    updatedAt = DateTimeField(required=True, custom_json=makeHttpDatetime)
