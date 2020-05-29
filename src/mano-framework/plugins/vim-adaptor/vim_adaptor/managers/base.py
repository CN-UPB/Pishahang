import os
from typing import List

from config2.config import config
from jinja2 import Template
from python_terraform import Terraform


class TerraformFunctionManager:
    """
    A base class for function managers that abstracts Terraform template compilation and
    Terraform invocations
    """

    def __init__(self, function_id: str, descriptor: dict, vars={}):
        self.function_id = function_id
        self.descriptor = descriptor
        self.vars = vars
        self._template_dir = os.path.join(config.terraform_workdir, self.function_id)

        self._terraform = Terraform(
            working_dir=self._template_dir, terraform_bin_path="./terraform"
        )

        # Create a directory for compiled templates
        os.makedirs(self._template_dir, exist_ok=True)

    def _compile_templates(self, templates: List[str], context={}):
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
            target_path = os.path.join(self._template_dir, os.path.basename(file_path))

            with open(file_path) as input_file:
                template = Template(input_file.read())
                with open(target_path, "w") as output_file:
                    output_file.write(template.render(context))

    def _tf_init(self):
        """
        Runs `terraform init`
        """
        return self._terraform.init(var=self.vars)

    def _tf_plan(self):
        """
        Runs `terraform plan`
        """
        return self._terraform.plan(var=self.vars)

    def _tf_apply(self):
        """
        Runs `terraform apply`
        """
        return self._terraform.apply(var=self.vars)

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
