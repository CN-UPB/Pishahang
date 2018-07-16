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
import logging
import os
import sys
import unittest
import xmlrunner

import rift.downloader as downloader

TEST_URL = "https://raw.githubusercontent.com/RIFTIO/RIFT.ware/master/rift-shell"

class UrlTestCase(unittest.TestCase):
    def setUp(self):
        pass

    @classmethod
    def set_logger(cls, log):
        cls.log = log

    def _common_checks(self, job):
        if job.status != "COMPLETED":
            return

        # assert job.bytes_downloaded == job.bytes_total
        assert job.stop_time > 0
        assert job.start_time > 0
        assert job.stop_time >= job.start_time

    def _display_result(self, url_downl):
        UrlTestCase.log.debug("URL download result: {}".format(url_downl))

    def test_file_download(self):
        """
        Asserts:
            1. Successful download
            2. Model attributes (Process percent, detail, status)
        """
        url_downl = downloader.UrlDownloader(TEST_URL)
        url_downl.download()
        assert os.path.isfile(url_downl.filepath)

        self._display_result(url_downl)
        assert url_downl.meta.status == downloader.DownloadStatus.COMPLETED
        # assert url_downl.job.progress_percent == 100
        assert "success" in url_downl.meta.detail
        self._common_checks(url_downl.meta)

    def test_file_not_exists(self):
        """
        Asserts:
            1. 404 download with retries
            2. Model attributes (Process percent, detail, status)
        """
        url_downl = downloader.UrlDownloader(TEST_URL + ".blah")
        url_downl.download()

        self._display_result(url_downl)
        assert not os.path.isfile(url_downl.filepath)
        assert url_downl.meta.status == downloader.DownloadStatus.FAILED
        assert "Max retries" in url_downl.meta.detail or "404" in url_downl.meta.detail

        self._common_checks(url_downl.meta)

    def test_cancellation(self):
        """
        Asserts:
            1. Cancel for a download and clean up of the downloaded file.
            2. Model attributes (Process percent, detail, status)
        """
        url = "http://speedtest.ftp.otenet.gr/files/test10Mb.db"
        url_dwld = downloader.UrlDownloader(url)
        loop = asyncio.get_event_loop()
        fut = loop.run_in_executor(None, url_dwld.download)

        def cancel():
            fut.cancel()
            url_dwld.cancel_download()

        @asyncio.coroutine
        def sleep():
            yield from asyncio.sleep(2)
            cancel()
            yield from asyncio.sleep(2)

        loop.run_until_complete(sleep())

        self._display_result(url_dwld)
        assert url_dwld.meta.status == downloader.DownloadStatus.CANCELLED
        assert url_dwld.meta.bytes_downloaded == url_dwld.meta.bytes_downloaded
        assert "cancel" in url_dwld.meta.detail
        self._common_checks(url_dwld.meta)

    def test_auth_url(self):
        url_downl = downloader.UrlDownloader(
                'https://api.github.com/user')

        url_downl.download()
        self._display_result(url_downl)


    def tearDown(self):
        pass


def main(argv=sys.argv[1:]):
    logging.basicConfig(format='TEST %(message)s')

    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')

    args, unknown = parser.parse_known_args(argv)
    if args.no_runner:
        runner = None

    # Set the global logging level
    log = logging.getLogger()
    log.setLevel(logging.DEBUG if args.verbose else logging.ERROR)
    UrlTestCase.set_logger(log)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()
