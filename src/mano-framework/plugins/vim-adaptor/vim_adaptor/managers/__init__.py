from vim_adaptor.managers.aws import AwsFunctionInstanceManager
from vim_adaptor.managers.base import (
    FunctionInstanceManagerFactory,
    ServiceInstanceHandlerFactory,
)
from vim_adaptor.managers.kubernetes import KubernetesFunctionInstanceManager
from vim_adaptor.managers.openstack import (
    OpenStackFunctionInstanceManager,
    OpenStackServiceInstanceHandler,
)
from vim_adaptor.models.vims import VimType

function_manager_factory = FunctionInstanceManagerFactory()
function_manager_factory.register_class(
    VimType.KUBERNETES.value, KubernetesFunctionInstanceManager
)
function_manager_factory.register_class(
    VimType.OPENSTACK.value, OpenStackFunctionInstanceManager
)
function_manager_factory.register_class(VimType.AWS.value, AwsFunctionInstanceManager)

service_handler_factory = ServiceInstanceHandlerFactory()
service_handler_factory.register_class(
    VimType.OPENSTACK.value, OpenStackServiceInstanceHandler
)

__all__ = ["function_manager_factory", "service_handler_factory"]
