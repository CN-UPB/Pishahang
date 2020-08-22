from datetime import datetime

from mongoengine import DateTimeField, Document, UUIDField
from mongoengine.fields import DictField, ReferenceField

from vim_adaptor.models.vims import BaseVim


class FunctionInstance(Document):
    """
    Document class that contains information on a network function instance. Documents
    are created by an `FunctionInstanceManagerFactory` and hold all the data to fully
    recreate the corresponding `FunctionInstanceManager` object.
    """

    id = UUIDField(primary_key=True)
    created_at = DateTimeField(default=datetime.utcnow)

    vim = ReferenceField(BaseVim)

    function_id = UUIDField(required=True)
    service_instance_id = UUIDField(required=True)
    descriptor = DictField(required=True)
