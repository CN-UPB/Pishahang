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

@file utils.py
@author Varun Prasad(varun.prasad@riftio.com)
@date 2016-06-14
"""

import logging
import os
import sys

import gi
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwLog', '1.0')

from gi.repository import RwcalYang
import rift.rwcal.cloudsim.net as net
import rwlogger
import rw_peas


class Logger():
    """A wrapper to hold all logging related configuration. """
    LOG_FILE = "/var/log/rift/cloudsim_server.log"
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __init__(self, daemon_mode=True, log_name=__name__, log_level=logging.DEBUG):
        """
        Args:
            daemon_mode (bool, optional): If set, then logs are pushed to the
                    file.
            log_name (str, optional): Logger name
            log_level (<Log level>, optional): INFO, DEBUG ..
        """
        self.logger = logging.getLogger(log_name)
        logging.basicConfig(level=log_level, format=self.FORMAT)

        if daemon_mode:
            handler = logging.FileHandler(self.LOG_FILE)
            handler.setFormatter(logging.Formatter(self.FORMAT))
            self.logger.addHandler(handler)



class CloudSimCalMixin(object):
    """Mixin class to provide cal plugin and account access to classes.
    """

    def __init__(self):
        self._cal, self._account = None, None

    @property
    def cal(self):
        if not self._cal:
            self.load_plugin()
        return self._cal

    @property
    def account(self):
        if not self._account:
            self.load_plugin()
        return self._account

    def load_plugin(self):
        """Load the cal plugin and account

        Returns:
            Tuple (Cal, Account)
        """
        plugin = rw_peas.PeasPlugin('rwcal_cloudsimproxy', 'RwCal-1.0')
        engine, info, extension = plugin()

        rwloggerctx = rwlogger.RwLog.Ctx.new("Cal-Log")
        cal = plugin.get_interface("Cloud")
        rc = cal.init(rwloggerctx)

        account = RwcalYang.CloudAccount()
        account.account_type = "cloudsim_proxy"
        account.cloudsim_proxy.host = "192.168.122.1"

        self._cal, self._account = cal, account


def check_and_create_bridge(func):
    """Decorator that checks if a bridge is available in the VM, if not checks
    for permission and tries to create one.
    """

    def func_wrapper(*args, **kwargs):
        logging.debug("Checking if bridge exists")

        if net.bridge_exists('virbr0'):
            logging.debug("Bridge exists, can proceed with further operations.")
        else:
            logging.warning("No Bridge exists, trying to create one.")

            if os.geteuid() != 0:
                logging.error("No bridge exists and cannot create one due to "
                    "insufficient privileges. Please create it manually using "
                    "'virsh net-start default' or re-run the same command as root.")
                sys.exit(1)

            net.virsh_initialize_default()

        return func(*args, **kwargs)

    return func_wrapper

