
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

from gi.repository import (
    RwDts as rwdts,
    ProtobufC,
    )

from rift.mano.utils.project import get_add_delete_update_cfgs

from . import accounts


class SDNAccountNotFound(Exception):
    pass


class SDNAccountError(Exception):
    pass


class SDNAccountConfigCallbacks(object):
    def __init__(self,
                 on_add_apply=None, on_add_prepare=None,
                 on_delete_apply=None, on_delete_prepare=None):

        @asyncio.coroutine
        def prepare_noop(*args, **kwargs):
            pass

        def apply_noop(*args, **kwargs):
            pass

        self.on_add_apply = on_add_apply
        self.on_add_prepare = on_add_prepare
        self.on_delete_apply = on_delete_apply
        self.on_delete_prepare = on_delete_prepare

        for f in ('on_add_apply', 'on_delete_apply'):
            ref = getattr(self, f)
            if ref is None:
                setattr(self, f, apply_noop)
                continue

            if asyncio.iscoroutinefunction(ref):
                raise ValueError('%s cannot be a coroutine' % (f,))

        for f in ('on_add_prepare', 'on_delete_prepare'):
            ref = getattr(self, f)
            if ref is None:
                setattr(self, f, prepare_noop)
                continue

            if not asyncio.iscoroutinefunction(ref):
                raise ValueError("%s must be a coroutine" % f)


class SDNAccountConfigSubscriber(object):
    XPATH = "C,/rw-sdn:sdn/rw-sdn:account"

    def __init__(self, dts, log, project, rwlog_hdl, sdn_callbacks, acctstore):
        self._dts = dts
        self._log = log
        self._project = project
        self._rwlog_hdl = rwlog_hdl
        self._reg = None

        self.accounts = acctstore

        self._sdn_callbacks = sdn_callbacks

    def add_account(self, account_msg):
        self._log.info("adding sdn account: {}".format(account_msg))

        account = accounts.SDNAccount(self._log, self._rwlog_hdl, account_msg)
        self.accounts[account.name] = account

        self._sdn_callbacks.on_add_apply(account)

    def delete_account(self, account_name):
        self._log.info("deleting sdn account: {}".format(account_name))
        del self.accounts[account_name]

        self._sdn_callbacks.on_delete_apply(account_name)

    def update_account(self, account_msg):
        """ Update an existing sdn account

        In order to simplify update, turn an update into a delete followed by
        an add.  The drawback to this approach is that we will not support
        updates of an "in-use" sdn account, but this seems like a
        reasonable trade-off.


        Arguments:
            account_msg - The sdn account config message
        """
        self._log.info("updating sdn account: {}".format(account_msg))

        self.delete_account(account_msg.name)
        self.add_account(account_msg)

    def deregister(self):
        if self._reg:
            self._reg.deregister()
            self._reg = None

    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, _):
            self._log.debug("Got sdn account apply config (xact: %s) (action: %s)", xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.debug("SDN account being re-added after restart.")
                        if not cfg.has_field('account_type'):
                            raise SDNAccountError("New SDN account must contain account_type field.")
                        self.add_account(cfg)
                else:
                    # When RIFT first comes up, an INSTALL is called with the current config
                    # Since confd doesn't actally persist data this never has any data so
                    # skip this for now.
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
            """ Prepare callback from DTS for SDN Account """

            action = xact_info.query_action
            self._log.debug("SDN account on_prepare config received (action: %s): %s",
                            xact_info.query_action, msg)

            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                if msg.name in self.accounts:
                    self._log.debug("SDN account already exists. Invoking update request")

                    # Since updates are handled by a delete followed by an add, invoke the
                    # delete prepare callbacks to give clients an opportunity to reject.
                    yield from self._sdn_callbacks.on_delete_prepare(msg.name)

                else:
                    self._log.debug("SDN account does not already exist. Invoking on_prepare add request")
                    if not msg.has_field('account_type'):
                        raise SDNAccountError("New sdn account must contain account_type field.")

                    account = accounts.SDNAccount(self._log, self._rwlog_hdl, msg)
                    yield from self._sdn_callbacks.on_add_prepare(account)

            elif action == rwdts.QueryAction.DELETE:
                # Check if the entire SDN account got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    yield from self._sdn_callbacks.on_delete_prepare(msg.name)

                else:
                    self._log.error("Deleting individual fields for SDN account not supported")
                    xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                    return

            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(SDNAccountConfigSubscriber.XPATH)
        self._log.debug("Registering for SDN Account config using xpath: %s",
                        xpath,
                        )

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                    xpath=xpath,
                    flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                    on_prepare=on_prepare,
                    )
