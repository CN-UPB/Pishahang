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
import logging
import os
import shutil
import stat
import sys
import unittest
import uuid
import xmlrunner

# Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwPkgMgmtYang', '1.0')
from gi.repository import (
        RwDts as rwdts,
        RwPkgMgmtYang,
        )
from rift.tasklets.rwpkgmgr.proxy import filesystem

import rift.tasklets.rwpkgmgr.publisher as pkg_publisher
import rift.tasklets.rwpkgmgr.rpc as rpc
import rift.test.dts
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT

TEST_STRING = "foobar"


class MockPublisher(object):
    def __init__(self, uid):
        self.assert_uid = uid

    @asyncio.coroutine
    def register_downloader(self, *args):
        return self.assert_uid


class MockProject(ManoProject):
    def __init__(self, log, uid=None):
        super().__init__(log, name=DEFAULT_PROJECT)
        self.job_handler = MockPublisher(uid)


class MockTasklet:
    def __init__(self, log, uid=None):
        self.log = log
        self.projects = {}
        project = MockProject(self.log,
                              uid=uid)
        project.publisher = None
        self.projects[project.name] = project


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

    def tearDown(self):
        super().tearDown()

    def create_mock_package(self, project):
        uid = str(uuid.uuid4())
        path = os.path.join(
                os.getenv('RIFT_VAR_ROOT'),
                "launchpad/packages/vnfd",
                project,
                uid)

        asset_path = os.path.join(path, "icons")

        os.makedirs(asset_path)
        open(os.path.join(path, "pong_vnfd.xml"), "wb").close()
        open(os.path.join(asset_path, "logo.png"), "wb").close()

        return uid, path

    @rift.test.dts.async_test
    def test_endpoint_discovery(self):
        """
        Verifies the following:
            The endpoint RPC returns a URL
        """
        proxy = filesystem.FileSystemProxy(self.loop, self.log, self.dts)
        endpoint = rpc.EndpointDiscoveryRpcHandler(self.log, self.dts, self.loop, proxy)
        yield from endpoint.register()

        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_GetPackageEndpoint.from_dict({
                "package_type": "VNFD",
                "package_id": "BLAHID",
                "project_name": DEFAULT_PROJECT})

        rpc_out = yield from self.dts.query_rpc(
                    "I,/get-package-endpoint",
                    rwdts.XactFlag.TRACE,
                    ip)

        for itr in rpc_out:
            result = yield from itr
            assert result.result.endpoint == 'https://127.0.0.1:8008/mano/api/package/vnfd/{}/BLAHID'.format(DEFAULT_PROJECT)

    @rift.test.dts.async_test
    def test_schema_rpc(self):
        """
        Verifies the following:
            The schema RPC return the schema structure
        """
        proxy = filesystem.FileSystemProxy(self.loop, self.log, self.dts)
        endpoint = rpc.SchemaRpcHandler(self.log, self.dts, self.loop, proxy)
        yield from endpoint.register()

        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_GetPackageSchema.from_dict({
                "package_type": "VNFD",
                "project_name": DEFAULT_PROJECT})

        rpc_out = yield from self.dts.query_rpc(
                    "I,/get-package-schema",
                    rwdts.XactFlag.TRACE,
                    ip)

        for itr in rpc_out:
            result = yield from itr
            assert "charms" in result.result.schema

    @rift.test.dts.async_test
    def test_file_proxy_rpc(self):
        """
            1. The file RPC returns a valid UUID thro' DTS
        """
        assert_uid = str(uuid.uuid4())

        uid, path = self.create_mock_package(DEFAULT_PROJECT)

        proxy = filesystem.FileSystemProxy(self.loop, self.log, self.dts)
        endpoint = rpc.PackageOperationsRpcHandler(
            self.log,
            self.dts,
            self.loop,
            proxy,
            MockTasklet(self.log, uid=assert_uid))
        yield from endpoint.register()

        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageFileAdd.from_dict({
                "package_type": "VNFD",
                "package_id": uid,
                "external_url": "https://raw.githubusercontent.com/RIFTIO/RIFT.ware/master/rift-shell",
                "package_path": "script/rift-shell",
                "project_name": DEFAULT_PROJECT})

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-file-add",
                    rwdts.XactFlag.TRACE,
                    ip)

        for itr in rpc_out:
            result = yield from itr
            assert result.result.task_id == assert_uid

        shutil.rmtree(path)

    @rift.test.dts.async_test
    def test_file_add_workflow(self):
        """
            Integration test:
                1. Verify the end to end flow of package ADD (NO MOCKS)
        """
        uid, path = self.create_mock_package(DEFAULT_PROJECT)

        proxy = filesystem.FileSystemProxy(self.loop, self.log, self.dts)
        tasklet = MockTasklet(self.log, uid=uid)
        project = tasklet.projects[DEFAULT_PROJECT]
        publisher = pkg_publisher.DownloadStatusPublisher(self.log, self.dts, self.loop, project)
        project.job_handler = publisher
        endpoint = rpc.PackageOperationsRpcHandler(
            self.log,
            self.dts,
            self.loop,
            proxy,
            tasklet)

        yield from publisher.register()
        yield from endpoint.register()

        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageFileAdd.from_dict({
                "package_type": "VNFD",
                "package_id": uid,
                "external_url": "https://raw.githubusercontent.com/RIFTIO/RIFT.ware/master/rift-shell",
                "project_name": DEFAULT_PROJECT,
                "vnfd_file_type": "ICONS",
                "package_path": "rift-shell"})

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-file-add",
                    rwdts.XactFlag.TRACE,
                    ip)

        yield from asyncio.sleep(5, loop=self.loop)
        filepath = os.path.join(path, ip.vnfd_file_type.lower(), ip.package_path)
        self.log.debug("Filepath: {}".format(filepath))
        assert os.path.isfile(filepath)
        mode = oct(os.stat(filepath)[stat.ST_MODE])
        assert str(mode) == "0o100664"

        shutil.rmtree(path)


    @rift.test.dts.async_test
    def test_file_delete_workflow(self):
        """
            Integration test:
                1. Verify the end to end flow of package ADD (NO MOCKS)
        """
        uid, path = self.create_mock_package(DEFAULT_PROJECT)

        proxy = filesystem.FileSystemProxy(self.loop, self.log, self.dts)
        endpoint = rpc.PackageDeleteOperationsRpcHandler(
            self.log,
            self.dts,
            self.loop,
            proxy)

        yield from endpoint.register()

        ip = RwPkgMgmtYang.YangInput_RwPkgMgmt_PackageFileDelete.from_dict({
                "package_type": "VNFD",
                "package_id": uid,
                "package_path": "logo.png",
                "vnfd_file_type": "ICONS",
                "project_name": DEFAULT_PROJECT})

        assert os.path.isfile(os.path.join(path, ip.vnfd_file_type.lower(), ip.package_path))

        rpc_out = yield from self.dts.query_rpc(
                    "I,/rw-pkg-mgmt:package-file-delete",
                    rwdts.XactFlag.TRACE,
                    ip)

        yield from asyncio.sleep(5, loop=self.loop)
        assert not os.path.isfile(os.path.join(path, ip.vnfd_file_type.lower(), ip.package_path))

        shutil.rmtree(path)

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
