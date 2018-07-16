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
import contextlib
import io
import logging
import os
import sys
import tempfile
import time
import unittest
import uuid
import xmlrunner

from rift.mano import cloud
from rift.tasklets.rwimagemgr import upload
from rift.package import checksums
from rift.test.dts import async_test
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT
import rw_status

import gi
gi.require_version('RwCal', '1.0')
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwCloudYang', '1.0')
gi.require_version('RwLog', '1.0')
gi.require_version('RwTypes', '1.0')
from gi.repository import (
        RwCal,
        RwCloudYang,
        RwLog,
        RwTypes,
        RwcalYang,
        )

rwstatus = rw_status.rwstatus_from_exc_map({
    IndexError: RwTypes.RwStatus.NOTFOUND,
    KeyError: RwTypes.RwStatus.NOTFOUND,
    })


class CreateImageMock(object):
    def __init__(self, log):
        self._log = log
        self.image_name = None
        self.image_checksum = None

        self.do_fail = False
        self.do_read_slow = False

        self._image_msgs = []

    def add_existing_image(self, image_msg):
        self._log.debug("Appending existing image msg: %s", image_msg)
        self._image_msgs.append(image_msg)

    @rwstatus
    def do_create_image(self, _, image):
        if self.do_fail:
            self._log.debug("Simulating failure")
            raise ValueError("FAILED")

        if not image.has_field("fileno"):
            raise ValueError("Image must have fileno")

        self.image_name = image.name

        # Create a duplicate file descriptor to allow this code to own
        # its own descritor (and thus close it) and allow the client to
        # own and close its own descriptor.
        new_fileno = os.dup(image.fileno)
        with os.fdopen(new_fileno, 'rb') as hdl:
            bytes_hdl = io.BytesIO()
            if self.do_read_slow:
                self._log.debug("slow reading from mock cal")
                try:
                    num_bytes = 0
                    while True:
                        d = os.read(new_fileno, 1024)
                        num_bytes += len(d)
                        bytes_hdl.write(d)
                        if not d:
                            self._log.debug("read %s bytes", num_bytes)
                            return

                        time.sleep(.05)

                except Exception as e:
                    self._log.warning("caught exception when reading: %s",
                                      str(e))
                    raise

            else:
                bytes_hdl.write(hdl.read())

            bytes_hdl.seek(0)
            self.image_checksum = checksums.checksum(bytes_hdl)
            bytes_hdl.close()

        return str(uuid.uuid4())

    @rwstatus
    def do_get_image_list(self, account):
        boxed_image_list = RwcalYang.YangData_RwProject_Project_VimResources()
        for msg in self._image_msgs:
            boxed_image_list.imageinfo_list.append(msg)

        return boxed_image_list


def create_random_image_file():
    with open("/dev/urandom", "rb") as rand_hdl:
        file_hdl = tempfile.NamedTemporaryFile("r+b")
        file_hdl.write(rand_hdl.read(1 * 1024 * 1024))
        file_hdl.flush()
        file_hdl.seek(0)
        return file_hdl


def get_file_hdl_gen(file_hdl):
    while True:
        try:
            d = file_hdl.read(64)
        except ValueError:
            return

        if not d:
            return

        yield d


def get_image_checksum(image_hdl):
    image_checksum = checksums.checksum(image_hdl)
    image_hdl.seek(0)
    return image_checksum


def create_image_info(image_name, image_checksum):
    image = RwcalYang.YangData_RwProject_Project_VimResources_ImageinfoList()
    image.name = image_name
    image.checksum = image_checksum
    image.disk_format = os.path.splitext(image_name)[1][1:]
    image.container_format = "bare"

    return image


class UploadTaskMixin(object):
    def __init__(self, log, loop):
        self._log = log
        self._loop = loop

    def create_image_hdl(self):
        image_hdl = create_random_image_file()

        return image_hdl

    @contextlib.contextmanager
    def create_upload_task(self, account, image_name="test.qcow2",
                           image_checksum=None, image_info=None):

        with self.create_image_hdl() as image_hdl:

            image_checksum = get_image_checksum(image_hdl) \
                if image_checksum is None else image_checksum

            image_info = create_image_info(image_name, image_checksum) \
                if image_info is None else image_info

            iter_hdl = get_file_hdl_gen(image_hdl)
            pipe_gen = upload.GlanceImagePipeGen(self._log, self._loop, iter_hdl)

            upload_task = upload.AccountImageUploadTask(
                    self._log, self._loop, account, image_info, pipe_gen.read_hdl,
                    write_canceller=pipe_gen
                    )
            pipe_gen.start()

            yield upload_task


