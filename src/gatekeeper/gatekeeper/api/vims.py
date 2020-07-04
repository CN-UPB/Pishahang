from gatekeeper.app import broker
from gatekeeper.exceptions import InternalServerError
from gatekeeper.util.casing import snakecaseDictKeys


def getVims():
    """
    Return the list of VIMs
    """
    return [
        {
            "id": vim["vim_uuid"],
            "name": vim["vim_name"],
            "country": vim["vim_country"],
            "city": vim["vim_city"],
            "type": vim["vim_type"].lower(),
            "coresTotal": vim["core_total"],
            "coresUsed": vim["core_used"],
            "memoryTotal": vim["memory_total"],
            "memoryUsed": vim["memory_used"],
        }
        for vim in broker.call_sync("infrastructure.management.compute.list").payload
    ]


def deleteVim(id: str):
    """
    Delete a VIM by id
    """
    response = broker.call_sync(
        "infrastructure.management.compute.remove", {"id": id}
    ).payload
    if response["request_status"] == "ERROR":
        raise InternalServerError(detail=response["message"])


def addVim(body: dict):
    response = broker.call_sync(
        "infrastructure.management.compute.add", snakecaseDictKeys(body)
    ).payload

    if response["request_status"] == "ERROR":
        raise InternalServerError(detail=response["message"])
    return {"id": response["id"]}, 201
