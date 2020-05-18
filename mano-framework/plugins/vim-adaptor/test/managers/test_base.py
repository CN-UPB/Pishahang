import os

from vim_adaptor.managers.base import TerraformFunctionManager


def test_template_compilation(fixture_fs):
    manager = TerraformFunctionManager("my-function-id", {"id": "my-descriptor-id"})
    assert os.path.exists(manager._template_dir)

    manager._compile_templates(
        [os.path.join(fixture_fs.fixture_dir, "simple_template.tmpl")]
    )
    target_file = os.path.join(manager._template_dir, "simple_template.tmpl")
    assert os.path.exists(target_file)
    with open(target_file) as f:
        assert "Descriptor Id: my-descriptor-id" == f.read()
