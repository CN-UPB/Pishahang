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
