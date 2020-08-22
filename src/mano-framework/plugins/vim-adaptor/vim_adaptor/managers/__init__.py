from vim_adaptor.managers.base import FunctionInstanceManagerFactory
from vim_adaptor.managers.kubernetes import KubernetesFunctionInstanceManager
from vim_adaptor.managers.openstack import OpenStackFunctionInstanceManager
from vim_adaptor.models.vims import VimType

factory = FunctionInstanceManagerFactory()
factory.register_class(VimType.KUBERNETES.value, KubernetesFunctionInstanceManager)
factory.register_class(VimType.OPENSTACK.value, OpenStackFunctionInstanceManager)

__all__ = ["factory"]
