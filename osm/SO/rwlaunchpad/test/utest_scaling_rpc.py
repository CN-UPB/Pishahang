#!/usr/bin/env python3

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

import argparse
import asyncio
import gi
import logging
import os
import sys
import time
import types
import unittest
import uuid
import xmlrunner

gi.require_version('RwCloudYang', '1.0')
gi.require_version('RwDts', '1.0')
gi.require_version('RwNsmYang', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('RwResourceMgrYang', '1.0')
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('NsrYang', '1.0')
gi.require_version('RwlogMgmtYang', '1.0')

from gi.repository import (
    RwCloudYang as rwcloudyang,
    RwDts as rwdts,
    RwLaunchpadYang as launchpadyang,
    RwNsmYang as rwnsmyang,
    RwNsrYang as rwnsryang,
    NsrYang as nsryang,
    RwResourceMgrYang as rmgryang,
    RwcalYang as rwcalyang,
    RwConfigAgentYang as rwcfg_agent,
    RwlogMgmtYang
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from gi.repository.RwTypes import RwStatus
import rift.mano.examples.ping_pong_nsd as ping_pong_nsd
import rift.tasklets
import rift.test.dts
import rw_peas




class ManoTestCase(rift.test.dts.AbstractDTSTest):
    """
    DTS GI interface unittests

    Note:  Each tests uses a list of asyncio.Events for staging through the
    test.  These are required here because we are bring up each coroutine
    ("tasklet") at the same time and are not implementing any re-try
    mechanisms.  For instance, this is used in numerous tests to make sure that
    a publisher is up and ready before the subscriber sends queries.  Such
    event lists should not be used in production software.
    """

    @classmethod
    def configure_suite(cls, rwmain):
        nsm_dir = os.environ.get('NSM_DIR')

        rwmain.add_tasklet(nsm_dir, 'rwnsmtasklet')

    @classmethod
    def configure_schema(cls):
        return rwnsmyang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    @staticmethod
    def get_cal_account(account_type, account_name):
        """
        Creates an object for class RwcalYang.Clo
        """
        account = rwcloudyang.YangData_RwProject_Project_CloudAccounts_CloudAccountList()
        if account_type == 'mock':
            account.name          = account_name
            account.account_type  = "mock"
            account.mock.username = "mock_user"
        elif ((account_type == 'openstack_static') or (account_type == 'openstack_dynamic')):
            account.name = account_name
            account.account_type = 'openstack'
            account.openstack.key = openstack_info['username']
            account.openstack.secret       = openstack_info['password']
            account.openstack.auth_url     = openstack_info['auth_url']
            account.openstack.tenant       = openstack_info['project_name']
            account.openstack.mgmt_network = openstack_info['mgmt_network']
        return account

    @asyncio.coroutine
    def configure_cloud_account(self, dts, cloud_type, cloud_name="cloud1"):
        account = self.get_cal_account(cloud_type, cloud_name)
        account_xpath = "C,/rw-cloud:cloud/rw-cloud:account[rw-cloud:name={}]".format(quoted_key(cloud_name))
        self.log.info("Configuring cloud-account: %s", account)
        yield from dts.query_create(account_xpath,
                                    rwdts.XactFlag.ADVISE,
                                    account)

    @asyncio.coroutine
    def wait_tasklets(self):
        yield from asyncio.sleep(5, loop=self.loop)

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", self.id())
        self.tinfo = self.new_tinfo(self.id())
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

    def test_create_nsr_record(self):

        @asyncio.coroutine
        def run_test():
            yield from self.wait_tasklets()

            cloud_type = "mock"
            yield from self.configure_cloud_account(self.dts, cloud_type, "mock_account")


            # Trigger an rpc
            rpc_ip = nsryang.YangInput_Nsr_ExecScaleIn.from_dict({
                'nsr_id_ref': '1',
                'instance_id': "1",
                'scaling_group_name_ref': "foo"})

            yield from self.dts.query_rpc("/nsr:exec-scale-in", 0, rpc_ip)

        future = asyncio.ensure_future(run_test(), loop=self.loop)
        self.run_until(future.done)
        if future.exception() is not None:
            self.log.error("Caught exception during test")
            raise future.exception()


def main():
    top_dir = __file__[:__file__.find('/modules/core/')]
    build_dir = os.path.join(top_dir, '.build/modules/core/rwvx/src/core_rwvx-build')
    launchpad_build_dir = os.path.join(top_dir, '.build/modules/core/mc/core_mc-build/rwlaunchpad')

    if 'NSM_DIR' not in os.environ:
        os.environ['NSM_DIR'] = os.path.join(launchpad_build_dir, 'plugins/rwnsm')

    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None

    ManoTestCase.log_level = logging.DEBUG if args.verbose else logging.WARN

    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()

# vim: sw=4
