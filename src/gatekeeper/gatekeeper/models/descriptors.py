"""
Descriptor-related Mongoengine document definitions
"""

from enum import Enum

from mongoengine import DictField, StringField

from .base import TimestampedDocument, UuidDocument


class DescriptorType(Enum):
    """
    An enumeration of valid `type` values for descriptors
    """

    SERVICE = "service"
    VM = "vm"
    CN = "cn"
    FPGA = "fpga"


class UploadedDescriptor(UuidDocument, TimestampedDocument):
    """
    A mongoengine document base class for arbitrary descriptors
    """

    meta = {'allow_inheritance': True}

    type = StringField(required=True, choices=[t.value for t in DescriptorType])
    descriptor = DictField(required=True)
