#!/usr/bin/env python
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

import argparse
import signal
import logging

import tornado
import tornado.httpserver

from pong import (
    Pong,
    PongAdminStatusHandler,
    PongServerHandler,
    PongStatsHandler,
)
from util.util import (
    VersionHandler,    
)

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(name)-8s :: %(message)s',
)

def main():
    log = logging.getLogger("main")

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pong-manager-port",
        required=False,
        default="18889",
        help="port number for pong")
    parser.add_argument(
        "--worker-count",
        required=False,
        default=5,
        help="ip address of pong")

    arguments = parser.parse_args()

    # setup application
    log.debug("setup application")
    pong_instance = Pong(arguments.worker_count)
    pong_application_arguments = {'pong_instance': pong_instance}
    pong_application = tornado.web.Application([
        (r"/version", VersionHandler, pong_application_arguments),
        (r"/api/v1/pong/stats", PongStatsHandler, pong_application_arguments),
        (r"/api/v1/pong/server/?([0-9a-z\.]*)", PongServerHandler, pong_application_arguments),
        (r"/api/v1/pong/adminstatus/([a-z]+)", PongAdminStatusHandler, pong_application_arguments)
    ])
    pong_server = tornado.httpserver.HTTPServer(
        pong_application)

    # setup SIGINT handler
    log.debug("setup SIGINT handler")
    def signal_handler(signal, frame):
        print("") # print newline to clear user input
        log.info("Exiting")
        pong_instance.stop()
        pong_server.stop()
        log.info("Sayonara!")
        quit()

    signal.signal(signal.SIGINT, signal_handler)
    
    # start
    log.debug("pong application listening on %s" % arguments.pong_manager_port)
    try:
        pong_server.listen(arguments.pong_manager_port)
    except OSError:
        print("port %s is already is use, exiting" % arguments.ping_manager_port)
        return
    tornado.ioloop.IOLoop.instance().start()
    
if __name__ == "__main__":
    main()


