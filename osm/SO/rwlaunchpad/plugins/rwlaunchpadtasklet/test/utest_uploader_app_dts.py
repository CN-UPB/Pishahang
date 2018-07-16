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
import logging

import shutil
import stat
import sys
import unittest
import uuid
import xmlrunner
import tornado
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.httputil

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

import requests
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.ioloop import IOLoop
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwPkgMgmtYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
from gi.repository import (
        RwDts as rwdts,
        RwPkgMgmtYang,
        RwProjectVnfdYang as RwVnfdYang,
        )

import rift.tasklets.rwlaunchpad.uploader as uploader
import rift.tasklets.rwlaunchpad.message as message
import rift.tasklets.rwlaunchpad.export as export
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT
import rift.test.dts
import rift.package.store

import mock

TEST_STRING = "foobar"

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


        mock_vnfd_catalog = mock.MagicMock()
        self.uid, path = self.create_mock_package(DEFAULT_PROJECT)

        mock_vnfd = RwVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd.from_dict({
              "id": self.uid
            })
        mock_vnfd_catalog = {self.uid: mock_vnfd}

        class MockTasklet:
            def __init__(cls):
                def get_vnfd_catalog(project=DEFAULT_PROJECT):
                    return mock_vnfd_catalog

                cls.log = self.log
                cls.loop = self.loop
                cls.dts = self.dts
                cls.get_vnfd_catalog = get_vnfd_catalog
                cls.get_nsd_catalog = None
                cls.project = None
            def _get_project(cls, project_name):
                if cls.project is None: 
                    cls.project = ManoProject(cls.log, project_name) 
                return cls.project

        vnfd_store = rift.package.store.VnfdPackageFilesystemStore(self.log, project=DEFAULT_PROJECT)
        nsd_store = rift.package.store.NsdPackageFilesystemStore(self.log, project=DEFAULT_PROJECT)

        self.app = uploader.UploaderApplication(MockTasklet(), vnfd_store=vnfd_store, nsd_store=nsd_store)
        self.app.onboarder.get_updated_descriptor = mock.MagicMock(return_value={'vnfd:vnfd':{'name':'mock', 'version':'mock'}})
        self.app.onboarder.onboard = mock.MagicMock()
        self.app.onboarder.update = mock.MagicMock()

        AsyncIOMainLoop().install()
        self.server = tornado.httpserver.HTTPServer(
            self.app,
            io_loop=IOLoop.current(),
        )

    def tearDown(self):
        super().tearDown()

    def create_mock_package(self, project):
        uid = str(uuid.uuid4())
        path = os.path.join(
                os.getenv('RIFT_VAR_ROOT'),
                "launchpad/packages/vnfd",
                project,
                uid)

        package_path = os.path.join(path, "pong_vnfd")

        os.makedirs(package_path)
        open(os.path.join(path, "pong_vnfd.xml"), "wb").close()
        open(os.path.join(path, "logo.png"), "wb").close()

        return uid, path

    @rift.test.dts.async_test
    def test_package_create_rpc(self):
        """
            1. Verify the package-create RPC handler
            2. Check if the log messages are updated which will be used by UI
                for polling
            3. Verify the package-update RPC handler
            4. Check if the log messages are updated which will be used by UI
                for polling
        """
        yield from self.app.register()
        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageCreate.from_dict({
                "package_type": "VNFD",
                "external_url":  "http://repo.riftio.com/releases/open.riftio.com/4.4.2/ping_vnfd.tar.gz",
                "project_name": DEFAULT_PROJECT
                })

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-create",
                    rwdts.XactFlag.TRACE,
                    ip)

        trans_id = None
        for itr in rpc_out:
            result = yield from itr
            trans_id = result.result.transaction_id

        assert trans_id is not None

        yield from asyncio.sleep(5, loop=self.loop)
        # Verify the message logs
        data = self.app.messages[trans_id]
        assert data is not None
        data = data[1]
        assert type(data) is message.DownloadSuccess

        # Update
        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageUpdate.from_dict({
                "package_type": "VNFD",
                "external_url":  "http://repo.riftio.com/releases/open.riftio.com/4.4.2/ping_vnfd.tar.gz",
                "project_name": DEFAULT_PROJECT
                })
        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-update",
                    rwdts.XactFlag.TRACE,
                    ip)

        trans_id = None
        for itr in rpc_out:
            result = yield from itr
            trans_id = result.result.transaction_id

        assert trans_id is not None
        yield from asyncio.sleep(5, loop=self.loop)
        # Verify the message logs
        data = self.app.messages[trans_id]
        assert data is not None
        data = data[1]
        assert type(data) is message.DownloadSuccess

    @rift.test.dts.async_test
    def test_package_export(self):
        """
            1. Verify if the package export RPC handler work
            2. A file is actually generated in the exports dir.
        """
        yield from self.app.register()
        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageExport.from_dict({
                "package_type": "VNFD",
                "package_id": self.uid
                })

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-export",
                    rwdts.XactFlag.TRACE,
                    ip)

        trans_id = None
        filename = None
        for itr in rpc_out:
            result = yield from itr
            trans_id = result.result.transaction_id
            filename = result.result.filename

        assert trans_id is not None

        # Verify the message logs
        data = self.app.messages[trans_id]
        assert data is not None
        data = data[-1]
        assert type(data) is export.ExportSuccess
        path = os.path.join(
                os.getenv("RIFT_VAR_ROOT"),
                "launchpad/exports",
                filename)


        print (path)
        assert os.path.isfile(path)


def main():
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None
    logging.basicConfig(format='TEST %(message)s')
    logging.getLogger().setLevel(logging.DEBUG)


    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()
