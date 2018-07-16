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
import base64
import concurrent.futures
import io
import json
import logging
import os
import sys
import tornado.testing
import tornado.web
import unittest
import uuid
import xmlrunner

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

from rift.package import convert
from rift.tasklets.rwlaunchpad import onboard
import rift.test.dts
import functools

import gi
gi.require_version('NsdYang', '1.0')
gi.require_version('VnfdYang', '1.0')
gi.require_version('ProjectNsdYang', '1.0')
gi.require_version('ProjectVnfdYang', '1.0')

from gi.repository import (
        NsdYang,
        VnfdYang,
        ProjectNsdYang,
        ProjectVnfdYang,
        )


class RestconfDescriptorHandler(tornado.web.RequestHandler):
    class AuthError(Exception):
        pass


    class ContentTypeError(Exception):
        pass


    class RequestBodyError(Exception):
        pass


    def initialize(self, log, auth, info):
        self._auth = auth
        # The superclass has self._log already defined so use a different name
        self._logger = log
        self._info = info
        self._logger.debug('Created restconf descriptor handler')

    def _verify_auth(self):
        if self._auth is None:
            return None

        auth_header = self.request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self._transforms = []
            self.finish()

            msg = "Missing Authorization header"
            self._logger.error(msg)
            raise RestconfDescriptorHandler.AuthError(msg)

        auth_header = auth_header.encode('ascii')
        auth_decoded = base64.decodebytes(auth_header[6:]).decode()
        login, password = auth_decoded.split(':', 2)
        login = login
        password = password
        is_auth = ((login, password) == self._auth)

        if not is_auth:
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self._transforms = []
            self.finish()

            msg = "Incorrect username and password in auth header: got {}, expected {}".format(
                    (login, password), self._auth
                    )
            self._logger.error(msg)
            raise RestconfDescriptorHandler.AuthError(msg)

    def _verify_content_type_header(self):
        content_type_header = self.request.headers.get('content-type')
        if content_type_header is None:
            self.set_status(415)
            self._transforms = []
            self.finish()

            msg = "Missing content-type header"
            self._logger.error(msg)
            raise RestconfDescriptorHandler.ContentTypeError(msg)

        if content_type_header != "application/vnd.yang.data+json":
            self.set_status(415)
            self._transforms = []
            self.finish()

            msg = "Unsupported content type: %s" % content_type_header
            self._logger.error(msg)
            raise RestconfDescriptorHandler.ContentTypeError(msg)

    def _verify_headers(self):
        self._verify_auth()
        self._verify_content_type_header()

    def _verify_request_body(self, descriptor_type):
        if descriptor_type not in ['nsd', 'vnfd']:
            raise ValueError("Unsupported descriptor type: %s" % descriptor_type)

        body = convert.decode(self.request.body)
        self._logger.debug("Received msg: {}".format(body))

        try:
            message = json.loads(body)
        except convert.SerializationError as e:
            self.set_status(400)
            self._transforms = []
            self.finish()

            msg = "Descriptor request body not valid"
            self._logger.error(msg)
            raise RestconfDescriptorHandler.RequestBodyError() from e

        self._info.last_request_message = message

        self._logger.debug("Received a valid descriptor request: {}".format(message))

    def put(self, descriptor_type):
        self._info.last_descriptor_type = descriptor_type
        self._info.last_method = "PUT"

        try:
            self._verify_headers()
        except (RestconfDescriptorHandler.AuthError,
                RestconfDescriptorHandler.ContentTypeError):
            return None

        try:
            self._verify_request_body(descriptor_type)
        except RestconfDescriptorHandler.RequestBodyError:
            return None

        self.write("Response doesn't matter?")

    def post(self, descriptor_type):
        self._info.last_descriptor_type = descriptor_type
        self._info.last_method = "POST"

        try:
            self._verify_headers()
        except (RestconfDescriptorHandler.AuthError,
                RestconfDescriptorHandler.ContentTypeError):
            return None

        try:
            self._verify_request_body(descriptor_type)
        except RestconfDescriptorHandler.RequestBodyError:
            return None

        self.write("Response doesn't matter?")


class HandlerInfo(object):
    def __init__(self):
        self.last_request_message = None
        self.last_descriptor_type = None
        self.last_method = None