class ImageMockMixin(object):
    ACCOUNT_MSG = RwCloudYang.YangData_RwProject_Project_Cloud_Account(
        name="mock",
        account_type="mock",
        )

    def __init__(self, log):
        self._log = log
        self._account = cloud.CloudAccount(
                self._log,
                RwLog.Ctx.new(__file__), ImageMockMixin.ACCOUNT_MSG
                )

        self._create_image_mock = CreateImageMock(self._log)

        # Mock the create_image call
        self._account.cal.create_image = self._create_image_mock.do_create_image
        self._account.cal.get_image_list = self._create_image_mock.do_get_image_list

    @property
    def account(self):
        return self._account

    @property
    def image_mock(self):
        return self._create_image_mock


class TestImageUploadTask(unittest.TestCase, UploadTaskMixin, ImageMockMixin):
    def __init__(self, *args, **kwargs):
        self._loop = asyncio.get_event_loop()
        self._log = logging.getLogger(__file__)

        ImageMockMixin.__init__(self, self._log)
        UploadTaskMixin.__init__(self, self._log, self._loop)
        unittest.TestCase.__init__(self, *args, **kwargs)

    @async_test
    def test_upload_image_task(self):
        with self.create_upload_task(self.account) as upload_task:
            yield from upload_task.start()

        self.assertIn("QUEUED", upload_task.state_stack)
        self.assertIn("CHECK_IMAGE_EXISTS", upload_task.state_stack)
        self.assertIn("UPLOADING", upload_task.state_stack)
        self.assertIn("COMPLETED", upload_task.state_stack)

        self.assertEqual("COMPLETED", upload_task.state)

        self.assertEqual(self.image_mock.image_name, upload_task.image_name)
        self.assertEqual(self.image_mock.image_checksum, upload_task.image_checksum)

        task_pb_msg = upload_task.pb_msg
        self.assertEqual(upload_task.image_name, task_pb_msg.image_name)

    # TODO: Fix this
    @unittest.skip("Causes coredump in OSM")
    @async_test
    def test_cancel_image_task(self):
        @asyncio.coroutine
        def wait_for_task_state(upload_task, state, timeout=10):
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if upload_task.state == state:
                    return

                yield from asyncio.sleep(.01)

            raise asyncio.TimeoutError()

        self.image_mock.do_read_slow = True

        with self.create_upload_task(self.account) as upload_task:
            upload_task.start()
            yield from wait_for_task_state(upload_task, "UPLOADING")
            upload_task.stop()
            self.assertEqual("CANCELLING", upload_task.state)
            yield from wait_for_task_state(upload_task, "CANCELLED")

    @async_test
    def test_create_image_failed(self):
        self.image_mock.do_fail = True

        with self.create_upload_task(self.account) as upload_task:
            yield from upload_task.start()

        self.assertEqual("FAILED", upload_task.state)

    @async_test
    def test_create_image_name_and_checksum_exists(self):
        with self.create_upload_task(self.account) as upload_task:
            image_entry = RwcalYang.YangData_RwProject_Project_VimResources_ImageinfoList(
                    id="asdf",
                    name=upload_task.image_name,
                    checksum=upload_task.image_checksum
                    )
            self.image_mock.add_existing_image(image_entry)

            yield from upload_task.start()

        # No image should have been uploaded, since the name and checksum
        self.assertEqual(self.image_mock.image_checksum, None)

        self.assertEqual("COMPLETED", upload_task.state)
        self.assertTrue("UPLOADING" not in upload_task.state_stack)


class TestUploadJob(unittest.TestCase, UploadTaskMixin, ImageMockMixin):
    def __init__(self, *args, **kwargs):
        self._loop = asyncio.get_event_loop()
        self._log = logging.getLogger(__file__)

        ImageMockMixin.__init__(self, self._log)
        UploadTaskMixin.__init__(self, self._log, self._loop)
        unittest.TestCase.__init__(self, *args, **kwargs)

    @async_test
    def test_single_task_upload_job(self):
        with self.create_upload_task(self.account) as upload_task:
            job = upload.ImageUploadJob(self._log, self._loop, [upload_task])
            self.assertEqual("QUEUED", job.state)
            yield from job.start()

        self.assertIn("QUEUED", job.state_stack)
        self.assertIn("IN_PROGRESS", job.state_stack)
        self.assertIn("COMPLETED", job.state_stack)

        self.assertEqual("COMPLETED", job.state)

        job_pb_msg = job.pb_msg
        self.assertEqual("COMPLETED", job_pb_msg.status)

    @async_test
    def test_multiple_tasks_upload_job(self):
        with self.create_upload_task(self.account) as upload_task1:
            with self.create_upload_task(self.account) as upload_task2:
                job = upload.ImageUploadJob(
                        self._log, self._loop, [upload_task1, upload_task2])
                yield from job.start()

        self.assertEqual("COMPLETED", job.state)

    @async_test
    def test_failed_task_in_job(self):
        self.image_mock.do_fail = True

        with self.create_upload_task(self.account) as upload_task:
            job = upload.ImageUploadJob(
                    self._log, self._loop, [upload_task])
            yield from job.start()

        self.assertEqual("FAILED", job.state)

    # TODO: Fix this
    @unittest.skip("Causes coredump in OSM")
    @async_test
    def test_cancel_job(self):
        @asyncio.coroutine
        def wait_for_job_state(upload_job, state, timeout=10):
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if upload_job.state == state:
                    return

                yield from asyncio.sleep(.01)

            raise asyncio.TimeoutError()

        self.image_mock.do_read_slow = True

        with self.create_upload_task(self.account) as upload_task:
            job = upload.ImageUploadJob(
                    self._log, self._loop, [upload_task])
            job.start()
            yield from wait_for_job_state(job, "IN_PROGRESS")
            job.stop()
            self.assertEqual("CANCELLING", job.state)
            yield from wait_for_job_state(job, "CANCELLED")

        self.assertEqual("CANCELLED", job.state)


