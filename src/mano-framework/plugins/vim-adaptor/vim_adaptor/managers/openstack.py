from copy import deepcopy

import bitmath

from vim_adaptor.managers.terraform import (
    TEMPLATE_BASE_PATH,
    TerraformFunctionInstanceManager,
)
from vim_adaptor.models.vims import OpenStackVim
from vim_adaptor.util import convert_size


class OpenStackFunctionInstanceManager(TerraformFunctionInstanceManager):

    manager_type = "openstack"

    templates = (TEMPLATE_BASE_PATH / "openstack").iterdir()

    def _get_tf_vars(self):
        vim: OpenStackVim = self.function_instance.vim
        return {
            "auth_url": "http://{}/identity".format(vim.address),
            "tenant_id": vim.tenant.id,
            "username": vim.username,
            "password": vim.password,
            "network_id": vim.tenant.external_network_id,
            "router_id": vim.tenant.external_network_id,
        }

    def _get_template_context(self):
        ctx = super()._get_template_context()

        # Copy the descriptor so we can manipulate it
        ctx["descriptor"] = deepcopy(ctx["descriptor"])

        # Convert resource requirements size units for each VDU
        for vdu in ctx["descriptor"]["virtual_deployment_units"]:
            requirements = vdu["resource_requirements"]
            memory = requirements["memory"]
            memory["size"] = round(
                convert_size(memory["size"], memory.get("size_unit", "MB"), bitmath.MB,)
            )
            # Remove the size unit so it does not lead to confusion
            requirements["memory"].pop("size_unit")

            if "storage" in requirements:
                storage = requirements["storage"]
                storage["size"] = round(
                    convert_size(
                        storage["size"], storage.get("size_unit", "MB"), bitmath.GB,
                    ),
                    3,
                )

        return ctx
