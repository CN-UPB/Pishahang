from mongoengine.errors import DoesNotExist

from connexion.exceptions import ProblemException
from gatekeeper.app import broker
from gatekeeper.models.vims import Aws, Kubernetes, OpenStack, Vim

NO_Vim_FOUND_MESSAGE = "No Vim matching the given id was found."


# Getting the VIMs

def getAllVims():
    """
    Returns the list of added Vims.
    """
    # return Vim.objects()
    vim = broker.call_sync_simple("infrastructure.management.compute.list")
    # return vim
    renameKey = {
        "core_total": "coreTotal",
        "core_used": "coreUsed",
        "memory_total": "memoryTotal",
        "memory_used": "memoryUsed",
        "vim_city": "vimCity",
        "vim_domain": "vimDomain",
        "vim_endpoint": "vimEndpoint",
        "vim_name": "vimName",
        "vim_type": "vimType",
        "vim_uuid": "vimUuid"
    }
    getVim = []
    for x in range(len(vim)):
        a = dict([(renameKey.get(k), v) for k, v in vim[x].items()])
        getVim.append(a)
    return getVim


# Deleting Vim

def deleteVim(id):
    """
    Delete A VIM by giving its uuid.
    """
    # try:
    #     vim = Vim.objects(id=id).get()
    #     vim.delete()
    return broker.call_sync_simple("infrastructure.management.compute.remove",
                                   msg={"uuid": id})
    # except DoesNotExist:
    #     raise ProblemException(404, "Not Found", NO_Vim_FOUND_MESSAGE)


# ADD vim

def addVim(body):

    if body["type"] == "aws":
        vim = Aws(**body).save()
        return vim
    elif body["type"] == "kubernetes":
        vim = Kubernetes(**body).save()
        addVim = {"vim_type": "Kubernetes", "configuration":
                                            {"cluster_ca_cert": body["ccc"]},
                                            "city": body["vimCity"],
                                            "name": body["vimName"], "country": body["country"],
                                            "vim_address": body["vimAddress"],
                                            "pass": body["serviceToken"]}
        return broker.call_sync_simple("infrastructure.management.compute.add", msg=addVim)

    elif body["type"] == "openStack":
        vim = OpenStack(**body).save()
        addVim = {"vim_type": "heat", "configuration":
                  {"tenant_ext_router": body["tenantExternalRouterId"],
                   "tenant_ext_net": body["tenantExternalNetworkId"],
                   "tenant": body["tenantId"]}, "city": body["city"],
                  "name": body["vimName"], "country": body["country"],
                  "vim_address": body["vimAddress"],
                  "username": body["username"], "pass": body["password"],
                  "domain": "Default"}
        returnValue = broker.call_sync_simple("infrastructure.management.compute.add",
                                              msg=addVim)
        return dict([(renameKey.get(k), v) for k, v in returnValue[0].items()])
