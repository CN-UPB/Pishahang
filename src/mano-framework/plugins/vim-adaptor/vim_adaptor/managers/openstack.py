from pathlib import Path

from vim_adaptor.managers.base import TEMPLATE_BASE_PATH, TerraformFunctionManager
from vim_adaptor.models.vims import OpenStackVim

TEMPLATE_PATH: Path = TEMPLATE_BASE_PATH / "openstack"


class OpenStackFunctionManager(TerraformFunctionManager):
    def __init__(
        self,
        vim_id: str,
        service_id: str,
        service_instance_id: str,
        function_id: str,
        function_instance_id: str,
        descriptor: dict,
    ):
        vim: OpenStackVim = OpenStackVim.get_by_id(vim_id)
        super().__init__(
            TEMPLATE_PATH,
            vim,
            service_id,
            service_instance_id,
            function_id,
            function_instance_id,
            descriptor,
            vars={
                "auth_url": "http://{}/identity".format(vim.address),
                "tenant_id": vim.tenant.id,
                "user_name": vim.username,
                "user_password": vim.password,
                "network_id": vim.tenant.external_network_id,
                "router_id": vim.tenant.external_network_id,
            },
        )
