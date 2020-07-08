from copy import deepcopy

from vim_adaptor.managers.terraform import (
    TEMPLATE_BASE_PATH,
    TerraformFunctionInstanceManager,
)
from vim_adaptor.models.vims import KubernetesVim


class KubernetesFunctionInstanceManager(TerraformFunctionInstanceManager):

    manager_type = "kubernetes"

    template_path = TEMPLATE_BASE_PATH / "kubernetes"

    def _get_tf_vars(self):
        vim: KubernetesVim = self.function_instance.vim
        return {"host": vim.url, "token": vim.service_token, "ccc": vim.ccc}

    def deploy(self) -> dict:
        """
        Deploys the network function and returns a Kubernetes function record
        """
        super().deploy()

        # Once needed, we can use this to get resource-specific data from terraform:
        # resources = self._tf_show()["values"]["root_module"]["resources"]

        instance = self.function_instance
        record = {
            **deepcopy(instance.descriptor),
            "id": str(instance.id),
            "version": "1",
            "status": "normal operation",
            "descriptor_reference": str(instance.function_id),
            "parent_ns": str(instance.service_instance_id),
        }

        for vdu in record["virtual_deployment_units"]:
            vdu["number_of_instances"] = (
                vdu["scale_in_out"]["minimum"]
                if "scale_in_out" in vdu and "minimum" in vdu["scale_in_out"]
                else 1
            )
            vdu["vim_id"] = str(instance.vim.id)

        return record
