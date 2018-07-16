
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
import gi
import rift.tasklets

from gi.repository import(
        RwCloudYang,
        RwDts as rwdts,
        RwTypes,
        )
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class CloudAccountNotFound(Exception):
    pass


class CloudAccountDtsOperdataHandler(object):
    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

        self._regh = None
        self._rpc = None
        self.cloud_accounts = {}

    def add_cloud_account(self, account):
        self.cloud_accounts[account.name] = account
        asyncio.ensure_future(
                account.start_validate_credentials(self._loop),
                loop=self._loop
                )

    def delete_cloud_account(self, account_name):
        del self.cloud_accounts[account_name]

    def get_saved_cloud_accounts(self, cloud_account_name):
        ''' Get Cloud Account corresponding to passed name, or all saved accounts if name is None'''
        saved_cloud_accounts = []

        if cloud_account_name is None or cloud_account_name == "":
            cloud_accounts = list(self.cloud_accounts.values())
            saved_cloud_accounts.extend(cloud_accounts)
        elif cloud_account_name in self.cloud_accounts:
            account = self.cloud_accounts[cloud_account_name]
            saved_cloud_accounts.append(account)
        else:
            errstr = "Cloud account {} does not exist".format(cloud_account_name)
            raise KeyError(errstr)

        return saved_cloud_accounts

    @asyncio.coroutine
    def create_notification(self, account):
        xpath = "N,/rw-cloud:cloud-notif"
        ac_status = RwCloudYang.YangNotif_RwCloud_CloudNotif()
        ac_status.name = account.name
        ac_status.message = account.connection_status.details

        yield from self._dts.query_create(xpath, rwdts.XactFlag.ADVISE, ac_status)
        self._log.info("Notification called by creating dts query: %s", ac_status)


    @asyncio.coroutine
    def _register_show_status(self):
        def get_xpath(cloud_name=None):
            return "D,/rw-cloud:cloud/account{}/connection-status".format(
                 "[name=%s]" % quoted_key(cloud_name) if cloud_name is not None else ''
            )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwCloudYang.YangData_RwProject_Project_Cloud_Account.schema().keyspec_to_entry(ks_path)
            cloud_account_name = path_entry.key00.name

            try:
                saved_accounts = self.get_saved_cloud_accounts(cloud_account_name)
                for account in saved_accounts:
                    connection_status = account.connection_status
                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=account.connection_status,
                            )
            except KeyError as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(get_xpath())
        self._regh = yield from self._dts.register(
                xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def _register_validate_rpc(self):
        def get_xpath():
            return "/rw-cloud:update-cloud-status"

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            if not msg.has_field("cloud_account"):
                raise CloudAccountNotFound("Cloud account name not provided")
            cloud_account_name = msg.cloud_account

            if not self._project.rpc_check(msg, xact_info=xact_info):
                return

            try:
                account = self.cloud_accounts[cloud_account_name]
            except KeyError:
                errmsg = "Cloud account name {} not found in project {}". \
                         format(cloud_account_name, self._project.name)
                xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           get_xpath(),
                                           errmsg)
                raise CloudAccountNotFound(errmsg)

            yield from account.start_validate_credentials(self._loop)

            yield from self.create_notification(account)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._rpc = yield from self._dts.register(
                xpath=get_xpath(),
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def register(self):
        self._log.debug("Register cloud account for project %s", self._project.name)
        yield from self._register_show_status()
        yield from self._register_validate_rpc()

    def deregister(self):
        self._log.debug("De-register cloud account for project %s", self._project.name)
        self._rpc.deregister()
        self._regh.deregister()
