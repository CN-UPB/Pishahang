import logging
from typing import Dict

from appcfg import get_config
from mongoengine import DoesNotExist, connect

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin
from slm import version
from slm.exceptions import (
    DeployRequestValidationError,
    InstantiationError,
    TerminationError,
)
from slm.slm import ServiceLifecycleManager
from slm.util import create_status_message

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

config = get_config(__name__)

MONGO_HOST = config["mongo"]


class ServiceLifecycleManagerPlugin(ManoBasePlugin):
    """
    Service Lifecycle Manager main class. Instantiate this class to run the SLM.
    """

    def __init__(self, *args, **kwargs):
        # Connect to MongoDB
        LOG.debug(f"Connecting to MongoDB at {MONGO_HOST}")
        connect(host=MONGO_HOST)
        LOG.info("Connected to MongoDB")

        # Map service ids to ServiceLifecycleManager instances
        self.managers: Dict[str, ServiceLifecycleManager] = {}

        super().__init__(*args, version=version, **kwargs)

    def declare_subscriptions(self):
        super().declare_subscriptions()
        self.conn.register_async_endpoint(
            self.on_service_instance_create, "service.instances.create"
        )
        self.conn.register_async_endpoint(
            self.on_service_instance_terminate, "service.instance.terminate"
        )

    def on_lifecycle_start(self, message: Message):
        super().on_lifecycle_start(message)
        LOG.info("SLM started and operational.")

    async def on_service_instance_create(self, message: Message):
        """
        Instantiate a service
        """

        try:
            manager = ServiceLifecycleManager.from_deploy_request(message, self.conn)
            self.managers[manager.service_id] = manager

            # Notify gatekeeper
            self.conn.notify(
                message.topic,
                create_status_message(status="INSTANTIATING"),
                correlation_id=message.correlation_id,
            )

            await manager.instantiate()
            return create_status_message(
                status="READY", payload={"nsr": {"id": manager.service_id}}
            )

        except (DeployRequestValidationError, InstantiationError) as e:
            return create_status_message(error=e)

    async def on_service_instance_terminate(self, message: Message):
        """
        Destory a service instance
        """

        service_id = message.payload["instance_id"]

        try:
            if service_id in self.managers:
                manager = self.managers[service_id]
            else:
                try:
                    manager = ServiceLifecycleManager.from_database(
                        service_id, self.conn
                    )
                except DoesNotExist:
                    raise TerminationError(
                        f"A service with instance id {service_id} is not known to the SLM"
                    )

            await manager.terminate()
            return create_status_message(status="TERMINATED")

        except TerminationError as e:
            return create_status_message(error=e)
