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

import argparse
import asyncio
import gi
import logging
import os
import sys
import unittest
import uuid
import xmlrunner

gi.require_version('RwDts', '1.0')
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwDts as rwdts,
        RwStagingMgmtYang
        )
import rift.tasklets.rwstagingmgr.publisher as publisher
import rift.test.dts
from rift.mano.utils.project import ManoProject
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class TestProject(ManoProject):
    def __init__(self, log, dts, loop):
        super().__init__(log)
        self._dts = dts
        self._loop = loop


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
        self.project = TestProject(self.log, self.dts, self.loop)

        self.job_handler = publisher.StagingStorePublisher(self.project)

    def tearDown(self):
        super().tearDown()

    @asyncio.coroutine
    def get_published_xpaths(self):
        published_xpaths = set()

        res_iter = yield from self.dts.query_read("D,/rwdts:dts")
        for i in res_iter:
            res = (yield from i).result
            for member in res.member:
                published_xpaths |= {reg.keyspec for reg in member.state.registration if reg.flags == "publisher"}

        return published_xpaths

    @asyncio.coroutine
    def read_xpath(self, xpath):
        itr = yield from self.dts.query_read(xpath)

        result = None
        for fut in itr:
            result = yield from fut
            return result.result

    @rift.test.dts.async_test
    def test_download_publisher(self):
        yield from self.job_handler.register()
        yield from asyncio.sleep(2, loop=self.loop)
        published_xpaths = yield from self.get_published_xpaths()
        assert self.job_handler.xpath() in published_xpaths
        self.job_handler.deregister()

    @rift.test.dts.async_test
    def test_publish(self):
        """
        """
        yield from self.job_handler.register()

        mock_msg = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict({
                "area_id": "123"})

        self.job_handler.on_staging_area_create(mock_msg)
        yield from asyncio.sleep(5, loop=self.loop)

        xpath = self.project.add_project("/staging-areas/staging-area[area-id={}]".
                                         format(quoted_key(mock_msg.area_id)))
        itr = yield from self.dts.query_read(xpath)


        result = None
        for fut in itr:
            result = yield from fut
            result = result.result

        print (result)
        assert result == mock_msg
        self.job_handler.deregister()

def main():
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None

    TestCase.log_level = logging.DEBUG if args.verbose else logging.WARN

    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()
