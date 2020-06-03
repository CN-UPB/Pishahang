import stringcase

from connexion.exceptions import ProblemException
from gatekeeper.app import broker


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
            "type": vim["type"],
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
        raise ProblemException(title="Invalid request", detail=response["message"])


def addVim(body: dict):
    response = broker.call_sync(
        "infrastructure.management.compute.add",
        {stringcase.snakecase(key): value for key, value in body.items()},
    ).payload

    if response["request_status"] == "ERROR":
        raise ProblemException(title="Invalid request", detail=response["message"])
    return {"id": response["id"]}, 201
