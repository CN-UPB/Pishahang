from typing import List

from mongoengine.errors import DoesNotExist

import connexion
from connexion.exceptions import ProblemException
from gatekeeper.app import broker
from gatekeeper.exceptions import DescriptorNotFoundError, ServiceNotFoundError
from gatekeeper.models.descriptors import (Descriptor, DescriptorSnapshot,
                                           DescriptorType)
from gatekeeper.models.services import Service
from gatekeeper.util.mongoengine_custom_json import to_custom_dict, to_custom_json
import json


def getServices():
    return Service.objects()


def _getServiceByIdOrFail(id: str) -> Service:
    try:
        return Service.objects(id=id).get()
    except DoesNotExist:
        raise ServiceNotFoundError()


def getServiceById(id):
    return _getServiceByIdOrFail(id)


def _getReferencedDescriptors(descriptor: Descriptor) -> List[Descriptor]:
    """
    Given a service descriptor, returns a list of all descriptors referenced by the service
    descriptor or raises a connexion `ProblemException` with a user-friendly message.
    """
    referencedDescriptors = []
    referencedDescriptorIds = set()

    if "network_functions" not in descriptor.content:
        raise ProblemException(
            status=400,
            title="Faulty Descriptor",
            detail='{} does not specify any network functions.'.format(
                descriptor.content)
        )

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
                detail=('{} contains reference to missing '
                        'Descriptor(vendor="{}",name="{}",version="{}"). '
                        'Please upload that descriptor and try again.').format(
                    descriptor.content, vendor, name, version
                )
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
                "You are trying to onboard a non-service descriptor. " +
                "Only service descriptors can be onboarded."
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
            descriptorSnapshots=[_createDescriptorSnapshot(d) for d in allDescriptors]
        )
        service.save()
        return service, 201
    except DoesNotExist:
        raise DescriptorNotFoundError(status="400")


def deleteServiceById(id):
    service = _getServiceByIdOrFail(id)

    instanceCount = len(service.instances)
    if instanceCount > 0:
        raise ProblemException(
            title="Bad Request",
            detail=("The service has {:d} instances that need to be stopped before it "
                    "can be deleted.").format(instanceCount)
        )

    service.delete()
    return service


# Service instances

def getServiceInstances(serviceId):
    service = _getServiceByIdOrFail(serviceId)
    return service.instances


def instantiateService(serviceId):
    service = _getServiceByIdOrFail(serviceId)

    # Generate payload for instantiation message
    payload = {
        "ingresses": [],
        "egresses": [],
        "user_data": {
            "customer": {
                "email": "pishahang@gmail.com",
                "phone": None,
                "keys": {"public": None, "private": None}
            },
            "developer": {"email":  None, "phone": None}
        }
    }
    vnfdCounter = 0
    for descriptor in service.descriptorSnapshots:
        descriptorContent = json.loads(to_custom_json(descriptor.content))
        descriptorContent['uuid'] = descriptor.id  # For backwards compatibility with SLM
        if descriptor.type == DescriptorType.SERVICE.value:
            payload['COSD'] = descriptorContent
        if descriptor.type == DescriptorType.OPENSTACK.value:
            payload['VNFD{:d}'.format(vnfdCounter)] = descriptorContent
        elif descriptor.type == DescriptorType.KUBERNETES.value:
            payload['CSD{:d}'.format(vnfdCounter)] = descriptorContent
        vnfdCounter += 1

    # Send instantiation message
    validationReply = broker.call_sync_simple("service.instances.create", msg=payload)
    if validationReply["status"] == "ERROR":
        raise ProblemException(
            status=500,
            title="Instantiation Failed",
            detail=validationReply["error"]
        )

    # TODO register for notification and create service instance in database, return instance
