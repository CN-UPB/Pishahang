from gatekeeper.app import broker

# from gatekeeper.models.vims import Vim


def getAllVims():
    """
    Returns the list of added Vims.
    """
    # return Vim.objects()
    vim = broker.call_sync("infrastructure.management.compute.list")
    # return vim
    # renameKey = {
    #     "core_total": "coreTotal",
    #     "core_used": "coreUsed",
    #     "memory_total": "memoryTotal",
    #     "memory_used": "memoryUsed",
    #     "vim_city": "vimCity",
    #     "vim_domain": "vimDomain",
    #     "vim_endpoint": "vimEndpoint",
    #     "vim_name": "vimName",
    #     "vim_type": "vimType",
    #     "vim_uuid": "vimUuid",
    # }
    # getVim = []
    # for x in range(len(vim)):
    #     a = dict([(renameKey.get(k), v) for k, v in vim[x].items()])
    #     getVim.append(a)
    return vim


def deleteVim(id):
    """
    Delete A VIM by giving its uuid.
    """
    return broker.call_sync("infrastructure.management.compute.remove", {"uuid": id})


def addVim(body):

    if body["type"] == "openStack":
        broker.call_sync(
            "infrastructure.management.compute.add",
            {
                "name": body["vimName"],
                "country": body["country"],
                "vimCity": body["vimCity"],
                "vimAddress": body["vimAddress"],
                "tenantId": body["tenantId"],
                "tenantExternalNetworkId": body["tenantExternalNetworkId"],
                "tenantExternalRouterId": body["tenantExternalRouterId"],
                "username": body["username"],
                "password": body["password"],
                "type": body["type"],
            },
        )

    elif body["type"] == "kubernetes":
        broker.call_sync(
            "infrastructure.management.compute.add",
            {
                "type": body["type"],
                "city": body["vimCity"],
                "name": body["vimName"],
                "country": body["country"],
                "vimAddress": body["vimAddress"],
                "serviceToken": body["serviceToken"],
                "ccc": body["ccc"],
            },
        )
    elif body["type"] == "aws":
        broker.call_sync(
            "infrastructure.management.compute.add",
            {
                "type": body["type"],
                "city": body["vimCity"],
                "name": body["vimName"],
                "country": body["country"],
                "accessKey": body["accessKey"],
                "secretKey": body["secretKey"],
            },
        )
