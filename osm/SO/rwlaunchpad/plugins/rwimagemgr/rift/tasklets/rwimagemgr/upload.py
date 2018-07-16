
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
import collections
import itertools
import os
import time
import threading

import rift.mano.cloud

import gi
gi.require_version('RwImageMgmtYang', '1.0')
from gi.repository import (
        RwImageMgmtYang,
        )


class UploadJobError(Exception):
    pass


class ImageUploadTaskError(Exception):
    pass


class ImageUploadError(ImageUploadTaskError):
    pass


class ImageListError(ImageUploadTaskError):
    pass


class ImageUploadJobController(object):
    """ This class starts and manages ImageUploadJobs """
    MAX_COMPLETED_JOBS = 20

    def __init__(self, project, max_completed_jobs=MAX_COMPLETED_JOBS):
        self._log = project.log
        self._loop = project.loop
        self._project = project
        self._job_id_gen = itertools.count(1)
        self._max_completed_jobs = max_completed_jobs

        self._jobs = {}
        self._completed_jobs = collections.deque(
                maxlen=self._max_completed_jobs
                )

    @property
    def pb_msg(self):
        """ the UploadJobs protobuf message """
        upload_jobs_msg = RwImageMgmtYang.YangData_RwProject_Project_UploadJobs()
        for job in self._jobs.values():
            upload_jobs_msg.job.append(job.pb_msg)

        return upload_jobs_msg

    @property
    def jobs(self):
        """ the tracked list of ImageUploadJobs """
        return self._jobs.values()

    @property
    def completed_jobs(self):
        """ completed jobs in the tracked list of ImageUploadJobs """
        return [job for job in self._jobs.values() if job in self._completed_jobs]

    @property
    def active_jobs(self):
        """ in-progress jobs in the tracked list of ImageUploadJobs """
        return [job for job in self._jobs.values() if job not in self._completed_jobs]

    def _add_job(self, job):
        self._jobs[job.id] = job

    def _start_job(self, job, on_completed=None):
        def on_job_completed(_):
            self._log.debug("%s completed.  Adding to completed jobs list.", job)

            # If adding a new completed job is going to overflow the
            # completed job list, find the first job that completed and
            # remove it from the tracked jobs.
            if len(self._completed_jobs) == self._completed_jobs.maxlen:
                first_completed_job = self._completed_jobs[-1]
                del self._jobs[first_completed_job.id]

            self._completed_jobs.appendleft(job)

        job_future = job.start()
        job_future.add_done_callback(on_job_completed)

        if on_completed is not None:
            job_future.add_done_callback(on_completed)

    def get_job(self, job_id):
        """ Get the UploadJob from the job id

        Arguments:
            job_id - the job id that was previously added to the controller

        Returns:
            The associated ImageUploadJob

        Raises:
            LookupError - Could not find the job id
        """
        if job_id not in self._jobs:
            raise LookupError("Could not find job_id %s" % job_id)

        return self._jobs[job_id]

    def create_job(self, image_tasks, on_completed=None):
        """ Create and start a ImageUploadJob from a list of ImageUploadTasks

        Arguments:
            image_tasks - a list of ImageUploadTasks
            on_completed - a callback which is added to the job future

        Returns:
            A ImageUploadJob id
        """
        self._log.debug("Creating new job from %s image tasks", len(image_tasks))
        new_job = ImageUploadJob(
                self._log,
                self._loop,
                image_tasks,
                job_id=next(self._job_id_gen)
                )

        self._add_job(new_job)
        self._start_job(new_job, on_completed=on_completed)

        return new_job.id


