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

from ping import (
    Ping,
    PingAdminStatusHandler,
    PingServerHandler,
    PingRateHandler,
    PingStatsHandler,
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
        "--ping-manager-port",
        required=False,
        default="18888",
        help="port number for ping")

    arguments = parser.parse_args()

    # setup application
    log.debug("setup application")
    ping_instance = Ping()
    ping_application_arguments = {'ping_instance': ping_instance}
    ping_application = tornado.web.Application([
        (r"/api/v1/ping/stats", PingStatsHandler, ping_application_arguments),
        (r"/api/v1/ping/adminstatus/([a-z]+)", PingAdminStatusHandler, ping_application_arguments),
        (r"/api/v1/ping/server/?([0-9a-z\.]*)", PingServerHandler, ping_application_arguments),
        (r"/api/v1/ping/rate/?([0-9]*)", PingRateHandler, ping_application_arguments),
        (r"/version", VersionHandler, ping_application_arguments)
    ])
    ping_server = tornado.httpserver.HTTPServer(
        ping_application)

    # setup SIGINT handler
    log.debug("setup SIGINT handler")
    def signal_handler(signal, frame):
        print("") # print newline to clear user input
        log.info("Exiting")
        ping_instance.stop()
        ping_server.stop()
        log.info("Sayonara!")
        quit()

    signal.signal(signal.SIGINT, signal_handler)
    
    # start
    log.debug("start")
    try:
        ping_server.listen(arguments.ping_manager_port)
    except OSError:
        print("port %s is already is use, exiting" % arguments.ping_manager_port)
        return

    tornado.ioloop.IOLoop.instance().start()
    
if __name__ == "__main__":
    main()


