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

import io
import logging
import os
import tempfile
import threading
import time
import zlib

import requests
import requests.exceptions
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
# disable unsigned certificate warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from . import base
from .local_file import LocalFileAdapter as LocalFileAdapter

class UrlDownloader(base.AbstractDownloader):
    """Handles downloads of URL with some basic retry strategy.
    """
    def __init__(self,
                 url,
                 file_obj=None,
                 auth=None,
                 delete_on_fail=True,
                 decompress_on_fly=False,
                 log=None):
        """
        Args:
            model (str or DownloadJob): Url string to download or the Yang model
            file_obj (str,file handle): Optional, If not set we create a temp
                location to store the file.
            delete_on_fail (bool, optional): Clean up the partially downloaded
                file, if the download failed or was canceled
            callback_handler (None, optional): Instance of base.DownloaderCallbackHandler
        """
        super().__init__()

        self.log = log or logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        self._fh, filename = self._validate_fn(file_obj)
        self.meta = base.DownloadMeta(url, filename)

        self.session = self._create_session()
        self._cancel_event = threading.Event()
        self.auth = auth

        self.delete_on_fail = delete_on_fail

        self.decompress_on_fly = decompress_on_fly
        self._decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)

    def __repr__(self):
        data = {"model": self.meta.as_dict()}
        return str(data)

    def _validate_fn(self, file_obj):
        """
        If no file object is given then create a temp file
        if a filename is given open the file in wb mode

        Finally verify the mode open mode of the file

        """
        if file_obj is None:
            _, file_obj = tempfile.mkstemp()
            # Reopen in wb mode
            file_obj = open(file_obj, "wb")

        # If the fh is a filename
        if type(file_obj) is str:
            file_obj = open(file_obj, "wb")

        if type(file_obj) is not io.BufferedWriter:
            raise base.InvalidDestinationError("Destination file cannot be"
                        "opened for write")

        return file_obj, file_obj.name

    def _create_session(self):
        session = requests.Session()
        # 3 connection attempts should be more than enough, We can't wait forever!
        # The user needs to be  updated of the status
        retries = Retry(total=2, backoff_factor=1)
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("file://", LocalFileAdapter())

        return session

    def update_data_from_headers(self, headers):
        """Update the model from the header of HEAD request

        Args:
            headers (dict): headers from HEAD response
        """
        self.meta.bytes_total = 0
        if 'Content-Length' in headers:
            self.meta.bytes_total = int(headers['Content-Length'])
        self.meta.progress_percent = 0
        self.meta.bytes_downloaded = 0

    @property
    def url(self):
        return self.meta.url

    @property
    def filepath(self):
        return self.meta.filepath

    # Start of override methods
    @property
    def download_id(self):
        return self.meta.download_id

    def cancel_download(self):
        self._cancel_event.set()

    def close(self):
        self.session.close()
        self._fh.close()

    def cleanup(self):
        """Remove the file if the download failed.
        """
        if self.meta.status in [base.DownloadStatus.FAILED, base.DownloadStatus.CANCELLED] and self.delete_on_fail:
            self.log.info("Cleaning up failed download and removing {}".format(
                    self.filepath))

            try:
                os.remove(self.filepath)
            except Exception:
                pass

    def download(self):
        """Start the download

        Trigger an HEAD request to get the meta data before starting the download
        """
        try:
            self._download()
        except Exception as e:
            self.log.exception(str(e))
            self.meta.detail = str(e)
            self.meta.stop_time = time.time()

            self.download_failed()

            # Close all file handles and clean up
            self.close()
            self.cleanup()

        self.download_finished()

    # end of override methods

    def check_and_decompress(self, chunk):
        if self.url.endswith(".gz") and self.decompress_on_fly:
            chunk = self._decompressor.decompress(chunk)

        return chunk

    def _download(self):

        url_options = {"verify": False, "timeout": 10}

        if self.auth is not None:
            url_options["auth"] = self.auth

        response = self.session.head(self.url, **url_options)

        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        # Prepare the meta data
        self.meta.update_data_with_head(response.headers)
        self.meta.start_download()

        self.download_progress()

        url_options["stream"] = True,
        request = self.session.get(self.url, **url_options)

        if request.status_code != requests.codes.ok:
            request.raise_for_status()

        # actual start time, excluding the HEAD request.
        for chunk in request.iter_content(chunk_size=1024 * 50):
            if self._cancel_event.is_set():
                self.log.info("Download of URL {} to {} has been cancelled".format(
                    self.url, self.filepath))
                break

            if chunk:  # filter out keep-alive new chunks
                self.meta.update_with_data(chunk)
                self.log.debug("Download progress: {}".format(self.meta.as_dict()))

                chunk = self.check_and_decompress(chunk)

                self._fh.write(chunk)
                #self.download_progress()

        self.meta.end_download()
        self.close()

        if self._cancel_event.is_set():
            self.download_cancelled()
        else:
            self.download_succeeded()

        self.cleanup()

    # Start of delegate calls
    def call_delegate(self, event):
        if not self.delegate:
            return

        getattr(self.delegate, event)(self.meta)

    def download_failed(self):
        self.meta.set_state(base.DownloadStatus.FAILED)
        self.call_delegate("on_download_failed")

    def download_cancelled(self):
        self.meta.detail = "Download canceled by user."
        self.meta.set_state(base.DownloadStatus.CANCELLED)
        self.call_delegate("on_download_cancelled")

    def download_progress(self):
        self.meta.detail = "Download in progress."
        self.meta.set_state(base.DownloadStatus.IN_PROGRESS)
        self.call_delegate("on_download_progress")

    def download_succeeded(self):
        self.meta.detail = "Download completed successfully."
        self.meta.set_state(base.DownloadStatus.COMPLETED)
        self.call_delegate("on_download_succeeded")

    def download_started(self):
        self.meta.detail = "Setting up download and extracting meta."
        self.meta.set_state(base.DownloadStatus.STARTED)
        self.call_delegate("on_download_started")

    def download_finished(self):
        self.call_delegate("on_download_finished")
