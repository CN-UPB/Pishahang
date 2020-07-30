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
import concurrent.futures as pool
import logging
import time
import uuid

from requests import RequestException

import manobase.repository as repository
from klm import helpers as tools
from klm import topics as t
from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("klm")
LOG.setLevel(logging.INFO)


class KubernetesLifecycleManager(ManoBasePlugin):
    """
    This class implements the cloud service lifecycle manager.
    """

    def __init__(self, **kwargs):
        """
        Initialize class and manobase.plugin.BasePlugin class.
        This will automatically connect to the broker, contact the
        plugin manager, and self-register this plugin to the plugin
        manager.

        After the connection and registration procedures are done, the
        'on_lifecycle_start' method is called.
        :return:
        """

        # Create the ledger that saves state
        self.cloud_services = {}
        self.ledger = {}
        self.thrd_pool = pool.ThreadPoolExecutor(max_workers=10)

        super().__init__(
            version="0.1-dev", description="Kubernetes Lifecycle Manager", **kwargs
        )

    def declare_subscriptions(self):
        """
        Declare topics that CLM subscribes on.
        """
        super().declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.manoconn.subscribe(self.cloud_service_instance_create, t.CS_DEPLOY)

    ##########################
    # CLM Threading management
    ##########################

    def get_ledger(self, cservice_id):
        return self.cloud_services[cservice_id]

    def get_cloud_services(self):
        return self.cloud_services

    def set_cloud_services(self, cloud_service_dict):
        self.cloud_services = cloud_service_dict

    def start_next_task(self, cservice_id):
        """
        This method makes sure that the next task in the schedule is started
        when a task is finished, or when the first task should begin.

        :param cservice_id: the inst uuid of the cloud service that is being handled.
        :param first: indicates whether this is the first task in a chain.
        """

        # If the kill field is active, the chain is killed
        if self.cloud_services[cservice_id]["kill_chain"]:
            LOG.info("Cloud Service %s: Killing running workflow", cservice_id)
            del self.cloud_services[cservice_id]
            return

        # Select the next task, only if task list is not empty
        if len(self.cloud_services[cservice_id]["schedule"]) > 0:

            # share state with other FLMs
            next_task = getattr(
                self, self.cloud_services[cservice_id]["schedule"].pop(0)
            )

            # Push the next task to the threading pool
            task = self.thrd_pool.submit(next_task, cservice_id)

            # Log if a task fails
            if task.exception() is not None:
                print(task.result())

            # When the task is done, the next task should be started if no flag
            # is set to pause the chain.
            if self.cloud_services[cservice_id]["pause_chain"]:
                self.cloud_services[cservice_id]["pause_chain"] = False
            else:
                self.start_next_task(cservice_id)

        else:
            del self.cloud_services[cservice_id]

    ####################
    # CLM input - output
    ####################

    def clm_error(self, cservice_id, error=None):
        """
        This method is used to report back errors to the SLM
        """
        if error is None:
            error = self.cloud_services[cservice_id]["error"]
        LOG.info("Cloud Service %s: error occured: %s", cservice_id, error)
        LOG.info("Cloud Service %s: informing SLM", cservice_id)

        message = {"status": "ERROR", "error": error, "timestamp": time.time()}

        corr_id = self.cloud_services[cservice_id]["orig_corr_id"]
        topic = self.cloud_services[cservice_id]["topic"]

        self.manoconn.notify(topic, message, correlation_id=corr_id)

        # Kill the current workflow
        self.cloud_services[cservice_id]["kill_chain"] = True

    def cloud_service_instance_create(self, message: Message):
        """
        This cloud service handles a received message on the *.cloud_service.create
        topic.
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Cloud Service instance create request received.")
        payload = message.payload

        cservice_id = payload["id"]

        # Add the function to the ledger
        self.add_cloud_service_to_ledger(
            payload, message.correlation_id, cservice_id, t.CS_DEPLOY
        )

        # Schedule the tasks that the FLM should do for this request.
        self.cloud_services[cservice_id]["schedule"].extend(
            ["deploy_cs", "store_csr", "inform_slm_on_deployment"]
        )

        LOG.info(
            "Cloud Service %s: New instantiation request received. Instantiation started.",
            cservice_id,
        )
        # Start the chain of tasks
        self.start_next_task(cservice_id)

        return self.cloud_services[cservice_id]["schedule"]

    def deploy_cs(self, cservice_id):
        """
        This methods requests the deployment of a cloud service
        """

        cloud_service = self.cloud_services[cservice_id]

        outg_message = {
            "csd": {**cloud_service["csd"], "instance_uuid": cloud_service["id"]},
            "vim_uuid": cloud_service["vim_uuid"],
            "service_instance_id": cloud_service["serv_id"],
        }

        corr_id = str(uuid.uuid4())
        self.cloud_services[cservice_id]["act_corr_id"] = corr_id

        LOG.info("IA contacted for cloud service deployment.")
        LOG.debug("Payload of request: %s", outg_message)
        # Contact the IA
        self.manoconn.call_async(
            self.ia_deploy_response, t.IA_DEPLOY, outg_message, correlation_id=corr_id
        )

        # Pause the chain of tasks to wait for response
        self.cloud_services[cservice_id]["pause_chain"] = True

    def ia_deploy_response(self, message: Message):
        """
        This method handles the response from the IA on the
        cs deploy request.
        """

        LOG.info("Response from IA on cs deploy call received.")
        LOG.debug("Payload of request: %s", message.payload)

        payload = message.payload

        cservice_id = tools.cserviceid_from_corrid(
            self.cloud_services, message.correlation_id
        )

        self.cloud_services[cservice_id]["status"] = payload["request_status"]

        if payload["request_status"] == "COMPLETED":
            LOG.info("Cs deployed correctly")
            self.cloud_services[cservice_id]["ia_csr"] = payload["csr"]
            self.cloud_services[cservice_id]["error"] = None

        else:
            LOG.info("Deployment failed: %s", payload["message"])
            self.cloud_services[cservice_id]["error"] = payload["message"]
            topic = self.cloud_services[cservice_id]["topic"]
            self.clm_error(cservice_id, topic)
            return

        self.start_next_task(cservice_id)

    def store_csr(self, cservice_id):
        """
        This method stores the csr in the repository
        """

        cloud_service = self.cloud_services[cservice_id]

        csr = cloud_service["ia_csr"]
        self.cloud_services[cservice_id]["csr"] = csr

        # Store the record
        LOG.info("Storing CSR")
        LOG.debug("CSR: %s", csr)
        try:
            repository.post("records/functions", csr)
        except RequestException as e:
            LOG.error("CSR storage failed", exc_info=e)
            self.cloud_services[cservice_id]["error"] = {
                "message": str(e),
            }

    def inform_slm_on_deployment(self, cservice_id):
        """
        In this method, the SLM is contacted to inform on the cs
        deployment.
        """
        LOG.info("Informing the SLM of the status of the cs deployment")

        cloud_service = self.cloud_services[cservice_id]

        self.manoconn.notify(
            t.CS_DEPLOY,
            {
                "csr": cloud_service["csr"],
                "status": cloud_service["status"],
                "error": cloud_service["error"],
            },
            correlation_id=cloud_service["orig_corr_id"],
        )

    ###########
    # CLM tasks
    ###########

    def add_cloud_service_to_ledger(self, payload, corr_id, cservice_id, topic):
        """
        This method adds new cloud services with their specifics to the ledger,
        so other cloud services can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param cservice_id: the instance uuid of the cloud service defined by SLM.
        """

        # Add the cloud service to the ledger and add instance ids
        self.cloud_services[cservice_id] = {
            "csd": payload["csd"],
            "id": cservice_id,
            "topic": topic,
            "orig_corr_id": corr_id,
            "payload": payload,
            # The service uuid that this cloud service belongs to
            "serv_id": payload["serv_id"],
            "vim_uuid": payload["vim_uuid"],
            "schedule": [],
            "pause_chain": False,
            "kill_chain": False,
            "act_corr_id": None,
            "message": None,
            "error": None,
        }

        return cservice_id

    def recreate_ledger(self, payload, corr_id, cserver_id, topic):
        """
        This method adds already existing cloud services with their specifics
        back to the ledger, so other methods can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param cserver_id: the instance uuid of the cloud service defined by SLM.
        """

        # Add the cloud service to the ledger and add instance ids
        self.cloud_services[cserver_id] = {}

        csr = {}
        self.cloud_services[cserver_id]["csr"] = csr

        if "csd" in payload.keys():
            csd = payload["csd"]
        else:
            csd = {}
        self.cloud_services[cserver_id]["csd"] = csd

        self.cloud_services[cserver_id]["id"] = cserver_id

        # Add the topic of the call
        self.cloud_services[cserver_id]["topic"] = topic

        # Add to correlation id to the ledger
        self.cloud_services[cserver_id]["orig_corr_id"] = corr_id

        # Add payload to the ledger
        self.cloud_services[cserver_id]["payload"] = payload

        # Add the service uuid that this cloud service belongs to
        self.cloud_services[cserver_id]["serv_id"] = payload["serv_id"]

        # Add the VIM uuid
        self.cloud_services[cserver_id]["vim_uuid"] = ""

        # Create the cloud service schedule
        self.cloud_services[cserver_id]["schedule"] = []

        # Create the chain pause and kill flag
        self.cloud_services[cserver_id]["pause_chain"] = False
        self.cloud_services[cserver_id]["kill_chain"] = False

        # Add error field
        self.cloud_services[cserver_id]["error"] = None

        return cserver_id


def main():
    """
    Entry point to start plugin.
    """
    KubernetesLifecycleManager()


if __name__ == "__main__":
    main()
