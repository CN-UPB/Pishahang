from copy import deepcopy

import bitmath

from vim_adaptor.managers.terraform import (
    TEMPLATE_BASE_PATH,
    TerraformFunctionInstanceManager,
    TerraformServiceInstanceHandler,
)
from vim_adaptor.models.vims import OpenStackVim
from vim_adaptor.util import convert_size


def get_tf_vars_by_vim(vim: OpenStackVim):
    return {
        "auth_url": f"http://{vim.address}/identity",
        "tenant_id": vim.tenant.id,
        "username": vim.username,
        "password": vim.password,
        "external_network_id": vim.tenant.external_network_id,
        "external_router_id": vim.tenant.external_network_id,
    }


TEMPLATE_PATH = TEMPLATE_BASE_PATH / "openstack"
SHARED_TEMPLATES = [
    (TEMPLATE_PATH / filename).with_suffix(".tf")
    for filename in ["main", "var", "data"]
]


class OpenStackFunctionInstanceManager(TerraformFunctionInstanceManager):

    templates = SHARED_TEMPLATES + [TEMPLATE_PATH / "function.tf"]

    def _get_tf_vars(self):
        return get_tf_vars_by_vim(self.function_instance.vim)

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
            memory.pop("size_unit", None)

            if "storage" in requirements:
                storage = requirements["storage"]
                storage["size"] = round(
                    convert_size(
                        storage["size"], storage.get("size_unit", "MB"), bitmath.GB,
                    ),
                    3,
                )
                memory.pop("size_unit", None)

        return ctx

    def deploy(self) -> dict:
        """
        Deploys the network function and returns an OpenStack function record
        """
        super().deploy()

        # We do not assemble all fields of the record here, as many of them do not seem
        # to be relevant. Chaining-relevant data (such as port IDs) can be extracted
        # from the output of `terraform show`, which can be retrieved like this:

        # resources = self.terraform.show()["values"]["root_module"]["resources"]

        instance = self.function_instance
        record = {
            **instance.descriptor,
            "id": str(instance.id),
            "version": "1",
            "status": "normal operation",
            "descriptor_reference": str(instance.function_id),
            "parent_ns": str(instance.service_instance_id),
        }

        for vdu in record["virtual_deployment_units"]:
            vdu["number_of_instances"] = 1

        return record


class OpenStackServiceInstanceHandler(TerraformServiceInstanceHandler):
    templates = SHARED_TEMPLATES + [TEMPLATE_PATH / "service.tf"]

    def _get_tf_vars(self):
        return get_tf_vars_by_vim(self.vim)
