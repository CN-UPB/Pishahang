from pathlib import Path
from uuid import uuid4

import pytest
from appcfg import get_config
from mongoengine.errors import DoesNotExist

from vim_adaptor.managers.base import (
    FunctionInstanceManager,
    FunctionInstanceManagerFactory,
    ServiceInstanceHandler,
    ServiceInstanceHandlerFactory,
)
from vim_adaptor.managers.terraform import TerraformFunctionInstanceManager
from vim_adaptor.models.service import ServiceInstance
from vim_adaptor.models.vims import BaseVim, VimType

config = get_config("vim_adaptor")


def uuid_string():
    return str(uuid4())


@pytest.fixture
def vim(mongo_connection):
    vim = BaseVim(name="MyVIM", country="country", city="city", type="aws")
    vim.save()
    yield vim
    vim.delete()


def test_manager_factory(mongo_connection, mocker, vim):

    def create_factory():
        factory = FunctionInstanceManagerFactory()
        factory.register_class(VimType.AWS.value, FunctionInstanceManager)
        return factory

    factory = create_factory()

    function_instance_id = uuid_string()
    function_id = uuid_string()
    service_instance_id = uuid_string()
    descriptor = {"name": "descriptor-name"}

    # Test manager creation
    manager = factory.create_instance(
        vim_id=str(vim.id),
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
    assert manager is factory.get_instance(function_instance_id)

    # Create another factory and test manager re-creation
    factory2 = create_factory()
    manager2 = factory2.get_instance(function_instance_id)
    assert function_instance == manager2.function_instance

    # Test manager deletion
    manager.destroy()

    with pytest.raises(DoesNotExist):
        factory.get_instance(function_instance_id)


def test_terraform_manager(mongo_connection, mocker, fs, vim):
    wrapper_class_mock = mocker.patch("vim_adaptor.managers.terraform.TerraformWrapper")

    TerraformFunctionInstanceManager.templates = Path("/my-template-dir/template.tf")

    factory = FunctionInstanceManagerFactory()
    factory.register_class(VimType.AWS.value, TerraformFunctionInstanceManager)

    manager = factory.create_instance(
        vim_id=str(vim.id),
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


def test_service_instance_handler_factory(mongo_connection, mocker, vim):
    for method in ["on_setup", "on_teardown"]:
        mocker.patch(f"vim_adaptor.managers.base.ServiceInstanceHandler.{method}")

    def create_factory():
        factory = ServiceInstanceHandlerFactory()
        factory.register_class(VimType.AWS.value, ServiceInstanceHandler)
        return factory

    factory1 = create_factory()

    service_instance_id = uuid_string()
    factory1.create_service_instance_handlers(
        service_instance_id, [vim], {str(vim.id): {"key": "value"}}
    )

    instance = factory1.get_instance(f"{service_instance_id}.{vim.id}")
    instance.on_setup.assert_called_once()
    instance.on_teardown.assert_not_called()

    # Test ServiceInstanceHandler recreation on teardown with another factory

    factory2 = create_factory()
    factory2.teardown_service_instance_handlers(service_instance_id)

    with pytest.raises(DoesNotExist):
        ServiceInstance.objects.get(id=service_instance_id)
