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

#asynctest looks for selectors under it's own package but in
#python3.3 it exists under the asyncio package
import sys
sys.path.append(asyncio.__path__[0])
import asynctest

import logging
import os
import unittest
import unittest.mock
import xmlrunner

import gi
gi.require_version("RwDts", "1.0")
gi.require_version("RwImageMgmtYang", "1.0")
from gi.repository import (
    RwDts,
    RwImageMgmtYang,
)

import rift.tasklets
import rift.test.dts

from rift.tasklets.rwimagemgr import tasklet
from rift.tasklets.rwimagemgr import upload
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT

from rift.test.dts import async_test

import utest_image_upload


def create_job_controller_mock():
    jc_mock = unittest.mock.Mock(upload.ImageUploadJobController)

    return jc_mock


def create_upload_task_creator_mock():
    creator_mock = asynctest.CoroutineMock(spec=["create_tasks_from_onboarded_create_rpc"])

    return creator_mock


class RwImageRPCTestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
        return RwImageMgmtYang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", self.id())
        self.tinfo = self.new_tinfo(self.id())

        self.project = ManoProject(self.log, name=DEFAULT_PROJECT)
        self.project._dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)
        self.project.cloud_accounts = {'mock'}

        self.task_creator_mock = create_upload_task_creator_mock()
        self.job_controller_mock = create_job_controller_mock()
        self.rpc_handler = tasklet.ImageDTSRPCHandler(
                self.project, object(), self.task_creator_mock,
                self.job_controller_mock
                )
        self.show_handler = tasklet.ImageDTSShowHandler(
                                self.project, self.job_controller_mock)

        self.tinfo_c = self.new_tinfo(self.id() + "_client")
        self.dts_c = rift.tasklets.DTS(self.tinfo_c, self.schema, self.loop)

        self._upload_mixin = utest_image_upload.UploadTaskMixin(self.log, self.loop)
        self._image_mock_mixin = utest_image_upload.ImageMockMixin(self)

    @async_test
    def test_create_job(self):
        yield from self.rpc_handler.register()
        yield from self.show_handler.register()

        account = self._image_mock_mixin.account
        with self._upload_mixin.create_upload_task(account) as upload_task:
            self.task_creator_mock.create_tasks_from_onboarded_create_rpc.return_value = [upload_task]
            self.job_controller_mock.create_job.return_value = 2
            type(self.job_controller_mock).pb_msg = unittest.mock.PropertyMock(
                    return_value=RwImageMgmtYang.YangData_RwProject_Project_UploadJobs.from_dict({
                        "job": [
                            {
                                "id": 2,
                                "upload_tasks": [upload_task.pb_msg],
                                "status": "COMPLETED"
                            }
                        ]
                    })
                  )

            create_job_msg = RwImageMgmtYang.YangInput_RwImageMgmt_CreateUploadJob.from_dict({
                "cloud_account": [upload_task.cloud_account],
                "onboarded_image": {
                    "image_name": upload_task.image_name,
                    "image_checksum": upload_task.image_checksum,
                },
                "project_name": self.project.name,
            })

            query_iter = yield from self.dts_c.query_rpc(
                    "I,/rw-image-mgmt:create-upload-job",
                    0,
                    create_job_msg,
                    )

            for fut_resp in query_iter:
                rpc_result = (yield from fut_resp).result

            self.assertEqual(2, rpc_result.job_id)

            self.assertTrue(
                    self.task_creator_mock.create_tasks_from_onboarded_create_rpc.called
                    )

            query_iter = yield from self.dts_c.query_read(
                    self.project.add_project("D,/rw-image-mgmt:upload-jobs"),
                    )

            for fut_resp in query_iter:
                rpc_result = (yield from fut_resp).result
                self.assertEqual(1, len(rpc_result.job))
                self.assertEqual(2, rpc_result.job[0].id)
                self.assertEqual(1, len(rpc_result.job[0].upload_tasks))


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
