from enum import Enum
from typing import Type

from ..models import Descriptor, OnboardedDescriptor, UploadedDescriptor
from ..util import makeErrorResponse


class DescriptorType(Enum):
    SERVICE = "service"
    VM = "vm"
    CN = "cn"
    FPGA = "fpga"


def getDescriptorsByType(descriptorClass: Type[Descriptor], type: DescriptorType):
    """
    Returns a QuerySet of descriptors of a specified Descriptor subclass and type.
    """
    return descriptorClass.objects(type=type)


def getUploadedDescriptorsByType(type: DescriptorType):
    """
    Returns a QuerySet of uploaded descriptors of a given type.
    """
    return getDescriptorsByType(UploadedDescriptor, type)


def getOnboardedDescriptorsByType(type: DescriptorType):
    """
    Returns a QuerySet of onboarded descriptors of a given type.
    """
    return getDescriptorsByType(OnboardedDescriptor, type)


def getDescriptorById(id):
    """
    Returns a given descriptor by its ID, or a 404 error if no descriptor matching the given id
    exists.
    """
    descriptors = Descriptor.objects(uuid=id)
    if(len(descriptors) != 0):
        return descriptors.first()
    return makeErrorResponse(404, "No descriptor matching the given id was found.")


def addUploadedDescriptor(body):
    d = UploadedDescriptor(**body)
    d.save()
    return d


# def deleteOnboardedDescriptor(uuid):
#     value = Descriptor.objects(uuid=uuid, location="Onboarded").delete()
#     if value == 1:
#         return "Deleted"
#     else:
#         return "Not Found"
