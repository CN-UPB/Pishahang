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


class Descriptor(UuidDocument, TimestampedDocument):
    """
    A mongoengine document class for arbitrary descriptors
    """

    type = StringField(required=True, choices=[t.value for t in DescriptorType])
    descriptor = DictField(required=True)