class TestUploadJobController(unittest.TestCase, UploadTaskMixin, ImageMockMixin):
    def __init__(self, *args, **kwargs):
        self._loop = asyncio.get_event_loop()
        self._log = logging.getLogger(__file__)
        self._project = ManoProject(self._log, name=DEFAULT_PROJECT)
        self._project._loop = self._loop
        ImageMockMixin.__init__(self, self._log)
        unittest.TestCase.__init__(self, *args, **kwargs)

    @async_test
    def test_controller_single_task_job(self):
        controller = upload.ImageUploadJobController(self._project)

        with self.create_upload_task(self.account) as upload_task:
            job_id = controller.create_job([upload_task])
            self.assertEqual(len(controller.active_jobs), 1)
            self.assertEqual(len(controller.completed_jobs), 0)

            job = controller.get_job(job_id)
            yield from job.wait()

            self.assertEqual(len(controller.active_jobs), 0)
            self.assertEqual(len(controller.completed_jobs), 1)

            upload_jobs_pb_msg = controller.pb_msg
            self.assertEqual(len(upload_jobs_pb_msg.job), 1)

    @async_test
    def test_controller_multi_task_job(self):
        controller = upload.ImageUploadJobController(self._project)

        with self.create_upload_task(self.account) as upload_task1:
            with self.create_upload_task(self.account) as upload_task2:
                job_id = controller.create_job([upload_task1, upload_task2])
                self.assertEqual(len(controller.active_jobs), 1)
                self.assertEqual(len(controller.completed_jobs), 0)

                job = controller.get_job(job_id)
                yield from job.wait()
                self.assertEqual(len(controller.active_jobs), 0)
                self.assertEqual(len(controller.completed_jobs), 1)

    @async_test
    def test_controller_multi_jobs(self):
        controller = upload.ImageUploadJobController(self._project)

        with self.create_upload_task(self.account) as upload_task1:
            with self.create_upload_task(self.account) as upload_task2:
                job1_id = controller.create_job([upload_task1])
                job2_id = controller.create_job([upload_task2])
                self.assertEqual(len(controller.active_jobs), 2)
                self.assertEqual(len(controller.completed_jobs), 0)

                job1 = controller.get_job(job1_id)
                job2 = controller.get_job(job2_id)

                yield from asyncio.wait(
                        [job1.wait(), job2.wait()],
                        loop=self._loop
                        )

                self.assertEqual(len(controller.active_jobs), 0)
                self.assertEqual(len(controller.completed_jobs), 2)


class TestRateCalc(unittest.TestCase):
    def test_no_smoothing(self):
        calc = upload.ByteRateCalculator(1)
        self.assertEqual(0, calc.rate)
        calc.add_measurement(100, 1)
        self.assertEqual(100, calc.rate)
        calc.add_measurement(400, 2)
        self.assertEqual(200, calc.rate)

    def test_smoothing(self):
        calc = upload.ByteRateCalculator(2)
        calc.add_measurement(100, 1)
        self.assertEqual(100, calc.rate)

        calc.add_measurement(400, 2)
        self.assertEqual(150, calc.rate)

        calc.add_measurement(400, 2)
        self.assertEqual(175, calc.rate)


class TestUploadProgress(unittest.TestCase):
    def setUp(self):
        self._loop = asyncio.get_event_loop()
        self._log = logging.getLogger(__file__)

    def test_write_proxy(self):
        mem_hdl = io.BytesIO()
        proxy = upload.UploadProgressWriteProxy(self._log, self._loop, 1000, mem_hdl)

        data = b'test_bytes'

        proxy.write(data)
        self.assertEqual(data, mem_hdl.getvalue())
        self.assertEqual(len(data), proxy.bytes_written)
        self.assertEqual(1000, proxy.bytes_total)
        self.assertEqual(1, proxy.progress_percent)

        proxy.close()
        self.assertTrue(mem_hdl.closed)


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
