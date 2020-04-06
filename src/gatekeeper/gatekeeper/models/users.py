"""
User-related Mongoengine document definitions
"""

import hashlib
import os

from mongoengine import BinaryField, BooleanField, StringField

from gatekeeper.models.base import TimestampedDocument, UuidDocument
from gatekeeper.util.mongoengine_custom_json import CustomJsonRules


def generateSalt() -> bytes:
    """
    Returns a random 32-byte salt that can be used with `hashPassword()`.
    """
    return os.urandom(32)


def hashPassword(password: str, salt: bytes) -> bytes:
    """
    Given a password, returns a hash using the given salt (use `generateSalt()`) to generate it.
    """
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),  # Convert the password to bytes
        salt,
        100000,  # It is recommended to use at least 100,000 iterations of SHA-256
        dklen=128  # Get a 128 byte key
    )


class User(UuidDocument, TimestampedDocument):
    """
    Represents a user.

    Note: A `User`'s password can be set and validated using `setPassword()` and
    `validatePassword()`. It may also be provided to the constructor.
    """

    def __init__(self, **kwargs):
        password = kwargs.pop("password", None)
        super(User, self).__init__(**kwargs)
        if password:
            self.setPassword(password)

    username = StringField(required=True, unique=True)
    isAdmin = BooleanField(required=True)

    passwordSalt = BinaryField(max_bytes=32, required=True, custom_json=CustomJsonRules.HIDDEN)
    passwordHash = BinaryField(max_bytes=128, required=True, custom_json=CustomJsonRules.HIDDEN)

    def setPassword(self, password: str):
        self.passwordSalt = generateSalt()
        self.passwordHash = hashPassword(password, self.passwordSalt)

    def validatePassword(self, password: str) -> bool:
        return bytes(self.passwordHash) == hashPassword(password, self.passwordSalt)

    meta = {'allow_inheritance': True}
