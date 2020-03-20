import connexion
from mongoengine.errors import DoesNotExist

from gatekeeper.models.descriptors import DescriptorType, UploadedDescriptor

NO_DESCRIPTOR_FOUND_MESSAGE = "No descriptor matching the given id was found."


# Uploaded descriptors

def getUploadedDescriptorsByType(type: DescriptorType):
    """
    Returns a QuerySet of uploaded descriptors of a given type.
    """
    return UploadedDescriptor.objects(type=type)


def getUploadedDescriptorById(id):
    """
    Returns a given uploaded descriptor by its ID, or a 404 error if no descriptor matching the
    given id exists.
    """
    try:
        return UploadedDescriptor.objects(id=id).get()
    except DoesNotExist:
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)


def addUploadedDescriptor(body):
    return UploadedDescriptor(**body).save(), 201


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
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)


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
        return connexion.problem(404, "Not Found", NO_DESCRIPTOR_FOUND_MESSAGE)
