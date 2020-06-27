import logging
from typing import List

from mongoengine.errors import DoesNotExist

import connexion
from connexion.exceptions import ProblemException
from gatekeeper.app import broker
from gatekeeper.exceptions import (
    DescriptorNotFoundError,
    ServiceInstanceNotFoundError,
    ServiceNotFoundError,
)
from gatekeeper.models.descriptors import Descriptor, DescriptorSnapshot, DescriptorType
from gatekeeper.models.services import Service, ServiceInstance
from gatekeeper.util.mongoengine_custom_json import to_custom_dict
from manobase.messaging import Message

logger = logging.getLogger(__name__)

SERVICE_CREATION_TOPIC = "service.instances.create"


def getServices():
    return Service.objects()


def _getServiceByIdOrFail(id: str) -> Service:
    try:
        return Service.objects.get(id=id)
    except DoesNotExist:
        raise ServiceNotFoundError()


def getServiceById(id):
    return _getServiceByIdOrFail(id)


def _getReferencedDescriptors(descriptor: Descriptor) -> List[Descriptor]:
    """
    Given a service descriptor, returns a list of all descriptors referenced by the
    service descriptor or raises a connexion `ProblemException` with a user-friendly
    message.
    """
    referencedDescriptors = []
    referencedDescriptorIds = set()

    if (
        "network_functions" not in descriptor.content
        and "cloud_services" not in descriptor.content
    ):
        raise ProblemException(
            status=400,
            title="Faulty Descriptor",
            detail="{} does not specify any network functions.".format(
                descriptor.content
            ),
        )

    if "network_functions" in descriptor.content:
        for function in descriptor.content.network_functions:
            try:
                vendor = function["vnf_vendor"]
                name = function["vnf_name"]
                version = function["vnf_version"]
                referencedDescriptor = Descriptor.objects(
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
                        "{} contains reference to missing "
                        'Descriptor(vendor="{}",name="{}",version="{}"). '
                        "Please upload that descriptor and try again."
                    ).format(descriptor.content, vendor, name, version),
                )

    else:
        # This is a quick copy-paste cheat due to the different schema for "cloud services"
        # (kubernetes descriptors). It can be removed one lucky day.
        for function in descriptor.content.cloud_services:
            try:
                vendor = function["service_vendor"]
                name = function["service_name"]
                version = function["service_version"]
                referencedDescriptor = Descriptor.objects(
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
                        "{} contains reference to missing "
                        'Descriptor(vendor="{}",name="{}",version="{}"). '
                        "Please upload that descriptor and try again."
                    ).format(descriptor.content, vendor, name, version),
                )

    return referencedDescriptors


def _createDescriptorSnapshot(descriptor: Descriptor) -> DescriptorSnapshot:
    return DescriptorSnapshot(**{field: descriptor[field] for field in descriptor})


def addService(body):
    """
    Onboards a service descriptor by its ID, adding a new service.
    """
    try:
        rootDescriptor: Descriptor = Descriptor.objects(id=body["id"]).get()
        if rootDescriptor.type != DescriptorType.SERVICE.value:
            return connexion.problem(
                400,
                "Service Descriptor Required",
                (
                    "You are trying to onboard a non-service descriptor. "
                    "Only service descriptors can be onboarded."
                ),
            )

        # Get referenced descriptors
        referencedDescriptors = _getReferencedDescriptors(rootDescriptor)
        allDescriptors = [rootDescriptor] + referencedDescriptors

        # Create and save service document
        service = Service(
            rootDescriptorId=rootDescriptor.id,
            vendor=rootDescriptor.content.vendor,
            name=rootDescriptor.content.name,
            version=rootDescriptor.content.version,
            descriptorSnapshots=[_createDescriptorSnapshot(d) for d in allDescriptors],
        )
        service.save()
        return service, 201
    except DoesNotExist:
        raise DescriptorNotFoundError(status="400")


def deleteServiceById(id):
    service = _getServiceByIdOrFail(id)

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

    for instance in service.instances:
        instance.delete()

    service.delete()
    return service


# Service instances


def getServiceInstances(serviceId):
    service = _getServiceByIdOrFail(serviceId)
    return service.instances


def instantiateService(serviceId):
    service = _getServiceByIdOrFail(serviceId)

    # Generate payload for instantiation message
    message = {
        "ingresses": [],
        "egresses": [],
        "user_data": {
            "customer": {
                "email": "pishahang@gmail.com",
                "phone": None,
                "keys": {"public": None, "private": None},
            },
            "developer": {"email": None, "phone": None},
        },
    }
    vnfdCounter = 0
    for descriptor in service.descriptorSnapshots:
        descriptorContent = to_custom_dict(descriptor.content)
        descriptorContent["uuid"] = str(
            descriptor.id
        )  # For backwards compatibility with SLM
        if descriptor.type == DescriptorType.SERVICE.value:
            message["COSD"] = descriptorContent
        if descriptor.type == DescriptorType.OPENSTACK.value:
            message["VNFD{:d}".format(vnfdCounter)] = descriptorContent
        elif descriptor.type == DescriptorType.KUBERNETES.value:
            message["CSD{:d}".format(vnfdCounter)] = descriptorContent
        vnfdCounter += 1

    # Send instantiation message
    validationReply = broker.call_sync(SERVICE_CREATION_TOPIC, message)
    if validationReply.payload["status"] == "ERROR":
        raise ProblemException(
            status=500,
            title="Instantiation Failed",
            detail=validationReply.payload["error"],
        )

    instance = ServiceInstance(
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
        if message.correlation_id == instance.correlationId:
            logger.debug("Received instantiation notification: %s", message.payload)

            instance.status = message.payload["status"]
            if message.payload["status"] == "ERROR":
                instance.message = str(message.payload["error"])
            instance.save()

            broker.unsubscribe(subscriptionId)

    subscriptionId = broker.register_notification_endpoint(
        onNotificationReceived, SERVICE_CREATION_TOPIC
    )

    return instance


def terminateServiceInstance(serviceId, instanceId):
    _getServiceByIdOrFail(serviceId)
    try:
        instance = ServiceInstance.objects.get(id=instanceId)
        instance.delete()
    except DoesNotExist:
        raise ServiceInstanceNotFoundError()
