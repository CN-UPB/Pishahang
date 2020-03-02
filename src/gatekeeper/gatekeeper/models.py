"""
mongoengine document definitions
"""

from uuid import uuid4

from mongoengine import UUIDField, DictField, StringField
from mongoengine_goodjson import Document


class Descriptor(Document):
    """
    A mongoengine document base class for arbitrary descriptors
    """
    uuid = UUIDField(default=uuid4, primary_key=True)
    type = StringField(required=True)
    descriptor = DictField(required=True)
    # setting file location Uploaded/Onboarded/Instantiated
    location = StringField(required=True)
