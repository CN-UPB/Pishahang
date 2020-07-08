import logging
import warnings
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Set, Tuple, Type, Union
from uuid import UUID

from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.models.vims import BaseVim


class FunctionInstanceManagerFactory:
    def __init__(self):
        # Map function instance ids to their manager objects:
        self._managers: Dict[str, "FunctionInstanceManager"] = {}

        # Map function instance ids to Dicts that map (manager class, vim id) tuples to
        # `ServiceInstanceHandler`s:
        self._service_instance_handlers: Dict[
            str,
            Dict[
                Tuple[Type["FunctionInstanceManager"], str],
                Set["ServiceInstanceHandler"],
            ],
        ] = defaultdict(dict)

        # Map manager types to manager classes:
        self._manager_classes: Dict[str, Type["FunctionInstanceManager"]] = {}

        self._lock = Lock()

    def register_manager_type(self, manager_class: Type["FunctionInstanceManager"]):
        """
        Registers a manager type at the factory. The FunctionInstanceManager subclass
        provided as `manager_class` can then be referred to via the class'
        `manager_type` string.
        """
        self._manager_classes[manager_class.manager_type] = manager_class

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

        manager = self._instantiate_manager(manager_type, function_instance)
        return manager

    def get_manager(self, function_instance_id: Union[str, UUID]):
        """
        Retrieves a FunctionInstanceManager by the id of its function instance. If the
        manager has not been created during this program execution, the corresponding
        FunctionInstance document is fetched from the database and a manager instance is
        re-created. Throws a `mongoengine.DoesNotExist` exception if no manager has
        previously been created for the given function instance id.
        """
        if function_instance_id in self._managers:
            return self._managers[function_instance_id]

        function_instance: FunctionInstance = FunctionInstance.objects.get(
            id=function_instance_id
        )
        return self._instantiate_manager(
            function_instance.manager_type, function_instance, is_recreation=True
        )

    def _instantiate_manager(
        self,
        manager_type: str,
        function_instance: FunctionInstance,
        is_recreation=False,
    ):
        manager_class = self._manager_classes[manager_type]
        service_instance_id = str(function_instance.service_instance_id)
        vim = function_instance.vim

        with self._lock:
            # Create the `ServiceInstanceHandler`s for the VIM if they are not yet
            # present
            if not self._are_service_handlers_instantiated(
                manager_class, service_instance_id, str(vim.id)
            ):
                handlers = self._instantiate_service_handlers(
                    manager_class, service_instance_id, vim
                )

                if not is_recreation:
                    for handler in handlers:
                        handler.on_init()

            manager = manager_class(function_instance, self)
            self._managers[str(function_instance.id)] = manager
            return manager

    def _get_service_handlers(
        self,
        manager_class: Type["FunctionInstanceManager"],
        service_instance_id: str,
        vim_id: str,
        remove=False,
    ) -> Set["ServiceInstanceHandler"]:
        handlers_by_manager_and_vim = self._service_instance_handlers[
            service_instance_id
        ]
        handlers = handlers_by_manager_and_vim[manager_class, vim_id]

        if remove:
            self._service_instance_handlers.pop(service_instance_id)

        return handlers

    def _are_service_handlers_instantiated(
        self,
        manager_class: Type["FunctionInstanceManager"],
        service_instance_id: str,
        vim_id: str,
    ):
        try:
            self._get_service_handlers(manager_class, service_instance_id, vim_id)
            return True
        except KeyError:
            return False

    def _instantiate_service_handlers(
        self,
        manager_class: Type["FunctionInstanceManager"],
        service_instance_id: str,
        vim: BaseVim,
    ) -> Set["ServiceInstanceHandler"]:
        handlers = {
            handler_class(manager_class, service_instance_id, vim)
            for handler_class in manager_class.service_instance_handlers
        }

        self._service_instance_handlers[service_instance_id][
            manager_class, str(vim.id)
        ] = handlers

        return handlers

    def _on_manager_destroyed(self, manager: "FunctionInstanceManager"):
        """
        Invoked by the `FunctionInstanceManager` base class on destruction of a
        FunctionInstanceManager instance.
        """
        function_instance = manager.function_instance
        function_instance_id = str(function_instance.id)
        manager_class = manager.__class__
        vim_id = str(function_instance.vim.id)

        with self._lock:
            function_instance.delete()
            self._managers.pop(function_instance_id)

            # If this was the last manager for a manager type, service instance, and
            # vim, call `on_destroy()` on the service handlers
            if self.count_managers(manager_class, function_instance_id, vim_id) == 0:
                for handler in self._get_service_handlers(
                    manager_class,
                    str(function_instance.service_instance_id),
                    vim_id,
                    remove=True,
                ):
                    handler.on_destroy()

    def count_managers(
        self,
        manager_class: Type["FunctionInstanceManager"],
        service_instance_id: Union[str, UUID],
        vim_id: Union[str, UUID],
    ) -> int:
        """
        Returns the number of `FunctionInstanceManager`s of a given
        `FunctionInstanceManager` subclass that exist for a specified
        `service_instance_id` and `vim_id`.
        """
        # Hide a deprecation warning until it gets fixed in MongoEngine:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            return FunctionInstance.objects(
                manager_type=manager_class.manager_type,
                service_instance_id=service_instance_id,
                vim=vim_id,
            ).count()


