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
import random
import sys
import unittest
import xmlrunner

import unittest.mock as mock

import rift.test.dts
import rift.tasklets.rwautoscaler.engine as engine
gi.require_version('RwDtsYang', '1.0')
from gi.repository import (
        RwNsrYang,
        NsrYang,
        ProjectNsdYang as NsdYang,
        RwLaunchpadYang as launchpadyang,
        RwVnfrYang,
        RwProjectVnfdYang as RwVnfdYang,
        RwProjectNsdYang as RwNsdYang,
        VnfrYang
        )
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


ScalingCriteria = NsdYang.YangData_RwProject_Project_NsdCatalog_Nsd_ScalingGroupDescriptor_ScalingPolicy_ScalingCriteria
ScalingPolicy = NsdYang.YangData_RwProject_Project_NsdCatalog_Nsd_ScalingGroupDescriptor_ScalingPolicy


class MockDelegate(engine.ScalingCriteria.Delegate):
    def __init__(self):
        self.scale_in_called = 0
        self.scale_out_called = 0

    def scale_in(self, name, val):
        print ("=============================================")
        print ("Scaling IN")
        print ("=============================================")
        self.scale_in_called += 1

    def scale_out(self, name, val):
        print ("=============================================")
        print ("Scaling OUT")
        print ("=============================================")
        self.scale_out_called += 1


class MockStore():
    def __init__(self, aggregation_type="AVERAGE", legacy=False):
        self.aggregation_type = aggregation_type
        self.legacy = legacy
        self.threshold_time = 2

    def __call__(self):
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

        mock_vnfr = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr.from_dict({'id': '1'})
        mock_vnfr.vnfd = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_Vnfd.from_dict({'id': '1'})

        store.get_vnfr = mock.MagicMock(return_value=mock_vnfr)

        mock_nsr = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr.from_dict({
            'ns_instance_config_ref': "1",
            'name_ref': "Foo",
            'nsd_ref': '1',
            'config_status': 'configured',
            'constituent_vnfr_ref': [{'vnfr_id': mock_vnfr.id}],
            })

        store.get_nsr = mock.MagicMock(return_value=mock_nsr)
        store.nsr = [mock_nsr]

        monp_cfg = [{'aggregation_type': self.aggregation_type,
                 'id': '1',
                 'name': 'ping-request-tx-count',
                 'value_type': 'INT',
                 'vnfd_monitoring_param': [
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '1'},
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '2'}]
                },
                {'aggregation_type': self.aggregation_type,
                 'id': '2',
                 'name': 'ping-request-tx-count',
                 'value_type': 'INT',
                 'vnfd_monitoring_param': [
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '1'},
                    {'vnfd_id_ref': '1',
                     'vnfd_monitoring_param_ref': '2'}]
                }]

        scale_in_val = 100
        scale_out_val = 200

        mock_nsd = RwNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd.from_dict({
            'id': '1',
            'name': 'mock',
            'short_name': 'm',
            'monitoring_param': (monp_cfg if not self.legacy else []),
            'constituent_vnfd': [{'member_vnf_index': 1,
                 'start_by_default': True,
                 'vnfd_id_ref': '1'},
                {'member_vnf_index': 2,
                 'start_by_default': True,
                 'vnfd_id_ref': '1'}],
            'scaling_group_descriptor': [{
                    "name": "http",
                    "vnfd_member": [{
                        'member_vnf_index_ref': 1,
                    }],
                    "scaling_policy": [{
                        "scaling_type": "automatic",
                        "enabled": True,
                        "threshold_time": self.threshold_time,
                        "cooldown_time": 60,
                        "scale_out_operation_type": "AND",
                        "scale_in_operation_type": "AND",
                        "scaling_criteria": [{
                            "name": "1",
                            "scale_in_threshold": scale_in_val,
                            "scale_out_threshold": scale_out_val,
                            "ns_monitoring_param_ref": "1"
                        },
                        {
                            "name": "2",
                            "scale_in_threshold": scale_in_val,
                            "scale_out_threshold": scale_out_val,
                            "ns_monitoring_param_ref": "2"
                        }]
                    }]
                }]
            })

        store.get_nsd = mock.MagicMock(return_value=mock_nsd)

        return store


class AutoscalarDtsTestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
        return launchpadyang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

        self.tinfo_sub = self.new_tinfo(str(test_id) + "_sub")
        self.dts_sub = rift.tasklets.DTS(self.tinfo_sub, self.schema, self.loop)

        self.mock_store = MockStore()

    def tearDown(self):
        super().tearDown()

    @asyncio.coroutine
    def _populate_mock_values(self, criterias, nsr_id, floor, ceil):
        # Mock publish
        # Verify Scale in AND operator
        NsMonParam = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_MonitoringParam

        publisher = rift.test.dts.DescriptorPublisher(self.log, self.dts, self.loop)

        for criteria in criterias:
            monp_id = criteria.ns_monitoring_param_ref
            w_xpath = "D,/rw-project:project/nsr:ns-instance-opdata/nsr:nsr"
            w_xpath = w_xpath + "[nsr:ns-instance-config-ref={}]/nsr:monitoring-param".format(quoted_key(nsr_id))
            xpath =  w_xpath + "[nsr:id={}]".format(quoted_key(monp_id))

            for i in range(self.mock_store.threshold_time + 2):
                value = random.randint(floor, ceil)

                monp = NsMonParam.from_dict({
                        'id': monp_id,
                        'value_integer': value,
                        'nsd_mon_param_ref': monp_id})

                yield from publisher.publish(w_xpath, xpath, monp)
                yield from asyncio.sleep(1)

    @rift.test.dts.async_test
    def test_scale_in(self):
        store = self.mock_store()

        # CFG
        floor, ceil = 0, 100
        nsr_id = store.get_nsr().ns_instance_config_ref
        policy_cfg = store.get_nsd().scaling_group_descriptor[0].scaling_policy[0]
        scaling_name = store.get_nsd().scaling_group_descriptor[0].name


        def make_policy():
            policy = engine.ScalingPolicy(
                    self.log, self.dts, self.loop,
                    store.get_nsr().ns_instance_config_ref, store.get_nsd().id,
                    scaling_name, policy_cfg, store, delegate=mock_delegate)

            return policy

        @asyncio.coroutine
        def scale_out(policy):
            yield from self._populate_mock_values(policy.scaling_criteria, nsr_id, 200, 300)
            # HACK TO RESET THE COOLING TIME
            policy._last_triggered_time = 0

        # Test 1: Scale in shouldn't be called, unless a scale-out happens
        mock_delegate = MockDelegate()
        policy = make_policy()
        yield from policy.register()
        yield from self._populate_mock_values(policy.scaling_criteria, nsr_id, floor, ceil)
        assert mock_delegate.scale_in_called == 0

        # Test 2: AND operation
        yield from scale_out(policy)
        yield from self._populate_mock_values(policy.scaling_criteria, nsr_id, floor, ceil)
        assert mock_delegate.scale_in_called == 1

        # Test 3: AND operation failure
        mock_delegate = MockDelegate()
        policy = make_policy()
        yield from policy.register()
        yield from scale_out(policy)
        yield from self._populate_mock_values([policy.scaling_criteria[0]], nsr_id, floor, ceil)
        assert mock_delegate.scale_in_called == 0


        # Test 4: OR operation
        mock_delegate = MockDelegate()
        policy = make_policy()
        policy_cfg.scale_in_operation_type = "OR"
        yield from policy.register()
        yield from scale_out(policy)
        yield from self._populate_mock_values([policy.scaling_criteria[0]], nsr_id, floor, ceil)
        assert mock_delegate.scale_in_called == 1

    @rift.test.dts.async_test
    def test_scale_out(self):
        """ Tests scale out

        Asserts:
            1. Scale out
            2. Scale out doesn't happen during cooldown
            3. AND operation
            4. OR operation.
        """
        store = self.mock_store()

        # CFG
        floor, ceil = 200, 300
        nsr_id = store.get_nsr().ns_instance_config_ref
        policy_cfg = store.get_nsd().scaling_group_descriptor[0].scaling_policy[0]
        scaling_name = store.get_nsd().scaling_group_descriptor[0].name


        def make_policy():
            policy = engine.ScalingPolicy(
                    self.log, self.dts, self.loop,
                    store.get_nsr().ns_instance_config_ref, store.get_nsd().id,
                    scaling_name, policy_cfg, store, delegate=mock_delegate)

            return policy

        # Test 1: Scale out should be called only when both the criteria are
        # exceeding.
        mock_delegate = MockDelegate()
        policy = make_policy()
        yield from policy.register()
        yield from self._populate_mock_values(policy.scaling_criteria, nsr_id, floor, ceil)
        assert mock_delegate.scale_out_called == 1

        # Test 2: Assert if Scale out doesn't happen when only one exceeds
        mock_delegate = MockDelegate()
        policy = make_policy()
        yield from policy.register()
        yield from self._populate_mock_values([policy.scaling_criteria[0]], nsr_id, floor, ceil)
        assert mock_delegate.scale_out_called == 0

        # Test 3: OR operation
        mock_delegate = MockDelegate()
        policy_cfg.scale_out_operation_type = "OR"
        policy = make_policy()
        yield from policy.register()
        yield from  self._populate_mock_values([policy.scaling_criteria[0]], nsr_id, floor, ceil)
        assert mock_delegate.scale_out_called == 1


def main():
    logging.basicConfig(format='TEST %(message)s')
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.no_runner:
        runner = None

    # Set the global logging level
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.ERROR)


    unittest.main(testRunner=runner, argv=[sys.argv[0]] + unittest_args)

if __name__ == '__main__':
    main()
