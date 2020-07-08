from pathlib import Path
from typing import Any, Dict, List

from vim_adaptor.managers.base import FunctionInstanceManager, ServiceInstanceHandler
from vim_adaptor.terraform import TERRAFORM_WORKDIR, TerraformWrapper

TEMPLATE_BASE_PATH: Path = Path(__file__).parents[1] / "templates"


class TerraformFunctionInstanceManager(FunctionInstanceManager):
    """
    An abstract base class for function instance managers that maintains an internal
    `TerraformWrapper` instance and the corresponding working directory. It also comes
    with a ServiceInstanceHandler that manages a shared per-service-instance working
    directory which contains the individual function instance's working directories.
    """

    class TerraformServiceInstanceHandler(ServiceInstanceHandler):
        def on_init(self):
            super().on_init()

            # Create service instance working directory
            self.workdir = TERRAFORM_WORKDIR / self.service_instance_id
            self.workdir.mkdir(parents=True, exist_ok=True)

        def on_destroy(self):
            # Remove service instance working directory
            self.workdir.rmdir()

            super().on_destroy()

    service_instance_handlers = FunctionInstanceManager.service_instance_handlers + [
        TerraformServiceInstanceHandler
    ]

    # The paths of Jinja2 templates that will be rendered to Terraform templates
    templates: List[Path]

    def __init__(self, *args, **kwargs):
        super(TerraformFunctionInstanceManager, self).__init__(*args, **kwargs)

        self.terraform = TerraformWrapper(
            workdir=TERRAFORM_WORKDIR
            / str(self.function_instance.service_instance_id)
            / str(self.function_instance.function_id),
            templates=self.templates,
            context=self._get_template_context(),
            tf_vars=self._get_tf_vars(),
        )

    def _get_tf_vars(self) -> Dict[str, str]:
        """
        To be overridden by subclasses. Returns the variables that will be set on
        terraform calls.
        """
        return {}

    def _get_template_context(self) -> Dict[str, Any]:
        """
        Returns the context that Jinja2 will use to render the templates. May be
        overridden by subclasses.
        """
        return {
            "function_instance_id": self.function_instance.id,
            "function_id": self.function_instance.function_id,
            "service_instance_id": self.function_instance.service_instance_id,
            "descriptor": self.function_instance.descriptor,
        }

    def deploy(self):
        """
        Deploys the network function managed by this TerraformFunctionInstanceManager by
        running `terraform plan`, followed by `terraform apply`. Raises a
        `TerraformException` on failure.
        """
        self.logger.info("Deploying")
        super(TerraformFunctionInstanceManager, self).deploy()
        self.terraform.plan()
        self.terraform.apply()
        self.logger.info("Deployment succeeded")

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionInstanceManager
        by running `terraform destroy`. Raises a `TerraformException` on failure.
        """
        self.logger.info("Destroying")
        self.terraform.destroy()
        self.terraform.remove_workdir()

        super(TerraformFunctionInstanceManager, self).destroy()
        self.logger.info("Destruction succeeded")
