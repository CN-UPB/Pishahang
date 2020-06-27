import logging
from copy import deepcopy
from pathlib import Path

from vim_adaptor.managers.base import TEMPLATE_BASE_PATH, TerraformFunctionManager
from vim_adaptor.models.vims import KubernetesVim

LOGGER = logging.getLogger(__name__)

TEMPLATE_PATH: Path = TEMPLATE_BASE_PATH / "kubernetes"


class KubernetesFunctionManager(TerraformFunctionManager):
    def __init__(
        self,
        vim_id: str,
        service_id: str,
        service_instance_id: str,
        function_id: str,
        function_instance_id: str,
        descriptor: dict,
    ):
        vim: KubernetesVim = KubernetesVim.get_by_id(vim_id)
        super().__init__(
            TEMPLATE_PATH,
            vim,
            service_id,
            service_instance_id,
            function_id,
            function_instance_id,
            descriptor,
            vars={"host": vim.url, "token": vim.service_token, "ccc": vim.ccc},
        )

    def deploy(self):
        """
        Deploys the network function and returns a Kubernetes Function Record
        """
        super().deploy()

        # Once needed, we can use this to get resource-specific data from terraform:
        # resources = self._tf_show()["values"]["root_module"]["resources"]

        record = {
            **deepcopy(self.descriptor),
            "id": self.function_instance_id,
            "version": "1",
            "status": "normal operation",
            "descriptor_reference": self.function_id,
            "parent_ns": self.service_instance_id,
        }

        for vdu in record["virtual_deployment_units"]:
            vdu["number_of_instances"] = (
                vdu["scale_in_out"]["minimum"]
                if "scale_in_out" in vdu and "minimum" in vdu["scale_in_out"]
                else 1
            )
            vdu["vim_id"] = str(self.vim.id)

        return record
