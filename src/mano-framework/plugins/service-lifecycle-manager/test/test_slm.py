from pathlib import Path
from test.util import simple_async_endpoint
from uuid import uuid4

import pytest
import yaml
from syrupy.matchers import path_type

from manobase.messaging import AsyncioBrokerConnection as Connection
from manobase.messaging import Message
from slm import topics
from slm.exceptions import InstantiationError, PlacementError, TerminationError
from slm.slm import ServiceLifecycleManager

TEST_DIR = Path(__file__).parent
DESCRIPTORS_DIR = TEST_DIR / "descriptors"


def load_descriptor(filename: str):
    with (DESCRIPTORS_DIR / filename).with_suffix(".yml").open() as f:
        return yaml.safe_load(f)


SERVICE_DESCRIPTOR = load_descriptor("sonata-demo")
FUNCTION_DESCRIPTORS = [
    load_descriptor(f) for f in ["firewall-vnfd", "iperf-vnfd", "tcpdump-vnfd"]
]

# A static VIM ID so it can be used in snapshot testing
VIM_ID = "87ecdc7c-665a-475a-b4f7-f053706ceb70"

PLACEMENT = {function["uuid"]: {"vim": VIM_ID} for function in FUNCTION_DESCRIPTORS}


@pytest.fixture
def deploy_request():
    """
    The payload of a deploy request message like the gatekeeper sends it.
    """
    return {"nsd": SERVICE_DESCRIPTOR, "vnfds": FUNCTION_DESCRIPTORS}


@pytest.fixture
def topology(connection: Connection):
    """
    Mocks the Infrastructure Adapter's response to topology requests and yields the
    topology that the IA returns
    """
    topology = []

    with simple_async_endpoint(connection, topics.IA_TOPOLOGY, topology):
        yield topology


@pytest.fixture
def mocked_placement(connection: Connection):
    """
    Mocks the placement plugin's response to placement requests with the global
    `PLACEMENT` constant
    """
    with simple_async_endpoint(connection, topics.MANO_PLACE, {"mapping": PLACEMENT}):
        yield


@pytest.fixture
async def fetched_placement(manager: ServiceLifecycleManager, mocked_placement):
    """
    Makes the manager retrieve a placement using `manager._fetch_placement()` and the
    `mocked_placement` fixture
    """
    await manager._fetch_placement(topology=[])


@pytest.fixture(scope="function")
def manager(connection: Connection, mongo_connection, deploy_request):
    """
    A fully initialized ServiceLifecycleManager instance
    """

    manager = ServiceLifecycleManager.from_deploy_request(
        Message(
            topic=topics.MANO_DEPLOY,
            payload=deploy_request,
            correlation_id=str(uuid4()),
        ),
        connection,
    )

    # Fix the service instance id for snapshot tests
    manager.service.id = "f86d5ec7-1a93-404d-80d1-e696369f8318"
    manager.service.save()

    yield manager

    manager.service.delete()  # Delete the Service document from MongoDB


@pytest.mark.asyncio
async def test_fetch_topology(manager: ServiceLifecycleManager, topology):
    assert topology == await manager._fetch_topology()


@pytest.mark.asyncio
async def test_fetch_placement(
    manager: ServiceLifecycleManager, connection: Connection, snapshot_endpoint
):
    topic = topics.MANO_PLACE

    # Should send placement request that matches snapshot
    with snapshot_endpoint(
        topic,
        {"mapping": PLACEMENT},
        matcher=path_type(mapping={"functions": (list,), "nsd": (dict,)}, strict=True),
    ):
        await manager._fetch_placement(topology=[])

    # Should store the placement in the Service document and its Function documents
    assert PLACEMENT == manager.service.placement
    for function in manager.service.functions:
        assert str(function.vim) == VIM_ID

    # Should raise PlacementError if the returned mapping is ``None``
    with simple_async_endpoint(connection, topic, {"mapping": None}):
        with pytest.raises(PlacementError):
            await manager._fetch_placement(topology=[])


@pytest.mark.asyncio
async def test_prepare_infrastructure(
    manager: ServiceLifecycleManager,
    connection: Connection,
    fetched_placement,
    snapshot_endpoint,
):
    topic = topics.IA_PREPARE

    # Should send request that matches snapshot
    with snapshot_endpoint(topic, response={"request_status": "COMPLETED"}):
        await manager._prepare_infrastructure()

    # Should raise errors from the IA
    with simple_async_endpoint(
        connection, topic, {"request_status": "ERROR", "message": "failed"}
    ):
        with pytest.raises(InstantiationError, match="failed"):
            await manager._prepare_infrastructure()


@pytest.mark.asyncio
async def test_deploy_vnfs(
    manager: ServiceLifecycleManager,
    connection: Connection,
    fetched_placement,
    snapshot_endpoint,
):
    topic = topics.MANO_DEPLOY

    # Should send requests that match their snapshots
    with snapshot_endpoint(
        topic,
        response={"request_status": "COMPLETED", "vnfr": {"key": "value"}},
        matcher=path_type(mapping={"vnfd": (dict,)}, strict=True),
    ):
        await manager._deploy_vnfs()

    # Should raise errors from the IA
    with simple_async_endpoint(
        connection, topic, {"request_status": "ERROR", "message": "failed"}
    ):
        with pytest.raises(InstantiationError, match="failed"):
            await manager._deploy_vnfs()


@pytest.mark.asyncio
async def test_destroy_vnfs(
    manager: ServiceLifecycleManager, connection: Connection, snapshot_endpoint,
):
    topic = topics.IA_REMOVE

    # Should send request that matches snapshot
    with snapshot_endpoint(topic, response={"request_status": "COMPLETED"}):
        await manager._destroy_vnfs()

    # Should raise errors from the IA
    with simple_async_endpoint(
        connection, topic, {"request_status": "ERROR", "message": "failed"}
    ):
        with pytest.raises(TerminationError, match="failed"):
            await manager._destroy_vnfs()
