"""
Descriptor-related Mongoengine document definitions
"""

from mongoengine import BooleanField, StringField, BinaryField

from .base import TimestampedDocument, UuidDocument


class User(UuidDocument, TimestampedDocument):
    """
    Represents a user.

    Note: `passwordSalt` and `passwordHash` can be generated using the functions from `util`.
    """

    username = StringField(required=True, unique=True)

    passwordSalt = BinaryField(max_bytes=32, required=True)
    passwordHash = BinaryField(max_bytes=128, required=True)

    isAdmin = BooleanField(required=True)

    # def to_mongo(self, *args, **kwargs):
    #     # Exclude passwordSalt and passwordHash from json representation
    #     data: dict = super().to_mongo(*args, **kwargs)
    #     # data.pop('passwordSalt')
    #     # data.pop('passwordHash')
    #     return data
