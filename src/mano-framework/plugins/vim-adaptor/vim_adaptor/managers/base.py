import logging
from threading import Lock
from typing import Dict, List, Type

from vim_adaptor.models.function import FunctionInstance
from vim_adaptor.models.service import ServiceInstance
from vim_adaptor.models.vims import BaseVim

LOGGER = logging.getLogger(__name__)


class BaseFactory:
    """
    Common base class for factory classes
    """

    def __init__(self):
        # Map instance ids to objects
        self._instances: Dict[str, "FunctionInstanceManager"] = {}

        # Map arbitrary identifiers to classes:
        self._classes: Dict[str, Type] = {}

        # Lock to make object creation thread-safe
        self._instances_lock = Lock()

    def register_class(
        self, identifier: str, instance_class: Type,
    ):
        """
        Registers a class with an arbitrary identifier
        """
        self._classes[identifier] = instance_class

    def create_instance(self, identifier: str, instance_id: str, args=(), kwargs={}):
        """
        Creates an instance of the class that was registered with the provided
        `identifier`. `instance_id` has to be a unique string that identifies the new
        instance.
        """
        with self._instances_lock:
            instance = self._classes[identifier](self, *args, **kwargs)
            self._instances[instance_id] = instance

        return instance

    def get_instance(self, instance_id: str):
        """
        Returns an instance by its id or raises a KeyError if no instance exists for
        the provided id.
        """
        return self._instances[instance_id]

    def _on_instance_destroyed(self, instance_id: str):
        """
        Invoked by instances when they are destroyed
        """

        with self._instances_lock:
            return self._instances.pop(instance_id)


class FunctionInstanceManagerFactory(BaseFactory):
    """
    A factory for `FunctionInstanceManager` objects that uses VIM types as identifiers
    for `FunctionInstanceManager` subclasses and persists the data provided to
    `create_instance` in a `FunctionInstance` document. The `get_instance` method
    recreates `FunctionInstanceManager` objects by their corresponding
    `FunctionInstance` document on demand.
    """

    def create_instance(
        self,
        vim_id: str,
        function_instance_id: str,
        function_id: str,
        service_instance_id: str,
        descriptor: dict,
    ):
        """
        Creates a FunctionInstanceManager for the first time and stores a
        FunctionInstance document in the database. Make sure to call this method only
        once per function instance and use `get_manager` to retrieve it at a later time.
        Raises a `VimNotFoundException` if a VIM with the provided ID does not exist.

        Args:
            vim_id: The VIM id of the VIM that the function instance manager refers to
            function_instance_id
            function_id
            service_instance_id
            descriptor: The descriptor of the network function that the manager will
                deploy
        """

        vim = BaseVim.get_by_id(vim_id)

        function_instance = FunctionInstance(
            id=function_instance_id,
            vim=vim,
            function_id=function_id,
            service_instance_id=service_instance_id,
            descriptor=descriptor,
        )
        function_instance.save()

        return super().create_instance(
            identifier=vim.type,
            instance_id=function_instance_id,
            args=(function_instance,),
        )

    def get_instance(self, instance_id: str):
        """
        Retrieves a `FunctionInstanceManager` by the id of its function instance. If the
        manager has not been created during this program execution, the corresponding
        FunctionInstance document is fetched from the database and a manager instance is
        re-created. Throws a `mongoengine.DoesNotExist` exception if no manager has
        previously been created for the given function instance id.
        """
        try:
            return super().get_instance(instance_id)
        except KeyError:
            function_instance: FunctionInstance = FunctionInstance.objects.get(
                id=instance_id
            )
            return super().create_instance(
                identifier=function_instance.vim.type,
                instance_id=instance_id,
                args=(function_instance,),
            )

    def _on_instance_destroyed(self, instance_id: "FunctionInstanceManager"):
        """
        Invoked by the `FunctionInstanceManager` base class on destruction of a
        FunctionInstanceManager instance. Deletes the FunctionInstance document from the
        database.
        """
        super()._on_instance_destroyed(instance_id).function_instance.delete()


class FunctionInstanceManager:
    """
    A FunctionInstanceManager is responsible for deploying and destroying a network
    function instance based on a `FunctionInstance` document. `FunctionInstanceManager`s
    are handed out by an `FunctionInstanceManagerFactory` instance.
    """

    class LoggerAdapter(logging.LoggerAdapter):
        """
        Logger adapter to prepend function instance details to log messages
        """

        def process(self, msg, kwargs):
            instance: FunctionInstance = self.extra["function_instance"]
            return (
                (
                    f"FunctionInstanceManager(Function: {instance.descriptor['name']},"
                    f" Service: {instance.service_instance_id},"
                    f" VIM: {instance.vim.name} ({instance.vim.id})): {msg:s}"
                ),
                kwargs,
            )

    service_instance_handlers: List["ServiceInstanceHandler"] = []

    def __init__(
        self,
        factory: FunctionInstanceManagerFactory,
        function_instance: FunctionInstance,
    ):
        """
        Initializes a FunctionInstanceManager. Do not call this yourself; use the
        `FunctionInstanceManagerFactory` instance at `vim_adaptor.managers.factory` instead.

        Args:
            function_instance: The FunctionInstance document the FunctionInstanceManager
                belongs to
            factory: The `FunctionInstanceManagerFactory` instance that created this
                `FunctionInstanceManager`
        """
        self.function_instance = function_instance
        self._factory = factory

        self.logger = self.LoggerAdapter(
            LOGGER, {"function_instance": function_instance}
        )

    def deploy(self):
        """
        Deploys the network function managed by this FunctionInstanceManager and returns
        the corresponding record as a dict.
        """
        pass

    def destroy(self):
        """
        Destroys the network function managed by this FunctionInstanceManager.
        """
        self._factory._on_instance_destroyed(str(self.function_instance.id))


