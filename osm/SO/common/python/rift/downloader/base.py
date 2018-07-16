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

import abc
import enum
import os
import uuid
import time


class InvalidDestinationError(Exception):
    pass


class DownloaderProtocol:
    """Listener of this class can implement the following method to get a
    callback
    """
    def on_download_started(self, job):
        """Called when the download starts

        Args:
            job (DownloadJob): Yang Model

        """
        pass

    def on_download_progress(self, job):
        """Called after each chunk is downloaded

        Args:
            job (DownloadJob): Yang Model

        """
        pass

    def on_download_succeeded(self, job):
        """Called when the download is completed successfully

        Args:
            job (DownloadJob): Yang Model

        """
        pass

    def on_download_failed(self, job):
        """Called when the download fails

        Args:
            job (DownloadJob): Yang Model

        """
        pass

    def on_download_cancelled(self, job):
        """Called when the download is canceled

        Args:
            job (DownloadJob): Yang Model

        """
        pass

    def on_download_finished(self, job):
        """Called when the download finishes regardless of the status of the
        download (success, failed or canceled)

        Args:
            job (DownloadJob): Yang Model

        """
        pass


class DownloadStatus(enum.Enum):
    STARTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5


class DownloadMeta:
    """Model data used by the downloader.
    """
    def __init__(self, url, dest_file):
        self.url = url
        self.filepath = dest_file
        self.download_id = str(uuid.uuid4())
        self.bytes_total = 0
        self.progress_percent = 0
        self.bytes_downloaded = 0
        self.bytes_per_second = 0
        self.status = None
        self.start_time = 0
        self.stop_time = 0
        self.detail = ""

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def start_download(self):
        self.start_time = time.time()

    def end_download(self):
        self.end_time = time.time()

    def set_state(self, state):
        self.status = state

    def update_with_data(self, downloaded_chunk):
        self.bytes_downloaded += len(downloaded_chunk)

        if self.bytes_total != 0:
            self.progress_percent = \
                int((self.bytes_downloaded / self.bytes_total) * 100)

        # compute bps
        seconds_elapsed = time.time() - self.start_time
        self.bytes_per_second = self.bytes_downloaded // seconds_elapsed

    def update_data_with_head(self, headers):
        """Update the model from the header of HEAD request

        Args:
            headers (dict): headers from HEAD response
        """
        if 'Content-Length' in headers:
            self.bytes_total = int(headers['Content-Length'])

    def as_dict(self):
        return self.__dict__


class AbstractDownloader:

    def __init__(self):
        self._delegate = None

    @property
    def delegate(self):
        return self._delegate

    @delegate.setter
    def delegate(self, delegate):
        self._delegate = delegate

    @abc.abstractproperty
    def download_id(self):
        pass

    @abc.abstractmethod
    def cancel_download(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def download(self):
        pass
