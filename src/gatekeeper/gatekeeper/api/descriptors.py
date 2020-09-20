from mongoengine.errors import DoesNotExist, NotUniqueError

from gatekeeper.exceptions import DescriptorNotFoundError, DuplicateDescriptorError
from gatekeeper.models.descriptors import Descriptor, DescriptorType


def getDescriptorsByType(user, type: DescriptorType):
    """
    Returns all descriptors of a given type.
    """
    return Descriptor.objects(userId=user, type=type)


def getDescriptorById(user, id):
    """
    Returns a given descriptor by its ID, or a 404 error if no descriptor matching the
    given id exists.
    """
    try:
        return Descriptor.objects(userId=user, id=id).get()
    except DoesNotExist:
        raise DescriptorNotFoundError()


def addDescriptor(user, body):
    try:
        return Descriptor(**body, userId=user).save(), 201
    except NotUniqueError:
        raise DuplicateDescriptorError()


def updateDescriptor(user, id, body):
    """
    Updates a given descriptor's content by its ID, or returns a 404 error if no
    descriptor matching the given id exists.
    """
    try:
        descriptor: Descriptor = Descriptor.objects(userId=user, id=id).get()
        descriptor.content = body["content"]

        if "contentString" in body:
            descriptor.contentString = body["contentString"]

        descriptor.save()
        return descriptor
    except DoesNotExist:
        raise DescriptorNotFoundError()
    except NotUniqueError:
        raise DuplicateDescriptorError()


def deleteDescriptorById(user, id):
    """
    Deletes a descriptor by its ID, or returns a 404 error if no descriptor matching the
    given id exists.
    """
    try:
        descriptor = Descriptor.objects(userId=user, id=id).get()
        descriptor.delete()
        return descriptor
    except DoesNotExist:
        raise DescriptorNotFoundError()
