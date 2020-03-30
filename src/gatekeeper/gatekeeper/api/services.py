from typing import List

import connexion
from connexion.exceptions import ProblemException
from mongoengine.errors import DoesNotExist

from gatekeeper.exceptions import DescriptorNotFoundError, ServiceNotFoundError
from gatekeeper.models.descriptors import (Descriptor, DescriptorSnapshot,
                                           DescriptorType)
from gatekeeper.models.services import Service


def getServices():
    return Service.objects()


def getServiceById(id):
    try:
        return Service.objects(id=id).get()
    except DoesNotExist:
        raise ServiceNotFoundError()


def getReferencedDescriptors(descriptor: Descriptor) -> List[Descriptor]:
    """
    Given a service descriptor, returns a list of all descriptors referenced by the service
    descriptor or raises a connexion `ProblemException` with a user-friendly message.
    """
    referencedDescriptors = []
    referencedDescriptorIds = set()

    if "network_functions" not in descriptor.descriptor:
        raise ProblemException(
            status=400,
            title="Faulty Descriptor",
            detail='{} does not specify any network functions.'.format(
                descriptor.descriptor)
        )

        # TODO This would be ok if there were references to other services instead

    for function in descriptor.descriptor.network_functions:
        try:
            vendor = function["vnf_vendor"]
            name = function["vnf_name"]
            version = function["vnf_version"]
            referencedDescriptor = Descriptor.objects(
                descriptor__vendor=vendor,
                descriptor__name=name,
                descriptor__version=version,
            ).get()

            if referencedDescriptor.id not in referencedDescriptorIds:
                referencedDescriptors.append(referencedDescriptor)
                referencedDescriptorIds.add(referencedDescriptor.id)

            # TODO Handle recursive service descriptors

        except DoesNotExist:
            raise ProblemException(
                status=400,
                title="Missing Dependency",
                detail='{} contains reference to missing ' +
                'Descriptor(vendor="{}",name="{}",version="{}"). ' +
                'Please upload that descriptor and try again.'.format(
                    descriptor.descriptor, vendor, name, version
                )
            )

    return referencedDescriptors


def createDescriptorSnapshot(descriptor: Descriptor) -> DescriptorSnapshot:
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
        referencedDescriptors = getReferencedDescriptors(rootDescriptor)
        allDescriptors = [rootDescriptor] + referencedDescriptors

        # Create and save service document
        service = Service(
            rootDescriptorId=rootDescriptor.id,
            descriptorSnapshots=[createDescriptorSnapshot(d) for d in allDescriptors]
        )
        service.save()
        return service, 201
    except DoesNotExist:
        raise DescriptorNotFoundError(status="400")


def deleteServiceById(id):
    try:
        service = Service.objects(id=id).get()
        # TODO Fail if the service has instances
        service.delete()
        return service
    except DoesNotExist:
        raise ServiceNotFoundError()
