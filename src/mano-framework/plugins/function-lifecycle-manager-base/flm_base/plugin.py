"""
Copyright (c) 2015 SONATA-NFV, 2017 Pishahang
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV, Pishahang,
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

Parts of this work have been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

import logging

from requests import RequestException

import manobase.repository as repository
from flm_base.exceptions import DeploymentError
from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class FunctionLifecycleManagerBasePlugin(ManoBasePlugin):
    """
    Generic Function Lifecycle Manager plugin base class
    """

    # A dict of all required northbound AMQP topic names that may be modified by
    # subclasses
    northbound_topics = {"deploy": "mano.function.deploy"}

    # A dict of all required southbound AMQP topic names that may be modified by
    # subclasses
    southbound_topics = {"deploy": "infrastructure.function.deploy"}

    def declare_subscriptions(self):
        super().declare_subscriptions()

        # The topic on which deploy requests are posted
        self.conn.register_async_endpoint(
            self.on_function_instance_create, self.northbound_topics["deploy"]
        )

    async def on_function_instance_create(self, message: Message):
        request = message.payload

        try:
            record = await self.deploy(
                request["function_instance_id"],
                request["service_instance_id"],
                request["vim_id"],
                request["vnfd"],
            )
            self.store_record(record)
            return {"status": "SUCCESS"}
        except DeploymentError as e:
            return {"status": "ERROR", "error": str(e)}

    async def deploy(
        self,
        function_instance_id: str,
        service_instance_id: str,
        vim_id: str,
        vnfd: dict,
    ):
        """
        Requests the deployment of a VNF from the VIM adaptor and returns the resulting
        record. Raises a `DeploymentError` on failure.
        """

        LOGGER.info(
            f"Requesting deployment of function instance {function_instance_id} from IA."
        )

        # Contact the IA
        response = (
            await self.manoconn.call(
                self.southbound_topics["deploy"],
                {
                    "function_instance_id": function_instance_id,
                    "service_instance_id": service_instance_id,
                    "vim_id": vim_id,
                    "vnfd": vnfd,
                },
            )
        ).payload

        if response["request_status"] == "ERROR":
            message = response["message"]
            LOGGER.info(
                f"Deployment of function instance {function_instance_id} failed: {message}"
            )
            raise DeploymentError(message)

        return response["vnfr"]

    @classmethod
    def store_record(cls, record: dict):
        """
        Stores the VNFR in the repository
        """

        LOGGER.info(f"Storing record {record['id']}")
        LOGGER.debug(f"VNFR: {record}")

        try:
            repository.post("records/functions", record)
        except RequestException as e:
            message = f"Error storing record {record['id']}"
            LOGGER.error(message, exc_info=e)
            raise DeploymentError(f"{message}: {e}")
