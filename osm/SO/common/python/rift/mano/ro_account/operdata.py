
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
import gi
import rift.mano.dts as mano_dts
import rift.tasklets
from . import accounts

from gi.repository import(
        RwRoAccountYang,
        RwDts as rwdts,
        RwTypes,
        )
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class ROAccountNotFound(Exception):
    pass

class ROAccountDtsOperdataHandler(object):
    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

        self._regh = None
        self._rpc = None
        self._rsic = None
        self._rdcp = None
        self.ro_accounts = {}
        self._nsr_sub = mano_dts.NsInstanceConfigSubscriber(
                                self._log,
                                self._dts,
                                self._loop,
                                self._project,
                                callback=self.handle_nsr)

    def handle_nsr(self, nsr, action):
        if action == rwdts.QueryAction.CREATE:
            try:
                self.ro_accounts[nsr.resource_orchestrator].live_instances += 1
            except KeyError as e:
                self.ro_accounts['rift'].live_instances += 1
        elif action == rwdts.QueryAction.DELETE:
            try:
                self.ro_accounts[nsr.resource_orchestrator].live_instances -= 1
            except KeyError as e:
                self.ro_accounts['rift'].live_instances -= 1

    def get_xpath(self):
        return "D,/rw-ro-account:ro-account-state/account"

    def get_qualified_xpath(self, ro_account_name):
        if ro_account_name is None:
            raise Exception("Account name cannot be None")

        return self._project.add_project("D,/rw-ro-account:ro-account-state/account{}".format(
             "[name=%s]" % quoted_key(ro_account_name))
        )

    def add_rift_ro_account(self):
        rift_acc = accounts.ROAccount()
        rift_acc._name = 'rift'
        rift_acc._status = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConnectionStatus(
                                                        status="success",
                                                        details="RO account connection status success"
                                                        )
        self.ro_accounts[rift_acc.name] = rift_acc
        rift_acc_state = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account(name=rift_acc.name)
        self._regh.create_element(self.get_qualified_xpath(rift_acc.name), rift_acc_state)

    def add_ro_account(self, account):
        self.ro_accounts[account.name] = account
        account.start_validate_ro_account(self._loop)

    def delete_ro_account(self, account_name):
        account = self.ro_accounts[account_name]
        del self.ro_accounts[account_name]

    def get_saved_ro_accounts(self, ro_account_name):
        ''' Get RO Account corresponding to passed name, or all saved accounts if name is None'''
        saved_ro_accounts = []

        if ro_account_name is None or ro_account_name == "":
            ro_accounts = list(self.ro_accounts.values())
            saved_ro_accounts.extend(ro_accounts)
        elif ro_account_name in self.ro_accounts:
            account = self.ro_accounts[ro_account_name]
            saved_ro_accounts.append(account)
        else:
            errstr = "RO account {} does not exist".format(ro_account_name)
            raise KeyError(errstr)

        return saved_ro_accounts

    @asyncio.coroutine
    def _register_show_status(self):
        def get_xpath(ro_account_name):
            return "D,/rw-ro-account:ro-account-state/account{}/connection-status".format(
                 "[name=%s]" % quoted_key(ro_account_name)
            )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account.schema().keyspec_to_entry(ks_path)
            ro_account_name = path_entry.key00.name

            try:
                saved_accounts = self.get_saved_ro_accounts(ro_account_name)
                for account in saved_accounts:
                    connection_status = account._status

                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=account._status,
                            )
            except Exception as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(self.get_xpath())
        self._regh = yield from self._dts.register(
                xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare),
                flags=rwdts.Flag.PUBLISHER,
                )

        #ATTN: TODO: Should ideally wait for
        #on_ready callback to be called.
        self.add_rift_ro_account()

    @asyncio.coroutine
    def _register_show_instance_count(self):
        def get_xpath(ro_account_name=None):
            return "D,/rw-ro-account:ro-account-state/account{}/instance-ref-count".format(
                 "[name=%s]" % quoted_key(ro_account_name) if ro_account_name is not None else ''
            )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account.schema().keyspec_to_entry(ks_path)
            ro_account_name = path_entry.key00.name

            try:
                saved_accounts = self.get_saved_ro_accounts(ro_account_name)
                for account in saved_accounts:
                    instance_count = account.live_instances
                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_InstanceRefCount(count=instance_count)
                            )
            except KeyError as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(get_xpath())
        self._rsic = yield from self._dts.register(
                xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def _register_validate_rpc(self):
        def get_xpath():
            return "/rw-ro-account:update-ro-account-status"

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            if not msg.has_field("ro_account"):
                raise ROAccountNotFound("RO account name not provided")
            ro_account_name = msg.ro_account

            if not self._project.rpc_check(msg, xact_info=xact_info):
                return

            try:
                account = self.ro_accounts[ro_account_name]
            except KeyError:
                errmsg = "RO account name {} not found in project {}". \
                         format(ro_account_name, self._project.name)
                xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           get_xpath(),
                                           errmsg)
                raise ROAccountNotFound(errmsg)

            if ro_account_name != 'rift':
                account.start_validate_ro_account(self._loop)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._rpc = yield from self._dts.register(
                xpath=get_xpath(),
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def _register_data_center_publisher(self):
        def get_xpath(ro_account_name=None):
            return "D,/rw-ro-account:ro-account-state/account{}/datacenters".format(
                 "[name=%s]" % quoted_key(ro_account_name) if ro_account_name is not None else ''
            )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account.schema().keyspec_to_entry(ks_path)
            ro_account_name = path_entry.key00.name

            try:
                saved_accounts = self.get_saved_ro_accounts(ro_account_name)
                for account in saved_accounts:
                    datacenters = []
                    if account.name == 'rift':
                        datacenters = [{'name': cloud.name, 'datacenter_type': cloud.account_type}
                                                    for cloud in self._project.cloud_accounts]
                    else :
                        datacenters = account._datacenters

                    response = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_Datacenters()
                    response.from_dict({'datacenters': datacenters})
                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=response
                            )
            except KeyError as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(get_xpath())
        self._rdcp = yield from self._dts.register(
                xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def _register_config_data_publisher(self):
        def get_xpath(ro_account_name=None):
            return "D,/rw-ro-account:ro-account-state/account{}/config-data".format(
                 "[name=%s]" % quoted_key(ro_account_name) if ro_account_name is not None else ''
            )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account.schema().keyspec_to_entry(ks_path)
            ro_account_name = path_entry.key00.name

            try:
                saved_accounts = self.get_saved_ro_accounts(ro_account_name)
                for account in saved_accounts:
                    ro_acct_type = account.ro_acccount_type

                    response = RwRoAccountYang.YangData_RwProject_Project_RoAccountState_Account_ConfigData(ro_account_type=ro_acct_type)
                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=response
                            )
            except KeyError as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(get_xpath())
        self._rcdp = yield from self._dts.register(
                xpath=xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare),
                flags=rwdts.Flag.PUBLISHER,
                )

    @asyncio.coroutine
    def register(self):
        self._log.debug("Register RO account for project %s", self._project.name)
        yield from self._register_show_status()
        yield from self._register_validate_rpc()
        yield from self._register_show_instance_count()
        yield from self._register_data_center_publisher()
        yield from self._register_config_data_publisher()
        yield from self._nsr_sub.register()

    def deregister(self):
        self._log.debug("De-register RO account for project %s", self._project.name)
        self._rpc.deregister()
        self._regh.deregister()
        self._rsic.deregister()
        self._rdcp.deregister()
        self._rcdp.deregister()
        self._nsr_sub.deregister()
