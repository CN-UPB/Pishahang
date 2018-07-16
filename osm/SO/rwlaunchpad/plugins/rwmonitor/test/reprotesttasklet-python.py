#!/usr/bin/env python3

import argparse
import asyncio
import concurrent.futures
import gi
import logging
import os
import rwlogger
import sys
import time
import unittest
import xmlrunner

gi.require_version("RwDts", "1.0")
from gi.repository import (
    RwDts as rwdts,
    RwDtsYang,
)
import rift.tasklets
import rift.test.dts

gi.require_version('RwLog', '1.0')

import rift.tasklets.rwmonitor.core as core
import rift.mano.cloud as cloud

from gi.repository import RwCloudYang, RwLog, RwVnfrYang
import rw_peas

from repro import update

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class DtsHandler(object):
    def __init__(self, tasklet):
        self.reg = None
        self.tasklet = tasklet

    @property
    def log(self):
        return self.tasklet.log

    @property
    def log_hdl(self):
        return self.tasklet.log_hdl

    @property
    def dts(self):
        return self.tasklet.dts

    @property
    def loop(self):
        return self.tasklet.loop

    @property
    def classname(self):
        return self.__class__.__name__


class VdurNfviMetricsPublisher(DtsHandler):
    """
    A VdurNfviMetricsPublisher is responsible for publishing the NFVI metrics
    from a single VDU.
    """

    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]/vnfr:vdur[vnfr:id={}]/rw-vnfr:nfvi-metrics"

    # This timeout defines the length of time the publisher will wait for a
    # request to a data source to complete. If the request cannot be completed
    # before timing out, the current data will be published instead.
    TIMEOUT = 2.0

    def __init__(self, tasklet, vnfr_id, vdur_id):
        """Create an instance of VdurNvfiPublisher

        Arguments:
            tasklet - the tasklet
            vdur    - the VDUR of the VDU whose metrics are published

        """
        super().__init__(tasklet)
        self._vnfr_id = vnfr_id
        self._vdur_id = vdur_id

        self._handle = None
        self._xpath = VdurNfviMetricsPublisher.XPATH.format(quoted_key(vnfr_id), quoted_key(vdur_id))

        self._deregistered = asyncio.Event(loop=self.loop)

    @property
    def xpath(self):
        """The XPATH that the metrics are published on"""
        return self._xpath

    @asyncio.coroutine
    def dts_on_prepare(self, xact_info, action, ks_path, msg):
        """Handles the DTS on_prepare callback"""
        self.log.debug("{}:dts_on_prepare".format(self.classname))

        if action == rwdts.QueryAction.READ:
            # If the publisher has been deregistered, the xpath element has
            # been deleted. So we do not want to publish the metrics and
            # re-created the element.
            if not self._deregistered.is_set():
                metrics = self.tasklet.on_retrieve_nfvi_metrics(self._vdur_id)
                xact_info.respond_xpath(
                        rwdts.XactRspCode.MORE,
                        self.xpath,
                        metrics,
                        )

        xact_info.respond_xpath(rwdts.XactRspCode.ACK, self.xpath)

    @asyncio.coroutine
    def register(self):
        """Register the publisher with DTS"""
        self._handle = yield from self.dts.register(
                xpath=self.xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=self.dts_on_prepare,
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    def deregister(self):
        """Deregister the publisher from DTS"""
        # Mark the publisher for deregistration. This prevents the publisher
        # from creating an element after it has been deleted.
        self._deregistered.set()

        # Now that we are done with the registration handle, delete the element
        # and tell DTS to deregister it
        self._handle.delete_element(self.xpath)
        self._handle.deregister()
        self._handle = None


class RwLogTestTasklet(rift.tasklets.Tasklet):
    """ A tasklet to test Python rwlog interactions  """
    def __init__(self, *args, **kwargs):
        super(RwLogTestTasklet, self).__init__(*args, **kwargs)
        self._dts = None
        self.rwlog.set_category("rw-logtest-log")
        self._metrics = RwVnfrYang.YangData_Vnfr_VnfrCatalog_Vnfr_Vdur_NfviMetrics()

    def start(self):
        """ The task start callback """
        super(RwLogTestTasklet, self).start()

        self._dts = rift.tasklets.DTS(self.tasklet_info,
                                      RwVnfrYang.get_schema(),
                                      self.loop,
                                      self.on_dts_state_change)
    @property
    def dts(self):
        return self._dts

    @asyncio.coroutine
    def init(self):
        pass

    def on_retrieve_nfvi_metrics(self, vdur_id):
        return self._metrics

    @asyncio.coroutine
    def run(self):
        def go():
            account_msg = RwCloudYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList.from_dict({
                "account_type": "openstack",
                "openstack": {
                        "key": "admin",
                        "secret": "mypasswd",
                        "auth_url": 'http://10.66.4.18:5000/v3/',
                        "tenant": "demo",
                        "mgmt_network": "private"
                    }
                })

            account = cloud.CloudAccount(
              self.log,
              RwLog.Ctx.new(__file__), account_msg
              )

            vim_id = "a7f30def-0942-4425-8454-1ffe02b7db1e"
            instances = 20

            executor = concurrent.futures.ThreadPoolExecutor(10)
            plugin = rw_peas.PeasPlugin("rwmon_ceilometer", 'RwMon-1.0')
            impl = plugin.get_interface("Monitoring")
            while True:
                tasks = []
                for _ in range(instances):
                    task = update(self.loop, self.log, executor, account.cal_account_msg, impl, vim_id)
                    tasks.append(task)

                self.log.debug("Running %s update tasks", instances)
                #self.loop.run_until_complete(asyncio.wait(tasks, loop=self.loop, timeout=20))
                done, pending = yield from asyncio.wait(tasks, loop=self.loop, timeout=20)
                self._metrics = done.pop().result()

        self._publisher = VdurNfviMetricsPublisher(self, "a7f30def-0942-4425-8454-1ffe02b7db1e", "a7f30def-0942-4425-8454-1ffe02b7db1e")
        yield from self._publisher.register()
        self.loop.create_task(go())

    @asyncio.coroutine
    def on_dts_state_change(self, state):
        switch = {
            rwdts.State.INIT: rwdts.State.REGN_COMPLETE,
            rwdts.State.CONFIG: rwdts.State.RUN,
        }

        handlers = {
            rwdts.State.INIT: self.init,
            rwdts.State.RUN: self.run,
        }

        # Transition application to next state
        handler = handlers.get(state, None)
        if handler is not None:
            yield from handler()

        # Transition dts to next state
        next_state = switch.get(state, None)
        if next_state is not None:
            self.log.debug("Changing state to %s", next_state)
            self._dts.handle.set_state(next_state)
