
# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import time
import asyncio
import ncclient
import ncclient.asyncio_manager

from gi.repository import RwYang
class ProxyConnectionError(Exception):
    pass


class NcClient(object):
    '''Class representing a Netconf Session'''

    OPERATION_TIMEOUT_SECS = 240

    def __init__(self, host, port, username, password, loop):
        '''Initialize a new Netconf Session instance

        Arguments:
            host - host ip
            port - host port
            username - credentials for accessing the host, username
            password - credentials for accessing the host, password

        Returns:
            A newly initialized Netconf session instance
        '''
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.loop = loop
        self._nc_mgr = None

        self._model = RwYang.Model.create_libyang()

    @asyncio.coroutine
    def connect(self, timeout=240):
        '''Connect Netconf Session

        Arguments:
            timeout - maximum time allowed before connect fails [default 30s]
        '''
        # logger.info("Connecting to confd (%s) SSH port (%s)", self.host, self.port)
        if self._nc_mgr:
            return

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            try:
                self._nc_mgr = yield from ncclient.asyncio_manager.asyncio_connect(
                    loop=self.loop,
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    # Setting allow_agent and look_for_keys to false will skip public key
                    # authentication, and use password authentication.
                    allow_agent=False,
                    look_for_keys=False,
                    hostkey_verify=False)

                # logger.info("Successfully connected to confd (%s) SSH port (%s)", self.host, self.port)
                self._nc_mgr.timeout = NcClient.OPERATION_TIMEOUT_SECS
                return

            except ncclient.NCClientError as e:
                # logger.debug("Could not connect to (%s) confd ssh port (%s): %s",
                #         self.host, self.port, str(e))
                pass

            yield from asyncio.sleep(5, loop=self.loop)

        raise ProxyConnectionError("Could not connect to Confd ({}) ssh port ({}): within the timeout {} sec.".format(
                self.host, self.port, timeout))

    def convert_to_xml(self, module, yang_obj):
        schema =  getattr(module, "get_schema")
        self._model.load_schema_ypbc(schema())

        get_xml = getattr(yang_obj, "to_xml_v2")

        return get_xml(self._model)

    @property
    def manager(self):
        return self._nc_mgr
