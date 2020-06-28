from pathlib import Path
from uuid import uuid4

from pyfakefs.fake_filesystem import FakeFilesystem

from vim_adaptor.managers.base import (
    FunctionInstanceManager,
    FunctionInstanceManagerFactory,
)
from vim_adaptor.managers.terraform import TerraformFunctionInstanceManager
from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.models.vims import BaseVim


def uuid_string():
    return str(uuid4())


def test_manager_factory(mongo_connection):
    def create_factory():
        factory = FunctionInstanceManagerFactory()
        factory.register_manager_type("test", FunctionInstanceManager)
        return factory

    factory = create_factory()

    vim = BaseVim(name="MyVIM", country="country", city="city", type="aws")
    vim.save()

    ids = [uuid_string() for _ in range(4)]

    manager = factory.create_manager(
        manager_type="test",
        vim=vim,
        function_instance_id=ids[0],
        function_id=ids[1],
        service_instance_id=ids[2],
        descriptor={"id": ids[3], "name": "descriptor-name"},
    )

    function_instance = manager.function_instance
    assert "MyVIM" == function_instance.vim.name
    assert ids == [
        str(function_instance.id),
        str(function_instance.function_id),
        str(function_instance.service_instance_id),
        function_instance.descriptor["id"],
    ]

    assert manager is factory.get_manager(ids[0])

    # Create another factory and test manager re-creation
    factory2 = create_factory()
    manager2 = factory2.get_manager(ids[0])
    assert function_instance == manager2.function_instance


def test_terraform_manager_initialization(mocker, fs: FakeFilesystem):
    mocker.patch(
        "vim_adaptor.managers.terraform.TerraformFunctionInstanceManager._tf_init"
    )
    TerraformFunctionInstanceManager.template_path = Path("/my-template-dir")

    fs.create_file(
        "/my-template-dir/template.tf",
        contents=(
            "Function Instance Id: {{ function_instance_id }}\n"
            "Function Id: {{ function_id }}\n"
            "Service Instance Id: {{ service_instance_id }}\n"
            "Descriptor Id: {{ descriptor.id }}"
        ),
    )

    function_instance = FunctionInstance(
        id=uuid_string(),
        vim=BaseVim(name="MyVIM", country="country", city="city", type="aws"),
        function_id=uuid_string(),
        service_instance_id=uuid_string(),
        descriptor={"id": "descriptor-id", "name": "descriptor-name"},
    )

    manager = TerraformFunctionInstanceManager(function_instance)

    # Template(s) should have been compiled
    assert manager._work_dir.exists()
    target_file: Path = manager._work_dir / "template.tf"
    assert target_file.exists()
    with target_file.open() as f:
        assert [
            "Function Instance Id: " + str(function_instance.id),
            "Function Id: " + str(function_instance.function_id),
            "Service Instance Id: " + str(function_instance.service_instance_id),
            "Descriptor Id: " + function_instance.descriptor["id"],
        ] == f.read().splitlines()

    # _tf_init should have been called
    manager._tf_init.assert_called()
