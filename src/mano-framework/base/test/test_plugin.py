"""
Copyright (c) 2017 Pishahang
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of Pishahang, nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.
"""

from threading import Event
from uuid import uuid4

import pytest
from pytest_voluptuous import S
from voluptuous import All, In, Length

from manobase.messaging import ManoBrokerRequestResponseConnection as Connection
from manobase.messaging import Message
from manobase.plugin import ManoBasePlugin

PLUGIN_UUID = str(uuid4())


@pytest.fixture(scope="module")
def connection():
    connection = Connection("test-connection", is_loopback=True)

    yield connection
    connection.close()


def test_registration_and_heartbeat(connection: Connection, reraise):
    registration_request_received = Event()

    def on_registration_request(message: Message):
        """
        When the registration request from the plugin is received, this method replies
        as if it were the plugin manager
        """
        with reraise:
            non_empty_string = All(str, Length(min=1))
            assert (
                S(
                    {
                        "name": non_empty_string,
                        "version": non_empty_string,
                        "description": non_empty_string,
                    }
                )
                == message.payload
            )
        return {"status": "OK", "uuid": PLUGIN_UUID}

    heartbeat_received = Event()

    def on_heartbeat(message: Message):
        with reraise:
            assert (
                S(
                    {
                        "uuid": PLUGIN_UUID,
                        "state": In(("READY", "RUNNING", "PAUSED", "FAILED")),
                    }
                )
                == message.payload
            )
        heartbeat_received.set()

    connection.register_async_endpoint(
        on_registration_request, "platform.management.plugin.register"
    )
    connection.subscribe(
        on_heartbeat, "platform.management.plugin." + PLUGIN_UUID + ".heartbeat",
    )

    plugin = ManoBasePlugin(
        use_loopback_connection=True, version="1.2.3", description="Test Plugin",
    )

    try:
        registration_request_received.wait(1)
        heartbeat_received.wait(1)

        assert plugin.uuid == PLUGIN_UUID
    finally:
        plugin.conn.close()
