from vim_adaptor.managers.terraform import (
    TEMPLATE_BASE_PATH,
    TerraformFunctionInstanceManager,
)
from vim_adaptor.models.vims import OpenStackVim


class OpenStackFunctionInstanceManager(TerraformFunctionInstanceManager):
    template_path = TEMPLATE_BASE_PATH / "openstack"

    def _get_tf_vars(self):
        vim: OpenStackVim = self.function_instance.vim
        return {
            "auth_url": "http://{}/identity".format(vim.address),
            "tenant_id": vim.tenant.id,
            "user_name": vim.username,
            "user_password": vim.password,
            "network_id": vim.tenant.external_network_id,
            "router_id": vim.tenant.external_network_id,
        }
