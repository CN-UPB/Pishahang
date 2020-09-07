import logging
from typing import List
from uuid import uuid4

import connexion
from connexion.exceptions import ProblemException
from mongoengine.errors import DoesNotExist
from requests.exceptions import RequestException

from gatekeeper.app import broker
from gatekeeper.exceptions import (
    DescriptorNotFoundError,
    InternalServerError,
    ServiceInstanceNotFoundError,
    ServiceNotFoundError,
)
from gatekeeper.models.descriptors import Descriptor, DescriptorSnapshot, DescriptorType
from gatekeeper.models.services import Service, ServiceInstance
from gatekeeper.util.mongoengine_custom_json import to_custom_dict
from manobase import repository
from manobase.messaging import Message

logger = logging.getLogger(__name__)

SERVICE_CREATION_TOPIC = "service.instances.create"
SERVICE_TERMINATION_TOPIC = "service.instance.terminate"


def getServices(user):
    return Service.objects(userId=user)


def _getServiceByIdOrFail(userId, serviceId: str) -> Service:
    try:
        return Service.objects.get(userId=userId, id=serviceId)
    except DoesNotExist:
        raise ServiceNotFoundError()


def getServiceById(user, id):
    return _getServiceByIdOrFail(user, id)


def _getReferencedDescriptors(userId: str, descriptor: Descriptor) -> List[Descriptor]:
    """
    Given a service descriptor, returns a list of all descriptors referenced by the
    service descriptor or raises a connexion `ProblemException` with a user-friendly
    message.
    """
    referencedDescriptors = []
    referencedDescriptorIds = set()

    if "network_functions" not in descriptor.content:
        raise ProblemException(
            status=400,
            title="Faulty Descriptor",
            detail="{} does not specify any network functions.".format(
                descriptor.content
            ),
        )

    for function in descriptor.content.network_functions:
        try:
            vendor = function["vnf_vendor"]
            name = function["vnf_name"]
            version = function["vnf_version"]
            referencedDescriptor = Descriptor.objects(
                userId=userId,
                content__descriptor_type="function",
                content__vendor=vendor,
                content__name=name,
                content__version=version,
            ).get()

            if referencedDescriptor.id not in referencedDescriptorIds:
                referencedDescriptors.append(referencedDescriptor)
                referencedDescriptorIds.add(referencedDescriptor.id)

        except DoesNotExist:
            raise ProblemException(
                status=400,
                title="Missing Dependency",
                detail=(
                    f"{descriptor.content} contains reference to missing "
                    f'Descriptor(descriptor_type="function", vendor="{vendor}", '
                    f'name="{name}",version="{version}"). '
                    f"Please upload that descriptor and try again."
                ),
            )

    return referencedDescriptors


def _createDescriptorSnapshot(descriptor: Descriptor) -> DescriptorSnapshot:
    snapshot = DescriptorSnapshot(**{field: descriptor[field] for field in descriptor})
    snapshot.id = str(uuid4())  # Generate a new ID for the snapshot
    return snapshot


def addService(user, body):
    """
    Onboards a service descriptor (by its ID) and the referenced function descriptors,
    adding a new service.
    """
    try:
        serviceDescriptor: Descriptor = Descriptor.objects.get(
            userId=user, id=body["id"]
        )
        if serviceDescriptor.type != DescriptorType.SERVICE.value:
            return connexion.problem(
                400,
                "Service Descriptor Required",
                (
                    "You are trying to onboard a non-service descriptor. "
                    "Only service descriptors can be onboarded."
                ),
            )

        # Create service document with descriptor snapshots
        service = Service(
            userId=user,
            descriptor=_createDescriptorSnapshot(serviceDescriptor),
            vendor=serviceDescriptor.content.vendor,
            name=serviceDescriptor.content.name,
            version=serviceDescriptor.content.version,
            functionDescriptors=[
                _createDescriptorSnapshot(descriptor)
                for descriptor in _getReferencedDescriptors(user, serviceDescriptor)
            ],
        )

        # Store the descriptors in the repository
        try:
            repository.post(
                "descriptors/services",
                {
                    **to_custom_dict(service.descriptor.content),
                    "id": str(service.descriptor.id),
                },
            )
            for descriptor in service.functionDescriptors:
                repository.post(
                    "descriptors/functions",
                    {**to_custom_dict(descriptor.content), "id": str(descriptor.id)},
                )
        except RequestException as e:
            raise InternalServerError(
                detail=f"Failed to store descriptors in repository: {e}"
            )

        service.save()
        return service, 201
    except DoesNotExist:
        raise DescriptorNotFoundError(status="400")


