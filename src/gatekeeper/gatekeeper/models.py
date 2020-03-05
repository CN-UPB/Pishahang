"""
mongoengine document definitions
"""

from uuid import uuid4

from mongoengine import DictField, StringField, UUIDField
from mongoengine_goodjson import Document


class Descriptor(Document):
    """
    A mongoengine document base class for arbitrary descriptors
    """
    uuid = UUIDField(default=uuid4, primary_key=True)
    type = StringField(required=True, )
    descriptor = DictField(required=True)

    meta = {'allow_inheritance': True}

class UploadedDescriptor(Descriptor):
    pass

class OnboardedDescriptor(Descriptor):
    pass


class OpenStack(Document):
    """
    A mongoengine document base class for arbitrary descriptors
    """
    uuid = UUIDField(default=uuid4, primary_key=True)
    type = StringField(required=True)
    vims = DictField(required=True)
