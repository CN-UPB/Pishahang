import json
import logging
import os
from pathlib import Path

import wrapt
from appcfg import get_config
from jinja2 import Environment, FileSystemLoader
from python_terraform import IsFlagged, Terraform

from vim_adaptor.exceptions import TerraformException
from vim_adaptor.models.vims import BaseVim

# Hide warnings of python_terraform – we raise exceptions instead.
logging.getLogger("python_terraform").setLevel(logging.ERROR)

# Remove hints from terraform output
os.environ["TF_IN_AUTOMATION"] = "true"

# Use this to get debug output from Terraform:
# os.environ["TF_LOG"] = "DEBUG"

config = get_config(__name__)

TEMPLATE_BASE_PATH: Path = Path(__file__).parent / "templates"
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
    def decorator(wrapped, instance: "TerraformFunctionManager", args, kwargs):

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


class TerraformFunctionManager:
    """
    A base class for function managers that abstracts Terraform template compilation,
    Terraform invocations, and VIM retrieval
    """

    def __init__(
        self,
        template_path: Path,
        vim: BaseVim,
        service_id: str,
        service_instance_id: str,
        function_id: str,
        function_instance_id: str,
        descriptor: dict,
        vars={},
    ):
        """
        Initializes a TerraformFunctionManager, compiles the templates from
        `template_dir` and runs `terraform init`. Raises a `TerraformException` if
        terraform fails to initialize.

        Args:

            template_path: The template directory to compile the templates from
            vim: The VIM model object of the TerraformFunctionManager (used for logging)
            service_id: The uuid of the service the manager belongs to
            service_instance_id: The uuid of the service instance the manager belongs to
            function_id: The uuid of the function the manager belongs to
            function_instance_id: The uuid of the function instance the manager belongs to
            descriptor: The descriptor of the network function that the manager will control
            vars: Environment variables that will be available to Terraform
        """
        self.vim = vim
        self.service_id = service_id
        self.service_instance_id = service_instance_id
        self.function_id = function_id
        self.function_instance_id = function_instance_id
        self.descriptor = descriptor
        self.vars = vars

        self._function_repr = "Function: {} ({}), Service: {}, VIM: {} ({})".format(
            descriptor["name"],
            function_instance_id,
            service_instance_id,
            vim.name,
            vim.id,
        )

        self.logger = logging.getLogger(
            "{}.FunctionManager({})".format(__name__, self._function_repr)
        )

        self._work_dir: Path = Path(
            config["terraform_workdir"]
        ) / self.service_instance_id / self.function_id
        self._work_dir.mkdir(parents=True, exist_ok=True)

        self._terraform = Terraform(
            working_dir=self._work_dir.as_posix(),
            terraform_bin_path=TERRAFORM_BIN_PATH.as_posix(),
        )

        self._render_templates(template_path)
        self._tf_init()

    def _render_templates(self, template_path: Path, context={}):
        """
        Render the templates from `template_path` and store them in `self._work_dir`.

        Args:

            template_path: The directory to read the templates from
            context: The render context. The `service_id`, `service_instance_id`,
                `function_id`, `function_instance_id`, and `descriptor` fields are set
                by default.
        """
        env = Environment(
            loader=FileSystemLoader(template_path.as_posix()),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.globals = {
            "service_id": self.service_id,
            "service_instance_id": self.service_instance_id,
            "function_id": self.function_id,
            "function_instance_id": self.function_instance_id,
            "descriptor": self.descriptor,
            **context,
        }

        self.logger.debug(
            "Rendering templates from %s to %s. Context: %s",
            template_path,
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
        self.logger.debug("Executing `terraform init`")
        return self._terraform.init(var=self.vars, input=False)

    @terraform_method()
    def _tf_plan(self):
        """
        Runs `terraform plan`
        """
        self.logger.debug("Executing `terraform plan`")
        return self._terraform.plan(
            var=self.vars, out="tfplan", input=False, detailed_exitcode=None
        )

    @terraform_method()
    def _tf_apply(self):
        """
        Runs `terraform apply`
        """
        self.logger.debug("Executing `terraform apply`")
        return self._terraform.apply(
            var=None, dir_or_plan="tfplan", input=False, auto_approve=IsFlagged,
        )  # No vars here, they are included in the plan already

    @terraform_method(return_json=True)
    def _tf_show(self):
        """
        Runs `terraform show` and returns the parsed JSON output
        """
        self.logger.debug("Executing `terraform show`")
        return self._terraform.cmd("show", no_color=IsFlagged, json=IsFlagged)

    @terraform_method()
    def _tf_destroy(self):
        """
        Runs `terraform destroy`
        """
        self.logger.debug("Executing `terraform destroy`")
        return self._terraform.destroy(var=self.vars, input=False)

    def deploy(self):
        """
        Deploys the network function managed by this TerraformFunctionManager by running
        `terraform plan`, followed by `terraform apply`. Raises a `TerraformException`
        on failure.
        """
        self.logger.info("Deploying")
        self._tf_plan()
        self._tf_apply()
        self.logger.info("Deployment succeeded")

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionManager by
        running `terraform destroy`. Raises a `TerraformException` on failure.
        """
        self.logger.info("Destroying")
        self._tf_destroy()
        self.logger.info("Destruction succeeded")
