
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

import asyncio
import rw_peas

import gi
gi.require_version('RwDts', '1.0')
import rift.tasklets
from rift.mano.utils.project import get_add_delete_update_cfgs

from gi.repository import (
    RwcalYang as rwcal,
    RwDts as rwdts,
    RwConfigAgentYang as rwcfg_agent,
    ProtobufC,
    )

class ConfigAccountNotFound(Exception):
    pass

class ConfigAccountError(Exception):
    pass


class ConfigAgentCallbacks(object):
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


class ConfigAgentSubscriber(object):
    XPATH = "C,/rw-config-agent:config-agent/account"

    def __init__(self, dts, log, project, config_callbacks):
        self._dts = dts
        self._log = log
        self._project = project
        self._reg = None

        self.accounts = {}

        self._config_callbacks = config_callbacks

    def add_account(self, account_msg):
        self._log.info("adding config account: {}".format(account_msg))

        self.accounts[account_msg.name] = account_msg

        self._config_callbacks.on_add_apply(account_msg)

    def delete_account(self, account_msg):
        self._log.info("deleting config account: {}".format(account_msg.name))
        del self.accounts[account_msg.name]

        self._config_callbacks.on_delete_apply(account_msg)

    def update_account(self, account_msg):
        """ Update an existing config-agent account

        In order to simplify update, turn an update into a delete followed by
        an add.  The drawback to this approach is that we will not support
        updates of an "in-use" config-agent account, but this seems like a
        reasonable trade-off.

        Arguments:
            account_msg - The config-agent account config message
        """

        self._log.info("updating config-agent account: {}".format(account_msg))
        self.delete_account(account_msg)
        self.add_account(account_msg)

    def deregister(self):
        self._log.debug("De-register config agent handler for project {}".
                        format(self._project.name))
        if self._reg:
            self._reg.deregister()
            self._reg = None

    def register(self):
        def apply_config(dts, acg, xact, action, _):
            self._log.debug("Got config account apply config (xact: %s) (action: %s)", xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.info("Config Agent Account {} being re-added after restart.".
                                       format(cfg.name))
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
                self.delete_account(cfg)

            # Handle Adds
            for cfg in add_cfgs:
                self.add_account(cfg)

            # Handle Updates
            for cfg in update_cfgs:
                self.update_account(cfg)

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for Config Account """

            action = xact_info.handle.query_action
            self._log.debug("Config account on_prepare config received (action: %s): %s",
                            xact_info.handle.query_action, msg)

            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                # If the account already exists, then this is an update.
                if msg.name in self.accounts:
                    self._log.debug("Config account already exists. Invoking on_prepare update request")
                    if msg.has_field("account_type"):
                        raise ConfigAccountError("Cannot change config's account-type")

                    # Since updates are handled by a delete followed by an add, invoke the
                    # delete prepare callbacks to give clients an opportunity to reject.
                    yield from self._config_callbacks.on_delete_prepare(msg.name)

                else:
                    self._log.debug("Config account does not already exist. Invoking on_prepare add request")
                    if not msg.has_field('account_type'):
                        raise ConfigAccountError("New Config account must contain account_type field.")

                    account = msg
                    yield from self._config_callbacks.on_add_prepare(account)

            elif action == rwdts.QueryAction.DELETE:
                # Check if the entire cloud account got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    yield from self._config_callbacks.on_delete_prepare(msg.name)
                else:
                    self._log.error("Deleting individual fields for config account not supported")
                    xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                    return

            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)


        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        with self._dts.appconf_group_create(acg_handler) as acg:
            xpath = self._project.add_project(ConfigAgentSubscriber.XPATH)
            self._log.debug("Registering for Config Account config using xpath: %s",
                            xpath)
            self._reg = acg.register(
                    xpath=xpath,
                    flags=rwdts.Flag.SUBSCRIBER,
                    on_prepare=on_prepare,
                    )
