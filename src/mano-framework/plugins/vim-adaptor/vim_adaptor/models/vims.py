from enum import Enum

from marshmallow_mongoengine import ModelSchema
from mongoengine import EmbeddedDocument, EmbeddedDocumentField, StringField
from mongoengine.errors import DoesNotExist
from mongoengine.fields import IntField

from vim_adaptor.exceptions import VimNotFoundException
from vim_adaptor.models.base import BaseDocument


class VimType(Enum):
    OPENSTACK = "openstack"
    KUBERNETES = "kubernetes"
    AWS = "aws"


class BaseVim(BaseDocument):
    """
    Common VIM document base class
    """

    meta = {"allow_inheritance": True}

    name = StringField(required=True)
    country = StringField(required=True)
    city = StringField(required=True)
    type = StringField(required=True, choices=[t.value for t in VimType])

    @classmethod
    def get_by_id(cls, vim_id: str) -> "BaseVim":
        try:
            return cls.objects.get(id=vim_id)
        except DoesNotExist:
            raise VimNotFoundException(cls.__class__.name, vim_id)

    def get_resource_utilization(self):
        raise NotImplementedError(
            "This method is only implemented for subclasses of BaseVim."
        )


class OpenStackTenant(EmbeddedDocument):
    id = StringField(required=True)
    external_network_id = StringField(required=True)
    external_router_id = StringField(required=True)


class OpenStackVim(BaseVim):
    address = StringField(required=True)
    username = StringField(required=True)
    password = StringField(required=True)
    tenant = EmbeddedDocumentField(OpenStackTenant, required=True)

    def get_resource_utilization(self):
        from vim_adaptor.resource_utilization.openstack import get_resource_utilization

        return get_resource_utilization(self)


class OpenStackVimSchema(ModelSchema):
    class Meta:
        model = OpenStackVim


class KubernetesVim(BaseVim):
    address = StringField(required=True)
    port = IntField(required=True)
    service_token = StringField(required=True)
    ccc = StringField(required=True)

    def get_resource_utilization(self):
        from vim_adaptor.resource_utilization.kubernetes import get_resource_utilization

        return get_resource_utilization(self)

    @property
    def url(self):
        return "https://{}:{}".format(self.address, self.port)


class KubernetesVimSchema(ModelSchema):
    class Meta:
        model = KubernetesVim


class AwsVim(BaseVim):
    access_key = StringField(required=True)
    secret_key = StringField(required=True)

    def get_resource_utilization(self):
        from vim_adaptor.resource_utilization.aws import get_resource_utilization

        return get_resource_utilization(self)


class AwsVimSchema(ModelSchema):
    class Meta:
        model = AwsVim