class ServiceInstanceHandlerFactory(BaseFactory):
    """
    A factory for `ServiceInstanceHandler` objects that uses VIM types as identifiers
    for `ServiceInstanceHandler` subclasses and persists the data provided to
    `create_service_instance_handlers` in a `ServiceInstance` document.

    Note:

        Only the `create_service_instance_handlers` and
        `teardown_service_instance_handlers` methods are meant to be used publically.
    """

    def create_service_instance_handlers(
        self,
        service_instance_id: str,
        vims: List[BaseVim],
        vim_details: Dict[str, dict],
    ):
        """
        Given a `service_instance_id`, a list of VIMs and a `vim_details` dict that maps
        vim id strings to details dicts, creates the corresponding
        `ServiceInstanceHandler` objects and calls their `on_setup()` methods.
        """
        service_instance = ServiceInstance(
            id=service_instance_id, vims=vims, vim_details=vim_details
        )
        service_instance.save()

        for handler in self._create_service_instance_handlers(service_instance):
            handler.on_setup()

    def _create_service_instance_handlers(
        self, service_instance: ServiceInstance
    ) -> List["ServiceInstanceHandler"]:
        handlers = []

        for vim in service_instance.vims:
            try:
                handlers.append(
                    self.create_instance(
                        vim.type,
                        f"{service_instance.id}.{vim.id}",
                        kwargs={
                            "service_instance_id": str(service_instance.id),
                            "vim": vim,
                            "details": service_instance.vim_details[str(vim.id)],
                        },
                    )
                )
            except KeyError:
                # Not every VIM needs to have a ServiceInstanceHandler associated with it.
                pass

        return handlers

    def teardown_service_instance_handlers(self, service_instance_id):
        """
        Calls the `on_teardown()` methods of all `ServiceInstanceHandler`s of the
        service specified by the provided `service_instance_id`. If no
        `ServiceInstanceHandler`s exist for that service but a corresponding
        ServiceInstance document is found in the database, the `ServiceInstanceHandler`s
        are recreated first. Otherwise, a `mongoengine.DoesNotExist` exception is
        raised.
        """
        service_instance = ServiceInstance.objects.get(id=service_instance_id)

        try:
            handlers = []
            for vim in service_instance.vims:
                if vim.type in self._classes:
                    handlers.append(
                        self.get_instance(f"{service_instance_id}.{vim.id}")
                    )
        except KeyError:
            # Handler has not yet been created during current application run
            handlers = self._create_service_instance_handlers(service_instance)

        for handler in handlers:
            handler.on_teardown()

        service_instance.delete()


class ServiceInstanceHandler:
    """
    A ServiceInstanceHandler is responsible to handle tasks related to service creation
    and destruction given a service id, a VIM id, and an optional dict with additional
    information specific to that service and vim (such as required VM images). It does
    so by implementing the two methods `on_setup` and `on_teardown`. This enables the
    implementation of per-service, per-vim setup and teardown tasks.

    `ServiceInstanceHandler`s are instantiated per-service, per-vim by a
    `ServiceInstanceHandlerFactory`.
    """

    class LoggerAdapter(logging.LoggerAdapter):
        """
        Logger adapter to prepend service instance details to log messages
        """

        def process(self, msg, kwargs):
            vim: BaseVim = self.extra["vim"]
            return (
                (
                    f"ServiceInstanceHandler("
                    f"Service: {self.extra['service_instance_id']},"
                    f" VIM: {vim.name} ({vim.id})): {msg:s}"
                ),
                kwargs,
            )

    def __init__(
        self,
        factory: ServiceInstanceHandlerFactory,
        service_instance_id: str,
        vim: BaseVim,
        details: dict,
    ):
        """
        Initializes a ServiceInstanceHandler.

        Args:
            factory
            service_instance_id
            vim: The Vim document representing the VIM that this ServiceInstanceHandler
                is responsible for
            details: A dict with additional details
        """
        self._factory = factory
        self.service_instance_id = str(service_instance_id)
        self.vim = vim
        self.details = details

        self.logger = self.LoggerAdapter(
            LOGGER, {"service_instance_id": self.service_instance_id, "vim": self.vim}
        )

    def on_setup(self):
        """
        Is invoked when
        `ServiceInstanceHandlerFactory.create_service_instance_handlers()` is called.
        """
        self.logger.info("Initializing")

    def on_teardown(self):
        """
        Is invoked when
        `ServiceInstanceHandlerFactory.teardown_service_instance_handlers()` is called.
        """
        self.logger.info("Tearing down")
        self._factory._on_instance_destroyed(
            f"{self.service_instance_id}.{self.vim.id}"
        )
