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
import mock
import os
import sys
import unittest
import uuid
import xmlrunner

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

gi.require_version('RwDts', '1.0')
gi.require_version('RwPkgMgmtYang', '1.0')
from gi.repository import (
        RwDts as rwdts,
        RwPkgMgmtYang
        )
import rift.tasklets.rwpkgmgr.downloader as downloader
import rift.tasklets.rwpkgmgr.publisher as pkg_publisher
import rift.test.dts
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class TestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
        return RwPkgMgmtYang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)
        self.project = ManoProject(self.log, name=DEFAULT_PROJECT)

        self.job_handler = pkg_publisher.DownloadStatusPublisher(self.log, self.dts,
                                                                 self.loop, self.project)

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
        published_xpaths = yield from self.get_published_xpaths()
        assert self.job_handler.xpath() in published_xpaths

    @rift.test.dts.async_test
    def test_publish(self):
        """
        Asserts:
            1. Verify if an update on_download_progess & on_download_finished
               triggers a DTS update
            2. Verify if the internal store is updated
        """
        yield from self.job_handler.register()

        mock_msg = RwPkgMgmtYang.YangData_RwProject_Project_DownloadJobs_Job.from_dict({
                "url": "http://foo/bar",
                "package_id": "123",
                "download_id": str(uuid.uuid4())})

        yield from self.job_handler._dts_publisher(mock_msg)
        yield from asyncio.sleep(5, loop=self.loop)

        xpath = self.project.add_project("/download-jobs/job[download-id={}]".
                                         format(quoted_key(mock_msg.download_id)))
        itr = yield from self.dts.query_read(xpath)

        result = None
        for fut in itr:
            result = yield from fut
            result = result.result

        self.log.debug("Mock msg: {}".format(mock_msg))
        assert result == mock_msg

        # Modify the msg
        mock_msg.url = "http://bar/foo"
        yield from self.job_handler._dts_publisher(mock_msg)
        yield from asyncio.sleep(5, loop=self.loop)

        itr = yield from self.dts.query_read(xpath)

        result = None
        for fut in itr:
            result = yield from fut
            result = result.result
        assert result == mock_msg


    @rift.test.dts.async_test
    def test_url_download(self):
        """
        Integration Test:
            Test the updates with download/url.py
        """
        yield from self.job_handler.register()

        proxy = mock.MagicMock()

        url = "http://sharedfiles/common/unittests/plantuml.jar"
        url_downloader = downloader.PackageFileDownloader(url, "1", "/", "VNFD", "SCRIPTS", "VNF_CONFIG", proxy)

        download_id = yield from self.job_handler.register_downloader(url_downloader)
        assert download_id is not None
       
        # Waiting for 5 secs to be sure that the file is downloaded
        yield from asyncio.sleep(10, loop=self.loop)
        xpath = self.project.add_project("/download-jobs/job[download-id={}]".format(
            quoted_key(download_id)))
        result = yield from self.read_xpath(xpath)
        self.log.debug("Test result before complete check - %s", result)
        assert result.status == "COMPLETED"
        assert len(self.job_handler.tasks) == 0

    @rift.test.dts.async_test
    def test_url_download_unreachable_ip(self):
        """
        Integration Test:
            Ensure that a bad IP does not block forever
        """
        yield from self.job_handler.register()

        proxy = mock.MagicMock()

        # Here, we are assuming that there is no HTTP server at 10.1.2.3
        url = "http://10.1.2.3/common/unittests/plantuml.jar"
        url_downloader = downloader.PackageFileDownloader(url, "1", "/", "VNFD", "SCRIPTS", "VNF_CONFIG", proxy)
        self.log.debug("Downloader url: {}".format(url_downloader))

        download_id = yield from self.job_handler.register_downloader(url_downloader)
        self.log.debug("Download id: {}".format(download_id))
        assert download_id is not None

        # Waiting for 60 secs to be sure all reconnect attempts have been exhausted
        yield from asyncio.sleep(60, loop=self.loop)
        xpath = self.project.add_project("/download-jobs/job[download-id={}]".
                                         format(quoted_key(download_id)))
        result = yield from self.read_xpath(xpath)
        self.log.debug("Test result before complete check - %s", result)
        assert result.status == "FAILED"
        assert len(self.job_handler.tasks) == 0


    @rift.test.dts.async_test
    def test_cancelled(self):
        """
        Integration Test:
            1. Test the updates with downloader.py
            2. Verifies if cancel triggers the job status to move to cancelled
        """
        yield from self.job_handler.register()

        proxy = mock.MagicMock()
        url = "http://sharedfiles/common/unittests/Fedora-x86_64-20-20131211.1-sda-ping.qcow2"
        url_downloader = downloader.PackageFileDownloader(url, "1", "/", "VNFD", "SCRIPTS", "VNF_CONFIG", proxy)

        download_id = yield from self.job_handler.register_downloader(url_downloader)
        assert download_id is not None
        xpath = self.project.add_project("/download-jobs/job[download-id={}]".
                                         format(quoted_key(download_id)))

        # wait long enough to have the state be in IN_PROGRESS
        yield from asyncio.sleep(0.2, loop=self.loop)

        result = yield from self.read_xpath(xpath)
        self.log.debug("Test result before in_progress check - %s", result)
        assert result.status == "IN_PROGRESS" 

        yield from self.job_handler.cancel_download(download_id)
        yield from asyncio.sleep(3, loop=self.loop)
        result = yield from self.read_xpath(xpath)
        self.log.debug("Test result before cancel check - %s", result)
        assert result.status == "CANCELLED"
        assert len(self.job_handler.tasks) == 0


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
