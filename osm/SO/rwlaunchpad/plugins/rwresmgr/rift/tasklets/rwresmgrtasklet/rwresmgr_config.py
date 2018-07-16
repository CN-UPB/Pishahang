
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
import logging
import time
import uuid
from enum import Enum

import gi
gi.require_version('RwDts', '1.0')
gi.require_version('RwYang', '1.0')
gi.require_version('RwResourceMgrYang', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('RwcalYang', '1.0')

from gi.repository import (
    RwDts as rwdts,
    RwYang,
    RwResourceMgrYang,
    RwLaunchpadYang,
    RwcalYang,
)

from gi.repository.RwTypes import RwStatus
import rift.tasklets
import rift.mano.cloud


class ResourceMgrConfig(object):
    XPATH_POOL_OPER_DATA = "D,/rw-resource-mgr:resource-pool-records"
    def __init__(self, dts, log, rwlog_hdl, loop, parent):
        self._dts = dts
        self._log = log
        self._rwlog_hdl = rwlog_hdl
        self._loop = loop
        self._parent = parent

        self._cloud_sub = None
        self._res_sub = None
        self._project = parent._project

    @asyncio.coroutine
    def register(self):
        yield from self.register_resource_pool_operational_data()
        yield from self.register_cloud_account_config()

    def deregister(self):
        self._log.debug("De-register for project {}".format(self._project.name))
        if self._cloud_sub:
            self._cloud_sub.deregister()
            self._cloud_sub = None

        if self._res_sub:
            self._res_sub.delete_element(
                self._project.add_project(ResourceMgrConfig.XPATH_POOL_OPER_DATA))
            self._res_sub.deregister()
            self._res_sub = None

    @asyncio.coroutine
    def register_cloud_account_config(self):
        def on_add_cloud_account_apply(account):
            self._log.debug("Received on_add_cloud_account: %s", account)
            self._parent.add_cloud_account_config(account)

        def on_delete_cloud_account_apply(account_name):
            self._log.debug("Received on_delete_cloud_account_apply: %s", account_name)
            self._parent.delete_cloud_account_config(account_name)

        @asyncio.coroutine
        def on_delete_cloud_account_prepare(account_name):
            self._log.debug("Received on_delete_cloud_account_prepare: %s", account_name)
            self._parent.delete_cloud_account_config(account_name, dry_run=True)

        cloud_callbacks = rift.mano.cloud.CloudAccountConfigCallbacks(
                on_add_apply=on_add_cloud_account_apply,
                on_delete_apply=on_delete_cloud_account_apply,
                on_delete_prepare=on_delete_cloud_account_prepare,
                )

        self._cloud_sub = rift.mano.cloud.CloudAccountConfigSubscriber(
            self._dts, self._log, self._rwlog_hdl,
            self._project, cloud_callbacks
        )
        yield from self._cloud_sub.register()

    @asyncio.coroutine
    def register_resource_pool_operational_data(self):
        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            self._log.debug("ResourceMgr providing resource-pool information")
            msg = RwResourceMgrYang.YangData_RwProject_Project_ResourcePoolRecords()

            cloud_accounts = self._parent.get_cloud_account_names()
            for cloud_account_name in cloud_accounts:
                pools = self._parent.get_pool_list(cloud_account_name)
                self._log.debug("Publishing information about cloud account %s %d resource pools",
                                cloud_account_name, len(pools))

                cloud_account_msg = msg.cloud_account.add()
                cloud_account_msg.name = cloud_account_name
                for pool in pools:
                    pool_info = self._parent.get_pool_info(cloud_account_name, pool.name)
                    cloud_account_msg.records.append(pool_info)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK,
                                    self._project.add_project(ResourceMgrConfig.XPATH_POOL_OPER_DATA),
                                    msg=msg,)

        xpath = self._project.add_project(ResourceMgrConfig.XPATH_POOL_OPER_DATA)
        self._log.debug("Registering for Resource Mgr resource-pool-record using xpath: {}".
                        format(xpath))

        handler=rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare)
        self._res_sub = yield from self._dts.register(xpath=xpath,
                                                      handler=handler,
                                                      flags=rwdts.Flag.PUBLISHER)
