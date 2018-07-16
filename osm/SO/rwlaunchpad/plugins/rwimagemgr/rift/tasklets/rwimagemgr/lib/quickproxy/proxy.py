import os
import sys
import urllib.parse as urlparse
import pprint
import http.cookies as Cookie
import datetime
import dateutil.parser
from copy import copy

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.escape

__all__ = ['run_proxy', 'RequestObj', 'ResponseObj']

DEFAULT_CALLBACK = lambda r: r


class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __str__(self):
        return str(self.__dict__)


class RequestObj(Bunch):
    '''
    An HTTP request object that contains the following request attributes:

    protocol: either 'http' or 'https'
    host: the destination hostname of the request
    port: the port for the request
    path: the path of the request ('/index.html' for example)
    query: the query string ('?key=value&other=value')
    fragment: the hash fragment ('#fragment')
    method: request method ('GET', 'POST', etc)
    username: always passed as None, but you can set it to override the user
    password: None, but can be set to override the password
    body: request body as a string
    headers: a dictionary of header / value pairs
        (for example {'Content-Type': 'text/plain', 'Content-Length': 200})
    follow_redirects: true to follow redirects before returning a response
    validate_cert: false to turn off SSL cert validation
    context: a dictionary to place data that will be accessible to the response
    '''
    pass


