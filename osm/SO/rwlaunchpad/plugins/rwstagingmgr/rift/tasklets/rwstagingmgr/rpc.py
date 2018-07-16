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
# Author(s): Varun Prasad
# Creation Date: 09/28/2016
#

import asyncio

import gi
gi.require_version("RwStagingMgmtYang", "1.0")
from gi.repository import (
   RwDts as rwdts,
   RwStagingMgmtYang)

import rift.mano.dts as mano_dts


# Shortcuts
RPC_STAGING_CREATE_ENDPOINT = RwStagingMgmtYang.YangOutput_RwStagingMgmt_CreateStagingArea


class StagingAreaCreateRpcHandler(mano_dts.AbstractRpcHandler):
    """RPC handler to generate staging Area"""

    def __init__(self, log, dts, loop, store):
        super().__init__(log, dts, loop)
        self.store = store

    @property
    def xpath(self):
        return "/rw-staging-mgmt:create-staging-area"

    @asyncio.coroutine
    def callback(self, ks_path, msg):
        """Forwards the request to proxy.
        """
        self.log.debug("Got a staging create request for {}".format(msg.as_dict()))
        staging_area = self.store.create_staging_area(msg)

        rpc_op = RPC_STAGING_CREATE_ENDPOINT.from_dict({
            "port": 4568,
            "endpoint": "api/upload/{}".format(staging_area.model.area_id)})

        return rpc_op
