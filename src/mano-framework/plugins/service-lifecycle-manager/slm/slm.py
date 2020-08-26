import logging
from copy import deepcopy
from typing import List
from uuid import uuid4

from requests import RequestException
from requests.exceptions import HTTPError
from voluptuous import ALLOW_EXTRA, All, Length, MultipleInvalid, Required, Schema

import slm.topics as topics
from manobase import repository
from manobase.messaging import AsyncioBrokerConnection, Message
from slm.exceptions import (
    DeployRequestValidationError,
    InstantiationError,
    PlacementError,
    TerminationError,
)
from slm.models import Function, Service
from slm.util import get_vm_image_id, raise_on_error_response, run_sync

DEPLOY_REQUEST_SCHEMA = Schema(
    {Required("nsd"): dict, Required("vnfds"): All(list, Length(min=1))},
    extra=ALLOW_EXTRA,
)

LOGGER = logging.getLogger(__name__)


class ServiceLifecycleManager:
    """
    A ServiceManager is responsible to handle the lifecycle of a single service
    instance.
    """

    class LoggerAdapter(logging.LoggerAdapter):
        """
        Logger adapter to prepend `ServiceManager(Service Instance Id: ...)` to log
        messages
        """

        def process(self, msg, kwargs):
            return (
                f"ServiceLifecycleManager(service_id: {self.extra['service_instance_id']}): {msg:s}",
                kwargs,
            )

    def __init__(self, service: Service, conn: AsyncioBrokerConnection, validate=True):
        """
        Instantiates a ServiceLifecycleManager for the provided `Service` document.
        """
        self.service = service
        self.conn = conn

        self.logger = self.LoggerAdapter(
            LOGGER, {"service_instance_id": self.service_id}
        )

    @classmethod
    def from_deploy_request(cls, message: Message, conn: AsyncioBrokerConnection):
        """
        Given a deploy request message, validates the message and creates the
        corresponding ``ServiceLifecycleManager``. Raises a
        ``DeployRequestValidationError`` if the message is invalid.
        """
        payload = message.payload

        try:
            # Validate the deploy request against the schema
            DEPLOY_REQUEST_SCHEMA(payload)
        except MultipleInvalid as e:
            raise DeployRequestValidationError(e.msg)

        service = Service(
            descriptor=payload["nsd"],
            functions=[
                Function(
                    descriptor=descriptor, id=descriptor["id"], instance_id=uuid4()
                )
                for descriptor in payload["vnfds"]
            ],
        )
        service.save()

        return cls(service, conn)

    @classmethod
    def from_database(cls, service_instance_id: str, conn: AsyncioBrokerConnection):
        """
        Recreates a `ServiceLifecycleManager` from a MongoDB document. Raises a
        `mongoengine.DoesNotExist` if no document exists for the given service instance.
        """
        return cls(Service.objects.get(id=service_instance_id), conn)

    @property
    def service_id(self):
        return str(self.service.id)

    @property
    def _record_endpoint(self):
        return f"records/services/{self.service_id}"

    async def instantiate(self):
        self.logger.info("Instantiating")

        # Onboard and instantiate the SSMs, if required.
        # if self.services[serv_id]["service"]["ssm"]:
        #     onboard_ssms
        #     instant_ssms
        # if "task" in self.services[serv_id]["service"]["ssm"]:
        #     trigger_task_ssm

        topology = await self._fetch_topology()

        # Perform the placement
        # if "placement" in self.services[serv_id]["service"]["ssm"]:
        #     req_placement_from_ssm
        # else:

        await self._fetch_placement(topology)
        await self._prepare_infrastructure()

        try:
            await self._deploy_vnfs()
            # vnfs_start
            # vnf_chain
            await self._setup_records()
            # wan_configure
            # start_monitoring
        except InstantiationError as inst_error:
            # Rollback the instantiation
            try:
                await self._destroy_vnfs()
            except TerminationError as term_error:
                # Add the termination error to the instantiation error's message
                inst_error.add_error(term_error)

            self.logger.info("Instantiation failed", exc_info=inst_error)
            raise inst_error

        self.logger.info("Instantiation succeeded")

    async def terminate(self):
        self.logger.info("Terminating")

        # stop_monitoring
        # wan_deconfigure
        # vnf_unchain
        # vnfs_stop

        await self._destroy_vnfs()

        # if self.services[serv_id]["service"]["ssm"]:
        #     terminate_ssms

        # for vnf in self.services[serv_id]["function"]:
        #     if vnf["fsm"] is not None:
        #         terminate_fsms
        #         break

        await self._teardown_records()

        # Delete the service document from MongoDB
        self.service.delete()

        self.logger.info("Termination succeeded")

    async def _fetch_topology(self) -> List[dict]:
        """
        Returns the current topology from the infrastructure adaptor.
        """
        self.logger.info("Requesting topology from infrastructure adaptor")
        return (await self.conn.call(topics.IA_TOPOLOGY)).payload

    async def _fetch_placement(self, topology: List[dict]):
        """
        Given a topology, requests a placement from the placement plugin and stores it
        in `self.service`. If no placement could be made, a ``PlacementError`` is raised
        instead.
        """
        self.logger.info("Requesting placement from placement plugin")

        request = {
            "nsd": self.service.descriptor,
            "functions": [function.descriptor for function in self.service.functions],
            "topology": topology,
            "serv_id": self.service_id,
        }

        # TODO NAPs
        request["nap"] = {}

        response = await self.conn.call(topics.MANO_PLACE, request)
        placement = response.payload["mapping"]

        if placement is None:
            self.logger.info("Unable to perform placement.")
            raise PlacementError()

        # Save placement in service document and its embedded function documents
        self.service.placement = placement
        for function in self.service.functions:
            function.vim = placement[str(function.id)]["vim"]

        self.service.save()

    async def _prepare_infrastructure(self):
        self.logger.info("Requesting IA to prepare the infrastructure")

        # Map VIM ids to vim details
        vims = {}

        for function in self.service.functions:
            vim_id = function.vim

            if vim_id not in vims:
                vims[vim_id] = {}

            descriptor = function.descriptor
            if descriptor["descriptor_flavor"] == "openstack":
                if "vm_images" not in vims[vim_id]:
                    vims[vim_id]["vm_images"] = []

                vims[vim_id]["vm_images"] += [
                    {
                        "id": get_vm_image_id(descriptor, vdu),
                        "url": vdu["vm_image"],
                        "md5": vdu["vm_image_md5"] if "vm_image_md5" in vdu else None,
                    }
                    for vdu in descriptor["virtual_deployment_units"]
                    if "vm_image" in vdu
                ]

        # Request preparation from IA
        response = (
            await self.conn.call(
                topics.IA_PREPARE, {"instance_id": self.service_id, "vims": vims}
            )
        ).payload

        raise_on_error_response(
            response,
            InstantiationError,
            self.logger,
            "Preparation of infrastructure failed",
        )

    async def _deploy_vnfs(self):
        # Map VNFD flavors to topics
        topics_map = {
            "openstack": topics.MANO_DEPLOY,
            "kubernetes": topics.MANO_CS_DEPLOY,
        }

        for function in self.service.functions:
            self.logger.info(f"Requesting the deployment of VNF {function.id}")

            flavor = function.descriptor["descriptor_flavor"]
            try:
                topic = topics_map[flavor]
            except KeyError:
                raise InstantiationError(
                    f'The SLM does not support VNFD flavor "{flavor}".'
                )

            response = (
                await self.conn.call(
                    topic,
                    {
                        "function_instance_id": str(function.instance_id),
                        "service_instance_id": self.service_id,
                        "vim_id": str(function.vim),
                        "vnfd": function.descriptor,
                    },
                )
            ).payload

            raise_on_error_response(
                response,
                InstantiationError,
                self.logger,
                f"Deployment of VNF {function.id} failed",
            )

            self.logger.info(f"VNF {function.id} deployed successfully")

    async def _destroy_vnfs(self):
        response = (
            await self.conn.call(
                topics.IA_REMOVE, {"service_instance_id": self.service_id},
            )
        ).payload

        raise_on_error_response(
            response, TerminationError, self.logger, "Termination failed"
        )

    def _generate_service_record(self, status: str) -> dict:
        """
        Generates the service's Network Service Record and returns it
        """
        descriptor: dict = self.service.descriptor
        record = deepcopy(descriptor)
        record.update(
            {
                "id": self.service_id,
                "status": status,
                "version": "1",
                "descriptor_reference": descriptor["id"],
                "network_functions": [
                    {"vnfr_id": str(function.instance_id)}
                    for function in self.service.functions
                ],
            }
        )

        return record

    async def _set_record_status(self, endpoint: str, status: str):
        """
        Updates a records' status field to a given status
        """
        version = (await run_sync(repository.get, endpoint))["version"]
        await run_sync(
            repository.patch,
            endpoint,
            {"status": status, "version": str(int(version) + 1)},
        )

    async def _set_function_records_status(self, status: str):
        """
        Updates the function records' status fields to `status`
        """
        for function in self.service.functions:
            await self._set_record_status(
                f"records/functions/{function.instance_id}", status
            )

    async def _setup_records(self):
        """
        Updates the function records' statuses to "normal operation"; creates and stores
        a network service record
        """
        try:
            self.logger.info("Updating status of function records")
            await self._set_function_records_status("normal operation")

            self.logger.info("Storing service record")
            record = self._generate_service_record(status="normal operation")
            await run_sync(repository.post, "records/services", record)
        except RequestException as e:
            if isinstance(e, HTTPError):
                e.args += (e.response.json(),)
            raise InstantiationError(
                f"Error while writing records to repository: {str(e)}"
            )

    async def _teardown_records(self):
        """
        Sets the status of the service and function records to "terminated".
        """
        try:
            self.logger.info("Updating record statusses")
            await self._set_function_records_status("terminated")
            await self._set_record_status(self._record_endpoint, "terminated")
        except RequestException as e:
            if isinstance(e, HTTPError):
                e.args += (e.response.json(),)
            raise TerminationError(f"Error updating records: {str(e)}")
