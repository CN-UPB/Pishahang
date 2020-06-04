from enum import Enum

from marshmallow_mongoengine import ModelSchema
from mongoengine import StringField, EmbeddedDocumentField, EmbeddedDocument
from mongoengine.errors import DoesNotExist

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


class OpenStackTenant(EmbeddedDocument):
    id = StringField(required=True)
    external_network_id = StringField(required=True)
    internal_router_id = StringField(required=True)


class OpenStackVim(BaseVim):
    address = StringField(required=True)
    username = StringField(required=True)
    password = StringField(required=True)
    tenant = EmbeddedDocumentField(OpenStackTenant, required=True)


class OpenStackVimSchema(ModelSchema):
    class Meta:
        model = OpenStackVim
        model_fields_kwargs = {
            field: {"load_only": True}
            for field in [
                "address",
                "tenant_id",
                "tenant_external_network_id",
                "tenant_external_router_id",
                "username",
                "password",
            ]
        }


class KubernetesVim(BaseVim):
    address = StringField(required=True)
    service_token = StringField(required=True)
    ccc = StringField(required=True)


class KubernetesVimSchema(ModelSchema):
    class Meta:
        model = KubernetesVim
        model_fields_kwargs = {
            field: {"load_only": True} for field in ["address", "service_token", "ccc"]
        }


class AwsVim(BaseVim):
    access_key = StringField(required=True)
    secret_key = StringField(required=True)


class AwsVimSchema(ModelSchema):
    class Meta:
        model = AwsVim
        model_fields_kwargs = {
            field: {"load_only": True} for field in ["access_key", "secret_key"]
        }
