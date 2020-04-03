from typing import Type

from mongoengine.errors import DoesNotExist

from connexion.exceptions import ProblemException
from gatekeeper.models.vims import Aws, Kubernetes, OpenStack, Vim

NO_Vim_FOUND_MESSAGE = "No Vim matching the given id was found."


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
    Delete A VIM by giving its uuid.
    """
    try:
        vim = Vim.objects(id=id).get()
        vim.delete()
        return vim
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_Vim_FOUND_MESSAGE)


# Update VIm


def updateAwsVim(id, body):
    """
    Update Vim by its id
    """
    try:
        vim = Aws.objects(id=id).get()
        secretKey = body.get("secretKey")
        accessKey = body.get("accessKey")
        vim.update({"accessKey": accessKey, "secretKey": secretKey})
        return vim
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_Vim_FOUND_MESSAGE)


# ADD vim

def addVim(body):
    if body["type"] == "aws":
        vim = Aws(**body).save()
    elif body["type"] == "kubernetes":
        vim = Kubernetes(**body).save()
    elif body["type"] == "openStack":
        vim = OpenStack(**body).save()
    return vim
