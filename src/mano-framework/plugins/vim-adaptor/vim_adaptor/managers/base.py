import logging
from pathlib import Path
from typing import Dict, Type

from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.models.vims import BaseVim


class FunctionInstanceManagerFactory:
    def __init__(self):
        # Map function instance ids to their manager objects:
        self._managers: Dict[str, "FunctionInstanceManager"] = {}

        # Map manager types to manager classes:
        self._manager_classes: Dict[str, Type["FunctionInstanceManager"]] = {}

    def register_manager_type(
        self, manager_type: str, manager_class: Type["FunctionInstanceManager"]
    ):
        """
        Registers a manager type at the factory. The arbitrary string provided as
        `manager_type` can then be used to refer to the subclass of
        FunctionInstanceManager provided as `manager_class`.
        """
        self._manager_classes[manager_type] = manager_class

    def create_manager(
        self,
        manager_type: str,
        vim: BaseVim,
        function_instance_id: str,
        function_id: str,
        service_instance_id: str,
        descriptor: dict,
    ):
        """
        Creates a FunctionInstanceManager for the first time and stores a
        FunctionInstance document in the database. Make sure to call this method only
        once per function instance and use `get_manager` to retrieve it at a later time.
        Raises a `TerraformException` if terraform fails to initialize.

        Args:
            manager_type: str,
            vim: The VIM object representing the VIM that the function instance manager shall use
            function_instance_id: The uuid of the function instance the manager belongs to
            function_id: The uuid of the function the manager belongs to
            service_instance_id: The uuid of the service instance the manager belongs to
            descriptor: The descriptor of the network function that the manager will control
        """
        function_instance = FunctionInstance(
            id=function_instance_id,
            manager_type=manager_type,
            vim=vim,
            function_id=function_id,
            service_instance_id=service_instance_id,
            descriptor=descriptor,
        )
        function_instance.save()

        manager = self._manager_classes[manager_type](function_instance)
        self._managers[function_instance_id] = manager
        return manager

    def get_manager(self, function_instance_id):
        """
        Retrieves a FunctionManager by the id of its function instance. If the manager
        has not been created during this program execution, the corresponding
        FunctionInstance document is fetched from the database and a manager instance is
        re-created. Throws a `mongoengine.DoesNotExist` exception if no manager has
        previously been created for the given function instance id.
        """
        if function_instance_id in self._managers:
            return self._managers[function_instance_id]

        function_instance: FunctionInstance = FunctionInstance.objects.get(
            id=function_instance_id
        )
        manager = self._manager_classes[function_instance.manager_type](
            function_instance
        )
        self._managers[function_instance_id] = manager
        return manager


class FunctionInstanceManager:
    """
    A FunctionInstanceManager is responsible to deploy and destroy a network function
    instance based on a `FunctionInstance` document. `FunctionInstanceManager`s are
    handed out by a `FunctionInstanceManagerFactory`.
    """

    template_path: Path = None

    def __init__(
        self, function_instance: FunctionInstance,
    ):
        """
        Initializes a FunctionInstanceManager. Do not call this yourself; use the
        `FunctionInstanceManagerFactory` instance at `vim_adaptor.managers.factory`
        instead.

        Args:
            function_instance: The FunctionInstance document the FunctionInstanceManager
            belongs to
        """
        self.function_instance = function_instance

        self.logger = logging.getLogger(
            "{}.{}(Function: {} ({}), Service: {}, VIM: {} ({}))".format(
                type(self).__module__,
                type(self).__name__,
                function_instance.descriptor["name"],
                function_instance.id,
                function_instance.service_instance_id,
                function_instance.vim.name,
                function_instance.vim.id,
            )
        )

    def deploy(self):
        """
        Deploys the network function managed by this FunctionInstanceManager.
        """
        self.logger.info("Deploying")

    def destroy(self):
        """
        Destroys the network function managed by this FunctionInstanceManager.
        """
        self.logger.info("Destroying")
