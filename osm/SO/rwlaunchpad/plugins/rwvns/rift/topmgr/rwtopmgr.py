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
import gi

gi.require_version('RwDts', '1.0')
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwTypes', '1.0')
gi.require_version('RwSdn', '1.0')
from gi.repository import (
    RwDts as rwdts,
    IetfNetworkYang,
    IetfNetworkTopologyYang,
    IetfL2TopologyYang,
    RwTopologyYang,
    RwsdnalYang,
    RwTypes
)

from gi.repository.RwTypes import RwStatus
import rift.tasklets

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class NwtopDiscoveryDtsHandler(object):
    """ Handles DTS interactions for the Discovered Topology registration """
    DISC_XPATH = "D,/nd:network"

    def __init__(self, dts, log, loop, project, acctmgr, nwdatastore):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._acctmgr = acctmgr
        self._nwdatastore = nwdatastore

        self._regh = None

    @property
    def regh(self):
        """ The registration handle associated with this Handler"""
        return self._regh

    def deregister(self):
        self._log.debug("De-register Topology discovery handler for project {}".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None

    @asyncio.coroutine
    def register(self):
        """ Register for the Discovered Topology path """

        @asyncio.coroutine
        def on_ready(regh, status):
            """  On_ready for Discovered Topology registration """
            self._log.debug("PUB reg ready for Discovered Topology handler regn_hdl(%s) status %s",
                                         regh, status)

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare for Discovered Topology registration"""
            self._log.debug(
                "Got topology on_prepare callback (xact_info: %s, action: %s): %s",
                xact_info, action, msg
                )

            if action == rwdts.QueryAction.READ:
                
                for name, sdnacct in self._acctstore.items():
                    if sdnacct.account_type != "odl":
                        continue
                    sdnintf = sdnacct.sdn

                    rc, nwtop = sdnintf.get_network_list(sdnacct.sdnal_account_msg)
                    #assert rc == RwStatus.SUCCESS
                    if rc != RwStatus.SUCCESS:
                        self._log.error("Fetching get network list for SDN Account %s failed", name)
                        xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                        return
                    
                    self._log.debug("Topology: Retrieved network attributes ")
                    for nw in nwtop.network:
                        # Add SDN account name
                        nw.rw_network_attributes.sdn_account_name = name
                        nw.server_provided = False
                        nw.network_id = name + ':' + nw.network_id
                        self._log.debug("...Network id %s", nw.network_id)
                        nw_xpath = ("D,/nd:network[network-id={}]").format(quoted_key(nw.network_id))
                        xact_info.respond_xpath(rwdts.XactRspCode.MORE,
                                        nw_xpath, nw)

                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
                #err = "%s action on discovered Topology not supported" % action
                #raise NotImplementedError(err)

        self._log.debug("Registering for discovered topology using xpath %s", NwtopDiscoveryDtsHandler.DISC_XPATH)

        handler = rift.tasklets.DTS.RegistrationHandler(
            on_ready=on_ready,
            on_prepare=on_prepare,
            )

        self._regh = yield from self._dts.register(
            NwtopDiscoveryDtsHandler.DISC_XPATH,
            flags=rwdts.Flag.PUBLISHER,
            handler=handler
            )


class NwtopStaticDtsHandler(object):
    """ Handles DTS interactions for the Static Topology registration """
    STATIC_XPATH = "C,/nd:network"

    def __init__(self, dts, log, loop, project, acctmgr, nwdatastore):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._acctmgr = acctmgr

        self._regh = None
        self.pending = {}
        self._nwdatastore = nwdatastore

    @property
    def regh(self):
        """ The registration handle associated with this Handler"""
        return self._regh

    def deregister(self):
        self._log.debug("De-register Topology static handler for project {}".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None

    @asyncio.coroutine
    def register(self):
        """ Register for the Static Topology path """

        @asyncio.coroutine
        def prepare_nw_cfg(dts, acg, xact, xact_info, ksp, msg, scratch):
            """Prepare for application configuration. Stash the pending
            configuration object for subsequent transaction phases"""
            self._log.debug("Prepare Network config received network id %s, msg %s",
                           msg.network_id, msg)
            self.pending[xact.id] = msg
            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        def apply_nw_config(dts, acg, xact, action, scratch):
            """Apply the pending configuration object"""
            if action == rwdts.AppconfAction.INSTALL and xact.id is None:
                self._log.debug("No xact handle.  Skipping apply config")
                return

            if xact.id not in self.pending:
                raise KeyError("No stashed configuration found with transaction id [{}]".format(xact.id))

            try:
                if action == rwdts.AppconfAction.INSTALL:
                    self._nwdatastore.create_network(self.pending[xact.id].network_id, self.pending[xact.id])
                elif action == rwdts.AppconfAction.RECONCILE:
                    self._nwdatastore.update_network(self.pending[xact.id].network_id, self.pending[xact.id])
            except:
                raise 

            self._log.debug("Create network config done")
            return RwTypes.RwStatus.SUCCESS

        self._log.debug("Registering for static topology using xpath %s", NwtopStaticDtsHandler.STATIC_XPATH)
        handler=rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_nw_config)

        with self._dts.appconf_group_create(handler=handler) as acg:
            self._regh = acg.register(xpath = NwtopStaticDtsHandler.STATIC_XPATH,
                                      flags = rwdts.Flag.SUBSCRIBER,
                                      on_prepare=prepare_nw_cfg)
