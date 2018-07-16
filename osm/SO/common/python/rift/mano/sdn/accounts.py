
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

import sys
import asyncio
from gi import require_version
require_version('RwTypes', '1.0')
require_version('RwsdnalYang', '1.0')
require_version('RwSdnYang', '1.0')

from gi.repository import (
        RwTypes,
        RwsdnalYang,
        RwSdnYang,
        )
import rw_peas

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async


class PluginLoadingError(Exception):
    pass


class SDNAccountCalError(Exception):
    pass


class SDNAccount(object):
    def __init__(self, log, rwlog_hdl, account_msg):
        self._log = log
        self._account_msg = account_msg.deep_copy()

        self._sdn_plugin = None
        self._engine = None

        self._sdn = self.plugin.get_interface("Topology")
        self._sdn.init(rwlog_hdl)

        self._status = RwSdnYang.YangData_RwProject_Project_Sdn_Account_ConnectionStatus(
                status="unknown",
                details="Connection status lookup not started"
                )

        self._validate_task = None

    @property
    def plugin(self):
        if self._sdn_plugin is None:
            try:
                self._sdn_plugin = rw_peas.PeasPlugin(
                        getattr(self._account_msg, self.account_type).plugin_name,
                        'RwSdn-1.0',
                        )

            except AttributeError as e:
                raise PluginLoadingError(str(e))

            self._engine, _, _ = self._sdn_plugin()

        return self._sdn_plugin

    def _wrap_status_fn(self, fn, *args, **kwargs):
        ret = fn(*args, **kwargs)
        rw_status = ret[0]
        if rw_status != RwTypes.RwStatus.SUCCESS:
            msg = "%s returned %s" % (fn.__name__, str(rw_status))
            self._log.error(msg)
            raise SDNAccountCalError(msg)

        # If there was only one other return value besides rw_status, then just
        # return that element.  Otherwise return the rest of the return values
        # as a list.
        return ret[1] if len(ret) == 2 else ret[1:]

    @property
    def sdn(self):
        return self._sdn

    @property
    def name(self):
        return self._account_msg.name

    @property
    def account_msg(self):
        return self._account_msg

    @property
    def sdnal_account_msg(self):
        return RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList.from_dict(
                self.account_msg.as_dict(),
                ignore_missing_keys=True,
                )

    def sdn_account_msg(self, account_dict):
        self._account_msg = RwSdnYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList.from_dict(account_dict)

    @property
    def account_type(self):
        return self._account_msg.account_type

    @property
    def connection_status(self):
        return self._status

    def update_from_cfg(self, cfg):
        self._log.debug("Updating parent SDN Account to %s", cfg)

        raise NotImplementedError("Update SDN account not yet supported")


    @asyncio.coroutine
    def validate_sdn_account_credentials(self, loop):
        self._log.debug("Validating SDN Account credentials %s",
                        self.name)
        self._status = RwSdnYang.YangData_RwProject_Project_Sdn_Account_ConnectionStatus(
                status="validating",
                details="SDN account connection validation in progress"
                )
        rwstatus, status = yield from loop.run_in_executor(
                None,
                self._sdn.validate_sdn_creds,
                self.sdnal_account_msg,
                )
        if rwstatus == RwTypes.RwStatus.SUCCESS:
            self._status = RwSdnYang.YangData_RwProject_Project_Sdn_Account_ConnectionStatus.from_dict(status.as_dict())
        else:
            self._status = RwSdnYang.YangData_RwProject_Project_Sdn_Account_ConnectionStatus(
                    status="failure",
                    details="Error when calling SDNAL validate SDN creds"
                    )

        if self._status.status == 'failure':
            self._log.error("SDN account validation failed; Acct: %s status: %s",
                            self.name, self._status)

    def start_validate_credentials(self, loop):
        if self._validate_task is not None:
            self._validate_task.cancel()
            self._validate_task = None

        self._validate_task = asyncio.ensure_future(
                self.validate_sdn_account_credentials(loop),
                loop=loop
                )
