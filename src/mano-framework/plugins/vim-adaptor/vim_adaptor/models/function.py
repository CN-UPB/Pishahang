from datetime import datetime

from mongoengine import DateTimeField, Document, UUIDField
from mongoengine.fields import DictField, ReferenceField, StringField

from vim_adaptor.models.vims import BaseVim


class FunctionInstance(Document):
    """
    Document class that contains information on a network function instance. Documents
    are created by a FunctionInstanceManagerFactory instance and hold all the data to
    fully recreate the corresponding FunctionInstanceManager object.
    """

    id = UUIDField(primary_key=True)
    created_at = DateTimeField(default=datetime.utcnow)
    manager_type = StringField(required=True)

    function_id = UUIDField(required=True)
    service_instance_id = UUIDField(required=True)
    descriptor = DictField(required=True)

    vim = ReferenceField(BaseVim)
