import requests
from config2.config import config

from gatekeeper.exceptions import InternalServerError, PluginNotFoundError

PLUGINMANAGER_API_URL = config.internalApis.pluginmanager


def _getPluginById(id):
    response = requests.get(PLUGINMANAGER_API_URL + "/" + id)
    if response.status_code == 404:
        raise PluginNotFoundError(id)

    plugin = response.json()

    # Map field names
    fieldNameMap = {
        "uuid": "id",
        "last_heartbeat_at": "lastHeartbeatAt",
        "registered_at": "registeredAt"
    }
    for originalFieldName, newFieldName in fieldNameMap.items():
        plugin[newFieldName] = plugin.pop(originalFieldName)

    return plugin


def getPlugins():
    pluginIds = requests.get(PLUGINMANAGER_API_URL).json()
    return [_getPluginById(id) for id in pluginIds]


def getPluginById(id):
    return _getPluginById(id)


def _validateRequestStatus(status, pluginId):
    """
    Depending on a plugin manager response status code, either raise an appropriate exception or
    return.
    """
    if status != 200:
        if status == 404:
            raise PluginNotFoundError(pluginId)
        raise InternalServerError(
            detail="The plugin manager replied with status code '{:d}'".format(status)
        )


def shutdownPluginById(id):
    status = requests.delete(PLUGINMANAGER_API_URL + "/" + id).status_code
    _validateRequestStatus(status, id)


def changePluginStateById(id, body):
    status = requests.put(
        "{}/{}/lifecycle".format(PLUGINMANAGER_API_URL, id),
        json={"target_state": body["targetState"]}
    ).status_code
    _validateRequestStatus(status, id)
