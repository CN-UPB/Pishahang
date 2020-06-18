from uuid import uuid4

from pytest_voluptuous import S

from manobase.messaging import ManoBrokerRequestResponseConnection as Connection
from manobase.messaging import Message


def testAddVim(api, broker: Connection, reraise):
    id = str(uuid4())  # VIM uuid returned by the vim-adaptor mock

    baseVimData = {
        "city": "my city",
        "country": "my country",
        "name": "my name",
    }

    vimData = {
        "aws": {
            **baseVimData,
            "type": "aws",
            "accessKey": "access key",
            "secretKey": "secret key",
        },
        "kubernetes": {
            **baseVimData,
            "type": "kubernetes",
            "serviceToken": "service token",
            "address": "address",
            "ccc": "ccc",
        },
        "openstack": {
            **baseVimData,
            "type": "openstack",
            "address": "address",
            "tenant": {
                "id": "tenant id",
                "externalNetworkId": "tenant external network id",
                "externalRouterId": "tenant external router id",
            },
            "username": "my username",
            "password": "my password",
        },
    }

    vimAdaptorResponse = {"request_status": "COMPLETED", "id": id}

    # Mock vim adaptor
    def onAddVimRequest(message: Message):
        with reraise(catch=True):
            # baseVimData should be contained in the payload
            assert S(baseVimData) <= message.payload

        return vimAdaptorResponse

    broker.register_async_endpoint(
        onAddVimRequest, "infrastructure.management.compute.add"
    )

    # Add all types of vims
    for data in vimData.values():
        reply = api.post("/api/v3/vims", json=data)
        assert 201 == reply.status_code
        assert {"id": id} == reply.get_json()

    # Let the mock vim adaptor reply with an error
    vimAdaptorResponse = {"request_status": "ERROR", "message": "error message"}
    reply = api.post("/api/v3/vims", json=vimData["aws"])
    assert 500 == reply.status_code
    assert "error message" == reply.get_json()["detail"]


def testDeleteVim(api, broker: Connection, reraise):
    id = str(uuid4())

    vimAdaptorResponse = {"request_status": "SUCCESS"}

    # Mock vim adaptor
    def onDeleteVimRequest(message: Message):
        with reraise(catch=True):
            assert {"id": id} == message.payload

        return vimAdaptorResponse

    broker.register_async_endpoint(
        onDeleteVimRequest, "infrastructure.management.compute.remove"
    )

    # Test successful deletion
    assert 204 == api.delete("/api/v3/vims/" + id).status_code

    # Test vim adaptor error response
    vimAdaptorResponse = {"request_status": "ERROR", "message": "error message"}
    reply = api.delete("/api/v3/vims/" + id)
    assert 500 == reply.status_code
    assert "error message" == reply.get_json()["detail"]


def testGetVims(api, broker: Connection):
    # Mock vim adaptor
    broker.register_async_endpoint(
        lambda message: [
            {
                "vim_uuid": "id",
                "vim_name": "name",
                "vim_country": "country",
                "vim_city": "city",
                "vim_type": "type",
                "core_total": 4,
                "core_used": 3,
                "memory_total": 2,
                "memory_used": 1,
            }
        ],
        "infrastructure.management.compute.list",
    )

    response = api.get("/api/v3/vims")
    assert 200 == response.status_code
    assert [
        {
            "id": "id",
            "name": "name",
            "country": "country",
            "city": "city",
            "type": "type",
            "coresTotal": 4,
            "coresUsed": 3,
            "memoryTotal": 2,
            "memoryUsed": 1,
        }
    ] == response.get_json()
