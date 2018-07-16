#
#   Copyright 2016-2017 RIFT.IO Inc
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
    RwcalYang as rwcal,
    RwTypes,
    ProtobufC,
    )

import rift.mano.cloud
import rift.mano.ro_account
import rift.mano.dts as mano_dts
import rift.tasklets

from . import rwnsmplugin

class CloudAccountConfigSubscriber:
    def __init__(self, log, dts, log_hdl, project):
        self._dts = dts
        self._log = log
        self._log_hdl = log_hdl
        self._project = project
        
        self._cloud_sub = rift.mano.cloud.CloudAccountConfigSubscriber(
                self._dts,
                self._log,
                self._log_hdl,
                self._project,
                rift.mano.cloud.CloudAccountConfigCallbacks())

    def get_cloud_account_sdn_name(self, account_name):
        if account_name in self._cloud_sub.accounts:
            self._log.debug("Cloud accnt msg is %s",self._cloud_sub.accounts[account_name].account_msg)
            if self._cloud_sub.accounts[account_name].account_msg.has_field("sdn_account"):
                sdn_account = self._cloud_sub.accounts[account_name].account_msg.sdn_account
                self._log.info("SDN associated with Cloud name %s is %s", account_name, sdn_account)
                return sdn_account
            else:
                self._log.debug("No SDN Account associated with Cloud name %s", account_name)
                return None

    def get_cloud_account_msg(self,account_name):
        if account_name in self._cloud_sub.accounts:
            self._log.debug("Cloud accnt msg is %s",self._cloud_sub.accounts[account_name].account_msg)
            return self._cloud_sub.accounts[account_name].account_msg

    @asyncio.coroutine
    def register(self):
       yield from self._cloud_sub.register()

    def deregister(self):
       self._cloud_sub.deregister()

class ROAccountConfigSubscriber:
    def __init__(self, dts, log, loop, project, records_publisher):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._records_publisher = records_publisher

        self._log.debug("Inside cloud - RO Account Config Subscriber init")
        
        self._ro_sub = rift.mano.ro_account.ROAccountConfigSubscriber(
                self._dts,
                self._log,
                self._loop,
                self._project,
                self._records_publisher,
                rift.mano.ro_account.ROAccountConfigCallbacks())

    def get_ro_plugin(self, account_name):
        if  (account_name is not None) and (account_name in self._ro_sub.accounts):
            ro_account = self._ro_sub.accounts[account_name]
            self._log.debug("RO Account associated with name %s is %s", account_name, ro_account)
            return ro_account.ro_plugin

        self._log.debug("RO Account associated with name %s using default plugin", account_name)
        return rwnsmplugin.RwNsPlugin(self._dts, self._log, self._loop, self._records_publisher, None, self._project)
            
    @asyncio.coroutine
    def register(self):
       self._log.debug("Registering ROAccount Config Subscriber")
       yield from self._ro_sub.register()

    def deregister(self):
       self._ro_sub.deregister()