
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
gi.require_version('RwDts', '1.0')
import rift.tasklets
from rift.mano.utils.project import get_add_delete_update_cfgs

from gi.repository import (
    RwDts as rwdts,
    ProtobufC,
    RwRoAccountYang,
    )

from . import accounts

class ROAccountConfigCallbacks(object):
    def __init__(self,
                 on_add_apply=None, on_delete_apply=None):

        @asyncio.coroutine
        def prepare_noop(*args, **kwargs):
            pass

        def apply_noop(*args, **kwargs):
            pass

        self.on_add_apply = on_add_apply
        self.on_delete_apply = on_delete_apply

        for f in ('on_add_apply', 'on_delete_apply'):
            ref = getattr(self, f)
            if ref is None:
                setattr(self, f, apply_noop)
                continue

            if asyncio.iscoroutinefunction(ref):
                raise ValueError('%s cannot be a coroutine' % (f,))

class ROAccountConfigSubscriber(object):
    XPATH = "C,/rw-ro-account:ro-account/rw-ro-account:account"

    def __init__(self, dts, log, loop, project, records_publisher, ro_callbacks):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._records_publisher = records_publisher
        self._ro_callbacks = ro_callbacks

        self._reg = None
        self.accounts = {}
        self._log.debug("Inside RO Account Config Subscriber init")

    def add_account(self, account_msg):
        self._log.debug("adding ro account: {}".format(account_msg))

        account = accounts.ROAccount(self._dts,
                self._log,
                self._loop,
                self._project,
                self._records_publisher,
                account_msg)
        self.accounts[account.name] = account
        self._ro_callbacks.on_add_apply(account)

    def delete_account(self, account_name):
        self._log.debug("Deleting RO account: {}".format(account_name))
        account = self.accounts[account_name]
        del self.accounts[account_name]  
        self._ro_callbacks.on_delete_apply(account_name)

    def deregister(self):
        self._log.debug("Project {}: De-register ro account handler".
                        format(self._project))
        if self._reg:
            self._reg.deregister()
            self._reg = None

    def update_account(self, account):
        """ Update an existing ro account

        In order to simplify update, turn an update into a delete followed by
        an add.  The drawback to this approach is that we will not support
        updates of an "in-use" ro account, but this seems like a
        reasonable trade-off.

        """
        self._log.debug("updating ro account: {}".format(account))

        self.delete_account(account.name)
        self.add_account(account)

    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, scratch):
            self._log.debug("Got ro account apply config (xact: %s) (action: %s)", xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.debug("RO account being re-added after restart.")
                        self.add_account(cfg)
                else:
                    self._log.debug("No xact handle.  Skipping apply config")

                return

            add_cfgs, delete_cfgs, update_cfgs = get_add_delete_update_cfgs(
                    dts_member_reg=self._reg,
                    xact=xact,
                    key_name="name",
                    )

            # Handle Deletes
            for cfg in delete_cfgs:
                self.delete_account(cfg.name)

            # Handle Adds
            for cfg in add_cfgs:
                self.add_account(cfg)

            # Handle Updates
            for cfg in update_cfgs:
                self.update_account(cfg)

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for RO Account """

            self._log.debug("RO account on_prepare config received (action: %s): %s",
                            xact_info.query_action, msg)
            try:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
            except rift.tasklets.dts.ResponseError as e:
                self._log.error(
                    "Subscriber DTS prepare for project {}, action {} in class {} failed: {}".
                    format(self._project, xact_info.query_action, self.__class__, e))

        self._log.debug("Registering for RO Account config using xpath: %s",
                        ROAccountConfigSubscriber.XPATH,
                        )
        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        xpath = self._project.add_project(ROAccountConfigSubscriber.XPATH)
        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                    xpath=xpath,
                    flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                    on_prepare=on_prepare,
                    )
