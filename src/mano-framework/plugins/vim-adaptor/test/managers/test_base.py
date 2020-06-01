from pathlib import Path

from vim_adaptor.managers.base import TerraformFunctionManager


def test_template_compilation(fixture_fs):
    manager = TerraformFunctionManager("my-function-id", {"id": "my-descriptor-id"})
    assert manager._template_dir.exists()

    manager._compile_templates([fixture_fs.fixture_dir / "simple_template.tmpl"])
    target_file: Path = manager._template_dir / "simple_template.tmpl"
    assert target_file.exists()
    with target_file.open() as f:
        assert "Descriptor Id: my-descriptor-id" == f.read()
