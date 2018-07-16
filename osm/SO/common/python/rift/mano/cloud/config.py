
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
import rw_peas

import gi
gi.require_version('RwDts', '1.0')
import rift.tasklets
from rift.mano.utils.project import get_add_delete_update_cfgs

from gi.repository import (
    RwcalYang as rwcal,
    RwDts as rwdts,
    ProtobufC,
    RwCloudYang,
    RwTypes
    )

from . import accounts

class CloudAccountNotFound(Exception):
    pass


class CloudAccountError(Exception):
    pass


class CloudAccountConfigCallbacks(object):
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


class CloudAccountConfigSubscriber(object):
    XPATH = "C,/rw-cloud:cloud/rw-cloud:account"

    def __init__(self, dts, log, rwlog_hdl, project, cloud_callbacks):
        self._dts = dts
        self._log = log
        self._rwlog_hdl = rwlog_hdl
        self._project = project
        self._reg = None

        self.accounts = {}

        self._cloud_callbacks = cloud_callbacks

    def add_account(self, account_msg):
        self._log.info("adding cloud account: {}".format(account_msg))

        account = accounts.CloudAccount(self._log, self._rwlog_hdl, account_msg)
        self.accounts[account.name] = account

        self._cloud_callbacks.on_add_apply(account)

    def delete_account(self, account_name):
        self._log.info("deleting cloud account: {}".format(account_name))
        del self.accounts[account_name]

        self._cloud_callbacks.on_delete_apply(account_name)

    def update_account(self, account_msg):
        """ Update an existing cloud account

        In order to simplify update, turn an update into a delete followed by
        an add.  The drawback to this approach is that we will not support
        updates of an "in-use" cloud account, but this seems like a
        reasonable trade-off.


        Arguments:
            account_msg - The cloud account config message
        """
        self._log.info("updating cloud account: {}".format(account_msg))

        self.delete_account(account_msg.name)
        self.add_account(account_msg)

    def deregister(self):
        self._log.debug("Project {}: De-register cloud account handler".
                        format(self._project))
        if self._reg:
            self._reg.deregister()
            self._reg = None

    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, scratch):
            self._log.debug("Got cloud account apply config (xact: %s) (action: %s)", xact, action)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    curr_cfg = self._reg.elements
                    for cfg in curr_cfg:
                        self._log.debug("Cloud account being re-added after restart.")
                        if not cfg.has_field('account_type'):
                            self._log.error("New cloud account must contain account_type field.")
                            xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                            return
                        self.add_account(cfg)
                else:
                    # When RIFT first comes up, an INSTALL is called with the current config
                    # Since confd doesn't actally persist data this never has any data so
                    # skip this for now.
                    self._log.debug("No xact handle.  Skipping apply config")

                return

            #Updating the account incase individual fields of cloud accounts is being deleted.
            if self._reg:
                for cfg in self._reg.get_xact_elements(xact):
                    if cfg.name in scratch.get('cloud_accounts', []):
                        self.update_account(cfg)
            scratch.pop('cloud_accounts', None)
            
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
            """ Prepare callback from DTS for Cloud Account """

            action = xact_info.query_action

            xpath = ks_path.to_xpath(RwCloudYang.get_schema())

            self._log.debug("Cloud account on_prepare config received (action: %s): %s",
                            xact_info.query_action, msg)

            if action in [rwdts.QueryAction.CREATE, rwdts.QueryAction.UPDATE]:
                if msg.name in self.accounts:
                    self._log.debug("Cloud account {} already exists. " \
                                    "Invoking update request".format(msg.name))

                    # Since updates are handled by a delete followed by an add, invoke the
                    # delete prepare callbacks to give clients an opportunity to reject.
                    yield from self._cloud_callbacks.on_delete_prepare(msg.name)

                else:
                    self._log.debug("Cloud account does not already exist. Invoking on_prepare add request")
                    if not msg.has_field('account_type'):
                        self._log.error("New cloud account must contain account_type field.")
                        xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                        return

                    account = accounts.CloudAccount(self._log, self._rwlog_hdl, msg)
                    yield from self._cloud_callbacks.on_add_prepare(account)

            elif action == rwdts.QueryAction.DELETE:
                # Check if the entire cloud account got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    try:
                        yield from self._cloud_callbacks.on_delete_prepare(msg.name)
                    except Exception as e:
                        err_msg = str(e)
                        xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE, xpath, err_msg)
                        xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                        return
                else:
                    fref.goto_proto_name(msg.to_pbcm(), "sdn_account")
                    if fref.is_field_deleted():
                        # SDN account disassociated from cloud account
                        account = self.accounts[msg.name]
                        dict_account = account.account_msg.as_dict()
                        del dict_account["sdn_account"]
                        account.cloud_account_msg(dict_account)
                    else:
                        #Updating Account incase individuals fields are being deleted
                        cloud_accounts = scratch.setdefault('cloud_accounts', [])
                        cloud_accounts.append(msg.name)

            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._log.debug("Registering for Cloud Account config using xpath: %s",
                        CloudAccountConfigSubscriber.XPATH,
                        )

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        )

        xpath = self._project.add_project(CloudAccountConfigSubscriber.XPATH)
        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                    xpath=xpath,
                    flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                    on_prepare=on_prepare,
                    )
