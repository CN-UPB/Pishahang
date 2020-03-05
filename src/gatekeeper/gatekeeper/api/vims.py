from ..models import OpenStack


def openStack(body):

    vimAddress = body.get("vimAddress")
    tenantId = body.get("tenantId")
    tenantExternalNetworkId = body.get("tenantExternalNetworkId")
    tenantExternalRouterId = body.get("tenantExternalRouterId")
    username = body.get("username")
    password = body.get("password")
    return {"Vim Address": vimAddress, "Tenant ID": tenantId, "Tenant External Network Id": tenantExternalNetworkId,
            "Tenant External Router ID": tenantExternalRouterId, "User Name": username, "Password": password}


def kubernetes(body):
    vimAddress = body.get("vimAddress")
    serviceToken = body.get("serviceToken")
    ccc = body.get("ccc")
    return {"Vim Address": vimAddress, "Service Token": serviceToken, "CCC": ccc}


def aws(body):
    secretKey = body.get("secretKey")

    return {"Secret Key": secretKey}
