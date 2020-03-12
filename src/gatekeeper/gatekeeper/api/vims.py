from typing import Type
from ..models import (Vim, OpenStack, Kubernetes, Aws, VimType)
from mongoengine.errors import DoesNotExist
from ..util import makeErrorResponse
NO_DESCRIPTOR_FOUND_MESSAGE = "No descriptor matching the given id was found."


# Add Vim
def addopenStack(body):
    vim = OpenStack(**body)
    vim.save()
    return vim


def addkubernetes(body):
    vim = Kubernetes(**body)
    vim.save()
    return vim


def addaws(body):
    vim = Aws(**body).save()
    return vim

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
        return makeErrorResponse(404, NO_DESCRIPTOR_FOUND_MESSAGE)

# Update VIm


def updateVim(id):
    """
    Update Vim by its id
    """
    pass
