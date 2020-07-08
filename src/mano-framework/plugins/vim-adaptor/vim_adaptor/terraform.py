import json
import logging
import shutil
from os import environ
from pathlib import Path
from typing import Any, Dict, Iterable

import wrapt
from appcfg import get_config
from jinja2 import Template
from python_terraform import IsFlagged, Terraform

from vim_adaptor.exceptions import TerraformException

# Hide warnings of python_terraform – we raise exceptions instead.
logging.getLogger("python_terraform").setLevel(logging.ERROR)

# Remove hints from terraform output
environ["TF_IN_AUTOMATION"] = "true"

# Use this to get debug output from Terraform:
# environ["TF_LOG"] = "DEBUG"

config = get_config(__name__)

TERRAFORM_BIN_PATH: Path = Path(__file__).parents[1] / "terraform"


def terraform_method(return_json=False):
    """
    A decorator factory to decorate a method that returns a python_terraform
    `return_code, stdout, stderr` tuple such that it raises and logs a
    TerraformException if return_code is not 0. If `return_json` is set to ``True``,
    `stdout` will be parsed as JSON and the resulting object will be returned from the
    decorated method.
    """

    @wrapt.decorator
    def decorator(wrapped, instance: "TerraformWrapper", args, kwargs):

        return_code, stdout, stderr = wrapped(*args, **kwargs)
        if return_code != 0:
            exception = TerraformException(return_code, stdout, stderr)
            instance._logger.error(
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


class TerraformWrapper:
    """
    Wraps Terraform template rendering (using Jinja2) and Terraform invocations
    """

    _logger = logging.Logger(__name__ + ".TerraformWrapper")

    def __init__(
        self,
        work_dir: Path,
        templates: Iterable[Path],
        context: Dict[str, Any],
        tf_vars: Dict[str, str],
    ):
        """
        Args:
            work_dir: The `Path` where rendered templates will be stored and terraform
                will be executed. Will be created if it does not yet exist.
            templates: The `Path`s of the Jinja2 template files that will be rendered
                and stored in `work_dir`
            context: The context that Jinja2 will use to render the templates
            tf_vars: A `dict` of Terraform variables that will be available to Terraform
        """

        self._work_dir = work_dir
        self._templates = templates
        self._context = context
        self._tf_vars = tf_vars

        work_dir.mkdir(parents=True, exist_ok=True)

        self._terraform = Terraform(
            working_dir=work_dir.as_posix(),
            terraform_bin_path=TERRAFORM_BIN_PATH.as_posix(),
        )

        self.render_templates(templates, context, work_dir)
        self.init()

    @classmethod
    def render_templates(
        cls, templates: Iterable[Path], context: Dict[str, any], output_dir: Path
    ):
        """
        Render the templates specified in `templates` using the context from
        `context` and store them in `output_dir`.
        """
        for template_path in templates:
            with template_path.open() as template_file:
                template = Template(
                    template_file.read(), trim_blocks=True, lstrip_blocks=True,
                )
                with (output_dir / template_path.name).open("w") as output_file:
                    output_file.write(template.render(context))

    def remove_work_dir(self):
        """
        Recursively removes the working directory of this `TerraformWrapper`
        """
        # Remove working directory
        shutil.rmtree(self._work_dir)

    @terraform_method()
    def init(self):
        """
        Runs `terraform init`
        """
        self._logger.debug("Running `terraform init`")
        return self._terraform.init(var=self._tf_vars, input=False)

    @terraform_method()
    def plan(self):
        """
        Runs `terraform plan`
        """
        self._logger.debug("Running `terraform plan`")
        return self._terraform.plan(
            var=self._tf_vars, out="tfplan", input=False, detailed_exitcode=None
        )

    @terraform_method()
    def apply(self):
        """
        Runs `terraform apply`
        """
        self._logger.debug("Running `terraform apply`")
        return self._terraform.apply(
            var=None, dir_or_plan="tfplan", input=False, auto_approve=IsFlagged,
        )  # No vars here, they are included in the plan already

    @terraform_method(return_json=True)
    def show(self):
        """
        Runs `terraform show` and returns the parsed JSON output
        """
        self._logger.debug("Running `terraform show`")
        return self._terraform.cmd("show", no_color=IsFlagged, json=IsFlagged)

    @terraform_method()
    def destroy(self):
        """
        Runs `terraform destroy`
        """
        self._logger.debug("Running `terraform destroy`")
        return self._terraform.destroy(var=self._tf_vars, input=False)

    @terraform_method()
    def state_rm(self, resource: str):
        """
        Runs `terraform state rm <resource>`
        """
        self._logger.debug("Running `terraform state rm {}`".format(resource))
        return self._terraform.cmd("state rm", resource)
