from pathlib import Path
from typing import Any, Dict, Iterable

from appcfg import get_config

from vim_adaptor.managers.base import FunctionInstanceManager
from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.terraform import TerraformWrapper

config = get_config(__name__)

TEMPLATE_BASE_PATH: Path = Path(__file__).parents[1] / "templates"


class TerraformFunctionInstanceManager(FunctionInstanceManager):
    """
    An abstract base class for function instance managers that maintains an internal
    `TerraformWrapper` instance.
    """

    # The paths of Jinja2 templates that will be rendered to Terraform templates
    templates: Iterable[Path] = None

    def __init__(
        self, function_instance: FunctionInstance,
    ):
        super(TerraformFunctionInstanceManager, self).__init__(function_instance)

        self._work_dir: Path = Path(config["terraform_workdir"]) / str(
            self.function_instance.service_instance_id
        ) / str(self.function_instance.function_id)

        self.terraform = TerraformWrapper(
            self._work_dir,
            self.templates,
            self._get_template_context(),
            self._get_tf_vars(),
        )

    def _get_tf_vars(self) -> Dict[str, str]:
        """
        To be overridden by subclasses. Returns the variables that will be set on
        terraform calls.
        """
        return {}

    def _get_template_context(self) -> Dict[str, Any]:
        """
        Returns the context that Jinja2 will use to render the templates.
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
        super(TerraformFunctionInstanceManager, self).deploy()
        self.terraform.plan()
        self.terraform.apply()
        self.logger.info("Deployment succeeded")

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionInstanceManager
        by running `terraform destroy`. Raises a `TerraformException` on failure.
        """
        super(TerraformFunctionInstanceManager, self).destroy()
        self.terraform.destroy()
        self.terraform.remove_work_dir()

        # Remove service instance directory if it is empty now
        service_instance_dir = self._work_dir.parent
        if len(list(service_instance_dir.iterdir())) == 0:
            service_instance_dir.rmdir()

        self.logger.info("Destruction succeeded")
