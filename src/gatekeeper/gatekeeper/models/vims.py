from datetime import datetime
from enum import Enum
from uuid import uuid4

from mongoengine import DateTimeField, DictField, Document, StringField, UUIDField
from .base import UuidDocument, TimestampedDocument


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
    type = StringField(required=True)

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
    A mongoengine document base class for AWS VIM
    """

    accessKey = StringField(required=True)
    secretKey = StringField(required=True)
