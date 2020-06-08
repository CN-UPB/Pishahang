import logging
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
            vars={"host": vim.address, "token": vim.service_token},
        )
