"""
mongoengine document definitions
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from mongoengine import DateTimeField, DictField, Document, StringField, UUIDField


class DescriptorType(Enum):
    """
    An enumeration of valid `type` values for descriptors
    """

    SERVICE = "service"
    VM = "vm"
    CN = "cn"
    FPGA = "fpga"


class TimestampedDocument(Document):
    """
    Abstract Mongoengine `Document` subclass that defines and manages a `createdAt` and an
    `updatedAt` field
    """

    meta = {'abstract': True}
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField()

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.utcnow()
        return super(TimestampedDocument, self).save(*args, **kwargs)


class UuidDocument(Document):
    """
    Abstract Mongoengine `Document` subclass that defines an `id` field containing an auto-generated
    UUID primary key
    """

    meta = {'abstract': True}
    id = UUIDField(default=uuid4, primary_key=True)


class Descriptor(UuidDocument, TimestampedDocument):
    """
    A mongoengine document base class for arbitrary descriptors
    """

    meta = {'allow_inheritance': True}

    type = StringField(required=True, choices=[
                       t.value for t in DescriptorType])
    descriptor = DictField(required=True)


class UploadedDescriptor(Descriptor):
    pass


class OnboardedDescriptor(Descriptor):
    pass


class VimType(Enum):
    """
    An enumeration of valid `type` values for VIM
    """

    OPENSTACK = "openstack"
    KUBERNETES = "kubernetes"
    AWS = "aws"


class Vim(UuidDocument, TimestampedDocument):
    """
    A mongoengine document base class for General VIM
    """
    meta = {'allow_inheritance': True}
    vimName = StringField(required=True)
    country = StringField(required=True)
    city = StringField(required=True)

    # type = StringField(required=True, choices=[
    #     t.value for t in VimType])


class OpenStack(Vim):
    """
    A mongoengine document base class for OpenStack VIM
    """

    vimAddress = StringField(required=True)
    tenantId = StringField(required=True)
    tenantExternalNetwrokId = StringField(required=True)
    tenantExternalRouterId = StringField(required=True)
    username = StringField(required=True)
    password = StringField(required=True)


class Kubernetes(Vim):
    """
    A mongoengine document base class for Kubernetes VIM
    """

    vimAddress = StringField(required=True)
    serviceToken = StringField(required=True)
    ccc = StringField(required=True)


class Aws(Vim):
    """
    A mongoengine document base class for Kubernetes VIM
    """

    accessKey = StringField(required=True)
    secretKey = StringField(required=True)
