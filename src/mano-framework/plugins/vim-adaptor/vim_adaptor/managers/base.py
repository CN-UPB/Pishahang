import logging
from pathlib import Path
from typing import List

import wrapt
from appcfg import get_config
from jinja2 import Template
from python_terraform import Terraform

from vim_adaptor.exceptions import TerraformException
from vim_adaptor.models.vims import BaseVim

# Hide warnings of python_terraform – we raise exceptions instead.
logging.getLogger("python_terraform").setLevel(logging.ERROR)

config = get_config(__name__)

TEMPLATE_BASE_PATH: Path = Path(__file__).parent / "templates"
TERRAFORM_BIN_PATH: Path = Path(__file__).parents[2] / "terraform"


@wrapt.decorator
def terraform_method(wrapped, instance: "TerraformFunctionManager", args, kwargs):
    """
    Decorate a method that returns a python_terraform `return_code, stdout, stderr`
    tuple such that it returns `None` if `return_code` is `0` and raises a
    TerraformException otherwise
    """

    return_code, stdout, stderr = wrapped(*args, **kwargs)
    if return_code != 0:
        exception = TerraformException(return_code, stdout, stderr)
        instance.logger.error("Terraform invocation failed: ", exc_info=exception)
        raise exception


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
        self.service_id = service_id
        self.service_instance_id = service_instance_id
        self.function_id = function_id
        self.function_instance_id = function_instance_id
        self.descriptor = descriptor
        self.vars = vars

        self._function_repr = 'function "{}" ({}) of service {} on VIM "{}" ({})'.format(
            descriptor["name"],
            function_instance_id,
            service_instance_id,
            vim.name,
            vim.id,
        )

        self.logger = logging.getLogger(
            "{}.FunctionManager({})".format(__name__, self._function_repr)
        )

        self._work_dir: Path = Path(config["terraform_workdir"]) / self.function_id
        self._work_dir.mkdir(parents=True, exist_ok=True)

        self._terraform = Terraform(
            working_dir=self._work_dir.as_posix(),
            terraform_bin_path=TERRAFORM_BIN_PATH.as_posix(),
        )

        self._compile_templates(list(template_path.iterdir()))
        self._tf_init()

    def _compile_templates(self, templates: List[Path], context={}):
        """
        Compile the templates from the file paths specified in `templates` and store
        them in `self._work_dir`.

        Args:

            templates: A list of paths of the template files that shall be compiled
            context: The compilation context. `service_id`, `service_instance_id`,
                `function_id`, `function_instance_id`, and `descriptor` field are set
                by default.
        """
        context = {
            "service_id": self.service_id,
            "service_instance_id": self.service_instance_id,
            "function_id": self.function_id,
            "function_instance_id": self.function_instance_id,
            "descriptor": self.descriptor,
            **context,
        }
        self.logger.debug("Compiling templates. Context: %s", context)

        for file_path in templates:
            target_path = self._work_dir / Path(file_path).name

            with file_path.open() as input_file:
                template = Template(input_file.read())
                with target_path.open("w") as output_file:
                    output_file.write(template.render(context))

    @terraform_method
    def _tf_init(self):
        """
        Runs `terraform init`
        """
        self.logger.debug("Executing `terraform init`")
        return self._terraform.init(var=self.vars)

    @terraform_method
    def _tf_plan(self):
        """
        Runs `terraform plan`
        """
        self.logger.debug("Executing `terraform plan`")
        return self._terraform.plan(var=self.vars)

    @terraform_method
    def _tf_apply(self):
        """
        Runs `terraform apply`
        """
        self.logger.debug("Executing `terraform apply`")
        return self._terraform.apply(var=self.vars)

    @terraform_method
    def _tf_destroy(self):
        """
        Runs `terraform destroy`
        """
        self.logger.debug("Executing `terraform destroy`")
        return self._terraform.destroy(var=self.vars)

    def deploy(self):
        """
        Deploys the network function managed by this TerraformFunctionManager by running
        `terraform plan`, followed by `terraform apply`. Raises a `TerraformException`
        on failure.
        """
        self.logger.info("Deploying network function")
        self._tf_plan()
        self._tf_apply()

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionManager by
        running `terraform destroy`. Raises a `TerraformException` on failure.
        """
        self.logger.info("Destroying network function")
        self._tf_destroy()
