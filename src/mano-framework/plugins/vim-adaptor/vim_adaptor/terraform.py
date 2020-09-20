import json
import logging
import shutil
import subprocess
from os import environ
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Tuple

from appcfg import get_config
from jinja2 import Template

from vim_adaptor.exceptions import TerraformException

# Remove hints from terraform output
environ["TF_IN_AUTOMATION"] = "true"

# Use this to get debug output from Terraform:
# environ["TF_LOG"] = "TRACE"

config = get_config(__name__)

TERRAFORM_BIN_PATH: Path = Path(__file__).parents[1] / "terraform"
TERRAFORM_WORKDIR = Path(config["terraform_workdir"])


class TerraformWrapper:
    """
    Wraps Terraform template rendering (using Jinja2) and Terraform invocations for a
    specified working directory
    """

    _logger = logging.Logger(__name__ + ".TerraformWrapper")

    def __init__(
        self,
        workdir: Path,
        templates: List[Path],
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

        self.workdir = workdir
        self._templates = templates
        self._context = context
        self._tf_vars = tf_vars

        self._invocation_lock = Lock()

        workdir.mkdir(parents=True, exist_ok=True)

        self.render_templates(templates, context, workdir)
        self.init()

    def _invoke(
        self, subcommand, *args: Tuple[str], vars: Dict[str, str] = None
    ) -> subprocess.CompletedProcess:
        """
        Invokes terraform with the provided arguments and variables and returns a
        `subprocess.CompletedProcess` object. Raises a `TerraformException` on error.
        """
        with self._invocation_lock:
            if vars is not None:
                args = [
                    '-var="{}={}"'.format(key, str(value).replace('"', '\\"'))
                    for key, value in vars.items()
                ] + list(args)

            result = subprocess.run(
                " ".join([TERRAFORM_BIN_PATH.as_posix(), subcommand, *args]),
                cwd=self.workdir,
                shell=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            if result.returncode != 0:
                exception = TerraformException(result.returncode, result.stdout)
                self._logger.error(
                    "Terraform invocation failed (exit code %d): ",
                    result.returncode,
                    exc_info=exception,
                )
                raise exception

            return result

    @classmethod
    def render_templates(
        cls, templates: List[Path], context: Dict[str, any], output_dir: Path
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

    def remove_workdir(self):
        """
        Recursively removes the working directory of this `TerraformWrapper`
        """
        # Remove working directory
        shutil.rmtree(self.workdir)

    def init(self):
        """
        Runs `terraform init`
        """
        self._logger.debug("Running `terraform init`")
        return self._invoke(
            "init",
            "-no-color",
            "-input=false",
            "-reconfigure",
            "-backend=true",
            vars=self._tf_vars,
        )

    def plan(self):
        """
        Runs `terraform plan`
        """
        self._logger.debug("Running `terraform plan`")
        return self._invoke(
            "plan", "-no-color", "-input=false", "-out=tfplan", vars=self._tf_vars
        )

    def apply(self):
        """
        Runs `terraform apply`
        """
        self._logger.debug("Running `terraform apply`")

        return self._invoke(
            "apply", "-no-color", "-input=false", "-auto-approve", "tfplan",
        )  # No vars here, they are included in the plan already

    def show(self) -> dict:
        """
        Runs `terraform show` and returns the parsed JSON output
        """
        self._logger.debug("Running `terraform show`")
        return json.loads(self._invoke("show", "-no-color", "-json").stdout)

    def destroy(self):
        """
        Runs `terraform destroy`
        """
        self._logger.debug("Running `terraform destroy`")
        return self._invoke(
            "destroy", "-no-color", "-input=false", "-force", vars=self._tf_vars
        )
