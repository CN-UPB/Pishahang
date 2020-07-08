from pathlib import Path
from uuid import uuid4

import pytest
from appcfg import get_config

from vim_adaptor.managers.base import (
    FunctionInstanceManager,
    FunctionInstanceManagerFactory,
)
from vim_adaptor.managers.terraform import TerraformFunctionInstanceManager
from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.models.vims import BaseVim
from mongoengine.errors import DoesNotExist

config = get_config("vim_adaptor")


def uuid_string():
    return str(uuid4())


def test_manager_factory(mongo_connection):
    FunctionInstanceManager.manager_type = "test"

    def create_factory():
        factory = FunctionInstanceManagerFactory()
        factory.register_manager_type(FunctionInstanceManager)
        return factory

    factory = create_factory()

    vim = BaseVim(name="MyVIM", country="country", city="city", type="aws")
    vim.save()

    ids = [uuid_string() for _ in range(4)]

    # Test manager creation
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
    manager2 = create_factory().get_manager(ids[0])
    assert function_instance == manager2.function_instance

    # Test manager counting
    assert 1 == factory.count_managers_per_vim(FunctionInstanceManager, vim.id)

    # Test manager deletion
    factory.delete_manager(function_instance.id)

    with pytest.raises(DoesNotExist):
        factory.get_manager(function_instance.id)

    # Count managers again
    assert 0 == factory.count_managers_per_vim(FunctionInstanceManager, vim.id)


def test_terraform_manager(mocker, fs):
    wrapper_class_mock = mocker.patch("vim_adaptor.managers.terraform.TerraformWrapper")

    TerraformFunctionInstanceManager.templates = Path("/my-template-dir/template.tf")

    function_instance = FunctionInstance(
        id=uuid_string(),
        vim=BaseVim(name="MyVIM", country="country", city="city", type="aws"),
        function_id=uuid_string(),
        service_instance_id=uuid_string(),
        descriptor={"id": "descriptor-id", "name": "descriptor-name"},
    )

    manager = TerraformFunctionInstanceManager(function_instance)

    # A TerraformWrapper should have been initialized
    wrapper_class_mock.assert_called_once()

    # Test deploy
    manager.terraform.plan.assert_not_called()
    manager.terraform.plan.assert_not_called()
    manager.deploy()
    manager.terraform.plan.assert_called_once()
    manager.terraform.apply.assert_called_once()

    # Test destroy
    function_dir = Path(config["terraform_workdir"]) / str(
        manager.function_instance.service_instance_id
    )
    function_dir.mkdir(parents=True)

    manager.terraform.destroy.assert_not_called()
    manager.destroy()
    manager.terraform.apply.assert_called_once()
