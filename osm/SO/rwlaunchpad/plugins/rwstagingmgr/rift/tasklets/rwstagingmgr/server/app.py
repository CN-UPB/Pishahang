
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

import logging
import os
import threading
import time

import requests
# disable unsigned certificate warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import tornado
import tornado.escape
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.web

import gi
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwStagingMgmtYang,
        )

from . import handler


MB = 1024 * 1024
GB = 1024 * MB
MAX_STREAMED_SIZE = 5 * GB


class StagingApplication(tornado.web.Application):
    MAX_BUFFER_SIZE = 1 * MB  # Max. size loaded into memory!
    MAX_BODY_SIZE = 1 * MB  # Max. size loaded into memory!
    PORT = 4568

    def __init__(self, store, loop, cleanup_interval=60):

        self.store = store
        self.loop  = loop 

        assert self.loop is not None

        self.cleaner = CleanupThread(self.store, loop=self.loop, cleanup_interval=cleanup_interval)
        self.cleaner.start()

        super(StagingApplication, self).__init__([
            (r"/api/upload/(.*)", handler.UploadStagingHandler, {'store': store}),
            (r"/api/download/(.*)", tornado.web.StaticFileHandler, {'path': store.root_dir}),
            ])


class CleanUpStaging(object):
    def __init__(self, store, log=None):
        """
        Args:
            store : Any store obj from store opackage
            log : Log handle
        """
        self.store = store
        self.log = log or logging.getLogger()
        self.log.setLevel(logging.DEBUG)

    def cleanup(self):
        # Extract package could return multiple packages if
        # the package is converted
        for root, dirs, files in os.walk(self.store.root_dir):
            for staging_id in dirs:
                try:
                    staging_area = self.store.get_staging_area(staging_id)
                    if staging_area.has_expired:
                        self.store.remove_staging_area(staging_area)
                except Exception as e:
                    # Ignore the temp directories
                    pass


class CleanupThread(threading.Thread):
    """Daemon thread that clean up the staging area
    """
    def __init__(self, store, loop, log=None, cleanup_interval=60):
        """
        Args:
            store: A compatible store object
            log (None, optional): Log handle
            cleanup_interval (int, optional): Cleanup interval in secs
            loop: Tasklet main loop
        """
        super().__init__()
        self.log      = log or logging.getLogger()
        self.store    = store
        self._cleaner = CleanUpStaging(store, log)
        self.cleanup_interval = cleanup_interval
        self.daemon   = True
        self.loop     = loop

        assert self.loop is not None

    def run(self):
        try:
            while True:
                self.loop.call_soon_threadsafe(self._cleaner.cleanup, )
                time.sleep(self.cleanup_interval)

        except Exception as e:
            self.log.exception(e)

