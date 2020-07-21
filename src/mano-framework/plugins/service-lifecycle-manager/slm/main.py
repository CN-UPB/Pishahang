import logging
from typing import Dict

from appcfg import get_config
from mongoengine import connect

from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin
from slm import version
from slm.exceptions import DeployRequestValidationError, InstantiationError
from slm.slm import ServiceLifecycleManager
from slm.util import create_status_message

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

config = get_config(__name__)


class ServiceLifecycleManagerPlugin(ManoBasePlugin):
    """
    Service Lifecycle Manager main class. Instantiate this class to run the SLM.
    """

    def __init__(self, *args, **kwargs):
        # Connect to MongoDB
        LOG.debug("Connecting to MongoDB at %s", config["mongo"])
        connect(host=config["mongo"])
        LOG.info("Connected to MongoDB")

        # Map service ids to ServiceLifecycleManager instances
        self.managers: Dict[str, ServiceLifecycleManager] = {}

        super(ServiceLifecycleManagerPlugin, self).__init__(
            *args, version=version, start_running=False, **kwargs
        )

    def declare_subscriptions(self):
        super(ServiceLifecycleManagerPlugin, self).declare_subscriptions()

    def on_lifecycle_start(self, message: Message):
        super(self.__class__, self).on_lifecycle_start(message)
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
            return create_status_message(status="READY")

        except (DeployRequestValidationError, InstantiationError) as e:
            return create_status_message(error=e)
