from copy import deepcopy

from vim_adaptor.managers.terraform import (
    TEMPLATE_BASE_PATH,
    TerraformFunctionInstanceManager,
)
from vim_adaptor.models.vims import AwsVim


class AwsFunctionInstanceManager(TerraformFunctionInstanceManager):

    templates = list((TEMPLATE_BASE_PATH / "aws").iterdir())

    def _get_tf_vars(self):
        vim: AwsVim = self.function_instance.vim
        return {
            "access_key": vim.access_key,
            "secret_key": vim.secret_key,
            "region": vim.region,
        }

    def deploy(self) -> dict:
        """
        Deploys the network function and returns an AWS function record
        """
        super().deploy()

        instance = self.function_instance
        record = {
            **deepcopy(instance.descriptor),
            "id": str(instance.id),
            "version": "1",
            "status": "normal operation",
            "descriptor_reference": str(instance.function_id),
            "parent_ns": str(instance.service_instance_id),
        }

        resources = self.terraform.show()["values"]["root_module"]["resources"]

        def get_resource_values_by_vdu_id(vdu_id: str):
            for resource in resources:
                if resource["name"] == vdu_id:
                    return resource["values"]

        for vdu in record["virtual_deployment_units"]:
            vdu["number_of_instances"] = 1
            vdu["vim_id"] = str(instance.vim.id)

            resource_values = get_resource_values_by_vdu_id(vdu["id"])
            # Add relevant fields from the terraform resource to the record
            for key in [
                "arn",
                "availability_zone",
                ("instance_id", "id"),
                "instance_state",
                "ipv6_addresses",
                "primary_network_interface_id",
                "private_ip",
                "public_dns",
                "public_ip",
                "subnet_id",
            ]:
                if isinstance(key, tuple):
                    vdu[key[0]] = resource_values[key[1]]
                else:
                    vdu[key] = resource_values[key]

        return record