class FunctionInstanceManager:
    """
    A FunctionInstanceManager is responsible for deploying and destroying a network
    function instance based on a `FunctionInstance` document. `FunctionInstanceManager`s
    are handed out by a `FunctionInstanceManagerFactory` instance.
    """

    service_instance_handlers: List["ServiceInstanceHandler"] = []

    # A string that identifies this class at the FunctionInstanceManagerFactory
    manager_type: str

    def __init__(
        self,
        function_instance: FunctionInstance,
        factory: FunctionInstanceManagerFactory,
    ):
        """
        Initializes a FunctionInstanceManager. Do not call this yourself; use the
        `FunctionInstanceManagerFactory` instance at `vim_adaptor.managers.factory`
        instead.

        Args:
            function_instance: The FunctionInstance document the FunctionInstanceManager
                belongs to
            factory: The `FunctionInstanceManagerFactory` instance that created this
                `FunctionInstanceManager`
        """
        self.function_instance = function_instance
        self._factory = factory

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
        pass

    def destroy(self):
        """
        Destroys the network function managed by this FunctionInstanceManager.
        """
        self._factory._on_manager_destroyed(self)


class ServiceInstanceHandler:
    """
    A ServiceInstanceHandler is responsible to handle tasks related to service creation
    and destruction given a service id. It does so by implementing the two methods
    `on_init` and `on_destroy`. This enables the implementation of per-service, per-vim,
    per-function-instance-manager-type setup and teardown tasks.

    `ServiceInstanceHandler`s are not supposed to be instantiated manually. Instead, the
    desired subclasses of `ServiceInstanceHandler` can be specified as a list in a
    `FunctionInstanceManager`'s `service_instance_handlers` class attribute. The
    `FunctionInstanceManagerFactory` will then instantiate the ServiceInstanceHandlers
    and invoke their methods accordingly. The reason behind the mapping of
    `FunctionInstanceManager`s to `ServiceInstanceHandler`s is that a service instance
    can include function instances on multiple VIMs, where dedicated per-service setup
    and teardown tasks may be required per VIM.
    """

    def __init__(
        self,
        manager_class: Type[FunctionInstanceManager],
        service_instance_id: Union[str, UUID],
        vim: BaseVim,
    ):
        """
        Initializes a ServiceInstanceHandler.

        Args:
            manager_class
            service_instance_id
            vim: The Vim document representing the VIM that this ServiceInstanceHandler
                is responsible for
        """
        self.manager_class = manager_class
        self.service_instance_id = str(service_instance_id)
        self.vim = vim

        self.logger = logging.getLogger(
            "{}.{}(Service Instance Id: {}, VIM: {} ({}))".format(
                type(self).__module__,
                type(self).__name__,
                service_instance_id,
                vim.name,
                vim.id,
            )
        )

    def on_init(self):
        """
        Is invoked by the `FunctionInstanceManagerFactory` when the first
        `FunctionInstanceManager` of a given service instance on a given VIM is
        created.
        """
        self.logger.info("Initializing")

    def on_destroy(self):
        """
        Is invoked by the `FunctionInstanceManagerFactory` when all
        `FunctionInstanceManager`s of a given service instance on a given VIM have been
        deleted.
        """
        self.logger.info("Destroying")
