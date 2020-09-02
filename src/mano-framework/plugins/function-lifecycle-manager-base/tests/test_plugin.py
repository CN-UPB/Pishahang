import pytest
from pytest_voluptuous import Partial, S

from flm_base.plugin import FunctionLifecycleManagerBasePlugin
from manobase.messaging import AsyncioBrokerConnection as Connection
from manobase.messaging import Message
from manobase.messaging.util import async_endpoint

DEPLOY_TOPIC_NORTH = FunctionLifecycleManagerBasePlugin.northbound_topics["deploy"]
DEPLOY_TOPIC_SOUTH = FunctionLifecycleManagerBasePlugin.southbound_topics["deploy"]


@pytest.mark.asyncio
async def test_instantiation(
    instance: FunctionLifecycleManagerBasePlugin,
    connection: Connection,
    mocker,
    reraise,
):
    # Mock repository.post
    mocked_post = mocker.patch("flm_base.plugin.repository.post")

    is_vim_adaptor_response_error = False

    def on_vim_adaptor_deploy(message: Message):
        with reraise(catch=True):
            assert (
                S(
                    {
                        "function_instance_id": str,
                        "service_instance_id": str,
                        "vim_id": str,
                        "vnfd": Partial({"id": str}),
                    }
                )
                == message.payload
            )

        return (
            {"request_status": "ERROR", "message": "error-message"}
            if is_vim_adaptor_response_error
            else {"request_status": "COMPLETED", "vnfr": {"id": "my-vnfr"}}
        )

    with async_endpoint(connection, DEPLOY_TOPIC_SOUTH, on_vim_adaptor_deploy):
        DEPLOY_MESSAGE = {
            "function_instance_id": "FIID",
            "service_instance_id": "SIID",
            "vim_id": "VIMID",
            "vnfd": {"id": "my-vnfd"},
        }

        # A deploy request should be handled successfully when the VIM adaptor replies
        # with a success message
        assert {"status": "SUCCESS"} == (
            await connection.call(DEPLOY_TOPIC_NORTH, DEPLOY_MESSAGE)
        ).payload

        # The VNF record should have been posted to the repository
        mocked_post.assert_called_once()

        # A deploy request should fail when the VIM adaptor replies with an error
        # message
        is_vim_adaptor_response_error = True
        assert {"status": "ERROR", "error": "error-message"} == (
            await connection.call(DEPLOY_TOPIC_NORTH, DEPLOY_MESSAGE)
        ).payload
