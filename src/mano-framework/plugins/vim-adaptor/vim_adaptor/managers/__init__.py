from vim_adaptor.managers.base import FunctionInstanceManagerFactory
from vim_adaptor.managers.kubernetes import KubernetesFunctionInstanceManager
from vim_adaptor.managers.openstack import OpenStackFunctionInstanceManager

factory = FunctionInstanceManagerFactory()
factory.register_manager_type("kubernetes", KubernetesFunctionInstanceManager)
factory.register_manager_type("openstack", OpenStackFunctionInstanceManager)

__all__ = ["factory"]
