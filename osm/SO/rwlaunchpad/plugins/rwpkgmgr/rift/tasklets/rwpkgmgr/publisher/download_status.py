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
# Author(s): Varun Prasad
# Creation Date: 09/25/2016
# 

import asyncio
import gi
import sys

from gi.repository import (RwDts as rwdts)
import rift.mano.dts as mano_dts

import rift.downloader as url_downloader
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import functools
import concurrent

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async

class DownloadStatusPublisher(mano_dts.DtsHandler, url_downloader.DownloaderProtocol):

    def __init__(self, log, dts, loop, project):
        super().__init__(log, dts, loop, project)
        self.tasks = {}


    def xpath(self, download_id=None):
        return self._project.add_project("D,/rw-pkg-mgmt:download-jobs/rw-pkg-mgmt:job" +
                                         ("[download-id={}]".
                                          format(quoted_key(download_id)) if download_id else ""))

    @asyncio.coroutine
    def _dts_publisher(self, job):
         # Publish the download state
         self.reg.update_element(
                        self.xpath(download_id=job.download_id), job)

    @asyncio.coroutine
    def register(self):
        self.reg = yield from self.dts.register(xpath=self.xpath(),
                  flags=rwdts.Flag.PUBLISHER|rwdts.Flag.CACHE|rwdts.Flag.NO_PREP_READ)

        assert self.reg is not None

    def dergister(self):
        self._log.debug("De-registering download status for project {}".
                        format(self.project.name))
        if self.reg:
            self.reg.deregister()
            self.reg = None
   
    @staticmethod 
    def _async_func(func, fut):
        try:
            ret = func()
            fut.set_result(ret)
        except Exception as e:
            fut.set_exception(e)

    def _schedule_dts_work(self, download_job_msg):
        # Create a coroutine
        cort = self._dts_publisher(download_job_msg)
        # Use main asyncio loop (running in main thread)
        newfunc = functools.partial(asyncio.ensure_future, cort, loop=self.loop)
        fut = concurrent.futures.Future()
        # Schedule future in main thread immediately
        self.loop.call_soon_threadsafe(DownloadStatusPublisher._async_func, newfunc, fut)
        res = fut.result()
        exc = fut.exception()
        if exc is not None:
            self.log.error("Caught future exception during download: %s type %s", str(exc), type(exc))
            raise exc
        return res

    def on_download_progress(self, download_job_msg):
        """callback that triggers update.
        """
        # Trigger progess update
        # Schedule a future in the main thread
        self._schedule_dts_work(download_job_msg)

    def on_download_finished(self, download_job_msg):
        """callback that triggers update.
        """

        # clean up the local cache
        key = download_job_msg.download_id
        if key in self.tasks:
            del self.tasks[key]

        # Publish the final state
        # Schedule a future in the main thread
        self._schedule_dts_work(download_job_msg)

    @asyncio.coroutine
    def register_downloader(self, downloader):
        downloader.delegate = self
        future = self.loop.run_in_executor(None, downloader.download)
        self.tasks[downloader.download_id] = (downloader, future)

        return downloader.download_id

    @asyncio.coroutine
    def cancel_download(self, key):
        task, future = self.tasks[key]

        future.cancel()
        task.cancel_download()

    def stop(self):
        self.deregister()

        for task, future in self.tasks:
            task.cancel()
            future.cancel()

    def deregister(self):
        """ de-register with dts """
        if self.reg is not None:
            self.reg.deregister()
            self.reg = None
