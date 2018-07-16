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
import logging
import json
import socket
import threading
import time

import tornado.web

from util.util import get_url_target
 
class Ping(object):
    def __init__(self):
        self._log = logging.getLogger("ping")
        self._log.setLevel(logging.DEBUG)

        self._ping_count = 0;
        self._request_count = 0;
        self._response_count = 0;

        self._pong_ip = None
        self._pong_port = None

        self._send_rate = 1 # per second

        self._close_lock = threading.Lock()

        self._enabled = False
        self._socket = None

    @property
    def rate(self):
        return self._send_rate

    @rate.setter
    def rate(self, value):
        self._log.debug("new rate: %s" % value)
        self._send_rate = value

    @property
    def pong_port(self):
        return self._pong_port

    @pong_port.setter
    def pong_port(self, value):
        self._log.debug("new pong port: %s" % value)
        self._pong_port = value

    @property
    def pong_ip(self):
        return self._pong_ip

    @pong_ip.setter
    def pong_ip(self, value):

        self._log.debug("new pong ip: %s" % value)
        self._pong_ip = value

    @property
    def enabled(self):
        return self._enabled

    @property
    def request_count(self):
        return self._request_count

    @property
    def response_count(self):
        return self._response_count

    def start(self):
        self._log.debug("starting")
        self._enabled = True
        # self.open_socket()
        self.send_thread = threading.Thread(target=self.send_ping)
        self.recv_thread = threading.Thread(target=self.recv_resp)
        self.send_thread.start()
        self.recv_thread.start()

    def stop(self):
        self._log.debug("stopping")
        self._enabled = False
        self.close_socket("stopping")

    def close_socket(self, msg):
        self._close_lock.acquire()
        if self._socket != None:
            self._socket.close()
            self._socket = None
            self._log.info("Closed socket with msg={}".format(msg))
        self._close_lock.release()

    def open_socket(self):
        try:
            self._log.debug("construct socket")
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(1)
        except socket.error as msg:
            self._log.error("error constructing socket %s" % msg)
            self._socket = None

        while self._enabled:
            try:
                self._log.info("Trying to connect....")
                self._socket.connect((self.pong_ip, self.pong_port))
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._log.info("Socket connected")
                break
            except socket.error as msg:
                time.sleep(1)
                

    def send_ping(self):
        self.open_socket()

        while self._enabled:
            if self._socket != None:
                req = "rwpingpong-{}".format(self._ping_count)
                try:
                    self._log.info("sending: %s" %req)
                    self._socket.sendall(req)
                    self._ping_count += 1
                    self._request_count += 1
                except socket.error as msg:
                    self._log.error("Error({}) sending data".format(msg))
                    self.close_socket(msg)
                    return
        
            time.sleep(1.0/self._send_rate)

        self._log.info("Stopping send_ping")

    def recv_resp(self):
        while self._enabled:
            respb = None
            if self._socket != None:
                try:
                    respb = self._socket.recv(1024)
                except socket.timeout:
                    continue
                except socket.error as msg:
                    self._log.error("Error({}) receiving data".format(msg))
                    time.sleep(1)
                    continue
                    # self.close_socket(msg)
                    # return

            if not respb:
                continue

            resp = respb.decode('UTF-8')
            self._response_count += 1
            self._log.info("receive: %s" % resp)

        self._log.info("Stopping recv_resp")

class PingServerHandler(tornado.web.RequestHandler):
    def initialize(self, ping_instance):
        self._ping_instance = ping_instance

    def get(self, args):
        response = {'ip': self._ping_instance.pong_ip,
                    'port': self._ping_instance.pong_port}

        self.write(response)

    def post(self, args):
        target = get_url_target(self.request.uri)
        body = self.request.body.decode("utf-8")
        body_header = self.request.headers.get("Content-Type")

        if "json" not in body_header:
            self.write("Content-Type must be some kind of json 2")
            self.set_status(405)
            return

        try:
            json_dicts = json.loads(body)
        except:
            self.write("Content-Type must be some kind of json 1")
            self.set_status(405)
            return

        if target == "server":
            if type(json_dicts['port']) is not int:
                self.set_status(405)
                return

            if type(json_dicts['ip']) not in (str, unicode):
                self.set_status(405)
                return

            self._ping_instance.pong_ip = json_dicts['ip']
            self._ping_instance.pong_port = json_dicts['port']

        else:
            self.set_status(404)
            return

        self.set_status(200)

class PingAdminStatusHandler(tornado.web.RequestHandler):
    def initialize(self, ping_instance):
        self._ping_instance = ping_instance

    def get(self, args):
        target = get_url_target(self.request.uri)
        if target == "state":
            value = "enabled" if self._ping_instance.enabled else "disabled"

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
            self.write("Content-Type must be some kind of json 2")
            self.set_status(405)            
            return
            
        try:
            json_dicts = json.loads(body)
        except:
            self.write("Content-Type must be some kind of json 1")
            self.set_status(405)            
            return

        if target == "state":
            if type(json_dicts['enable']) is not bool:
                self.set_status(405)            
                return

            if json_dicts['enable']:
                if not self._ping_instance.enabled:
                    self._ping_instance.start()
            else:
                self._ping_instance.stop()            

        else:
            self.set_status(404)
            return

        self.set_status(200)

class PingStatsHandler(tornado.web.RequestHandler):
    def initialize(self, ping_instance):
        self._ping_instance = ping_instance

    def get(self):
        response = {'ping-request-tx-count': self._ping_instance.request_count,
                    'ping-response-rx-count': self._ping_instance.response_count}

        self.write(response)

class PingRateHandler(tornado.web.RequestHandler):
    def initialize(self, ping_instance):
        self._ping_instance = ping_instance

    def get(self, args):
        response = { 'rate': self._ping_instance.rate }

        self.write(response)

    def post(self, args):
        target = get_url_target(self.request.uri)
        body = self.request.body.decode("utf-8")
        body_header = self.request.headers.get("Content-Type")

        if "json" not in body_header:
            self.set_status(405)
            return

        try:
            json_dicts = json.loads(body)
        except:
            self.set_status(405)
            return

        if target == "rate":
            if type(json_dicts['rate']) is not int:
                self.set_status(405)
                return

            self._ping_instance.rate = json_dicts['rate']
        else:
            self.set_status(404)
            return

        self.set_status(200)
