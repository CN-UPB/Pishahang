import json
import logging
import shutil
from os import environ
from pathlib import Path

import wrapt
from appcfg import get_config
from jinja2 import Environment, FileSystemLoader
from python_terraform import IsFlagged, Terraform

from vim_adaptor.exceptions import TerraformException
from vim_adaptor.managers.base import FunctionInstanceManager
from vim_adaptor.models.function import FunctionInstance

# Hide warnings of python_terraform – we raise exceptions instead.
logging.getLogger("python_terraform").setLevel(logging.ERROR)

# Remove hints from terraform output
environ["TF_IN_AUTOMATION"] = "true"

# Use this to get debug output from Terraform:
# environ["TF_LOG"] = "DEBUG"

config = get_config(__name__)

TEMPLATE_BASE_PATH: Path = Path(__file__).parents[1] / "templates"
TERRAFORM_BIN_PATH: Path = Path(__file__).parents[2] / "terraform"


def terraform_method(return_json=False):
    """
    A decorator factory to decorate a method that returns a python_terraform
    `return_code, stdout, stderr` tuple such that it raises and logs a
    TerraformException if return_code is not 0. If `return_json` is set to ``True``,
    `stdout` will be parsed as JSON and the resulting object will be returned from the
    decorated method.
    """

    @wrapt.decorator
    def decorator(wrapped, instance: "FunctionInstanceManager", args, kwargs):

        return_code, stdout, stderr = wrapped(*args, **kwargs)
        if return_code != 0:
            exception = TerraformException(return_code, stdout, stderr)
            instance.logger.error(
                "Terraform invocation failed (exit code %d): ",
                return_code,
                exc_info=exception,
            )
            raise exception

        if not return_json:
            return return_code, stdout, stderr

        # Parse stdout as JSON
        return json.loads(stdout)

    return decorator


class TerraformFunctionInstanceManager(FunctionInstanceManager):
    """
    An abstract base class for terraform-base function instance managers that abstracts
    Terraform template compilation (using Jinja2) and Terraform invocations
    """

    # The path that Jinja2 will render Terraform templates from
    template_path: Path = None

    def __init__(
        self, function_instance: FunctionInstance,
    ):
        super(TerraformFunctionInstanceManager, self).__init__(function_instance)

        self._work_dir: Path = Path(config["terraform_workdir"]) / str(
            self.function_instance.service_instance_id
        ) / str(self.function_instance.function_id)
        self._work_dir.mkdir(parents=True, exist_ok=True)

        self._tf_vars = self._get_tf_vars()
        self._terraform = Terraform(
            working_dir=self._work_dir.as_posix(),
            terraform_bin_path=TERRAFORM_BIN_PATH.as_posix(),
        )

        self._render_templates()
        self._tf_init()

    def _get_tf_vars(self) -> dict:
        """
        To be overridden by subclasses.
        Returns the variables that will be set on terraform calls.
        """
        return {}

    def _get_template_context(self) -> dict:
        """
        Returns the context that Jinja2 will use to render the templates.
        """
        return {
            "function_instance_id": self.function_instance.id,
            "function_id": self.function_instance.function_id,
            "service_instance_id": self.function_instance.service_instance_id,
            "descriptor": self.function_instance.descriptor,
        }

    def _render_templates(self):
        """
        Render the templates from `template_path` using the context returned by
        `_get_template_context()` and store them in `_work_dir`.
        """
        env = Environment(
            loader=FileSystemLoader(self.template_path.as_posix()),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.globals = self._get_template_context()

        self.logger.debug(
            "Rendering templates from %s to %s. Context: %s",
            self.template_path,
            self._work_dir,
            env.globals,
        )
        for template_name in env.list_templates():
            with (self._work_dir / template_name).open("w") as target_file:
                target_file.write(env.get_template(template_name).render())

    @terraform_method()
    def _tf_init(self):
        """
        Runs `terraform init`
        """
        self.logger.debug("Running `terraform init`")
        return self._terraform.init(var=self._tf_vars, input=False)

    @terraform_method()
    def _tf_plan(self):
        """
        Runs `terraform plan`
        """
        self.logger.debug("Running `terraform plan`")
        return self._terraform.plan(
            var=self._tf_vars, out="tfplan", input=False, detailed_exitcode=None
        )

    @terraform_method()
    def _tf_apply(self):
        """
        Runs `terraform apply`
        """
        self.logger.debug("Running `terraform apply`")
        return self._terraform.apply(
            var=None, dir_or_plan="tfplan", input=False, auto_approve=IsFlagged,
        )  # No vars here, they are included in the plan already

    @terraform_method(return_json=True)
    def _tf_show(self):
        """
        Runs `terraform show` and returns the parsed JSON output
        """
        self.logger.debug("Running `terraform show`")
        return self._terraform.cmd("show", no_color=IsFlagged, json=IsFlagged)

    @terraform_method()
    def _tf_destroy(self):
        """
        Runs `terraform destroy`
        """
        self.logger.debug("Running `terraform destroy`")
        return self._terraform.destroy(var=self._tf_vars, input=False)

    def deploy(self):
        """
        Deploys the network function managed by this TerraformFunctionInstanceManager by
        running `terraform plan`, followed by `terraform apply`. Raises a
        `TerraformException` on failure.
        """
        super(TerraformFunctionInstanceManager, self).deploy()
        self._tf_plan()
        self._tf_apply()
        self.logger.info("Deployment succeeded")

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionInstanceManager
        by running `terraform destroy`. Raises a `TerraformException` on failure.
        """
        super(TerraformFunctionInstanceManager, self).destroy()
        self._tf_destroy()

        # Remove working directory
        shutil.rmtree(self._work_dir)

        # Remove service instance directory if it is empty now
        service_instance_dir = self._work_dir.parent
        if len(list(service_instance_dir.iterdir())) == 0:
            service_instance_dir.rmdir()

        self.logger.info("Destruction succeeded")
