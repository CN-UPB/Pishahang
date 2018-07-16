#!/usr/bin/env python3

import argparse
import asyncio
import concurrent.futures
import logging
import os
import sys
import unittest
import xmlrunner
import time

import gi
gi.require_version('RwLog', '1.0')

import rift.tasklets.rwmonitor.core as core
import rift.mano.cloud as cloud

from gi.repository import RwCloudYang, RwLog, RwVnfrYang
import rw_peas

@asyncio.coroutine
def update(loop, log, executor, account, plugin, vim_id):
    """Update the NFVI metrics for the associated VDUR

    This coroutine will request new metrics from the data-source and update
    the current metrics.

    """
    try:
        # Make the request to the plugin in a separate thread and do
        # not exceed the timeout
        _, metrics = yield from asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    plugin.nfvi_metrics,
                    account,
                    vim_id
                    ),
                timeout=10,
                loop=loop,
                )

    except asyncio.TimeoutError:
        msg = "timeout on request for nfvi metrics (vim-id = {})"
        log.warning(msg.format(vim_id))
        return

    except Exception as e:
        log.exception(e)
        return

    try:
        # Create uninitialized metric structure
        vdu_metrics = RwVnfrYang.YangData_Vnfr_VnfrCatalog_Vnfr_Vdur_NfviMetrics()

        # VCPU
        vdu_metrics.vcpu.total = 5
        vdu_metrics.vcpu.utilization = metrics.vcpu.utilization

        # Memory (in bytes)
        vdu_metrics.memory.used = metrics.memory.used
        vdu_metrics.memory.total = 5000
        vdu_metrics.memory.utilization = 100 * vdu_metrics.memory.used / vdu_metrics.memory.total

        # Storage
        try:
            vdu_metrics.storage.used = metrics.storage.used
            utilization = 100 * vdu_metrics.storage.used / vdu_metrics.storage.total
            if utilization > 100:
                utilization = 100

            vdu_metrics.storage.utilization = utilization

        except ZeroDivisionError:
            vdu_metrics.storage.utilization = 0

        # Network (incoming)
        vdu_metrics.network.incoming.packets = metrics.network.incoming.packets
        vdu_metrics.network.incoming.packet_rate = metrics.network.incoming.packet_rate
        vdu_metrics.network.incoming.bytes = metrics.network.incoming.bytes
        vdu_metrics.network.incoming.byte_rate = metrics.network.incoming.byte_rate

        # Network (outgoing)
        vdu_metrics.network.outgoing.packets = metrics.network.outgoing.packets
        vdu_metrics.network.outgoing.packet_rate = metrics.network.outgoing.packet_rate
        vdu_metrics.network.outgoing.bytes = metrics.network.outgoing.bytes
        vdu_metrics.network.outgoing.byte_rate = metrics.network.outgoing.byte_rate

        # External ports
        vdu_metrics.external_ports.total = 5

        # Internal ports
        vdu_metrics.internal_ports.total = 5

        return vdu_metrics

    except Exception as e:
        log.exception(e)


class TestUploadProgress(unittest.TestCase):
    ACCOUNT_MSG = RwCloudYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList.from_dict({
        "account_type": "openstack",
        "openstack": {
                "key": "admin",
                "secret": "mypasswd",
                "auth_url": 'http://10.66.4.18:5000/v3/',
                "tenant": "demo",
                "mgmt_network": "private"
            }
        })

    def setUp(self):
        self._loop = asyncio.get_event_loop()
        self._log = logging.getLogger(__file__)
        self._account = cloud.CloudAccount(
                self._log,
                RwLog.Ctx.new(__file__), TestUploadProgress.ACCOUNT_MSG
                )

    def test_many_updates(self):
        vim_id = "a7f30def-0942-4425-8454-1ffe02b7db1e"
        instances = 20

        executor = concurrent.futures.ThreadPoolExecutor(10)
        while True:
            tasks = []
            for _ in range(instances):
                plugin = rw_peas.PeasPlugin("rwmon_ceilometer", 'RwMon-1.0')
                impl = plugin.get_interface("Monitoring")
                task = update(self._loop, self._log, executor, self._account.cal_account_msg, impl, vim_id)
                tasks.append(task)
                task = update(self._loop, self._log, executor, self._account.cal_account_msg, impl, vim_id)
                tasks.append(task)
                task = update(self._loop, self._log, executor, self._account.cal_account_msg, impl, vim_id)
                tasks.append(task)
            self._log.debug("Running %s update tasks", instances)
            self._loop.run_until_complete(asyncio.wait(tasks, loop=self._loop, timeout=20))


def main(argv=sys.argv[1:]):
    logging.basicConfig(format='TEST %(message)s')

    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')

    args, unknown = parser.parse_known_args(argv)
    if args.no_runner:
        runner = None

    # Set the global logging level
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.ERROR)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()
