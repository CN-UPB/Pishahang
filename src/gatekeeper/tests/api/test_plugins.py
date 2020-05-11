from gatekeeper.api.plugins import PLUGINMANAGER_API_URL


def makeResponse(pluginId):
    return {
        "description": "",
        "last_heartbeat_at": "",
        "name": "",
        "registered_at": "",
        "state": "",
        "uuid": pluginId,
        "version": "v0.02",
    }


def makeConvertedResponse(pluginId):
    return {
        "description": "",
        "lastHeartbeatAt": "",
        "name": "",
        "registeredAt": "",
        "state": "",
        "id": pluginId,
        "version": "v0.02",
    }


def testGetPluginById(api, requests_mock):
    requests_mock.get(PLUGINMANAGER_API_URL + "/nonexistentId", status_code=404)
    assert 404 == api.get("/api/v3/plugins/nonexistentId").status_code

    requests_mock.get(PLUGINMANAGER_API_URL + "/myId", json=makeResponse("myId"))
    response = api.get("/api/v3/plugins/myId")
    assert 200 == response.status_code
    assert makeConvertedResponse("myId") == response.get_json()


def testGetPlugins(api, requests_mock):
    ids = ["id1", "id2"]

    requests_mock.get(PLUGINMANAGER_API_URL, json=ids)
    for id in ids:
        requests_mock.get(PLUGINMANAGER_API_URL + "/" + id, json=makeResponse(id))

    response = api.get("/api/v3/plugins")
    assert 200 == response.status_code
    assert [makeConvertedResponse(id) for id in ids] == response.get_json()


def testShutdownPluginById(api, requests_mock):
    for status in [500, 404]:
        requests_mock.delete(PLUGINMANAGER_API_URL + "/myId", status_code=status)
        assert status == api.delete("/api/v3/plugins/myId").status_code

    requests_mock.delete(PLUGINMANAGER_API_URL + "/myId", status_code=200)
    assert 204 == api.delete("/api/v3/plugins/myId").status_code


def testChangePluginStateById(api, requests_mock):
    def pluginManagerMock(request, context):
        assert {"target_state": "pause"} == request.json()

    requests_mock.put(PLUGINMANAGER_API_URL + "/myId/lifecycle", json=pluginManagerMock)

    assert (
        204
        == api.put(
            "/api/v3/plugins/myId/lifecycle", json={"targetState": "pause"}
        ).status_code
    )
