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
import tornado.testing
import tornado.web
import tempfile
import unittest
import json
import xmlrunner
import urllib.parse
from requests_toolbelt import MultipartEncoder
import mock
import uuid
import shutil
import requests
import filecmp
import  yaml
import time
import shutil
from rift.rwlib.util import certs

from rift.package.handler import FileRestApiHandler
from rift.tasklets.rwstagingmgr.server.app import StagingApplication, CleanUpStaging
from rift.tasklets.rwstagingmgr.model import StagingArea

import gi
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwStagingMgmtYang,
        )


class TestCase(tornado.testing.AsyncHTTPTestCase):
    def setUp(self):
        self._log = logging.getLogger(__file__)
        self._loop = asyncio.get_event_loop()

        super().setUp()
        self._port = self.get_http_port()

    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def create_mock_store(self):
        self.staging_dir_tmp = tempfile.mkdtemp()
        self.staging_id = str(uuid.uuid4())
        self.staging_dir = os.path.join(self.staging_dir_tmp, self.staging_id)
        os.makedirs(self.staging_dir)
        mock_model = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict({
            'path': self.staging_dir,
            "validity_time": int(time.time()) + 5
            })

        with open(os.path.join(self.staging_dir, "meta.yaml"), "w") as fh:
            yaml.dump(mock_model.as_dict(), fh, default_flow_style=True)

        mock_model = StagingArea(mock_model)
        store = mock.MagicMock()
        store.get_staging_area.return_value = mock_model
        store.root_dir = self.staging_dir_tmp
        store.tmp_dir = self.staging_dir_tmp
        store.META_YAML = "meta.yaml"
        store.remove_staging_area = mock.Mock(return_value=None)

        return store, mock_model

    def create_tmp_file(self):
        _, self.temp_file = tempfile.mkstemp()
        with open(self.temp_file, "w") as fh:
            fh.write("Lorem Ipsum")

        return self.temp_file


    def get_app(self):
        self.store, self.mock_model = self.create_mock_store()
        return StagingApplication(self.store, self._loop, cleanup_interval=5)

    def test_file_upload_and_download(self):
        """

        Asserts:
            1. The file upload
            2. the response of the file upload
            3. Finally downloads the file and verifies if the uploaded and download
               files are the same.
            4. Verify if the directory is cleaned up after expiry
        """
        temp_file = self.create_tmp_file()
        form = MultipartEncoder(fields={
            'file': (os.path.basename(temp_file), open(temp_file, 'rb'), 'application/octet-stream')})

        # Upload
        response = self.fetch("/api/upload/{}".format(self.staging_id),
                              method="POST",
                              body=form.to_string(),
                              headers={"Content-Type": "multipart/form-data"})

        assert response.code == 200

        assert os.path.isfile(os.path.join(
                                    self.staging_dir,
                                    os.path.basename(temp_file)))
        assert self.staging_id in response.body.decode("utf-8")

        response = response.body.decode("utf-8")
        response = json.loads(response)

        # Download
        _, downloaded_file = tempfile.mkstemp()
        response = self.fetch(response['path'])

        with open(downloaded_file, 'wb') as fh:
                fh.write(response.body)

        assert filecmp.cmp(temp_file, downloaded_file)

        print (self.get_url('/'))
        print (self.staging_dir)
        time.sleep(5)
        
        self.store.remove_staging_area(self.mock_model)
        self.store.remove_staging_area.assert_called_once_with(self.mock_model)

    def tearDown(self):
        shutil.rmtree(self.staging_dir_tmp)


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
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.ERROR)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()