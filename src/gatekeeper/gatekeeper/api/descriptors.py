from typing import Type

from mongoengine.errors import DoesNotExist

from ..models import (Descriptor, DescriptorType, OnboardedDescriptor,
                      UploadedDescriptor)
from ..util import makeErrorResponse


# Getting descriptors

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


def getDescriptorById(descriptorClass: Type[Descriptor], id):
    """
    Returns a given descriptor by its ID, or a 404 error if no descriptor matching the given id
    exists.
    """
    try:
        descriptor = descriptorClass.objects(id=id).get()
        return descriptor
    except DoesNotExist:
        return makeErrorResponse(404, "No descriptor matching the given id was found.")


def getUploadedDescriptorById(id):
    return getDescriptorById(UploadedDescriptor, id)


def getOnboardedDescriptorById(id):
    return getDescriptorById(OnboardedDescriptor, id)


# Adding descriptors

def addUploadedDescriptor(body):
    descriptor = UploadedDescriptor(**body)
    descriptor.save()
    return descriptor


# Deleting descriptors

def deleteUploadedDescriptorById(id):
    """
    Deletes an uploaded descriptor by its ID, or returns a 404 error if no descriptor matching the
    given id exists.
    """
    try:
        descriptor = UploadedDescriptor.objects(id=id).get()
        descriptor.delete()
        return descriptor
    except DoesNotExist:
        return makeErrorResponse(404, "No descriptor matching the given id was found.")
