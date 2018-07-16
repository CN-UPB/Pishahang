
#
#   Copyright 2016-2017 RIFT.IO Inc
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
import concurrent.futures
import gi

from rift.mano.utils.project import ManoProject

gi.require_version("RwImageMgmtYang", "1.0")
from gi.repository import (
    RwImageMgmtYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class UploadJobError(Exception):
    pass


class UploadJobFailed(UploadJobError):
    pass


class UploadJobCancelled(UploadJobFailed):
    pass


class UploadJobClient(object):
    """ An upload job DTS client

    This class wraps the DTS upload job actions to be more easily reused across
    various components
    """
    def __init__(self, log, loop, dts):
        self._log = log
        self._loop = loop
        self._dts = dts

    def create_job(self, image_name, image_checksum, project, cloud_account_names=None):
        """ Create an image upload_job and return an UploadJob instance

        Arguments:
            image_name - The name of the image in the image catalog
            image_checksum - The checksum of the image in the catalog
            cloud_account_names - Names of the cloud accounts to upload the image to.
                                  None uploads the image to all cloud accounts.

        Returns:
            An UploadJob instance
        """
        self._log.debug("Project {}: Create image upload job for image {} to {}".
                        format(project, image_name, cloud_account_names))

        create_job_msg = RwImageMgmtYang.YangInput_RwImageMgmt_CreateUploadJob.from_dict({
            "project_name": project,
            "onboarded_image": {
                "image_name": image_name,
                "image_checksum": image_checksum,
                }
            })

        if cloud_account_names is not None:
            create_job_msg.cloud_account = cloud_account_names

        query_iter = yield from self._dts.query_rpc(
                "I,/rw-image-mgmt:create-upload-job",
                0,
                create_job_msg,
                )

        for fut_resp in query_iter:
            rpc_result = (yield from fut_resp).result

            job_id = rpc_result.job_id

        return UploadJob(self._log, self._loop, self._dts, job_id, project)

    def create_job_threadsafe(self, image_name, image_checksum, project, cloud_account_names=None):
        """ A thread-safe, syncronous wrapper for create_job """
        future = concurrent.futures.Future()

        def on_done(asyncio_future):
            if asyncio_future.exception() is not None:
                future.set_exception(asyncio_future.exception())

            elif asyncio_future.result() is not None:
                future.set_result(asyncio_future.result())

        def add_task():
            task = self._loop.create_task(
                    self.create_job(image_name, image_checksum, project, cloud_account_names)
                    )
            task.add_done_callback(on_done)

        self._loop.call_soon_threadsafe(add_task)
        return future.result()


class UploadJob(object):
    """ A handle for a image upload job """
    def __init__(self, log, loop, dts, job_id, project):
        self._log = log
        self._loop = loop
        self._dts = dts
        self._job_id = job_id
        self._project = project

    @asyncio.coroutine
    def wait_until_complete(self):
        """ Wait until the upload job reaches a terminal state

        Raises:
            UploadJobError: A generic exception occured in the upload job
            UploadJobFailed: The upload job failed
            UploadJobCancelled: The upload job was cancelled
        """
        self._log.debug("waiting for upload job %s to complete", self._job_id)
        xpath = ManoProject.prefix_project("D,/rw-image-mgmt:upload-jobs/" +
                                           "rw-image-mgmt:job[rw-image-mgmt:id={}]".
                                           format(quoted_key(str(self._job_id))),
                                           project=self._project,
                                           log=self._log)

        while True:
            query_iter = yield from self._dts.query_read(xpath)
            job_status_msg = None
            for fut_resp in query_iter:
                job_status_msg = (yield from fut_resp).result
                break

            if job_status_msg is None:
                raise UploadJobError("did not get a status response for job_id: %s",
                                     self._job_id)

            if job_status_msg.status == "COMPLETED":
                msg = "upload job %s completed successfully" % self._job_id
                self._log.debug(msg)
                return

            elif job_status_msg.status == "FAILED":
                msg = "upload job %s as not successful: %s" % (self._job_id, job_status_msg.status)
                self._log.error(msg)
                raise UploadJobFailed(msg)

            elif job_status_msg.status == "CANCELLED":
                msg = "upload job %s was cancelled" % self._job_id
                self._log.error(msg)
                raise UploadJobCancelled(msg)

            yield from asyncio.sleep(.5, loop=self._loop)

    def wait_until_complete_threadsafe(self):
        """ A thread-safe, synchronous wrapper for wait_until_complete """

        future = concurrent.futures.Future()

        def on_done(asyncio_future):
            if asyncio_future.exception() is not None:
                future.set_exception(asyncio_future.exception())
                return

            future.set_result(asyncio_future.result())

        def add_task():
            task = self._loop.create_task(self.wait_until_complete())
            task.add_done_callback(on_done)

        self._loop.call_soon_threadsafe(add_task)
        return future.result()