class ResponseObj(Bunch):
    '''
    An HTTP response object that contains the following request attributes:

    code: response code, such as 200 for 'OK'
    headers: the response headers
    pass_headers: a list or set of headers to pass along in the response. All
        other headeres will be stripped out. By default this includes:
        ('Date', 'Cache-Control', 'Server', 'Content-Type', 'Location')
    body: response body as a string
    context: the context object from the request
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('code', 200)
        kwargs.setdefault('headers', {})
        kwargs.setdefault('pass_headers', True)
        kwargs.setdefault('body', '')
        kwargs.setdefault('context', {})
        super(ResponseObj, self).__init__(**kwargs)


class ResponseStreamWriterFuture(tornado.concurrent.Future):
    def __init__(self, write_fn, *args, **kwargs):
        self.write_fn = write_fn
        super().__init__(*args, **kwargs)


def _make_proxy(methods, io_loop, req_callback, resp_callback, err_callback, debug_level=0):

    @tornado.web.stream_request_body
    class ProxyHandler(tornado.web.RequestHandler):

        SUPPORTED_METHODS = methods

        def initialize(self):
            self.proxy_request_ready = tornado.concurrent.Future()
            self.request_future = None

        def on_connection_close(self):
            if self.request_future is not None:
                self.request_future.set_result(False)

        def create_body_producer_future(self, write_fn):
            self.request_future = ResponseStreamWriterFuture(write_fn)
            self.proxy_request_ready.set_result(True)
            return self.request_future

        @tornado.gen.coroutine
        def data_received(self, chunk):
            yield self.proxy_request_ready

            yield self.request_future.write_fn(chunk)

        def make_requestobj(self, request):
            '''
            creates a request object for this request
            '''

            # get url for request
            # surprisingly, tornado's HTTPRequest sometimes
            # has a uri field with the full uri (http://...)
            # and sometimes it just contains the path. :(

            url = request.uri
            if not url.startswith(u'http'):
                url = u"{proto}://{netloc}{path}".format(
                    proto=request.protocol,
                    netloc=request.host,
                    path=request.uri
                )

            parsedurl = urlparse.urlparse(url)

            # Passing on the transfer encoding header, causes Tornado to not
            # transmit valid chunks
            headers = request.headers.copy()
            if "Transfer-encoding" in headers:
                del headers["Transfer-Encoding"]

            # create request object

            requestobj = RequestObj(
                method=request.method,
                protocol=parsedurl.scheme,
                username=None,
                password=None,
                host=parsedurl.hostname,
                port=parsedurl.port or 80,
                path=parsedurl.path,
                query=parsedurl.query,
                fragment=parsedurl.fragment,
                #body=request.body,
                headers=headers,
                follow_redirects=False,
                validate_cert=True,
                context={}
            )

            return requestobj, parsedurl


        def make_request(self, obj, parsedurl):
            '''
            converts a request object into an HTTPRequest
            '''

            obj.headers.setdefault('Host', obj.host)

            if obj.username or parsedurl.username or \
                obj.password or parsedurl.password:

                auth = u"{username}:{password}@".format(
                    username=obj.username or parsedurl.username,
                    password=obj.password or parsedurl.password
                )

            else:
                auth = ''

            url = u"{proto}://{auth}{host}{port}{path}{query}{frag}"
            url = url.format(
                proto=obj.protocol,
                auth=auth,
                host=obj.host,
                port=(u':' + str(obj.port)) if (obj.port and obj.port != 80) else u'',
                path=u'/'+obj.path.lstrip(u'/') if obj.path else u'',
                query=u'?'+obj.query.lstrip(u'?') if obj.query else u'',
                frag=obj.fragment
            )

            body_producer = None
            if "Transfer-encoding" in self.request.headers and \
                    self.request.headers["Transfer-Encoding"] == "chunked":
                body_producer = self.create_body_producer_future

            req = tornado.httpclient.HTTPRequest(
                url=url,
                method=obj.method,
                body_producer=body_producer,
                decompress_response=False,
                headers=obj.headers,
                follow_redirects=obj.follow_redirects,
                allow_nonstandard_methods=True,
                request_timeout=1*60*60 #1 hour
            )

            return req

        def prepare(self):

            request = self.request
            if debug_level >= 4:
                print("<<<<<<<< REQUEST <<<<<<<<")
                pprint.pprint(request.__dict__)

            MB = 1024 * 1024
            GB = 1024 * MB

            MAX_STREAMED_SIZE = 50 * GB
            request.connection.set_max_body_size(MAX_STREAMED_SIZE)

            requestobj, parsedurl = self.make_requestobj(request)

            if debug_level >= 3:
                print("<<<<<<<< REQUESTOBJ <<<<<<<<")
                pprint.pprint(requestobj.__dict__)

            if debug_level >= 1:
                debugstr = "serving request from %s:%d%s " % (requestobj.host,
                                                              requestobj.port or 80,
                                                              requestobj.path)

            modrequestobj = req_callback(requestobj)

            if isinstance(modrequestobj, ResponseObj):
                self.handle_response(modrequestobj)
                return

            if debug_level >= 1:
                print(debugstr + "to %s:%d%s" % (modrequestobj.host,
                                                 modrequestobj.port or 80,
                                                 modrequestobj.path))

            outreq = self.make_request(modrequestobj, parsedurl)

            if debug_level >= 2:
                print(">>>>>>>> REQUEST >>>>>>>>")
                print("%s %s" % (outreq.method, outreq.url))
                for k, v in outreq.headers.items():
                    print( "%s: %s" % (k, v))

            # send the request

            def _resp_callback(response):
                self.handle_response(response, context=modrequestobj.context)

            client = tornado.httpclient.AsyncHTTPClient(io_loop=io_loop)
            try:
                client.fetch(outreq, _resp_callback,
                             validate_cert=modrequestobj.validate_cert)
            except tornado.httpclient.HTTPError as e:
                if hasattr(e, 'response') and e.response:
                    self.handle_response(e.response,
                                         context=modrequestobj.context,
                                         error=True)
                else:
                    self.set_status(500)
                    self.write('Internal server error:\n' + str(e))
                    self.finish()


        def handle_response(self, response, context={}, error=False):

            if not isinstance(response, ResponseObj):
                if debug_level >= 4:
                    print("<<<<<<<< RESPONSE <<<<<<<")
                    pprint.pprint(response.__dict__)

                responseobj = ResponseObj(
                    code=response.code,
                    headers=response.headers,
                    pass_headers=True,
                    body=response.body,
                    context=context,
                )
            else:
                responseobj = response

            if debug_level >= 3:
                print("<<<<<<<< RESPONSEOBJ <<<<<<<")
                responseprint = copy(responseobj)
                responseprint.body = "-- body content not displayed --"
                pprint.pprint(responseprint.__dict__)

            if not error:
                mod = resp_callback(responseobj)
            else:
                mod = err_callback(responseobj)

            # set the response status code

            if mod.code == 599:
                self.set_status(500)
                self.write('Internal server error. Server unreachable.')
                self.finish()
                return

            self.set_status(mod.code)

            # set the response headers

            if type(mod.pass_headers) == bool:
                header_keys = mod.headers.keys() if mod.pass_headers else []
            else:
                header_keys = mod.pass_headers
            for key in header_keys:
                if key.lower() == "set-cookie":
                    cookies = Cookie.BaseCookie()
                    cookies.load(tornado.escape.native_str(mod.headers.get(key)))
                    for cookie_key in cookies:
                        cookie = cookies[cookie_key]
                        params = dict(cookie)
                        expires = params.pop('expires', None)
                        if expires:
                            expires = dateutil.parser.parse(expires)
                        self.set_cookie(
                            cookie.key,
                            cookie.value,
                            expires = expires,
                            **params
                        )
                else:
                    val = mod.headers.get(key)
                    self.set_header(key, val)

            if debug_level >= 2:
                print(">>>>>>>> RESPONSE (%s) >>>>>>>" % mod.code)
                for k, v in self._headers.items():
                    print("%s: %s" % (k, v))
                if hasattr(self, '_new_cookie'):
                    print(self._new_cookie.output())

            # set the response body

            if mod.body:
                self.write(mod.body)

            self.finish()

        @tornado.web.asynchronous
        def get(self):
            pass

        @tornado.web.asynchronous
        def options(self):
            pass

        @tornado.web.asynchronous
        def head(self):
            pass

        @tornado.web.asynchronous
        def put(self):
            self.request_future.set_result(True)

        @tornado.web.asynchronous
        def patch(self):
            self.request_future.set_result(True)

        @tornado.web.asynchronous
        def post(self):
            self.request_future.set_result(True)

        @tornado.web.asynchronous
        def delete(self):
            pass


    return ProxyHandler


def run_proxy(port,
              methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD'],
              req_callback=DEFAULT_CALLBACK,
              resp_callback=DEFAULT_CALLBACK,
              err_callback=DEFAULT_CALLBACK,
              test_ssl=False,
              debug_level=0,
              io_loop=None,
              address="",
              ):

    """
    Run proxy on the specified port.

    methods: the HTTP methods this proxy will support
    req_callback: a callback that is passed a RequestObj that it should
        modify and then return
    resp_callback: a callback that is given a ResponseObj that it should
        modify and then return
    err_callback: in the case of an error, this callback will be called.
        there's no difference between how this and the resp_callback are
        used.
    test_ssl: if true, will wrap the socket in an self signed ssl cert
    start_ioloop: if True (default), the tornado IOLoop will be started
        immediately.
    debug_level: 0 no debug, 1 basic, 2 verbose
    """

    io_loop = tornado.ioloop.IOLoop.instance() if io_loop is None else io_loop

    app = tornado.web.Application([
        (r'.*', _make_proxy(methods=methods,
                            io_loop=io_loop,
                            req_callback=req_callback,
                            resp_callback=resp_callback,
                            err_callback=err_callback,
                            debug_level=debug_level)),
    ])

    if test_ssl:
        this_dir, this_filename = os.path.split(__file__)
        kwargs = {
            "ssl_options": {
                "certfile": os.path.join(this_dir, "data", "test.crt"),
                "keyfile": os.path.join(this_dir, "data", "test.key"),
            },
            "io_loop": io_loop,
        }
    else:
        kwargs = {"io_loop": io_loop}

    http_server = tornado.httpserver.HTTPServer(app, **kwargs)
    http_server.listen(port, address)
    return http_server


if __name__ == '__main__':
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print("Starting HTTP proxy on port %d" % port)
    run_proxy(port)
