"""
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

@file cal_server.py
@author Austin Cormier(austin.cormier@riftio.com)
@author Varun Prasad(varun.prasad@riftio.com)
@date 2016-06-14
"""

import asyncio
import logging
import os
import signal
import sys

import tornado
import tornado.httpserver
import tornado.web
import tornado.platform.asyncio

import gi
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwCal', '1.0')
gi.require_version('RwLog', '1.0')
gi.require_version('RwTypes', '1.0')
from gi.repository import (
    RwcalYang,
    RwLog
)

import rw_peas
import rift.tasklets
import rift.rwcal.cloudsim.net
import rift.rwcal.cloudsim.lvm as lvm
import rift.rwcal.cloudsim.lxc as lxc
import rift.rwcal.cloudsim.shell as shell

from . import app

logger = logging.getLogger(__name__)

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async


class CalServer():
    HTTP_PORT = 9002
    cal_interface = None

    @staticmethod
    def verify_requirements(log):
        """
        Check if all the requirements are met
        1. bridgeutils should be installed
        2. The user should be root
        """
        try:
            shell.command('/usr/sbin/brctl show')
        except shell.ProcessError:
            log.exception('/usr/sbin/brctl command not found, please install '
                'bridge-utils (yum install bridge-utils)')
            sys.exit(1)

        if os.geteuid() != 0:
            log.error("User should be root to start the server.")
            sys.exit(1)

    def __init__(self, logging_level=logging.DEBUG):
        self.app = None
        self.server = None
        self.log_hdl = RwLog.Ctx.new("a")
        self.log = logger
        self.log.setLevel(logging_level)

    def get_cal_interface(self):
        self.log.debug("Creating CAL interface.")
        if CalServer.cal_interface is None:
            plugin = rw_peas.PeasPlugin('rwcal_cloudsim', 'RwCal-1.0')
            engine, info, extension = plugin()

            CalServer.cal_interface = plugin.get_interface("Cloud")
            CalServer.cal_interface.init(self.log_hdl)

        return CalServer.cal_interface

    def cleanup(self):
        self.log.info("Cleaning up resources and backing store.")
        for container in lxc.containers():
            self.log.debug("Stopping {}".format(container))
            lxc.stop(container)

        for container in lxc.containers():
            lxc.destroy(container)

        lvm.destroy('rift')


    def start(self):
        """Start the server."""

        cal = self.get_cal_interface()
        account = RwcalYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList(account_type="cloudsim")

        tornado.platform.asyncio.AsyncIOMainLoop().install()
        loop = asyncio.get_event_loop()

        self.app = app.CalProxyApp(self.log, loop, cal, account)
        self.server = tornado.httpserver.HTTPServer(self.app)

        self.log.info("Starting Cal Proxy Http Server on port %s",
                      CalServer.HTTP_PORT)
        self.server.listen(CalServer.HTTP_PORT)

        def startup():
            self.log.info("Creating a default network")
            rift.rwcal.cloudsim.net.virsh_initialize_default()
            self.log.info("Creating backing store")
            lvm.create('rift')

        loop.add_signal_handler(signal.SIGHUP, self.cleanup)
        loop.add_signal_handler(signal.SIGTERM, self.cleanup)

        try:
            loop.run_in_executor(None, startup)
            loop.run_forever()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as exc:
            self.log.exception(exc)


    def stop(self):
      try:
         self.server.stop()
      except Exception:
         self.log.exception("Caught Exception in LP stop:", sys.exc_info()[0])
         raise
