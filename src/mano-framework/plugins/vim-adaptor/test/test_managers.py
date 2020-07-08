from pathlib import Path
from uuid import uuid4

import pytest
from appcfg import get_config
from mongoengine.errors import DoesNotExist

from vim_adaptor.managers.base import (
    FunctionInstanceManager,
    FunctionInstanceManagerFactory,
    ServiceInstanceHandler,
)
from vim_adaptor.managers.terraform import TerraformFunctionInstanceManager
from vim_adaptor.models.vims import BaseVim

config = get_config("vim_adaptor")


def uuid_string():
    return str(uuid4())


def test_manager_factory(mongo_connection, mocker):
    mocker.patch(__name__ + ".ServiceInstanceHandler")

    FunctionInstanceManager.manager_type = "test"
    FunctionInstanceManager.service_instance_handlers = [ServiceInstanceHandler]

    def create_factory():
        factory = FunctionInstanceManagerFactory()
        factory.register_manager_type(FunctionInstanceManager)
        return factory

    factory = create_factory()

    vim = BaseVim(name="MyVIM", country="country", city="city", type="aws")
    vim.save()

    function_instance_id = uuid_string()
    function_id = uuid_string()
    service_instance_id = uuid_string()
    descriptor = {"name": "descriptor-name"}

    # Test manager creation
    manager = factory.create_manager(
        manager_type="test",
        vim=vim,
        function_instance_id=function_instance_id,
        function_id=function_id,
        service_instance_id=service_instance_id,
        descriptor={"name": "descriptor-name"},
    )

    function_instance = manager.function_instance
    assert "MyVIM" == function_instance.vim.name
    assert function_instance_id == str(function_instance.id)
    assert function_id == str(function_instance.function_id)
    assert service_instance_id == str(function_instance.service_instance_id)
    assert descriptor == function_instance.descriptor

    # Test manager retrieval
    assert manager is factory.get_manager(function_instance_id)

    def get_service_instance_handler(factory: FunctionInstanceManagerFactory):
        assert {
            function_instance.service_instance_id
        } == factory._service_instance_handlers.keys()

        return list(
            factory._service_instance_handlers[function_instance.service_instance_id]
        )[0]

    # Verify that a ServiceInstanceHandler has been created and that `on_init()` has
    # been called on it
    handler = get_service_instance_handler(factory)
    handler.on_init.assert_called_once()
    handler.reset_mock()  # Because the same handler Mock will be returned the next time

    # Create another factory and test manager re-creation
    factory2 = create_factory()
    manager2 = factory2.get_manager(function_instance_id)
    assert function_instance == manager2.function_instance

    # The other factory should also have recreated the ServiceInstanceHandler, but
    # without calling `on_init()`
    get_service_instance_handler(factory2).on_init.assert_not_called()

    # Test manager counting
    assert 1 == factory.count_managers(
        FunctionInstanceManager, service_instance_id, vim.id
    )

    # Test manager deletion
    manager.destroy()

    # `on_destroy()` should have been called on the service instance handler
    handler.on_destroy.assert_called_once()

    # The references of all service instance handlers should have been deleted
    assert (
        function_instance.service_instance_id not in factory._service_instance_handlers
    )

    with pytest.raises(DoesNotExist):
        factory.get_manager(function_instance_id)

    # Count managers again
    assert 0 == factory.count_managers(
        FunctionInstanceManager, service_instance_id, vim.id
    )


def test_terraform_manager(mongo_connection, mocker, fs):
    wrapper_class_mock = mocker.patch("vim_adaptor.managers.terraform.TerraformWrapper")

    TerraformFunctionInstanceManager.manager_type = "terraform"
    TerraformFunctionInstanceManager.templates = Path("/my-template-dir/template.tf")

    factory = FunctionInstanceManagerFactory()
    factory.register_manager_type(TerraformFunctionInstanceManager)

    vim = BaseVim(name="MyVIM", country="country", city="city", type="aws")
    vim.save()

    manager = factory.create_manager(
        manager_type="terraform",
        vim=vim,
        function_instance_id=uuid_string(),
        function_id=uuid_string(),
        service_instance_id=uuid_string(),
        descriptor={"id": "descriptor-id", "name": "descriptor-name"},
    )

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
