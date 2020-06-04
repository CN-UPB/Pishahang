from pathlib import Path
from typing import List

import wrapt
from appcfg import get_config
from jinja2 import Template
from python_terraform import Terraform

from vim_adaptor.exceptions import TerraformException

config = get_config(__name__)

TEMPLATE_BASE_PATH: Path = Path(__file__).parent / "templates"
TERRAFORM_BIN_PATH: Path = Path(__file__).parents[2] / "terraform"


@wrapt.decorator
def terraform_method(wrapped, instance, args, kwargs):
    """
    Decorate a method that returns a python_terraform `return_code, stdout, stderr`
    tuple such that it returns `None` if `return_code` is `0` and raises a
    TerraformException otherwise
    """

    return_code, stdout, stderr = wrapped(*args, **kwargs)
    if return_code != 0:
        raise TerraformException(return_code, stdout, stderr)


class TerraformFunctionManager:
    """
    A base class for function managers that abstracts Terraform template compilation and
    Terraform invocations
    """

    def __init__(self, function_id: str, descriptor: dict, vars={}):
        self.function_id = function_id
        self.descriptor = descriptor
        self.vars = vars

        self._template_dir: Path = Path(config["terraform_workdir"]) / self.function_id
        self._template_dir.mkdir(parents=True, exist_ok=True)

        self._terraform = Terraform(
            working_dir=self._template_dir.as_posix(),
            terraform_bin_path=TERRAFORM_BIN_PATH.as_posix(),
        )

    def _compile_templates(self, templates: List[Path], context={}):
        """
        Compile the templates from the file paths specified in `templates` and store
        them in `self._template_dir`.

        Args:
            templates: The path of a directory that contains the template files that
                shall be compiled
            context: The template context. Note that a `descriptor` field is included by
                default.
        """
        context.setdefault("descriptor", self.descriptor)

        for file_path in templates:
            target_path = self._template_dir / Path(file_path).name

            with file_path.open() as input_file:
                template = Template(input_file.read())
                with target_path.open("w") as output_file:
                    output_file.write(template.render(context))

    @terraform_method
    def _tf_init(self):
        """
        Runs `terraform init`
        """
        return self._terraform.init(var=self.vars)

    @terraform_method
    def _tf_plan(self):
        """
        Runs `terraform plan`
        """
        return self._terraform.plan(var=self.vars)

    @terraform_method
    def _tf_apply(self):
        """
        Runs `terraform apply`
        """
        return self._terraform.apply(var=self.vars)

    @terraform_method
    def _tf_destroy(self):
        """
        Runs `terraform destroy`
        """
        return self._terraform.destroy(var=self.vars)

    def deploy(self):
        """
        Deploys the network function managed by this TerraformFunctionManager
        """
        pass

    def destroy(self):
        """
        Destroys the network function managed by this TerraformFunctionManager
        """
        pass
