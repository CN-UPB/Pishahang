from datetime import datetime

from mongoengine import DateTimeField, Document, UUIDField
from mongoengine.fields import DictField, ListField, ReferenceField

from vim_adaptor.models.vims import BaseVim


class ServiceInstance(Document):
    """
    Document class to store
    """

    id = UUIDField(primary_key=True)
    created_at = DateTimeField(default=datetime.utcnow)

    vims = ListField(ReferenceField(BaseVim))

    # A dict that mapps VIM ids to their details dicts
    vim_details = DictField(required=True)
