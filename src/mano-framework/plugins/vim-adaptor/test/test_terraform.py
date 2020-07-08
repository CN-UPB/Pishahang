from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from vim_adaptor.terraform import TerraformWrapper


def test_terraform_wrapper(mocker, fs: FakeFilesystem):
    mocker.patch("vim_adaptor.terraform.TerraformWrapper.init")

    fs.create_file(
        "/my-template-dir/template.tf", contents=("Context variable: {{ my_var }}"),
    )

    terraform = TerraformWrapper(
        work_dir=Path("/workdir"),
        templates=[Path("/my-template-dir/template.tf")],
        context={"my_var": "value"},
        tf_vars={},
    )

    # Template(s) should have been compiled
    assert terraform._work_dir.exists()
    rendered_template_file: Path = terraform._work_dir / "template.tf"
    assert rendered_template_file.exists()
    with rendered_template_file.open() as f:
        assert "Context variable: value" == f.read()

    # `init()` should have been called
    terraform.init.assert_called()

    # Remove working directory
    terraform.remove_work_dir()
    assert not rendered_template_file.exists()
    assert not terraform._work_dir.exists()
