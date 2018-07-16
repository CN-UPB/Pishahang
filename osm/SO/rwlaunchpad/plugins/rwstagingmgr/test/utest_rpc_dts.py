#!/usr/bin/env python3

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

import asyncio
import argparse
import os
import shutil
import sys
import unittest
import uuid
import xmlrunner
import mock
import uuid

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwDts as rwdts,
        RwStagingMgmtYang,
        )


import rift.tasklets.rwstagingmgr.rpc as rpc
import rift.test.dts


class TestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
        return RwStagingMgmtYang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

    def tearDown(self):
        super().tearDown()

    @rift.test.dts.async_test
    def test_staging_area_create(self):
        """
        Verifies the following:
            The endpoint RPC returns a URL
        """
        uid = str(uuid.uuid4())
        mock_model = mock.MagicMock()
        mock_model.model.area_id = uid
        mock_store = mock.MagicMock()
        mock_store.create_staging_area.return_value = mock_model

        endpoint = rpc.StagingAreaCreateRpcHandler(self.log, self.dts, self.loop, mock_store)
        yield from endpoint.register()

        yield from asyncio.sleep(2, loop=self.loop)

        ip = RwStagingMgmtYang.YangInput_RwStagingMgmt_CreateStagingArea.from_dict({
                "package_type": "VNFD"})

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-staging-mgmt:create-staging-area",
                    rwdts.XactFlag.TRACE,
                    ip)

        for itr in rpc_out:
            result = yield from itr
            print (result)
            assert uid in result.result.endpoint

def main():
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None


    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()
