from pathlib import Path

from vim_adaptor.managers.base import TerraformFunctionManager
from vim_adaptor.models.vims import BaseVim


def test_initialization(fixture_fs, mocker):
    mocker.patch("vim_adaptor.managers.base.TerraformFunctionManager._tf_init")

    vim = BaseVim(name="MyVIM", country="country", city="city", type="AWS")

    manager = TerraformFunctionManager(
        fixture_fs.fixture_dir,
        vim,
        "service-id",
        "service-instance-id",
        "function-id",
        "function-instance-id",
        {"id": "descriptor-id", "name": "descriptor-name"},
    )

    # Templates should have been compiled
    assert manager._work_dir.exists()
    target_file: Path = manager._work_dir / "simple_template.tmpl"
    assert target_file.exists()
    with target_file.open() as f:
        assert (
            "Descriptor Id: descriptor-id\n"
            "Function Id: function-id\n"
            "Function Instance Id: function-instance-id\n"
            "Service Id: service-id\n"
            "Service Instance Id: service-instance-id"
        ) == f.read()

    # _tf_init should have been called
    manager._tf_init.assert_called()
