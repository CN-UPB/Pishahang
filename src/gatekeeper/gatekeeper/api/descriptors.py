from typing import Type

from mongoengine.errors import DoesNotExist

from ..models import (Descriptor, DescriptorType, OnboardedDescriptor,
                      UploadedDescriptor)
from ..util import makeMessageResponse

NO_DESCRIPTOR_FOUND_MESSAGE = "No descriptor matching the given id was found."


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
        return descriptorClass.objects(id=id).get()
    except DoesNotExist:
        return makeMessageResponse(404, NO_DESCRIPTOR_FOUND_MESSAGE)


def getUploadedDescriptorById(id):
    return getDescriptorById(UploadedDescriptor, id)


def getOnboardedDescriptorById(id):
    return getDescriptorById(OnboardedDescriptor, id)


# Adding descriptors

def addUploadedDescriptor(body):
    return UploadedDescriptor(**body).save()


# Updating descriptors

def updateUploadedDescriptor(id, body):
    """
    Updates a given descriptor by its ID, or returns a 404 error if no descriptor matching the given
    id exists.
    """
    try:
        descriptor: UploadedDescriptor = UploadedDescriptor.objects(id=id).get()
        descriptor.descriptor = body["descriptor"]
        descriptor.save()
        return descriptor
    except DoesNotExist:
        return makeMessageResponse(404, NO_DESCRIPTOR_FOUND_MESSAGE)


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
        return makeMessageResponse(404, NO_DESCRIPTOR_FOUND_MESSAGE)
