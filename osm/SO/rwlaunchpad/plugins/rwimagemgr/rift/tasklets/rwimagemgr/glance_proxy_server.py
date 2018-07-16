
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

import json

from .lib import quickproxy
import rift.tasklets.tornado


class GlanceConfig(object):
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 9292
    DEFAULT_TOKEN = "test"

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=DEFAULT_TOKEN):
        self.host = host
        self.port = port
        self.token = token


class GlanceImageCreateRequest(object):
    def __init__(self, name, size, checksum, disk_format, container_format):
        self.name = name
        self.size = size
        self.checksum = checksum
        self.disk_format = disk_format
        self.container_format = container_format

    def __repr__(self):
        return "{}({})".format(
                self.__class__.__name__,
                dict(
                    name=self.name,
                    size=self.size,
                    checksum=self.checksum,
                    )
                )

    @classmethod
    def from_header_dict(cls, header_dict):
        """
        curl -i -X POST -H 'x-image-meta-container_format: bare' -H
        'Transfer-Encoding: chunked' -H 'User-Agent: python-glanceclient' -H
        'x-image-meta-size: 13167616' -H 'x-image-meta-is_public: False' -H
        'X-Auth-Token: test' -H 'Content-Type: application/octet-stream' -H
        'x-image-meta-checksum: 64d7c1cd2b6f60c92c14662941cb7913' -H
        'x-image-meta-disk_format: raw' -H 'x-image-meta-name:
        cirros-0.3.2-x86_64-disk.img'
        """

        name = header_dict["x-image-meta-name"]
        try:
            size = int(header_dict["x-image-meta-size"])
        except KeyError:
            size = None

        try:
            checksum = header_dict["x-image-meta-checksum"]
        except KeyError:
            checksum = None

        disk_format = header_dict["x-image-meta-disk_format"]
        container_format = header_dict["x-image-meta-container_format"]

        return cls(name=name, size=size, checksum=checksum,
                   disk_format=disk_format, container_format=container_format)


class GlanceImageCreateResponse(object):
    def __init__(self, id, name, status, size, checksum):
        self.id = id
        self.name = name
        self.status = status
        self.size = size
        self.checksum = checksum

    def __repr__(self):
        return "{}({})".format(
                self.__class__.__name__,
                dict(
                    id=self.id,
                    name=self.name,
                    status=self.status,
                    checksum=self.checksum,
                    )
                )

    @classmethod
    def from_response_body(cls, response_body):
        """
        {"image": {"status": "active", "deleted": false, "container_format":
        "bare", "min_ram": 0, "updated_at": "2016-06-24T14:41:38.598199",
        "owner": null, "min_disk": 0, "is_public": false, "deleted_at": null,
        "id": "5903cb2d-53db-4343-b055-586475a077f5", "size": 13167616, "name":
        "cirros-0.3.2-x86_64-disk.img", "checksum":
        "64d7c1cd2b6f60c92c14662941cb7913", "created_at":
        "2016-06-24T14:41:38.207356", "disk_format": "raw",
        "properties": {}, "protected": false}}
        """

        response_dict = json.loads(response_body.decode())
        image = response_dict["image"]

        id = image["id"]
        name = image["name"]
        status = image["status"]
        size = image["size"]
        checksum = image["checksum"]

        return cls(
                id=id, name=name, status=status,
                size=size, checksum=checksum
                )


class GlanceHTTPMockProxy(object):
    def __init__(self, log, loop, on_http_request, on_http_response):
        self._log = log
        self._loop = loop
        self._on_http_request = on_http_request
        self._on_http_response = on_http_response

    def start(self):
        pass

    def stop(self):
        pass


class QuickProxyServer(object):
    """ This class implements a HTTP Proxy server
    """
    DEFAULT_PROXY_PORT = 9999
    DEBUG_LEVEL = 0

    def __init__(self, log, loop, proxy_port=DEFAULT_PROXY_PORT):
        self._log = log
        self._loop = loop
        self._proxy_port = proxy_port

        self._proxy_server = None

    def __repr__(self):
        return "{}(port={})".format(self.__class__.__name__, self._proxy_port)

    def start(self, on_http_request, on_http_response):
        """ Start the proxy server

        Arguments:
            on_http_request - A callback when a http request is initiated
            on_http_response - A callback when a http response is initiated

        """
        self._log.debug("Starting %s", self)
        io_loop = rift.tasklets.tornado.TaskletAsyncIOLoop(
                asyncio_loop=self._loop
                )

        self._proxy_server = quickproxy.run_proxy(
                port=self._proxy_port,
                req_callback=on_http_request,
                resp_callback=on_http_response,
                io_loop=io_loop,
                debug_level=QuickProxyServer.DEBUG_LEVEL,
                address="127.0.0.1",
                )

    def stop(self):
        """ Stop the proxy server """
        if self._proxy_server is None:
            self._log.warning("%s already stopped")
            return

        self._log.debug("Stopping %s", self)
        self._proxy_server.stop()
        self._proxy_server = None


class GlanceHTTPProxyServer(object):
    """ This class implements a HTTP Proxy server

    Proxying requests to glance has the following high-level advantages:
       - Allows us to intercept HTTP requests and responses to hook in functionality
       - Allows us to configure the glance catalog server and keep the endpoint the same
    """

    DEFAULT_GLANCE_CONFIG = GlanceConfig()

    def __init__(self, log, loop,
                 http_proxy_server,
                 glance_config=DEFAULT_GLANCE_CONFIG,
                 on_create_image_request=None,
                 on_create_image_response=None,
                 ):

        self._log = log
        self._loop = loop
        self._http_proxy_server = http_proxy_server
        self._glance_config = glance_config

        self._on_create_image_request = on_create_image_request
        self._on_create_image_response = on_create_image_response

    def _handle_create_image_request(self, request):
        image_request = GlanceImageCreateRequest.from_header_dict(request.headers)
        self._log.debug("Parsed image request: %s", image_request)
        if self._on_create_image_request is not None:
            self._on_create_image_request(image_request)

        # Store the GlanceImageCreateRequest in the request context so it
        # is available in the response
        request.context["image_request"] = image_request

        return request

    def _handle_create_image_response(self, response):
        image_request = response.context["image_request"]

        self._log.debug("Got response body: %s", response.body)
        image_response = GlanceImageCreateResponse.from_response_body(response.body)
        self._log.debug("Parsed image response: %s", image_response)
        if self._on_create_image_response is not None:
            response = self._on_create_image_response(image_response, image_request)

        return response

    def start(self):
        """ Start the glance proxy server """
        def request_callback(request):
            # Redirect the request to the actual glance server
            self._log.debug("Proxying request to glance (path: %s, method: %s)",
                            request.path, request.method)

            # Save the path and method to detect whether the response for
            # for a create_image request
            request.context["path"] = request.path
            request.context["method"] = request.method

            if request.path.endswith("images") and request.method == "POST":
                request = self._handle_create_image_request(request)

            # Redirect the request to the actual glance server
            request.host = self._glance_config.host
            request.port = self._glance_config.port

            return request

        def response_callback(response):
            self._log.debug("Got glance request response: %s", response)

            if response.context["path"].endswith("images") and response.context["method"] == "POST":
                response = self._handle_create_image_response(response)

            return response

        self._http_proxy_server.start(
                on_http_request=request_callback,
                on_http_response=response_callback
                )

    def stop(self):
        """ Stop the glance proxy server """
        self._http_proxy_server.stop()
