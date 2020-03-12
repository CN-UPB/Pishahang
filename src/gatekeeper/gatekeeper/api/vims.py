from typing import Type
from ..models.vims import (Vim, OpenStack, Kubernetes, Aws)
from mongoengine.errors import DoesNotExist
from ..util import makeMessageResponse
NO_DESCRIPTOR_FOUND_MESSAGE = "No descriptor matching the given id was found."


# Getting the Added Vims
def getAllVims():
    """
    Returns the list of added Vims.
    """
    return getVims(Vim)


def getVims(vimClass: Type[Vim]):
    """
    Returns all subset of Vims
    """
    return vimClass.objects()

# Deleting Vim


def deleteVim(id):
    """
    Returns the list of added Vims.
    """
    return deleteVimById(Vim, id)


def deleteVimById(vimClass: Type[Vim], id):
    """
    Deletes a Vim by its ID, or returns a 404 error if no Vim matching the
    given id exists.
    """
    try:
        vim = vimClass.objects(id=id).get()
        vim.delete()
        return vim
    except DoesNotExist:
        return makeMessageResponse(404, NO_DESCRIPTOR_FOUND_MESSAGE)

# Update VIm


def updateAwsVim(id, body):
    """
    Update Vim by its id
    """
    return updateAwsVimByID(Aws, id, body)


def updateAwsVimByID(awsClass: Type[Aws], id, body):
    vim: Aws = awsClass.objects(id=id).get()
    vim = Aws(**body).save()
    return vim


# ADD vim
def addVim(body):
    if body["type"] == "aws":
        vim = Aws(**body).save()
        return vim
    elif body["type"] == "kubernetes":
        vim = Kubernetes(**body).save()
        return vim
    elif body["type"] == "OpenStack":
        vim = OpenStack(**body).save()
        return vim
