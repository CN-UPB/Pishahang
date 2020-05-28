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

import requests
import yaml

import manobase.messaging as messaging
from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin
from olm import helpers as tools
from olm import topics as t

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("olm")
LOG.setLevel(logging.INFO)


class OpenStackLifecycleManager(ManoBasePlugin):
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
        self.functions = {}

        self.thrd_pool = pool.ThreadPoolExecutor(max_workers=10)

        self.ledger = {}

        self.connections = {}
        self.osm_user = "specific-management"
        self.osm_pass = "sonata"
        base = "amqp://" + self.osm_user + ":" + self.osm_pass
        self.osm_url_base = base + "@son-broker:5672/"

        super().__init__(
            version="0.1-dev", description="OpenStack Lifecycle Manager", **kwargs
        )

    def declare_subscriptions(self):
        """
        Declare topics that FLM subscribes on.
        """
        super().declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.conn.subscribe(self.function_instance_create, t.VNF_DEPLOY)

        # The topic on which start requests are posted.
        self.conn.subscribe(self.function_instance_start, t.VNF_START)

        # The topic on which configurre requests are posted.
        self.conn.subscribe(self.function_instance_config, t.VNF_CONFIG)

        # The topic on which stop requests are posted.
        self.conn.subscribe(self.function_instance_stop, t.VNF_STOP)

        # The topic on which stop requests are posted.
        self.conn.subscribe(self.function_instance_scale, t.VNF_SCALE)

        # The topic on which terminate requests are posted.
        self.conn.subscribe(self.function_instance_kill, t.VNF_KILL)

    ##########################
    # FLM Threading management
    ##########################

    def get_ledger(self, func_id):

        return self.functions[func_id]

    def get_functions(self):

        return self.functions

    def set_functions(self, functions_dict):

        self.functions = functions_dict

        return

    def start_next_task(self, func_id):
        """
        This method makes sure that the next task in the schedule is started
        when a task is finished, or when the first task should begin.

        :param func_id: the inst uuid of the function that is being handled.
        :param first: indicates whether this is the first task in a chain.
        """

        # If the kill field is active, the chain is killed
        if self.functions[func_id]["kill_chain"]:
            LOG.info("Function %s: Killing running workflow", func_id)
            # TODO: delete FSMs, records, stop
            # TODO: Or, jump into the kill workflow.
            del self.functions[func_id]
            return

        # Select the next task, only if task list is not empty
        if len(self.functions[func_id]["schedule"]) > 0:

            # share state with other FLMs
            next_task = getattr(self, self.functions[func_id]["schedule"].pop(0))

            # Push the next task to the threadingpool
            task = self.thrd_pool.submit(next_task, func_id)

            # Log if a task fails
            if task.exception() is not None:
                print(task.result())

            # When the task is done, the next task should be started if no flag
            # is set to pause the chain.
            if self.functions[func_id]["pause_chain"]:
                self.functions[func_id]["pause_chain"] = False
            else:
                self.start_next_task(func_id)

        else:
            del self.functions[func_id]

    ####################
    # FLM input - output
    ####################

    def flm_error(self, func_id, error=None):
        """
        This method is used to report back errors to the SLM
        """
        if error is None:
            error = self.functions[func_id]["error"]
        LOG.info("Function %s: error occured: %s", func_id, error)
        LOG.info("Function %s: informing SLM", func_id)

        self.conn.notify(
            self.functions[func_id]["topic"],
            {"status": "failed", "error": error, "timestamp": time.time()},
            correlation_id=self.functions[func_id]["orig_corr_id"],
        )

        # Kill the current workflow
        self.functions[func_id]["kill_chain"] = True

    def function_instance_create(self, message: Message):
        """
        This function handles a received message on the *.function.create
        topic.
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance create request received.")
        payload = message.payload
        corr_id = message.correlation_id
        func_id = payload["id"]

        # Add the function to the ledger
        self.add_function_to_ledger(payload, corr_id, func_id, message.topic)

        # Schedule the tasks that the FLM should do for this request.
        add_schedule = []

        # Onboard and instantiate the FSMs, if required.
        if self.functions[func_id]["fsm"]:
            add_schedule.append("onboard_fsms")
            add_schedule.append("instant_fsms")

            if "task" in self.functions[func_id]["fsm"].keys():
                add_schedule.append("trigger_task_fsm")

        add_schedule.append("deploy_vnf")
        add_schedule.append("store_vnfr")
        add_schedule.append("inform_slm_on_deployment")

        self.functions[func_id]["schedule"].extend(add_schedule)

        LOG.info(
            "Function %s: New instantiation request received. Instantiation started.",
            func_id,
        )
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def function_instance_start(self, message: Message):
        """
        This method starts the vnf start workflow
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance start request received.")
        payload = message.payload
        corr_id = message.correlation_id
        func_id = payload["vnf_id"]

        # recreate the ledger
        self.recreate_ledger(payload, corr_id, func_id, message.topic)

        # Check if VNFD defines a start FSM, if not, no action can be taken
        if "start" not in self.functions[func_id]["fsm"].keys():
            msg = ": No start FSM provided, start event ignored."
            LOG.info("Function %s%s", func_id, msg)

            self.functions[func_id]["message"] = msg
            self.respond_to_request(func_id)

            del self.functions[func_id]
            return

        # If a start FSM is present, continu with workflow
        # add the payload for the FSM
        self.functions[func_id]["start"] = payload["data"]

        # Schedule the tasks that the FLM should do for this request.
        add_schedule = ["trigger_start_fsm", "respond_to_request"]

        self.functions[func_id]["schedule"].extend(add_schedule)

        LOG.info("Function %s: New start request received.", func_id)
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def function_instance_config(self, message: Message):
        """
        This method starts the vnf config workflow
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance config request received.")
        payload = message.payload
        func_id = payload["vnf_id"]

        # recreate the ledger
        self.recreate_ledger(payload, message.correlation_id, func_id, t.VNF_CONFIG)

        # Check if VNFD defines a start FSM, if not, no action can be taken
        if "configure" not in self.functions[func_id]["fsm"].keys():
            msg = ": No config FSM provided, config event ignored."
            LOG.info("Function %s%s", func_id, msg)

            self.functions[func_id]["message"] = msg
            self.respond_to_request(func_id)

            del self.functions[func_id]
            return

        # add the payload for the FSM
        self.functions[func_id]["configure"] = payload["data"]

        # Schedule the tasks that the FLM should do for this request.
        self.functions[func_id]["schedule"].extend(
            ["trigger_configure_fsm", "respond_to_request"]
        )

        msg = ": New config request received."
        LOG.info("Function %s%s", func_id, msg)
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def function_instance_stop(self, message: Message):
        """
        This method starts the vnf stop workflow
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance stop request received.")
        payload = message.payload
        func_id = payload["vnf_id"]

        # recreate the ledger
        self.recreate_ledger(payload, message.correlation_id, func_id, message.topic)

        # Check if VNFD defines a stop FSM, if not, no action can be taken
        if "stop" not in self.functions[func_id]["fsm"].keys():
            msg = ": No stop FSM provided, start event ignored."
            LOG.info("Function %s%s", func_id, msg)

            self.functions[func_id]["message"] = msg
            self.respond_to_request(func_id)

            del self.functions[func_id]
            return

        # add the payload for the FSM
        self.functions[func_id]["stop"] = payload["data"]

        # Schedule the tasks that the FLM should do for this request.
        self.functions[func_id]["schedule"].extend(
            ["trigger_stop_fsm", "respond_to_request"]
        )

        LOG.info("Function %s: New stop request received.", func_id)
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def function_instance_scale(self, message: Message):
        """
        This method starts the vnf scale workflow
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance scale request received.")
        payload = yaml.load(payload)
        func_id = payload["vnf_id"]

        # recreate the ledger
        self.recreate_ledger(payload, message.correlation_id, func_id, message.topic)

        # Check if VNFD defines a stop FSM, if not, no action can be taken
        if "scale" not in self.functions[func_id]["fsm"].keys():
            msg = ": No scale FSM provided, scale event ignored."
            LOG.info("Function %s%s", func_id, msg)

            self.functions[func_id]["message"] = msg
            self.respond_to_request(func_id)

            del self.functions[func_id]
            return

        # add the payload for the FSM
        self.functions[func_id]["scale"] = payload["data"]

        # Schedule the tasks that the FLM should do for this request.
        add_schedule = ["trigger_scale_fsm"]
        # TODO: add interaction with Mistral when FSM responds (using the
        # content of the response)
        add_schedule.append("update_vnfr_after_scale")
        add_schedule.append("respond_to_request")

        self.functions[func_id]["schedule"].extend(add_schedule)

        LOG.info("Function %s: New scale request received.", func_id)
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def function_instance_kill(self, message: Message):
        """
        This method starts the vnf kill workflow
        """

        # Don't trigger on self created messages
        if self.name == message.app_id:
            return

        LOG.info("Function instance kill request received.")
        payload = message.payload
        func_id = payload["id"]

        # recreate the ledger
        self.recreate_ledger(payload, message.correlation_id, func_id, message.topic)

        # Schedule the tasks that the FLM should do for this request.
        add_schedule = []

        # TODO: add the relevant methods for the kill workflow

        self.functions[func_id]["schedule"].extend(add_schedule)

        LOG.info("Function %s: New kill request received.", func_id)
        # Start the chain of tasks
        self.start_next_task(func_id)

        return self.functions[func_id]["schedule"]

    def onboard_fsms(self, func_id):
        """
        This method instructs the fsm registry manager to onboard the
        required FSMs.

        :param func_id: The instance uuid of the function
        """

        corr_id = str(uuid.uuid4())
        # Sending the vnfd to the SRM triggers it to onboard the fsms
        self.conn.call_async(
            self.resp_onboard,
            t.SRM_ONBOARD,
            {"VNFD": self.functions[func_id]["vnfd"]},
            correlation_id=corr_id,
        )

        # Add correlation id to the ledger for future reference
        self.functions[func_id]["act_corr_id"] = corr_id

        # Pause the chain of tasks to wait for response
        self.functions[func_id]["pause_chain"] = True

        LOG.info("Function %s: FSM on-board trigger sent to SMR.", func_id)

    def resp_onboard(self, message: Message):
        """
        This method handles the response from the SMR on the fsm onboard call
        """

        func_id = tools.funcid_from_corrid(self.functions, message.correlation_id)
        LOG.info("Function %s: Onboard resp received from SMR.", func_id)

        payload = message.payload

        for key in payload.keys():
            if payload[key]["error"] == "None":
                LOG.info("Function %s: FSMs onboarding succesful", func_id)
            else:
                msg = ": FSM onboarding failed: " + payload[key]["error"]
                LOG.info("Function %s%s", func_id, msg)
                self.fm_error(func_id, t.GK_CREATE, error=payload[key]["error"])

        # Continue with the scheduled tasks
        self.start_next_task(func_id)

    def instant_fsms(self, func_id):
        """
        This method instructs the fsm registry manager to instantiate the
        required FSMs.

        :param func_id: The instance uuid of the function
        """

        corr_id = str(uuid.uuid4())
        # Sending the NSD to the SRM triggers it to instantiate the ssms

        msg_for_smr = {"VNFD": self.functions[func_id]["vnfd"], "UUID": func_id}

        if self.functions[func_id]["private_key"]:
            msg_for_smr["private_key"] = self.functions[func_id]["private_key"]

        LOG.info(
            "Function %s: Keys in message for FSM instant: %s",
            func_id,
            msg_for_smr.keys(),
        )

        self.conn.call_async(
            self.resp_instant, t.SRM_INSTANT, msg_for_smr, correlation_id=corr_id
        )

        # Add correlation id to the ledger for future reference
        self.functions[func_id]["act_corr_id"] = corr_id

        # Pause the chain of tasks to wait for response
        self.functions[func_id]["pause_chain"] = True

        LOG.info("FSM instantiation trigger sent to SMR")

    def resp_instant(self, message: Message):
        """
        This method handles responses to a request to onboard the fsms
        of a new function.
        """

        # Retrieve the function uuid
        func_id = tools.funcid_from_corrid(self.functions, message.correlation_id)
        msg = ": Instantiating response received from SMR."
        LOG.info("Function %s%s", func_id, msg)
        LOG.debug(message.payload)

        for fsm_type in self.functions[func_id]["fsm"].keys():
            fsm = self.functions[func_id]["fsm"][fsm_type]
            response = message.payload[fsm["id"]]
            fsm["instantiated"] = False
            if response["error"] == "None":
                LOG.info("Function %s: FSM instantiated correctly.", func_id)
                fsm["instantiated"] = True
            else:
                msg = ": FSM instantiation failed: " + response["error"]
                LOG.info("Function %s%s", func_id, msg)
                self.flm_error(func_id, error=response["error"])

            fsm["uuid"] = response["uuid"]

        # Setup broker connection with the SSMs of this service.
        url = self.osm_url_base + "fsm-" + func_id
        fsm_conn = messaging.ManoBrokerRequestResponseConnection(self.name, url=url)

        self.fsm_connections[func_id] = fsm_conn

        # Continue with the scheduled tasks
        self.start_next_task(func_id)

    def deploy_vnf(self, func_id):
        """
        This methods requests the deployment of a vnf
        """

        function = self.functions[func_id]

        outg_message = {
            "vnfd": {**function["vnfd"], "instance_uuid": function["id"]},
            "vim_uuid": function["vim_uuid"],
            "service_instance_id": function["serv_id"],
        }

        if "public_key" in function:
            outg_message["public_key"] = function["public_key"]

        corr_id = str(uuid.uuid4())
        self.functions[func_id]["act_corr_id"] = corr_id

        LOG.info("IA contacted for function deployment.")
        LOG.debug("Payload of request: %s", outg_message)
        # Contact the IA
        self.conn.call_async(
            self.IA_deploy_response, t.IA_DEPLOY, outg_message, correlation_id=corr_id
        )

        # Pause the chain of tasks to wait for response
        self.functions[func_id]["pause_chain"] = True

    def IA_deploy_response(self, message: Message):
        """
        This method handles the response from the IA on the
        vnf deploy request.
        """

        LOG.info("Response from IA on vnf deploy call received.")
        LOG.debug("Payload of request: %s", message.payload)

        inc_message = message.payload

        func_id = tools.funcid_from_corrid(self.functions, message.correlation_id)

        self.functions[func_id]["status"] = inc_message["request_status"]

        if inc_message["request_status"] == "COMPLETED":
            LOG.info("Vnf deployed correctly")
            self.functions[func_id]["ia_vnfr"] = inc_message["vnfr"]
            self.functions[func_id]["error"] = None

        else:
            LOG.info("Deployment failed: %s", inc_message["message"])
            self.functions[func_id]["error"] = inc_message["message"]
            topic = self.functions[func_id]["topic"]
            self.flm_error(func_id, topic)
            return

        self.start_next_task(func_id)

    def store_vnfr(self, func_id):
        """
        This method stores the vnfr in the repository
        """

        function = self.functions[func_id]

        # Build the record
        vnfr = tools.build_vnfr(function["ia_vnfr"], function["vnfd"])
        self.functions[func_id]["vnfr"] = vnfr
        LOG.info(yaml.dump(vnfr))

        # Store the record
        url = t.VNFR_REPOSITORY_URL + "vnf-instances"
        vnfr_response = requests.post(url, json=vnfr, timeout=1.0)
        LOG.info("Storing VNFR on %s", url)
        LOG.debug("VNFR: %s", vnfr)

        if vnfr_response.status_code == 200:
            LOG.info("VNFR storage accepted.")
        # If storage fails, add error code and message to rply to gk
        else:
            error = {
                "http_code": vnfr_response.status_code,
                "message": vnfr_response.json(),
            }
            self.functions[func_id]["error"] = error
            LOG.info("vnfr to repo failed: %s", error)
        # except:
        #     error = {'http_code': '0',
        #              'message': 'Timeout contacting VNFR server'}
        #     LOG.info('time-out on vnfr to repo')

        return

    def update_vnfr_after_scale(self, func_id):
        """
        This method updates the vnfr after a vnf scale event
        """

        # TODO: for now, this method only updates the version
        # number of the record. Once the mistral interaction
        # is added, other fields of the record might need upates
        # as well

        error = None
        vnfr = self.functions[func_id]["vnfr"]
        vnfr_id = func_id

        # Updating version number
        old_version = int(vnfr["version"])
        cur_version = old_version + 1
        vnfr["version"] = str(cur_version)

        # Updating the record
        vnfr["id"] = vnfr_id
        del vnfr["uuid"]
        del vnfr["updated_at"]
        del vnfr["created_at"]

        # Put it
        url = t.VNFR_REPOSITORY_URL + "vnf-instances/" + vnfr_id

        LOG.info("Service %s: VNFR update: %s", serv_id, url)

        try:
            vnfr_resp = requests.put(url, json=vnfr, timeout=1.0)
            vnfr_resp_json = str(vnfr_resp.json())

            if vnfr_resp.status_code == 200:
                msg = ": VNFR update accepted for " + vnfr_id
                LOG.info("Service %s%s", serv_id, msg)
            else:
                msg = ": VNFR update not accepted: " + vnfr_resp_json
                LOG.info("Service %s%s", serv_id, msg)
                error = {"http_code": vnfr_resp.status_code, "message": vnfr_resp_json}
        except:
            error = {"http_code": "0", "message": "Timeout when contacting VNFR repo"}

        if error is not None:
            LOG.info("record update failed: %s", error)
            self.functions[func_id]["error"] = error
            self.flm_error(func_id)

    def inform_slm_on_deployment(self, func_id):
        """
        In this method, the SLM is contacted to inform on the vnf
        deployment.
        """
        LOG.info("Informing the SLM of the status of the vnf deployment")

        function = self.functions[func_id]

        corr_id = self.functions[func_id]["orig_corr_id"]
        self.conn.notify(
            t.VNF_DEPLOY,
            {
                "vnfr": function["vnfr"],
                "status": function["status"],
                "error": function["error"],
            },
            correlation_id=corr_id,
        )

    def trigger_task_fsm(self, func_id):
        """
        This method triggers the task FSM.
        """
        LOG.info("Triggering task FSM.")

        # Generating the message for the FSM
        message = {"schedule": self.functions[func_id]["schedule"], "fsm_type": "task"}

        # Topic needs to be added, so the task FSM knows for which workflow
        # the schedule needs to be adapted.
        message["topic"] = topic

        # Generating the corr_id
        corr_id = str(uuid.uuid4())
        self.functions[func_id]["act_corr_id"] = corr_id

        fsm_conn = self.connections[func_id]

        # Making the call
        fsm_conn.call_async(
            self.fsm_task_response, topic, yaml.dump(payload), correlation_id=corr_id
        )

        # Pause the chain
        self.functions[func_id]["pause_chain"] = True

    def fsm_task_response(self, message: Message):
        """
        This method handles a response from a task FSM.
        """
        response = message.payload

        func_id = tools.funcid_from_corrid(self.functions, message.correlation_id)

        LOG.info("Response from task FSM received")

        if response["status"] == "COMPLETED":
            LOG.info("FSM finished successfully")
            self.functions[func_id]["schedule"] = response["schedule"]

        else:
            LOG.info("task FSM failed: %s", response["error"])
            self.functions[func_id]["error"] = response["error"]
            self.flm_error(func_id)
            return

        self.start_next_task(func_id)

    def trigger_start_fsm(self, func_id):
        """
        This method is called to trigger the start FSM.
        """
        self.trigger_fsm(func_id, "start")

    def trigger_stop_fsm(self, func_id):
        """
        This method is called to trigger the stop FSM.
        """
        self.trigger_fsm(func_id, "stop")

    def trigger_scale_fsm(self, func_id):
        """
        This method is called to trigger the scale FSM.
        """
        self.trigger_fsm(func_id, "scale")

    def trigger_configure_fsm(self, func_id):
        """
        This method is called to trigger the configure FSM.
        """
        self.trigger_fsm(func_id, "configure")

    def trigger_fsm(self, func_id, fsm_type):
        """
        This is a generic method for triggering start/stop/configure FSMs.
        """
        LOG.info("Triggering %s FSM.", fsm_type)

        # Generating the payload for the call
        payload = {"content": self.functions[func_id][fsm_type], "fsm_type": fsm_type}

        # Creating the topic
        topic = "generic.fsm." + func_id

        # Generating the corr_id
        corr_id = str(uuid.uuid4())
        self.functions[func_id]["act_corr_id"] = corr_id
        self.functions[func_id]["active_fsm"] = fsm_type

        # Making the call
        self.connections[func_id].call_async(
            self.fsm_generic_response, topic, payload, correlation_id=corr_id
        )

        # Pause the chain
        self.functions[func_id]["pause_chain"] = True

    def fsm_generic_response(self, message: Message):
        """
        This method handles a response to a generic FSM trigger call
        """
        response = message.payload

        func_id = tools.funcid_from_corrid(self.functions, message.correlation_id)
        fsm_type = self.functions[func_id]["active_fsm"]

        LOG.info("Response from %s FSM received", fsm_type)

        if response["status"] == "COMPLETED":
            LOG.info("FSM finished successfully")

        else:
            LOG.info("%s FSM failed: %s", fsm_type, response["error"])
            self.functions[func_id]["error"] = response["error"]
            self.flm_error(func_id)
            return

        self.start_next_task(func_id)

    def respond_to_request(self, func_id):
        """
        This method creates a response message for the sender of requests.
        """

        message = {
            "timestamp": time.time(),
            "error": self.functions[func_id]["error"],
            "vnf_id": func_id,
        }

        if self.functions[func_id]["error"] is None:
            message["status"] = "COMPLETED"
        else:
            message["status"] = "FAILED"

        if self.functions[func_id]["message"] is not None:
            message["message"] = self.functions[func_id]["message"]

        LOG.info("Generating response to the workflow request")
        self.conn.notify(
            self.functions[func_id]["topic"],
            message,
            correlation_id=self.functions[func_id]["orig_corr_id"],
        )

    ###########
    # FLM tasks
    ###########

    def add_function_to_ledger(self, payload, corr_id, func_id, topic):
        """
        This method adds new functions with their specifics to the ledger,
        so other functions can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param func_id: the instance uuid of the function defined by SLM.
        """

        self.functions[func_id] = {
            "vnfd": payload["vnfd"],
            "id": func_id,
            "topic": topic,  # Topic of the call
            "orig_corr_id": corr_id,
            "payload": payload,
            "serv_id": payload["serv_id"],  # Service uuid that this function belongs to
            "vim_uuid": payload["vim_uuid"],
            "schedule": [],
            # Create the FSM dict if FSMs are defined in VNFD:
            "fsm": tools.get_fsm_from_vnfd(payload["vnfd"]),
            "pause_chain": False,
            "kill_chain": False,
            # Payload fields for FSMs:
            "start": None,
            "stop": None,
            "configure": None,
            "act_corr_id": None,
            "message": None,
            "error": None,
            "public_key": payload["public_key"],
            "private_key": payload["private_key"],
        }

        return func_id

    def recreate_ledger(self, payload, corr_id, func_id, topic):
        """
        This method adds already existing functions with their specifics
        back to the ledger, so other methods can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param func_id: the instance uuid of the function defined by SLM.
        """

        # Add the function to the ledger and add instance ids
        self.functions[func_id] = {}

        # TODO: add the real vnfr here
        vnfr = {}
        self.functions[func_id]["vnfr"] = vnfr

        if "vnfd" in payload.keys():
            vnfd = payload["vnfd"]
        else:
            # TODO: retrieve VNFD from CAT based on func_id
            vnfd = {}
        self.functions[func_id]["vnfd"] = vnfd

        self.functions[func_id]["id"] = func_id

        # Add the topic of the call
        self.functions[func_id]["topic"] = topic

        # Add to correlation id to the ledger
        self.functions[func_id]["orig_corr_id"] = corr_id

        # Add payload to the ledger
        self.functions[func_id]["payload"] = payload

        # Add the service uuid that this function belongs to
        self.functions[func_id]["serv_id"] = payload["serv_id"]

        # Add the VIM uuid
        self.functions[func_id]["vim_uuid"] = ""

        # Create the function schedule
        self.functions[func_id]["schedule"] = []

        # Create the FSM dict if FSMs are defined in VNFD
        fsm_dict = tools.get_fsm_from_vnfd(vnfd)
        self.functions[func_id]["fsm"] = fsm_dict

        # Create the chain pause and kill flag

        self.functions[func_id]["pause_chain"] = False
        self.functions[func_id]["kill_chain"] = False

        # Create payload fields for FSMs
        self.functions[func_id]["start"] = None
        self.functions[func_id]["stop"] = None
        self.functions[func_id]["configure"] = None
        self.functions[func_id]["act_corr_id"] = None
        self.functions[func_id]["message"] = None

        # Add error field
        self.functions[func_id]["error"] = None

        return func_id


def main():
    """
    Entry point to start plugin.
    :return:
    """
    OpenStackLifecycleManager()


if __name__ == "__main__":
    main()
