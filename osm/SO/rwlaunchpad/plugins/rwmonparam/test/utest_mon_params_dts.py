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
import itertools
import logging
import os
import sys
import unittest
import uuid

import xmlrunner
import unittest.mock as mock

from rift.tasklets.rwmonparam import vnfr_core as vnf_mon_params
from rift.tasklets.rwmonparam import nsr_core as nsr_mon_params
import rift.test.dts

import gi
gi.require_version('RwDtsYang', '1.0')
from gi.repository import (
        VnfrYang as vnfryang,
        RwNsrYang,
        RwLaunchpadYang as launchpadyang,
        RwDts as rwdts,
        RwVnfrYang,
        RwProjectVnfdYang as RwVnfdYang,
        RwProjectNsdYang as RwNsdYang,
        )

import utest_mon_params


class MonParamMsgGenerator(object):
    def __init__(self, num_messages=1):
        ping_path = r"/api/v1/ping/stats"
        self._endpoint_msg = vnfryang.YangData_RwProject_Project_VnfrCatalog_Vnfr_HttpEndpoint.from_dict({
            'path': ping_path,
            'https': 'true',
            'polling_interval_secs': 1,
            'username': 'admin',
            'password': 'password',
            'headers': [{'key': 'TEST_KEY', 'value': 'TEST_VALUE'}],
            })

        self._mon_param_msgs = []
        for i in range(1, num_messages):
            self._mon_param_msgs.append(vnfryang.YangData_RwProject_Project_VnfrCatalog_Vnfr_MonitoringParam.from_dict({
                'id': '%s' % i,
                'name': 'param_num_%s' % i,
                'json_query_method': "NAMEKEY",
                'http_endpoint_ref': ping_path,
                'value_type': "INT",
                'value_integer': i,
                'description': 'desc for param_num_%s' % i,
                'group_tag': 'Group1',
                'widget_type': 'COUNTER',
                'units': 'packets'
                })
            )

        self._msgs = iter(self.mon_param_msgs)

    @property
    def mon_param_msgs(self):
        return self._mon_param_msgs

    @property
    def endpoint_msgs(self):
        return [self._endpoint_msg]

    def next_message(self):
        return next(self._msgs)



class MonParamsDtsTestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
        return launchpadyang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 480

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

        self.tinfo_sub = self.new_tinfo(str(test_id) + "_sub")
        self.dts_sub = rift.tasklets.DTS(self.tinfo_sub, self.schema, self.loop)

        self.msg_gen = MonParamMsgGenerator(4)
        self.vnf_handler = vnf_mon_params.VnfMonitorDtsHandler(
                self.log, self.dts, self.loop, 1, "1.1.1.1",
                self.msg_gen.mon_param_msgs, self.msg_gen.endpoint_msgs
                )

        store = self.setup_mock_store(aggregation_type=None,
            monps=None,
            legacy=True)

        self.nsr_handler = nsr_mon_params.NsrMonitorDtsHandler(
            self.log, self.dts, self.loop, store.nsr[0], [store.get_vnfr()], store)


    def tearDown(self):
        super().tearDown()

    def setup_mock_store(self, aggregation_type, monps, legacy=False):
        store = mock.MagicMock()

        mock_vnfd =  RwVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd.from_dict({
            'id': "1",
            'monitoring_param': [
                {'description': 'no of ping requests',
                 'group_tag': 'Group1',
                 'http_endpoint_ref': 'api/v1/ping/stats',
                 'id': '1',
                 'json_query_method': 'NAMEKEY',
                 'name': 'ping-request-tx-count',
                 'units': 'packets',
                 'value_type': 'INT',
                 'widget_type': 'COUNTER'},
                {'description': 'no of ping responses',
                 'group_tag': 'Group1',
                 'http_endpoint_ref': 'api/v1/ping/stats',
                 'id': '2',
                 'json_query_method': 'NAMEKEY',
                 'name': 'ping-response-rx-count',
                 'units': 'packets',
                 'value_type': 'INT',
                 'widget_type': 'COUNTER'}],
            })
        store.get_vnfd = mock.MagicMock(return_value=mock_vnfd)

        mock_vnfr = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr.from_dict({
            'id': '1',
            'monitoring_param': ([monp.as_dict() for monp in monps] if not legacy else [])
            })
        mock_vnfr.vnfd = vnfryang.YangData_RwProject_Project_VnfrCatalog_Vnfr_Vnfd.from_dict({'id': '1'})
        store.get_vnfr = mock.MagicMock(return_value=mock_vnfr)

        mock_nsr = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr.from_dict({
            'ns_instance_config_ref': "1",
            'name_ref': "Foo",
            'constituent_vnfr_ref': [{'vnfr_id': mock_vnfr.id}],

            })
        store.get_nsr = mock.MagicMock(return_value=mock_nsr)
        store.nsr = [mock_nsr]

        monp = [{'aggregation_type': aggregation_type,
                 'id': '1',
                 'description': 'no of ping requests',
                 'group_tag': 'Group1',
                 'units': 'packets',
                 'widget_type': 'COUNTER',
                 'name': 'ping-request-tx-count',
                 'value_type': 'INT',
                 'vnfd_monitoring_param': [
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '1'},
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '2'}]
                }]

        mock_nsd = RwNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd.from_dict({
            'id': str(uuid.uuid1()),
            'monitoring_param': (monp if not legacy else [])
            })

        store.get_nsd = mock.MagicMock(return_value=mock_nsd)

        return store

    @asyncio.coroutine
    def get_published_xpaths(self):
        published_xpaths = set()

        res_iter = yield from self.dts.query_read("D,/rwdts:dts")
        for i in res_iter:
            res = (yield from i).result
            for member in res.member:
                published_xpaths |= {reg.keyspec for reg in member.state.registration if reg.flags == "publisher"}

        return published_xpaths

    @asyncio.coroutine
    def register_vnf_publisher(self):
        yield from self.vnf_handler.register()

    def add_param_to_publisher(self, publisher):
        msg = self.msg_gen.next_message()
        publisher.on_update_mon_params([msg])
        return msg

    @asyncio.coroutine
    def register_vnf_test_subscriber(self, on_prepare=None):
        ready_event = asyncio.Event(loop=self.loop)

        # Register needs to wait till reg-ready is hit, dts does not provide it
        # out-of-the-box.
        @asyncio.coroutine
        def on_ready(*args, **kwargs):
            ready_event.set()

        self.vnf_test_subscriber = yield from self.dts_sub.register(
                self.vnf_handler.xpath(),
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_ready=on_ready, on_prepare=on_prepare
                    ),
                flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.CACHE,
                )

        yield from ready_event.wait()

    def get_ns_mon_param_msgs(self):
        return self.ns_handler.get_nsr_mon_param_msgs({'1':['1']})

    @rift.test.dts.async_test
    def _test_vnf_handler_registration(self):
        yield from self.vnf_handler.register()
        published_xpaths = yield from self.get_published_xpaths()
        assert self.vnf_handler.xpath() in published_xpaths

    @rift.test.dts.async_test
    def _test_add_vnf_mon_params(self):
        yield from self.register_vnf_publisher()
        self.add_param_to_publisher(self.vnf_handler)

        yield from self.register_vnf_test_subscriber()
        self.add_param_to_publisher(self.vnf_handler)

        # RIFT-12888: Elements do not go immediately into cache after on_prepare.
        # Because of this, we can't guarantee that the second param will actually be
        # in the cache yet.
        elements = list(self.vnf_test_subscriber.elements)
        assert len(elements) > 0
        for element in elements:
            assert element in self.msg_gen.mon_param_msgs

    @rift.test.dts.async_test
    def _test_nsr_handler_registration(self):
        yield from self.nsr_handler.register()
        published_xpaths = yield from self.get_published_xpaths()
        assert self.nsr_handler.xpath() in published_xpaths

    def _test_publish(self, aggregation_type, expected_value, legacy=False):

        self.msg_gen = MonParamMsgGenerator(5)
        store = self.setup_mock_store(aggregation_type=aggregation_type,
            monps=self.msg_gen.mon_param_msgs,
            legacy=legacy)

        self.vnf_handler = vnf_mon_params.VnfMonitorDtsHandler(
                self.log, self.dts, self.loop, 1, "1.1.1.1",
                self.msg_gen.mon_param_msgs, self.msg_gen.endpoint_msgs
                )

        self.nsr_handler = nsr_mon_params.NsrMonitorDtsHandler(
            self.log, self.dts, self.loop, store.nsr[0], [store.get_vnfr()], store)

        # def callback():
        yield from self.nsr_handler.register()
        yield from self.nsr_handler.start()
        published_xpaths = yield from self.get_published_xpaths()

        yield from self.register_vnf_publisher()
        self.add_param_to_publisher(self.vnf_handler)
        self.add_param_to_publisher(self.vnf_handler)

        nsr_id = store.get_nsr().ns_instance_config_ref

        yield from asyncio.sleep(2, loop=self.loop)

        itr = yield from self.dts.query_read(self.nsr_handler.xpath(),
            rwdts.XactFlag.MERGE)


        values = []
        for res in itr:
            result = yield from res
            nsr_monp = result.result
            values.append(nsr_monp.value_integer)

        print (values)
        assert expected_value in values

    @rift.test.dts.async_test
    def _test_nsr_monitor_publish_avg(self):
        yield from self._test_publish("AVERAGE", 1)

    @rift.test.dts.async_test
    def _test_nsr_monitor_publish_sum(self):
        yield from self._test_publish("SUM", 3)


    @rift.test.dts.async_test
    def _test_nsr_monitor_publish_max(self):
        yield from self._test_publish("MAXIMUM", 2)

    @rift.test.dts.async_test
    def _test_nsr_monitor_publish_min(self):
        yield from self._test_publish("MINIMUM", 1)

    @rift.test.dts.async_test
    def test_nsr_monitor_publish_count(self):
        yield from self._test_publish("COUNT", 2)

    @rift.test.dts.async_test
    def test_legacy_nsr_monitor_publish_avg(self):
        yield from self._test_publish("AVERAGE", 1, legacy=True)

    @rift.test.dts.async_test
    def test_vnfr_add_delete(self):
        yield from self._test_publish("SUM", 3)

        self.msg_gen = MonParamMsgGenerator(5)
        store = self.setup_mock_store(aggregation_type="SUM",
            monps=self.msg_gen.mon_param_msgs)
        new_vnf_handler = vnf_mon_params.VnfMonitorDtsHandler(
                self.log, self.dts, self.loop, 2, "2.2.2.1",
                self.msg_gen.mon_param_msgs, self.msg_gen.endpoint_msgs
                )
        yield from new_vnf_handler.register()

        # add a new vnfr 
        new_vnfr = store.get_vnfr()
        new_vnfr.id = '2'
        yield from self.nsr_handler.update([new_vnfr])

        # check if the newly created one has been added in the model
        poller = self.nsr_handler.mon_params_pollers[0]
        assert len(poller.monp.nsr_mon_param_msg.vnfr_mon_param_ref) == 4
        assert len(poller.subscribers) == 4
        assert len(poller.monp.vnfr_monparams) == 4

        # publish new values
        yield from asyncio.sleep(2, loop=self.loop)
        self.add_param_to_publisher(new_vnf_handler)
        self.add_param_to_publisher(new_vnf_handler)
        yield from asyncio.sleep(3, loop=self.loop)

        itr = yield from self.dts.query_read(self.nsr_handler.xpath(),
            rwdts.XactFlag.MERGE)

        values = []
        for res in itr:
            result = yield from res
            nsr_monp = result.result
            values.append(nsr_monp.value_integer)

        assert values[0] == 6

        # delete the VNFR
        yield from self.nsr_handler.delete([new_vnfr])

        # check if the newly created one has been added in the model
        poller = self.nsr_handler.mon_params_pollers[0]
        assert len(poller.monp.vnfr_monparams) == 2
        assert len(poller.monp.nsr_mon_param_msg.vnfr_mon_param_ref) == 2
        assert len(poller.subscribers) == 2

        self.msg_gen = MonParamMsgGenerator(5)
        self.add_param_to_publisher(self.vnf_handler)
        self.add_param_to_publisher(self.vnf_handler)
        yield from asyncio.sleep(2, loop=self.loop)

        itr = yield from self.dts.query_read(self.nsr_handler.xpath(),
            rwdts.XactFlag.MERGE)
        values = []
        for res in itr:
            result = yield from res
            nsr_monp = result.result
            values.append(nsr_monp.value_integer)

        assert values[0] == 3



def main():
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None

    MonParamsDtsTestCase.log_level = logging.DEBUG if args.verbose else logging.WARN

    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()