class ImageUploadJob(object):
    """ This class manages a set of ImageUploadTasks

    In order to push an image (or set of images) to many cloud accounts, and get a single
    status on that operation, we need a single status that represents all of those tasks.

    The ImageUploadJob provides a single endpoint to control all the tasks and report
    when all images are successfully upload or when any one fails.
    """
    STATES = ("QUEUED", "IN_PROGRESS", "CANCELLING", "CANCELLED", "COMPLETED", "FAILED")
    TIMEOUT_JOB = 6 * 60 * 60  # 6 hours
    JOB_GEN = itertools.count(1)

    def __init__(self, log, loop, upload_tasks, job_id=None, timeout_job=TIMEOUT_JOB):
        self._log = log
        self._loop = loop
        self._upload_tasks = upload_tasks
        self._job_id = next(ImageUploadJob.JOB_GEN) if job_id is None else job_id
        self._timeout_job = timeout_job

        self._state = "QUEUED"
        self._state_stack = [self._state]

        self._start_time = time.time()
        self._stop_time = 0

        self._task_future_map = {}
        self._job_future = None

    def __repr__(self):
        return "{}(job_id={}, state={})".format(
                self.__class__.__name__, self._job_id, self._state
                )

    @property
    def id(self):
        return self._job_id

    @property
    def state(self):
        """ The state of the ImageUploadJob """
        return self._state

    @state.setter
    def state(self, new_state):
        """ Set the state of the ImageUploadJob """
        states = ImageUploadJob.STATES
        assert new_state in states
        assert states.index(new_state) >= states.index(self._state)
        self._state_stack.append(new_state)

        self._state = new_state

    @property
    def state_stack(self):
        """ The list of states that this job progressed through  """
        return self._state_stack

    @property
    def pb_msg(self):
        """ The UploadJob protobuf message """
        task = RwImageMgmtYang.YangData_RwProject_Project_UploadJobs_Job.from_dict({
            "id": self._job_id,
            "status": self._state,
            "start_time": self._start_time,
            "upload_tasks": [task.pb_msg for task in self._upload_tasks]
        })

        if self._stop_time:
            task.stop_time = self._stop_time

        return task

    def _start_upload_tasks(self):
        self._log.debug("Starting %s upload tasks", len(self._upload_tasks))

        for upload_task in self._upload_tasks:
            upload_task.start()

    @asyncio.coroutine
    def _wait_for_upload_tasks(self):
        self._log.debug("Waiting for upload tasks to complete")

        wait_coroutines = [t.wait() for t in self._upload_tasks]
        if wait_coroutines:
            yield from asyncio.wait(
                    wait_coroutines,
                    timeout=self._timeout_job,
                    loop=self._loop
                    )

        self._log.debug("All upload tasks completed")

    def _set_final_job_state(self):
        failed_tasks = []
        for task in self._upload_tasks:
            if task.state != "COMPLETED":
                failed_tasks.append(task)

        if failed_tasks:
            self._log.error("%s had %s FAILED tasks.", self, len(failed_tasks))
            for ftask in failed_tasks:
                self._log.error("%s : Failed to upload image : %s to cloud_account : %s", self, ftask.image_name, ftask.cloud_account)
            self.state = "FAILED"
        else:
            self._log.debug("%s tasks completed successfully", len(self._upload_tasks))
            self.state = "COMPLETED"

    @asyncio.coroutine
    def _cancel_job(self):
        for task in self._upload_tasks:
            task.stop()

        # TODO: Wait for all tasks to actually reach terminal
        # states.

        self.state = "CANCELLED"

    @asyncio.coroutine
    def _do_job(self):
        self.state = "IN_PROGRESS"
        self._start_upload_tasks()
        try:
            yield from self._wait_for_upload_tasks()
        except asyncio.CancelledError:
            self._log.debug("%s was cancelled.  Cancelling all tasks.",
                            self)
            self._loop.create_task(self._cancel_job())
            raise
        finally:
            self._stop_time = time.time()
            self._job_future = None

        self._set_final_job_state()

    @asyncio.coroutine
    def wait(self):
        """ Wait for the job to reach a terminal state """
        if self._job_future is None:
            raise UploadJobError("Job not started")

        yield from asyncio.wait_for(
                self._job_future,
                self._timeout_job,
                loop=self._loop
                )

    def start(self):
        """ Start the job and all child tasks """
        if self._state != "QUEUED":
            raise UploadJobError("Job already started")

        self._job_future = self._loop.create_task(self._do_job())
        return self._job_future

    def stop(self):
        """ Stop the job and all child tasks  """
        if self._job_future is not None:
            self.state = "CANCELLING"
            self._job_future.cancel()