def deleteServiceById(user, id):
    service = _getServiceByIdOrFail(user, id)

    activeInstances = 0
    for instance in service.instances:
        if instance.status != "ERROR":
            activeInstances += 1

    if activeInstances > 0:
        raise ProblemException(
            title="Bad Request",
            detail=(
                "The service has {:d} active instances that need to be terminated "
                "before the service can be deleted."
            ).format(activeInstances),
        )

    # Delete the descriptors from the repository
    try:
        repository.delete(f"descriptors/services/{service.descriptor.id}")
        for descriptor in service.functionDescriptors:
            repository.delete(f"descriptors/functions/{descriptor.id}")
    except RequestException as e:
        raise InternalServerError(
            detail=f"Failed to delete descriptors from repository: {e}"
        )

    for instance in service.instances:
        instance.delete()

    service.delete()
    return service


# Service instances


def getServiceInstances(user, serviceId):
    service = _getServiceByIdOrFail(user, serviceId)
    return service.instances


def instantiateService(user, serviceId):
    service = _getServiceByIdOrFail(user, serviceId)

    # Send instantiation message
    validationReply = broker.call_sync(
        SERVICE_CREATION_TOPIC,
        {
            "ingresses": [],
            "egresses": [],
            "nsd": {
                **to_custom_dict(service.descriptor.content),
                "id": str(service.descriptor.id),
            },
            "vnfds": [
                {**to_custom_dict(descriptor.content), "id": str(descriptor.id)}
                for descriptor in service.functionDescriptors
            ],
        },
    )

    if validationReply.payload["status"] == "ERROR":
        raise ProblemException(
            status=500,
            title="Instantiation Failed",
            detail=validationReply.payload["error"],
        )

    instance = ServiceInstance(
        userId=user,
        status=validationReply.payload["status"],
        correlationId=validationReply.correlation_id,
    )
    instance.save()
    service.instances.append(instance)
    service.save()

    def onNotificationReceived(message: Message):
        """
        React to the SLM's notification about the instantiation outcome
        """
        if message.correlation_id != instance.correlationId:
            return

        payload = message.payload

        logger.debug("Received instantiation notification: %s", payload)

        instance.status = payload["status"]
        if payload["status"] == "ERROR":
            instance.message = str(payload["error"])
        else:
            # Get instance id
            instance.internalId = payload["nsr"]["id"]

        instance.save()

        broker.unsubscribe(subscriptionId)

    subscriptionId = broker.register_notification_endpoint(
        onNotificationReceived, SERVICE_CREATION_TOPIC
    )

    return instance


def terminateServiceInstance(user, serviceId, instanceId):
    _getServiceByIdOrFail(user, serviceId)
    try:
        instance: ServiceInstance = ServiceInstance.objects.get(
            userId=user, id=instanceId
        )
    except DoesNotExist:
        raise ServiceInstanceNotFoundError()

    if not instance.internalId:
        instance.delete()
        return

    def onResponseReceived(message: Message):
        payload = message.payload

        logger.debug("Received termination response: %s", payload)

        instance.status = payload["status"]
        if payload["status"] == "ERROR":
            instance.message = "Termination failed: {}".format(payload["error"])
            instance.save()
        else:
            instance.delete()

    # Request service termination at the SLM
    broker.call_async(
        onResponseReceived,
        SERVICE_TERMINATION_TOPIC,
        {"instance_id": str(instance.internalId)},
    )

    instance.status = "TERMINATING"
    instance.internalId = None  # Prevent another deletion request
    instance.save()
