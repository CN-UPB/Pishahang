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
import tornado.platform.asyncio
import tornado.testing
import tornado.web
import tempfile
import unittest
import json
import xmlrunner

from rift.package.handler import FileRestApiHandler

import gi
gi.require_version('ProjectNsdYang', '1.0')
gi.require_version('ProjectVnfdYang', '1.0')

from gi.repository import (
        ProjectNsdYang as NsdYang,
        ProjectVnfdYang as VnfdYang,
        )


class FileServerTestCase(tornado.testing.AsyncHTTPTestCase):
    def setUp(self):
        self._log = logging.getLogger(__file__)
        self._loop = asyncio.get_event_loop()

        super().setUp()
        self._port = self.get_http_port()

    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def get_app(self):

        def create_mock_structure():
            path = tempfile.mkdtemp()
            package_path = os.path.join(path, "pong_vnfd")
            os.makedirs(package_path)
            open(os.path.join(path, "pong_vnfd.xml"), "wb").close()
            open(os.path.join(path, "logo.png"), "wb").close()

            return path

        self.path = create_mock_structure()
        print (self.path)

        return tornado.web.Application([
            (r"/api/package/vnfd/(.*)", FileRestApiHandler, {"path": self.path}),
            ])

    def test_get_file(self):
        response = self.fetch("/api/package/vnfd/pong_vnfd.xml")
        assert response.code == 200

    def test_get_folder(self):
        response = self.fetch("/api/package/vnfd/")
        assert response.code == 200

        data = json.loads(response.body.decode("utf-8"))
        files = [content['name'] for content in data['contents']]
        assert "pong_vnfd.xml" in files
        assert "logo.png" in files


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
