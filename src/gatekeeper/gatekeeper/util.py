import hashlib
import os
from datetime import datetime, timezone

from bson import json_util
from flask.json import JSONEncoder
from mongoengine.base import BaseDocument
from mongoengine.queryset import QuerySet

from gatekeeper.models.users import User


class MongoEngineJSONEncoder(JSONEncoder):
    """
    A JSONEncoder which provides serialization of MongoEngine
    documents and queryset objects.
    """

    def default(self, obj):
        if isinstance(obj, BaseDocument):
            doc: dict = obj.to_mongo()

            # Convert IDs
            if "_id" in doc and "id" not in doc:
                doc["id"] = str(doc.pop("_id"))

            # Convert datetime fields to RFC 3339 format (in UTC time zone)
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.replace(tzinfo=timezone.utc, microsecond=0).isoformat()

            # Remove Mongoengine class field if it exists
            if "_cls" in doc:
                doc.pop("_cls")

            # Remove passwordSalt and passwordHash for Users
            if isinstance(obj, User):
                doc.pop("passwordSalt")
                doc.pop("passwordHash")

            return json_util._json_convert(doc)
        if isinstance(obj, QuerySet):
            return [self.default(entry) for entry in obj]

        return super().default(obj)


def makeMessageDict(status: int, detail: str):
    """
    Given a `detail` string with a message and a `status` integer, returns a dictionary containing
    those two items.
    """
    return {"detail": detail, "status": status}


def makeMessageResponse(status: int, detail: str):
    """
    Given a `detail` string and a `status` integer, returns a tuple containing the result of
    `makeErrorDict()` and the `status` code. This can be returned from flask route handlers.
    """
    return makeMessageDict(status, detail), status


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
