import logging
from pathlib import Path

from vim_adaptor.managers.base import TEMPLATE_BASE_PATH, TerraformFunctionManager
from vim_adaptor.models.vims import KubernetesVim

LOGGER = logging.getLogger(__name__)

TEMPLATE_PATH: Path = TEMPLATE_BASE_PATH / "kubernetes"


class KubernetesFunctionManager(TerraformFunctionManager):
    def __init__(
        self,
        service_id: str,
        service_instance_id: str,
        function_instance_id: str,
        descriptor: dict,
        vim_id: str,
    ):
        vim: KubernetesVim = KubernetesVim.get_by_id(vim_id)
        super().__init__(
            function_instance_id,
            descriptor,
            vars={"host": vim.address, "token": vim.service_token},
        )
        self._function_repr = 'function "{}" ({}) of service {} on VIM "{}" ({})'.format(
            descriptor["name"],
            function_instance_id,
            service_instance_id,
            vim.name,
            vim.id,
        )
        self._compile_templates(
            list(TEMPLATE_PATH.iterdir()),
            context={
                "descriptor": descriptor,
                "service_id": service_id,
                "service_instance_id": service_instance_id,
                "function_instance_id": function_instance_id,
            },
        )
        self._tf_init()

    def deploy(self):
        LOGGER.info("Deploying %s", self._function_repr)
        self._tf_plan()
        self._tf_apply()