class OnboardTestCase(tornado.testing.AsyncHTTPTestCase):
    DESC_SERIALIZER_MAP = {
            "nsd": convert.NsdSerializer(),
            "vnfd": convert.VnfdSerializer(),
            }

    AUTH = ("admin","admin")
    def setUp(self):
        self._log = logging.getLogger(__file__)
        self._loop = asyncio.get_event_loop()

        self._handler_info = HandlerInfo()
        super().setUp()
        self._port = self.get_http_port()
        self._onboarder = onboard.DescriptorOnboarder(
                log=self._log, port=self._port
                )

    def get_new_ioloop(self):
        return tornado.platform.asyncio.AsyncIOMainLoop()

    def get_app(self):
        attrs = dict(auth=OnboardTestCase.AUTH, log=self._log, info=self._handler_info)
        return tornado.web.Application([
            (r"/api/config/project/default/.*/(nsd|vnfd)",
             RestconfDescriptorHandler, attrs),
            ])


    def get_msg(self, desc=None):
        if desc is None:
            desc = NsdYang.YangData_Nsd_NsdCatalog_Nsd(id=str(uuid.uuid4()), name="nsd_name")
        serializer = OnboardTestCase.DESC_SERIALIZER_MAP['nsd']
        jstr = serializer.to_json_string(desc, project_ns=False)
        self._desc = jstr
        hdl = io.BytesIO(str.encode(jstr))
        return serializer.from_file_hdl(hdl, ".json")

    def get_json(self, msg):
        serializer = OnboardTestCase.DESC_SERIALIZER_MAP['nsd']
        json_data = serializer.to_json_string(msg, project_ns=True)
        return json.loads(json_data)

    @rift.test.dts.async_test
    def test_onboard_nsd(self):
        nsd_msg = self.get_msg()
        yield from self._loop.run_in_executor(None, functools.partial(self._onboarder.onboard, descriptor_msg=nsd_msg, auth=OnboardTestCase.AUTH))
        self.assertEqual(self._handler_info.last_request_message, self.get_json(nsd_msg))
        self.assertEqual(self._handler_info.last_descriptor_type, "nsd")
        self.assertEqual(self._handler_info.last_method, "POST")

    @rift.test.dts.async_test
    def test_update_nsd(self):
        nsd_msg = self.get_msg()
        yield from self._loop.run_in_executor(None, functools.partial(self._onboarder.update, descriptor_msg=nsd_msg, auth=OnboardTestCase.AUTH))
        self.assertEqual(self._handler_info.last_request_message, self.get_json(nsd_msg))
        self.assertEqual(self._handler_info.last_descriptor_type, "nsd")
        self.assertEqual(self._handler_info.last_method, "PUT")

    @rift.test.dts.async_test
    def test_bad_descriptor_type(self):
        nsd_msg = NsdYang.YangData_Nsd_NsdCatalog_Nsd()
        with self.assertRaises(TypeError):
            yield from self._loop.run_in_executor(None, self._onboarder.update, nsd_msg)

        with self.assertRaises(TypeError):
            yield from self._loop.run_in_executor(None, self._onboarder.onboard, nsd_msg)

    @rift.test.dts.async_test
    def test_bad_port(self):
        # Use a port not used by the instantiated server
        new_port = self._port - 1
        self._onboarder.port = new_port
        nsd_msg = self.get_msg()

        with self.assertRaises(onboard.OnboardError):
            yield from self._loop.run_in_executor(None, self._onboarder.onboard, nsd_msg)

        with self.assertRaises(onboard.UpdateError):
            yield from self._loop.run_in_executor(None, self._onboarder.update, nsd_msg)

    @rift.test.dts.async_test
    def test_timeout(self):
        # Set the timeout to something minimal to speed up test
        self._onboarder.timeout = .1

        nsd_msg = self.get_msg()

        # Force the request to timeout by running the call synchronously so the
        with self.assertRaises(onboard.OnboardError):
            self._onboarder.onboard(nsd_msg)

        # Force the request to timeout by running the call synchronously so the
        with self.assertRaises(onboard.UpdateError):
            self._onboarder.update(nsd_msg)


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