class ByteRateCalculator(object):
    """  This class produces a byte rate from inputted measurements"""
    def __init__(self, rate_time_constant):
        self._rate = 0
        self._time_constant = rate_time_constant

    @property
    def rate(self):
        return self._rate

    def add_measurement(self, num_bytes, time_delta):
        rate = num_bytes / time_delta
        if self._rate == 0:
            self._rate = rate
        else:
            self._rate += ((rate - self._rate) / self._time_constant)

        return self._rate


class UploadProgressWriteProxy(object):
    """ This class implements a write proxy with produces various progress stats

    In order to keep the complexity of the UploadTask down, this class acts as a
    proxy for a file write.  By providing the original handle to be written to
    and having the client class call write() on this object, we can produce the
    various statistics to be consumed.
    """
    RATE_TIME_CONSTANT = 5

    def __init__(self, log, loop, bytes_total, write_hdl):
        self._log = log
        self._loop = loop
        self._bytes_total = bytes_total
        self._write_hdl = write_hdl

        self._bytes_written = 0
        self._byte_rate = 0

        self._rate_calc = ByteRateCalculator(UploadProgressWriteProxy.RATE_TIME_CONSTANT)
        self._rate_task = None

    def write(self, data):
        self._write_hdl.write(data)
        self._bytes_written += len(data)

    def close(self):
        self._write_hdl.close()
        if self._rate_task is not None:
            self._log.debug("stopping rate monitoring task")
            self._rate_task.cancel()

    def start_rate_monitoring(self):
        """ Start the rate monitoring task """
        @asyncio.coroutine
        def periodic_rate_task():
            try:
                while True:
                    start_time = time.time()
                    start_bytes = self._bytes_written
                    yield from asyncio.sleep(1, loop=self._loop)
                    time_period = time.time() - start_time
                    num_bytes = self._bytes_written - start_bytes

                    self._byte_rate = self._rate_calc.add_measurement(num_bytes, time_period)
            except asyncio.CancelledError:
                self._log.debug("rate monitoring task cancelled")

        self._log.debug("starting rate monitoring task")
        self._rate_task = self._loop.create_task(periodic_rate_task())

    @property
    def progress_percent(self):
        if self._bytes_total == 0:
            return 0

        return int(self._bytes_written / self._bytes_total * 100)

    @property
    def bytes_written(self):
        return self._bytes_written

    @property
    def bytes_total(self):
        return self._bytes_total

    @property
    def bytes_rate(self):
        return self._byte_rate


class GlanceImagePipeGen(object):
    """ This class produces a read file handle from a generator that produces bytes

    The CAL API takes a file handle as an input.  The Glance API creates a generator
    that produces byte strings.  This class acts as the mediator by creating a pipe
    and pumping the bytestring from the generator into the write side of the pipe.

    A pipe has the useful feature here that it will block at the buffer size until
    the reader has consumed.  This allows us to only pull from glance and push at the
    pace of the reader preventing us from having to store the images locally on disk.
    """
    def __init__(self, log, loop, data_gen):
        self._log = log
        self._loop = loop
        self._data_gen = data_gen

        read_fd, write_fd = os.pipe()

        self._read_hdl = os.fdopen(read_fd, 'rb')
        self._write_hdl = os.fdopen(write_fd, 'wb')
        self._close_hdl = self._write_hdl

        self._stop = False
        self._t = None

    @property
    def write_hdl(self):
        return self._write_hdl

    @write_hdl.setter
    def write_hdl(self, new_write_hdl):
        self._write_hdl = new_write_hdl

    @property
    def read_hdl(self):
        return self._read_hdl

    def _gen_writer(self):
        self._log.debug("starting image data write to pipe")
        try:
            for data in self._data_gen:
                if self._stop:
                    break

                try:
                    self._write_hdl.write(data)
                except (BrokenPipeError, ValueError) as e:
                    self._log.warning("write pipe closed: %s", str(e))
                    return

        except Exception as e:
            self._log.exception("error when writing data to pipe: %s", str(e))

        finally:
            self._log.debug("closing write side of pipe")
            try:
                self._write_hdl.close()
            except OSError:
                pass

    def start(self):
        t = threading.Thread(target=self._gen_writer)
        t.daemon = True
        t.start()

        self._t = t

    def stop(self):
        self._log.debug("stop requested, closing write side of pipe")
        self._stop = True
        if self._t is not None:
            self._t.join(timeout=1)


