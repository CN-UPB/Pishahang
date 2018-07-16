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
# Creation Date: 09/28/2016
#

import tornado.httpclient
import tornado.web
import tornadostreamform.multipart_streamer as multipart_streamer
import logging
import os

MB = 1024 * 1024
GB = 1024 * MB

MAX_STREAMED_SIZE = 5 * GB

class HttpMessageError(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class RequestHandler(tornado.web.RequestHandler):
    def options(self, *args, **kargs):
        pass

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers',
                        'Content-Type, Cache-Control, Accept, X-Requested-With, Authorization')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE')


class StoreStreamerPart(multipart_streamer.MultiPartStreamer):
    """
    Create a Part streamer with a custom temp directory. Using the default
    tmp directory and trying to move the file to $RIFT_VAR_ROOT occasionally
    causes link errors. So create a temp directory within the staging area.
    """
    def __init__(self, store, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store

    def create_part(self, headers):
        #RIFT-18071: tmp directory was not getting created - throwing an error in the system test cases in HA failover.
        if not os.path.exists(self.store.tmp_dir):
            os.makedirs(self.store.tmp_dir)
        return multipart_streamer.TemporaryFileStreamedPart(self, headers, tmp_dir=self.store.tmp_dir)


@tornado.web.stream_request_body
class UploadStagingHandler(RequestHandler):
    def initialize(self, store):
        """Initialize the handler

        Arguments:
            log  - the logger that this handler should use
            loop - the tasklets ioloop

        """
        self.log = logging.getLogger()
        self.store = store

        self.part_streamer = None

    @tornado.gen.coroutine
    def prepare(self):
        """Prepare the handler for a request

        The prepare function is the first part of a request transaction. It
        creates a temporary file that uploaded data can be written to.

        """
        if self.request.method != "POST":
            return

        self.request.connection.set_max_body_size(MAX_STREAMED_SIZE)

        # Retrieve the content type and parameters from the request
        content_type = self.request.headers.get('content-type', None)
        if content_type is None:
            raise tornado.httpclient.HTTPError(400, "No content type set")

        content_type, params = tornado.httputil._parse_header(content_type)

        if "multipart/form-data" != content_type.lower():
            raise tornado.httpclient.HTTPError(415, "Invalid content type")

        # You can get the total request size from the headers.
        try:
            total = int(self.request.headers.get("Content-Length", "0"))
        except KeyError:
            self.log.warning("Content length header not found")
            # For any well formed browser request, Content-Length should have a value.
            total = 0

        # And here you create a streamer that will accept incoming data
        self.part_streamer = StoreStreamerPart(self.store, total)


    @tornado.gen.coroutine
    def data_received(self, chunk):
        """When a chunk of data is received, we forward it to the multipart streamer."""
        self.part_streamer.data_received(chunk)

    def post(self, staging_id):
        """Handle a post request

        The function is called after any data associated with the body of the
        request has been received.

        """
        try:
            # You MUST call this to close the incoming stream.
            self.part_streamer.data_complete()
            desc_parts = self.part_streamer.get_parts_by_name("file")
            if len(desc_parts) != 1:
                raise tornado.httpclient.HTTPError(400, "File option not found")

            binary_data = desc_parts[0]
            staging_area = self.store.get_staging_area(staging_id)
            filename = binary_data.get_filename()
            staging_area.model.name = filename
            staging_area.model.size = binary_data.get_size()

            dest_file = os.path.join(staging_area.model.path, filename)
            binary_data.move(dest_file)

            self.set_status(200)
            self.write(tornado.escape.json_encode({
                "path": "/api/download/{}/{}".format(staging_id, filename)
                    }))

        finally:
            self.part_streamer.release_parts()
            self.finish()

