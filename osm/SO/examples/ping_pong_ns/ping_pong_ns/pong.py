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

from datetime import date
from Queue import Queue
import logging
import json
import socket
import threading
import time

import tornado.web

from util.util import get_url_target
 
class Stats(object):
    def __init__(self):
        self._request_count = 0
        self._response_count = 0

        self._lock = threading.Lock()

    @property
    def request_count(self):
        with self._lock:
            return self._request_count

    @request_count.setter
    def request_count(self, value):
        with self._lock:
            self._request_count = value

    @property
    def response_count(self):
        with self._lock:
            return self._response_count

    @response_count.setter
    def response_count(self, value):
        with self._lock:
            self._response_count = value
        
class Worker(threading.Thread):
    def __init__(self, log, connections, stats):
        super(Worker, self).__init__()
        self._log = log
        self._connections = connections
        self._stats = stats

        self._running = True

        self._lock = threading.Lock()
        
    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value

    def run(self):
        while self.running:
            try:
                connection = self._connections.get_nowait()
            except:
                continue
            
            try:
                req = connection.recv(1024)
            except socket.error as msg:
                self._log.error("error with connection read: " % msg)
                self._connections.put(connection)
                continue

            if not req:
                self._connections.put(connection)
                continue

            resp = req.decode('UTF-8')
            self._log.debug("got: %s", resp)

            self._stats.request_count += 1

            try:
                connection.sendall(resp)
                self._stats.response_count += 1
            except socket.error as msg:
                self._log.error("error with connection read: " % msg)
                self._connections.put(connection)
                continue

            self._connections.put(connection)        

class Pong(object):
    def __init__(self, worker_count=5):
        self._log = logging.getLogger("pong")
        self._log.setLevel(logging.DEBUG)

        self.listen_ip = None
        self.listen_port = None

        self._lock = threading.Lock()

        self._connections = Queue()
        
        self._stats = Stats()

        self._workers = list()

        self._enabled = False

        for _ in range(worker_count):
            self._workers.append(Worker(self._log, self._connections, self._stats))

    @property
    def listen_port(self):
        return self._listen_port

    @listen_port.setter
    def listen_port(self, value):
        self._log.debug("new listen port: %s" % value)
        self._listen_port = value

    @property
    def listen_ip(self):
        return self._listen_ip

    @listen_ip.setter
    def listen_ip(self, value):
        self._log.debug("listen pong ip: %s" % value)
        self._listen_ip = value


    @property
    def enabled(self):
        with self._lock:
            return self._enabled

    @property
    def request_count(self):
        return self._stats.request_count

    @property
    def response_count(self):
        return self._stats.response_count

    def start(self):
        self._log.debug("starting")
        self._enabled = True
        self.listener_thread = threading.Thread(target=self._listen)
        self.listener_thread.start()
        for worker in self._workers:
            worker.start()

    def stop(self):
        with self._lock:
            self._enabled = False

            self._log.debug("stopping workers")
            for worker in self._workers:
                worker.running = False

            self._log.debug("joining on workers")
            for worker in self._workers:
                if worker.is_alive():
                    worker.join()

            while self._connections.full():
                try:
                    connection = self._connections.get_nowait()
                    connection.close()
                except:
                    pass

    def close_socket(self, msg):
        with self._lock:
            if self._socket != None:
                self._socket.shutdown(socket.SHUT_RD)
                self._socket.close()
                self._socket = None
                self._log.info("Closed socket with msg={}".format(msg))

    def _listen(self):
        if self._listen_ip is None or self.listen_port is None:
            self._log.error("address not properly configured to listen")
            return

        self._log.info("listen for incomming connections")
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # self._socket.bind((self.listen_ip, self.listen_port))
            self._socket.bind(("0.0.0.0", self.listen_port))
            self._socket.settimeout(1)

            while self.enabled:
                
                try:
                    self._socket.listen(1)
                    connection, address = self._socket.accept()
                except socket.timeout:
                    continue
                self._log.info("Accepted connection from {}".format(address))

                self._connections.put(connection)
            else:
                self.stop()
        except socket.error as msg:
            self.close_socket(msg)

class PongStatsHandler(tornado.web.RequestHandler):
    def initialize(self, pong_instance):
        self._pong_instance = pong_instance

    def get(self):
        response = {'ping-request-rx-count': self._pong_instance.request_count,
                    'ping-response-tx-count': self._pong_instance.response_count}

        self.write(response)


class PongServerHandler(tornado.web.RequestHandler):
    def initialize(self, pong_instance):
        self._pong_instance = pong_instance

    def get(self, args):
        response = {'ip': self._pong_instance.listen_ip,
                    'port': self._pong_instance.listen_port}

        self.write(response)

    def post(self, args):
        target = get_url_target(self.request.uri)
        body = self.request.body.decode("utf-8")
        body_header = self.request.headers.get("Content-Type")

        if "json" not in body_header:
            self.write("Content-Type must be some kind of json")
            self.set_status(405)
            return

        try:
            json_dicts = json.loads(body)
        except:
            self.write("Content-Type must be some kind of json")
            self.set_status(405)
            return

        if target == "server":

            if type(json_dicts['port']) is not int:
                self.set_status(405)
                return

            if type(json_dicts['ip']) not in (str, unicode):
                self.set_status(405)
                return

            self._pong_instance.listen_ip = json_dicts['ip']
            self._pong_instance.listen_port = json_dicts['port']

        else:
            self.set_status(404)
            return

        self.set_status(200)

class PongAdminStatusHandler(tornado.web.RequestHandler):
    def initialize(self, pong_instance):
        self._pong_instance = pong_instance

    def get(self, args):
        target = get_url_target(self.request.uri)
        
        if target == "state":
            value = "enabled" if self._pong_instance.enabled else "disabled"

            response = { 'adminstatus': value }
        else:
            self.set_status(404)
            return

        self.write(response)

    def post(self, args):
        target = get_url_target(self.request.uri)
        body = self.request.body.decode("utf-8")
        body_header = self.request.headers.get("Content-Type")

        if "json" not in body_header:
            self.write("Content-Type must be some kind of json")
            self.set_status(405)            
            return
            
        try:
            json_dicts = json.loads(body)
        except:
            self.write("Content-Type must be some kind of json")
            self.set_status(405)            
            return

        if target == "state":
            if type(json_dicts['enable']) is not bool:
                self.set_status(405)            
                return

            if json_dicts['enable']:
                if not self._pong_instance.enabled:
                    self._pong_instance.start()
            else:
                self._pong_instance.stop()

        else:
            self.set_status(404)
            return

        self.set_status(200)