class AccountImageUploadTask(object):
    """ This class manages an create_image task from an image info and file handle

    Manage the upload of a image to a configured cloud account.
    """
    STATES = ("QUEUED", "CHECK_IMAGE_EXISTS", "UPLOADING", "CANCELLING", "CANCELLED", "COMPLETED", "FAILED")

    TIMEOUT_CHECK_EXISTS = 10
    TIMEOUT_IMAGE_UPLOAD = 6 * 60 * 60  # 6 hours

    def __init__(self, log, loop, account, image_info, image_hdl,
                 timeout_exists=TIMEOUT_CHECK_EXISTS, timeout_upload=TIMEOUT_IMAGE_UPLOAD,
                 progress_info=None, write_canceller=None
                 ):
        self._log = log
        self._loop = loop
        self._account = account
        self._image_info = image_info.deep_copy()
        self._image_hdl = image_hdl

        self._timeout_exists = timeout_exists
        self._timeout_upload = timeout_upload

        self._progress_info = progress_info
        self._write_canceller = write_canceller

        self._state = "QUEUED"
        self._state_stack = [self._state]

        self._detail = "Task is waiting to be started"
        self._start_time = time.time()
        self._stop_time = 0
        self._upload_future = None

        if not image_info.has_field("name"):
            raise ValueError("image info must have name field")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        states = AccountImageUploadTask.STATES
        assert new_state in states
        assert states.index(new_state) >= states.index(self._state)
        self._state_stack.append(new_state)

        self._state = new_state

    @property
    def state_stack(self):
        return self._state_stack

    @property
    def image_id(self):
        """ The image name being uploaded """
        return self._image_info.id

    @property
    def image_name(self):
        """ The image name being uploaded """
        return self._image_info.name

    @property
    def image_checksum(self):
        """ The image checksum being uploaded """
        if self._image_info.has_field("checksum"):
            return self._image_info.checksum

        return None

    @property
    def cloud_account(self):
        """ The cloud account name which the image is being uploaded to """
        return self._account.name

    @property
    def pb_msg(self):
        """ The UploadTask protobuf message """
        task = RwImageMgmtYang.YangData_RwProject_Project_UploadJobs_Job_UploadTasks.from_dict({
            "cloud_account": self.cloud_account,
            "image_id": self.image_id,
            "image_name": self.image_name,
            "status": self.state,
            "detail": self._detail,
            "start_time": self._start_time,
        })

        if self.image_checksum is not None:
            task.image_checksum = self.image_checksum

        if self._stop_time:
            task.stop_time = self._stop_time

        if self._progress_info:
            task.bytes_written = self._progress_info.bytes_written
            task.bytes_total = self._progress_info.bytes_total
            task.progress_percent = self._progress_info.progress_percent
            task.bytes_per_second = self._progress_info.bytes_rate

        if self.state == "COMPLETED":
            task.progress_percent = 100

        return task

    def _get_account_images(self):
        account_images = []
        self._log.debug("getting image list for account {}".format(self._account.name))
        try:
            account_images = self._account.get_image_list()
        except rift.mano.cloud.CloudAccountCalError as e:
            msg = "could not get image list for account {}".format(self._account.name)
            self._log.error(msg)
            raise ImageListError(msg) from e

        return account_images

    def _has_existing_image(self):
        account = self._account

        account_images = self._get_account_images()

        matching_images = [i for i in account_images if i.name == self.image_name]

        if self.image_checksum is not None:
            matching_images = [i for i in matching_images if i.checksum == self.image_checksum]

        if matching_images:
            self._log.debug("found matching image with checksum in account %s",
                            account.name)
            return True

        self._log.debug("did not find matching image with checksum in account %s",
                        account.name)
        return False

    def _upload_image(self):
        image = self._image_info
        account = self._account

        image.fileno = self._image_hdl.fileno()

        self._log.debug("uploading to account {}: {}".format(account.name, image))
        try:
            image.id = account.create_image(image)
        except rift.mano.cloud.CloudAccountCalError as e:
            msg = "error when uploading image {} to cloud account: {}".format(image.name, str(e))
            self._log.error(msg)
            raise ImageUploadError(msg) from e

        self._log.debug('uploaded image (id: {}) to account{}: {}'.format(
                        image.id, account.name, image.name))

        return image.id

    @asyncio.coroutine
    def _do_upload(self):
        try:
            self.state = "CHECK_IMAGE_EXISTS"
            has_image = yield from asyncio.wait_for(
                    self._loop.run_in_executor(None, self._has_existing_image),
                    timeout=self._timeout_exists,
                    loop=self._loop
                    )
            if has_image:
                self.state = "COMPLETED"
                self._detail = "Image already exists on destination"
                return

            self.state = "UPLOADING"
            self._detail = "Uploading image"

            # Note that if the upload times out, the upload thread may still
            # stick around.  We'll need another method of cancelling the task
            # through the VALA interface.
            image_id = yield from asyncio.wait_for(
                    self._loop.run_in_executor(None, self._upload_image),
                    timeout=self._timeout_upload,
                    loop=self._loop
                    )

        except asyncio.CancelledError as e:
            self.state = "CANCELLED"
            self._detail = "Image upload cancelled"

        except ImageUploadTaskError as e:
            self.state = "FAILED"
            self._detail = str(e)

        except asyncio.TimeoutError as e:
            self.state = "FAILED"
            self._detail = "Timed out during upload task: %s" % str(e)

        else:
            # If the user does not provide a checksum and performs a URL source
            # upload with an incorrect URL, then Glance does not indicate a failure
            # and the CAL cannot detect an incorrect upload.  In this case, use
            # the bytes_written to detect a bad upload and mark the task as failed.
            if self._progress_info and self._progress_info.bytes_written == 0:
                self.state = "FAILED"
                self._detail = "No bytes written.  Possible bad image source."
                return

            self.state = "COMPLETED"
            self._detail = "Image successfully uploaded.  Image id: %s" % image_id

        finally:
            self._stop_time = time.time()
            self._upload_future = None

    @asyncio.coroutine
    def wait(self):
        """ Wait for the upload task to complete """
        if self._upload_future is None:
            raise ImageUploadError("Task not started")

        yield from asyncio.wait_for(
                self._upload_future,
                self._timeout_upload, loop=self._loop
                )

    def start(self):
        """ Start the upload task """
        if self._state != "QUEUED":
            raise ImageUploadError("Task already started")

        self._log.info("Starting %s", self)

        self._upload_future = self._loop.create_task(self._do_upload())

        return self._upload_future

    def stop(self):
        """ Stop the upload task in progress """
        if self._upload_future is None:
            self._log.warning("Cannot cancel %s.  Not in progress.", self)
            return

        self.state = "CANCELLING"
        self._detail = "Cancellation has been requested"

        self._log.info("Cancelling %s", self)
        self._upload_future.cancel()
        if self._write_canceller is not None:
            self._write_canceller.stop()
