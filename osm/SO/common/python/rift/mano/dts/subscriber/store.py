"""
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

@file store.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 09-Jul-2016

"""

import asyncio
import enum

from gi.repository import RwDts as rwdts
from . import core, ns_subscriber, vnf_subscriber


class SubscriberStore(core.SubscriberDtsHandler):
    """A convenience class that hold all the VNF and NS related config and Opdata
    """
    KEY = enum.Enum('KEY', 'NSR NSD VNFD VNFR')

    def __init__(self, log, dts, loop, project, callback=None):
        super().__init__(log, dts, loop, project)

        params = (self.log, self.dts, self.loop, self.project)

        self._nsr_sub = ns_subscriber.NsrCatalogSubscriber(*params, callback=self.on_nsr_change)
        self._nsrs = {}
        self._nsd_sub = ns_subscriber.NsdCatalogSubscriber(*params)

        self._vnfr_sub = vnf_subscriber.VnfrCatalogSubscriber(*params, callback=self.on_vnfr_change)
        self._vnfrs = {}
        self._vnfd_sub = vnf_subscriber.VnfdCatalogSubscriber(*params)

    @property
    def vnfd(self):
        return list(self._vnfd_sub.reg.get_xact_elements())

    @property
    def nsd(self):
        return list(self._nsd_sub.reg.get_xact_elements())

    @property
    def vnfr(self):
        return list(self._vnfrs.values())

    @property
    def nsr(self):
        return list(self._nsrs.values())

    def _unwrap(self, values, id_name):
        try:
            return values[0]
        except KeyError:
            self.log.exception("Unable to find the object with the given "
                "ID {}".format(id_name))

    def get_nsr(self, nsr_id):
        values = [nsr for nsr in self.nsr if nsr.ns_instance_config_ref == nsr_id]
        return self._unwrap(values, nsr_id)

    def get_nsd(self, nsd_id):
        values = [nsd for nsd in self.nsd if nsd.id == nsd_id]
        return self._unwrap(values, nsd_id)

    def get_vnfr(self, vnfr_id):
        values = [vnfr for vnfr in self.vnfr if vnfr.id == vnfr_id]
        return self._unwrap(values, vnfr_id)

    def get_vnfd(self, vnfd_id):
        values = [vnfd for vnfd in self.vnfd if vnfd.id == vnfd_id]
        return self._unwrap(values, vnfd_id)

    @asyncio.coroutine
    def register(self):
        yield from self._vnfd_sub.register()
        yield from self._nsd_sub.register()
        yield from self._vnfr_sub.register()
        yield from self._nsr_sub.register()

    def deregister(self):
        self._log.debug("De-register store for project {}".
                        format(self._project))
        self._vnfd_sub.deregister()
        self._nsd_sub.deregister()
        self._vnfr_sub.deregister()
        self._nsr_sub.deregister()

    @asyncio.coroutine
    def refresh_store(self, subsriber, store):
        itr = yield from self.dts.query_read(subsriber.get_xpath())

        store.clear()
        for res in itr:
            result = yield from res
            result = result.result
            store[getattr(result, subsriber.key_name())] = result

    def on_nsr_change(self, msg, action):
        if action == rwdts.QueryAction.DELETE:
            if msg.ns_instance_config_ref in self._nsrs:
                del self._nsrs[msg.ns_instance_config_ref]
            return

        self.loop.create_task(self.refresh_store(self._nsr_sub, self._nsrs))

    def on_vnfr_change(self, msg, action):
        if action == rwdts.QueryAction.DELETE:
            if msg.id in self._vnfrs:
                del self._vnfrs[msg.id]
            return

        self.loop.create_task(self.refresh_store(self._vnfr_sub, self._vnfrs))
