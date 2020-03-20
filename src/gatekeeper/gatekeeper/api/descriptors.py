import connexion
from mongoengine.errors import DoesNotExist

from gatekeeper.models.descriptors import DescriptorType, Descriptor

NO_DESCRIPTOR_FOUND_MESSAGE = "No descriptor matching the given id was found."


def getDescriptorsByType(type: DescriptorType):
    """
    Returns all descriptors of a given type.
    """
    return Descriptor.objects(type=type)


def getDescriptorById(id):
    """
    Returns a given descriptor by its ID, or a 404 error if no descriptor matching the
    given id exists.
    """
    try:
        return Descriptor.objects(id=id).get()
    except DoesNotExist:
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)


def addDescriptor(body):
    return Descriptor(**body).save(), 201


def updateDescriptor(id, body):
    """
    Updates a given descriptor by its ID, or returns a 404 error if no descriptor matching the given
    id exists.
    """
    try:
        descriptor: Descriptor = Descriptor.objects(id=id).get()
        descriptor.descriptor = body["descriptor"]
        descriptor.save()
        return descriptor
    except DoesNotExist:
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)


def deleteDescriptorById(id):
    """
    Deletes a descriptor by its ID, or returns a 404 error if no descriptor matching the given id
    exists.
    """
    try:
        descriptor = Descriptor.objects(id=id).get()
        descriptor.delete()
        return descriptor
    except DoesNotExist:
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)
