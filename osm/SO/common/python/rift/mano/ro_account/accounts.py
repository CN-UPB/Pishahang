
#
#   Copyright 2017 RIFT.IO Inc
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
import asyncio

from gi.repository import (
    RwDts as rwdts,
    RwRoAccountYang,
    )

import rift.mano.dts as mano_dts
import rift.tasklets

from rift.tasklets.rwnsmtasklet import openmano_nsm
from rift.tasklets.rwnsmtasklet import rwnsmplugin

class ROAccount(object):
    """
    RO Account Model class
    """
    DEFAULT_PLUGIN = rwnsmplugin.RwNsPlugin

    def __init__(self, dts=None, log=None, loop=None, project=None, records_publisher=None, account_msg=None):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._records_publisher = records_publisher
        self._account_msg = None
        if account_msg is not None:
            self._account_msg = account_msg.deep_copy()
            self._name = self._account_msg.name

        self._datacenters = []
        self._status = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConnectionStatus(
                status="unknown",
                details="Connection status lookup not started"
                )
        self.live_instances = 0

        if self._dts is None:
            return

        self._nsm_plugins = rwnsmplugin.NsmPlugins()
        self._nsm_cls = self.DEFAULT_PLUGIN

        try:
            self._nsm_cls = self._nsm_plugins.class_by_plugin_name(
                    account_msg.ro_account_type
                    )
        except KeyError as e:
            self._log.warning(
                "RO account nsm plugin not found: %s.  Using standard rift nsm.",
                account_msg.name
                )

        self._ro_plugin = self._create_plugin(self._nsm_cls, account_msg)

    @property
    def name(self):
        return self._name

    @property
    def account_msg(self):
        return self._account_msg

    @property
    def ro_acccount_type(self):
        return self._account_msg.ro_account_type if self._account_msg else 'rift'

    @property
    def ro_plugin(self):
        return self._ro_plugin

    @property
    def connection_status(self):
        return self._status

    def _create_plugin(self, nsm_cls, account_msg):
        self._log.debug("Instantiating new RO account using class: %s", nsm_cls)
        nsm_instance = nsm_cls(self._dts, self._log, self._loop,
                               self._records_publisher, account_msg, self._project)
        return nsm_instance

    def check_ro_account_status(self):
        self._log.debug("Checking RO Account Status. Acct: %s",
                        self.name)
        self._status = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConnectionStatus(
                status="validating",
                details="RO account connection status check in progress"
                )
        try:
            datacenter_copy = []
            for uuid, name in self._ro_plugin._cli_api.datacenter_list():
                datacenter_copy.append({
                            'uuid':uuid,
                            'name':name
                            }
                        )
            self._datacenters = datacenter_copy
            self._status = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConnectionStatus(
                status="success",
                details="RO account connection status success"
                )
        except:
            self._status = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConnectionStatus(
                status="failure",
                details="RO account connection status failure"
                )
            self._log.warning("RO account connection status failure, Acct:%s, status:%s",
                              self.name, self._status)

    def start_validate_ro_account(self, loop):
        loop.run_in_executor(None, self.check_ro_account_status)
