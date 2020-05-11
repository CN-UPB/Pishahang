from gatekeeper.app import broker


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
        "vim_uuid": "vimUuid",
    }
    getVim = []
    for x in range(len(vim)):
        a = dict([(renameKey.get(k), v) for k, v in vim[x].items()])
        getVim.append(a)
    return getVim


def deleteVim(id):
    """
    Delete A VIM by giving its uuid.
    """
    return broker.call_sync_simple(
        "infrastructure.management.compute.remove", msg={"uuid": id}
    )


def addVim(body):

    if body["type"] == "kubernetes":
        addVim = {
            "vim_type": "Kubernetes",
            "configuration": {"cluster_ca_cert": body["ccc"]},
            "city": body["vimCity"],
            "name": body["vimName"],
            "country": body["country"],
            "vim_address": body["vimAddress"],
            "pass": body["serviceToken"],
        }
        return broker.call_sync_simple(
            "infrastructure.management.compute.add", msg=addVim
        )

    elif body["type"] == "openStack":
        addVim = {
            "vim_type": "heat",
            "configuration": {
                "tenant_ext_router": body["tenantExternalRouterId"],
                "tenant_ext_net": body["tenantExternalNetworkId"],
                "tenant": body["tenantId"],
            },
            "city": body["city"],
            "name": body["vimName"],
            "country": body["country"],
            "vim_address": body["vimAddress"],
            "username": body["username"],
            "pass": body["password"],
            "domain": "Default",
        }
        return broker.call_sync_simple(
            "infrastructure.management.compute.add", msg=addVim
        )
