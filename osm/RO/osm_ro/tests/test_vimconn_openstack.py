# -*- coding: utf-8 -*-

##
# Copyright 2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

"""
This module contains unit tests for the OpenStack VIM connector
Run this directly with python2 or python3.
"""

import copy
import unittest

import mock
from neutronclient.v2_0.client import Client

from osm_ro import vimconn
from osm_ro.vimconn_openstack import vimconnector


__author__ = "Igor D.C."
__date__ = "$23-aug-2017 23:59:59$"


class TestSfcOperations(unittest.TestCase):
    def setUp(self):
        # instantiate dummy VIM connector so we can test it
        self.vimconn = vimconnector(
            '123', 'openstackvim', '456', '789', 'http://dummy.url', None,
            'user', 'pass')

    def _test_new_sfi(self, create_port_pair, sfc_encap,
                      ingress_ports=['5311c75d-d718-4369-bbda-cdcc6da60fcc'],
                      egress_ports=['230cdf1b-de37-4891-bc07-f9010cf1f967']):
        # input to VIM connector
        name = 'osm_sfi'
        # + ingress_ports
        # + egress_ports
        # TODO(igordc): must be changed to NSH in Queens (MPLS is a workaround)
        correlation = 'mpls'
        if sfc_encap is not None:
            if not sfc_encap:
                correlation = None

        # what OpenStack is assumed to respond (patch OpenStack's return value)
        dict_from_neutron = {'port_pair': {
            'id': '3d7ddc13-923c-4332-971e-708ed82902ce',
            'name': name,
            'description': '',
            'tenant_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'project_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'ingress': ingress_ports[0] if len(ingress_ports) else None,
            'egress': egress_ports[0] if len(egress_ports) else None,
            'service_function_parameters': {'correlation': correlation}
        }}
        create_port_pair.return_value = dict_from_neutron

        # what the VIM connector is expected to
        # send to OpenStack based on the input
        dict_to_neutron = {'port_pair': {
            'name': name,
            'ingress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
            'egress': '230cdf1b-de37-4891-bc07-f9010cf1f967',
            'service_function_parameters': {'correlation': correlation}
        }}

        # call the VIM connector
        if sfc_encap is None:
            result = self.vimconn.new_sfi(name, ingress_ports, egress_ports)
        else:
            result = self.vimconn.new_sfi(name, ingress_ports, egress_ports,
                                          sfc_encap)

        # assert that the VIM connector made the expected call to OpenStack
        create_port_pair.assert_called_with(dict_to_neutron)
        # assert that the VIM connector had the expected result / return value
        self.assertEqual(result, dict_from_neutron['port_pair']['id'])

    def _test_new_sf(self, create_port_pair_group):
        # input to VIM connector
        name = 'osm_sf'
        instances = ['bbd01220-cf72-41f2-9e70-0669c2e5c4cd',
                     '12ba215e-3987-4892-bd3a-d0fd91eecf98',
                     'e25a7c79-14c8-469a-9ae1-f601c9371ffd']

        # what OpenStack is assumed to respond (patch OpenStack's return value)
        dict_from_neutron = {'port_pair_group': {
            'id': '3d7ddc13-923c-4332-971e-708ed82902ce',
            'name': name,
            'description': '',
            'tenant_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'project_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'port_pairs': instances,
            'group_id': 1,
            'port_pair_group_parameters': {
                "lb_fields": [],
                "ppg_n_tuple_mapping": {
                    "ingress_n_tuple": {},
                    "egress_n_tuple": {}
                }}
        }}
        create_port_pair_group.return_value = dict_from_neutron

        # what the VIM connector is expected to
        # send to OpenStack based on the input
        dict_to_neutron = {'port_pair_group': {
            'name': name,
            'port_pairs': ['bbd01220-cf72-41f2-9e70-0669c2e5c4cd',
                           '12ba215e-3987-4892-bd3a-d0fd91eecf98',
                           'e25a7c79-14c8-469a-9ae1-f601c9371ffd']
        }}

        # call the VIM connector
        result = self.vimconn.new_sf(name, instances)

        # assert that the VIM connector made the expected call to OpenStack
        create_port_pair_group.assert_called_with(dict_to_neutron)
        # assert that the VIM connector had the expected result / return value
        self.assertEqual(result, dict_from_neutron['port_pair_group']['id'])

    def _test_new_sfp(self, create_port_chain, sfc_encap, spi):
        # input to VIM connector
        name = 'osm_sfp'
        classifications = ['2bd2a2e5-c5fd-4eac-a297-d5e255c35c19',
                           '00f23389-bdfa-43c2-8b16-5815f2582fa8']
        sfs = ['2314daec-c262-414a-86e3-69bb6fa5bc16',
               'd8bfdb5d-195e-4f34-81aa-6135705317df']

        # TODO(igordc): must be changed to NSH in Queens (MPLS is a workaround)
        correlation = 'mpls'
        chain_id = 33
        if sfc_encap is not None:
            if not sfc_encap:
                correlation = None
        if spi:
            chain_id = spi

        # what OpenStack is assumed to respond (patch OpenStack's return value)
        dict_from_neutron = {'port_chain': {
            'id': '5bc05721-079b-4b6e-a235-47cac331cbb6',
            'name': name,
            'description': '',
            'tenant_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'project_id': '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c',
            'chain_id': chain_id,
            'flow_classifiers': classifications,
            'port_pair_groups': sfs,
            'chain_parameters': {'correlation': correlation}
        }}
        create_port_chain.return_value = dict_from_neutron

        # what the VIM connector is expected to
        # send to OpenStack based on the input
        dict_to_neutron = {'port_chain': {
            'name': name,
            'flow_classifiers': ['2bd2a2e5-c5fd-4eac-a297-d5e255c35c19',
                                 '00f23389-bdfa-43c2-8b16-5815f2582fa8'],
            'port_pair_groups': ['2314daec-c262-414a-86e3-69bb6fa5bc16',
                                 'd8bfdb5d-195e-4f34-81aa-6135705317df'],
            'chain_parameters': {'correlation': correlation}
        }}
        if spi:
            dict_to_neutron['port_chain']['chain_id'] = spi

        # call the VIM connector
        if sfc_encap is None:
            if spi is None:
                result = self.vimconn.new_sfp(name, classifications, sfs)
            else:
                result = self.vimconn.new_sfp(name, classifications, sfs,
                                              spi=spi)
        else:
            if spi is None:
                result = self.vimconn.new_sfp(name, classifications, sfs,
                                              sfc_encap)
            else:
                result = self.vimconn.new_sfp(name, classifications, sfs,
                                              sfc_encap, spi)

        # assert that the VIM connector made the expected call to OpenStack
        create_port_chain.assert_called_with(dict_to_neutron)
        # assert that the VIM connector had the expected result / return value
        self.assertEqual(result, dict_from_neutron['port_chain']['id'])

    def _test_new_classification(self, create_flow_classifier, ctype):
        # input to VIM connector
        name = 'osm_classification'
        definition = {'ethertype': 'IPv4',
                      'logical_source_port':
                          'aaab0ab0-1452-4636-bb3b-11dca833fa2b',
                      'protocol': 'tcp',
                      'source_ip_prefix': '192.168.2.0/24',
                      'source_port_range_max': 99,
                      'source_port_range_min': 50}

        # what OpenStack is assumed to respond (patch OpenStack's return value)
        dict_from_neutron = {'flow_classifier': copy.copy(definition)}
        dict_from_neutron['flow_classifier'][
            'id'] = '7735ec2c-fddf-4130-9712-32ed2ab6a372'
        dict_from_neutron['flow_classifier']['name'] = name
        dict_from_neutron['flow_classifier']['description'] = ''
        dict_from_neutron['flow_classifier'][
            'tenant_id'] = '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c'
        dict_from_neutron['flow_classifier'][
            'project_id'] = '130b1e97-b0f1-40a8-8804-b6ad9b8c3e0c'
        create_flow_classifier.return_value = dict_from_neutron

        # what the VIM connector is expected to
        # send to OpenStack based on the input
        dict_to_neutron = {'flow_classifier': copy.copy(definition)}
        dict_to_neutron['flow_classifier']['name'] = 'osm_classification'

        # call the VIM connector
        result = self.vimconn.new_classification(name, ctype, definition)

        # assert that the VIM connector made the expected call to OpenStack
        create_flow_classifier.assert_called_with(dict_to_neutron)
        # assert that the VIM connector had the expected result / return value
        self.assertEqual(result, dict_from_neutron['flow_classifier']['id'])

    @mock.patch.object(Client, 'create_flow_classifier')
    def test_new_classification(self, create_flow_classifier):
        self._test_new_classification(create_flow_classifier,
                                      'legacy_flow_classifier')

    @mock.patch.object(Client, 'create_flow_classifier')
    def test_new_classification_unsupported_type(self, create_flow_classifier):
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_classification,
                          create_flow_classifier, 'h265')

    @mock.patch.object(Client, 'create_port_pair')
    def test_new_sfi_with_sfc_encap(self, create_port_pair):
        self._test_new_sfi(create_port_pair, True)

    @mock.patch.object(Client, 'create_port_pair')
    def test_new_sfi_without_sfc_encap(self, create_port_pair):
        self._test_new_sfi(create_port_pair, False)

    @mock.patch.object(Client, 'create_port_pair')
    def test_new_sfi_default_sfc_encap(self, create_port_pair):
        self._test_new_sfi(create_port_pair, None)

    @mock.patch.object(Client, 'create_port_pair')
    def test_new_sfi_bad_ingress_ports(self, create_port_pair):
        ingress_ports = ['5311c75d-d718-4369-bbda-cdcc6da60fcc',
                         'a0273f64-82c9-11e7-b08f-6328e53f0fa7']
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfi,
                          create_port_pair, True, ingress_ports=ingress_ports)
        ingress_ports = []
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfi,
                          create_port_pair, True, ingress_ports=ingress_ports)

    @mock.patch.object(Client, 'create_port_pair')
    def test_new_sfi_bad_egress_ports(self, create_port_pair):
        egress_ports = ['230cdf1b-de37-4891-bc07-f9010cf1f967',
                        'b41228fe-82c9-11e7-9b44-17504174320b']
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfi,
                          create_port_pair, True, egress_ports=egress_ports)
        egress_ports = []
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfi,
                          create_port_pair, True, egress_ports=egress_ports)

    @mock.patch.object(vimconnector, 'get_sfi')
    @mock.patch.object(Client, 'create_port_pair_group')
    def test_new_sf(self, create_port_pair_group, get_sfi):
        get_sfi.return_value = {'sfc_encap': 'mpls'}
        self._test_new_sf(create_port_pair_group)

    @mock.patch.object(vimconnector, 'get_sfi')
    @mock.patch.object(Client, 'create_port_pair_group')
    def test_new_sf_inconsistent_sfc_encap(self, create_port_pair_group,
                                           get_sfi):
        get_sfi.return_value = {'sfc_encap': 'nsh'}
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sf, create_port_pair_group)

    @mock.patch.object(Client, 'create_port_chain')
    def test_new_sfp_with_sfc_encap(self, create_port_chain):
        self._test_new_sfp(create_port_chain, True, None)

    @mock.patch.object(Client, 'create_port_chain')
    def test_new_sfp_without_sfc_encap(self, create_port_chain):
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfp,
                          create_port_chain, False, None)
        self.assertRaises(vimconn.vimconnNotSupportedException,
                          self._test_new_sfp,
                          create_port_chain, False, 25)

    @mock.patch.object(Client, 'create_port_chain')
    def test_new_sfp_default_sfc_encap(self, create_port_chain):
        self._test_new_sfp(create_port_chain, None, None)

    @mock.patch.object(Client, 'create_port_chain')
    def test_new_sfp_with_sfc_encap_spi(self, create_port_chain):
        self._test_new_sfp(create_port_chain, True, 25)

    @mock.patch.object(Client, 'create_port_chain')
    def test_new_sfp_default_sfc_encap_spi(self, create_port_chain):
        self._test_new_sfp(create_port_chain, None, 25)

    @mock.patch.object(Client, 'list_flow_classifier')
    def test_get_classification_list(self, list_flow_classifier):
        # what OpenStack is assumed to return to the VIM connector
        list_flow_classifier.return_value = {'flow_classifiers': [
            {'source_port_range_min': 2000,
             'destination_ip_prefix': '192.168.3.0/24',
             'protocol': 'udp',
             'description': '',
             'ethertype': 'IPv4',
             'l7_parameters': {},
             'source_port_range_max': 2000,
             'destination_port_range_min': 3000,
             'source_ip_prefix': '192.168.2.0/24',
             'logical_destination_port': None,
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'destination_port_range_max': None,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'logical_source_port': 'aaab0ab0-1452-4636-bb3b-11dca833fa2b',
             'id': '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d',
             'name': 'fc1'}]}

        # call the VIM connector
        filter_dict = {'protocol': 'tcp', 'ethertype': 'IPv4'}
        result = self.vimconn.get_classification_list(filter_dict.copy())

        # assert that VIM connector called OpenStack with the expected filter
        list_flow_classifier.assert_called_with(**filter_dict)
        # assert that the VIM connector successfully
        # translated and returned the OpenStack result
        self.assertEqual(result, [
            {'id': '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d',
             'name': 'fc1',
             'description': '',
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'ctype': 'legacy_flow_classifier',
             'definition': {
                 'source_port_range_min': 2000,
                 'destination_ip_prefix': '192.168.3.0/24',
                 'protocol': 'udp',
                 'ethertype': 'IPv4',
                 'l7_parameters': {},
                 'source_port_range_max': 2000,
                 'destination_port_range_min': 3000,
                 'source_ip_prefix': '192.168.2.0/24',
                 'logical_destination_port': None,
                 'destination_port_range_max': None,
                 'logical_source_port': 'aaab0ab0-1452-4636-bb3b-11dca833fa2b'}
             }])

    def _test_get_sfi_list(self, list_port_pair, correlation, sfc_encap):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair.return_value = {'port_pairs': [
            {'ingress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'egress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'service_function_parameters': {'correlation': correlation},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'c121ebdd-7f2d-4213-b933-3325298a6966',
             'name': 'osm_sfi'}]}

        # call the VIM connector
        filter_dict = {'name': 'osm_sfi', 'description': ''}
        result = self.vimconn.get_sfi_list(filter_dict.copy())

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair.assert_called_with(**filter_dict)
        # assert that the VIM connector successfully
        # translated and returned the OpenStack result
        self.assertEqual(result, [
            {'ingress_ports': ['5311c75d-d718-4369-bbda-cdcc6da60fcc'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'egress_ports': ['5311c75d-d718-4369-bbda-cdcc6da60fcc'],
             'sfc_encap': sfc_encap,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'c121ebdd-7f2d-4213-b933-3325298a6966',
             'name': 'osm_sfi'}])

    @mock.patch.object(Client, 'list_port_pair')
    def test_get_sfi_list_with_sfc_encap(self, list_port_pair):
        self._test_get_sfi_list(list_port_pair, 'nsh', True)

    @mock.patch.object(Client, 'list_port_pair')
    def test_get_sfi_list_without_sfc_encap(self, list_port_pair):
        self._test_get_sfi_list(list_port_pair, None, False)

    @mock.patch.object(Client, 'list_port_pair_group')
    def test_get_sf_list(self, list_port_pair_group):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair_group.return_value = {'port_pair_groups': [
            {'port_pairs': ['08fbdbb0-82d6-11e7-ad95-9bb52fbec2f2',
                            '0d63799c-82d6-11e7-8deb-a746bb3ae9f5'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'port_pair_group_parameters': {},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'f4a0bde8-82d5-11e7-90e1-a72b762fa27f',
             'name': 'osm_sf'}]}

        # call the VIM connector
        filter_dict = {'name': 'osm_sf', 'description': ''}
        result = self.vimconn.get_sf_list(filter_dict.copy())

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair_group.assert_called_with(**filter_dict)
        # assert that the VIM connector successfully
        # translated and returned the OpenStack result
        self.assertEqual(result, [
            {'instances': ['08fbdbb0-82d6-11e7-ad95-9bb52fbec2f2',
                           '0d63799c-82d6-11e7-8deb-a746bb3ae9f5'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'f4a0bde8-82d5-11e7-90e1-a72b762fa27f',
             'name': 'osm_sf'}])

    def _test_get_sfp_list(self, list_port_chain, correlation, sfc_encap):
        # what OpenStack is assumed to return to the VIM connector
        list_port_chain.return_value = {'port_chains': [
            {'port_pair_groups': ['7d8e3bf8-82d6-11e7-a032-8ff028839d25',
                                  '7dc9013e-82d6-11e7-a5a6-a3a8d78a5518'],
             'flow_classifiers': ['1333c2f4-82d7-11e7-a5df-9327f33d104e',
                                  '1387ab44-82d7-11e7-9bb0-476337183905'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'chain_parameters': {'correlation': correlation},
             'chain_id': 40,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': '821bc9be-82d7-11e7-8ce3-23a08a27ab47',
             'name': 'osm_sfp'}]}

        # call the VIM connector
        filter_dict = {'name': 'osm_sfp', 'description': ''}
        result = self.vimconn.get_sfp_list(filter_dict.copy())

        # assert that VIM connector called OpenStack with the expected filter
        list_port_chain.assert_called_with(**filter_dict)
        # assert that the VIM connector successfully
        # translated and returned the OpenStack result
        self.assertEqual(result, [
            {'service_functions': ['7d8e3bf8-82d6-11e7-a032-8ff028839d25',
                                   '7dc9013e-82d6-11e7-a5a6-a3a8d78a5518'],
             'classifications': ['1333c2f4-82d7-11e7-a5df-9327f33d104e',
                                 '1387ab44-82d7-11e7-9bb0-476337183905'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'sfc_encap': sfc_encap,
             'spi': 40,
             'id': '821bc9be-82d7-11e7-8ce3-23a08a27ab47',
             'name': 'osm_sfp'}])

    @mock.patch.object(Client, 'list_port_chain')
    def test_get_sfp_list_with_sfc_encap(self, list_port_chain):
        self._test_get_sfp_list(list_port_chain, 'nsh', True)

    @mock.patch.object(Client, 'list_port_chain')
    def test_get_sfp_list_without_sfc_encap(self, list_port_chain):
        self._test_get_sfp_list(list_port_chain, None, False)

    @mock.patch.object(Client, 'list_flow_classifier')
    def test_get_classification(self, list_flow_classifier):
        # what OpenStack is assumed to return to the VIM connector
        list_flow_classifier.return_value = {'flow_classifiers': [
            {'source_port_range_min': 2000,
             'destination_ip_prefix': '192.168.3.0/24',
             'protocol': 'udp',
             'description': '',
             'ethertype': 'IPv4',
             'l7_parameters': {},
             'source_port_range_max': 2000,
             'destination_port_range_min': 3000,
             'source_ip_prefix': '192.168.2.0/24',
             'logical_destination_port': None,
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'destination_port_range_max': None,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'logical_source_port': 'aaab0ab0-1452-4636-bb3b-11dca833fa2b',
             'id': '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d',
             'name': 'fc1'}
        ]}

        # call the VIM connector
        result = self.vimconn.get_classification(
            '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d')

        # assert that VIM connector called OpenStack with the expected filter
        list_flow_classifier.assert_called_with(
            id='22198366-d4e8-4d6b-b4d2-637d5d6cbb7d')
        # assert that VIM connector successfully returned the OpenStack result
        self.assertEqual(result,
                         {'id': '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d',
                          'name': 'fc1',
                          'description': '',
                          'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'ctype': 'legacy_flow_classifier',
                          'definition': {
                              'source_port_range_min': 2000,
                              'destination_ip_prefix': '192.168.3.0/24',
                              'protocol': 'udp',
                              'ethertype': 'IPv4',
                              'l7_parameters': {},
                              'source_port_range_max': 2000,
                              'destination_port_range_min': 3000,
                              'source_ip_prefix': '192.168.2.0/24',
                              'logical_destination_port': None,
                              'destination_port_range_max': None,
                              'logical_source_port':
                                  'aaab0ab0-1452-4636-bb3b-11dca833fa2b'}
                          })

    @mock.patch.object(Client, 'list_flow_classifier')
    def test_get_classification_many_results(self, list_flow_classifier):
        # what OpenStack is assumed to return to the VIM connector
        list_flow_classifier.return_value = {'flow_classifiers': [
            {'source_port_range_min': 2000,
             'destination_ip_prefix': '192.168.3.0/24',
             'protocol': 'udp',
             'description': '',
             'ethertype': 'IPv4',
             'l7_parameters': {},
             'source_port_range_max': 2000,
             'destination_port_range_min': 3000,
             'source_ip_prefix': '192.168.2.0/24',
             'logical_destination_port': None,
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'destination_port_range_max': None,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'logical_source_port': 'aaab0ab0-1452-4636-bb3b-11dca833fa2b',
             'id': '22198366-d4e8-4d6b-b4d2-637d5d6cbb7d',
             'name': 'fc1'},
            {'source_port_range_min': 1000,
             'destination_ip_prefix': '192.168.3.0/24',
             'protocol': 'udp',
             'description': '',
             'ethertype': 'IPv4',
             'l7_parameters': {},
             'source_port_range_max': 1000,
             'destination_port_range_min': 3000,
             'source_ip_prefix': '192.168.2.0/24',
             'logical_destination_port': None,
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'destination_port_range_max': None,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'logical_source_port': 'aaab0ab0-1452-4636-bb3b-11dca833fa2b',
             'id': '3196bafc-82dd-11e7-a205-9bf6c14b0721',
             'name': 'fc2'}
        ]}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnConflictException,
                          self.vimconn.get_classification,
                          '3196bafc-82dd-11e7-a205-9bf6c14b0721')

        # assert the VIM connector called OpenStack with the expected filter
        list_flow_classifier.assert_called_with(
            id='3196bafc-82dd-11e7-a205-9bf6c14b0721')

    @mock.patch.object(Client, 'list_flow_classifier')
    def test_get_classification_no_results(self, list_flow_classifier):
        # what OpenStack is assumed to return to the VIM connector
        list_flow_classifier.return_value = {'flow_classifiers': []}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnNotFoundException,
                          self.vimconn.get_classification,
                          '3196bafc-82dd-11e7-a205-9bf6c14b0721')

        # assert the VIM connector called OpenStack with the expected filter
        list_flow_classifier.assert_called_with(
            id='3196bafc-82dd-11e7-a205-9bf6c14b0721')

    @mock.patch.object(Client, 'list_port_pair')
    def test_get_sfi(self, list_port_pair):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair.return_value = {'port_pairs': [
            {'ingress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'egress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'service_function_parameters': {'correlation': 'nsh'},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'c121ebdd-7f2d-4213-b933-3325298a6966',
             'name': 'osm_sfi1'},
        ]}

        # call the VIM connector
        result = self.vimconn.get_sfi('c121ebdd-7f2d-4213-b933-3325298a6966')

        # assert the VIM connector called OpenStack with the expected filter
        list_port_pair.assert_called_with(
            id='c121ebdd-7f2d-4213-b933-3325298a6966')
        # assert the VIM connector successfully returned the OpenStack result
        self.assertEqual(result,
                         {'ingress_ports': [
                             '5311c75d-d718-4369-bbda-cdcc6da60fcc'],
                          'egress_ports': [
                              '5311c75d-d718-4369-bbda-cdcc6da60fcc'],
                          'sfc_encap': True,
                          'description': '',
                          'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'id': 'c121ebdd-7f2d-4213-b933-3325298a6966',
                          'name': 'osm_sfi1'})

    @mock.patch.object(Client, 'list_port_pair')
    def test_get_sfi_many_results(self, list_port_pair):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair.return_value = {'port_pairs': [
            {'ingress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'egress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'service_function_parameters': {'correlation': 'nsh'},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'c121ebdd-7f2d-4213-b933-3325298a6966',
             'name': 'osm_sfi1'},
            {'ingress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'egress': '5311c75d-d718-4369-bbda-cdcc6da60fcc',
             'service_function_parameters': {'correlation': 'nsh'},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'c0436d92-82db-11e7-8f9c-5fa535f1261f',
             'name': 'osm_sfi2'}
        ]}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnConflictException,
                          self.vimconn.get_sfi,
                          'c0436d92-82db-11e7-8f9c-5fa535f1261f')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair.assert_called_with(
            id='c0436d92-82db-11e7-8f9c-5fa535f1261f')

    @mock.patch.object(Client, 'list_port_pair')
    def test_get_sfi_no_results(self, list_port_pair):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair.return_value = {'port_pairs': []}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnNotFoundException,
                          self.vimconn.get_sfi,
                          'b22892fc-82d9-11e7-ae85-0fea6a3b3757')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair.assert_called_with(
            id='b22892fc-82d9-11e7-ae85-0fea6a3b3757')

    @mock.patch.object(Client, 'list_port_pair_group')
    def test_get_sf(self, list_port_pair_group):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair_group.return_value = {'port_pair_groups': [
            {'port_pairs': ['08fbdbb0-82d6-11e7-ad95-9bb52fbec2f2'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'port_pair_group_parameters': {},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'aabba8a6-82d9-11e7-a18a-d3c7719b742d',
             'name': 'osm_sf1'}
        ]}

        # call the VIM connector
        result = self.vimconn.get_sf('b22892fc-82d9-11e7-ae85-0fea6a3b3757')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair_group.assert_called_with(
            id='b22892fc-82d9-11e7-ae85-0fea6a3b3757')
        # assert that VIM connector successfully returned the OpenStack result
        self.assertEqual(result,
                         {'instances': [
                             '08fbdbb0-82d6-11e7-ad95-9bb52fbec2f2'],
                          'description': '',
                          'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'id': 'aabba8a6-82d9-11e7-a18a-d3c7719b742d',
                          'name': 'osm_sf1'})

    @mock.patch.object(Client, 'list_port_pair_group')
    def test_get_sf_many_results(self, list_port_pair_group):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair_group.return_value = {'port_pair_groups': [
            {'port_pairs': ['08fbdbb0-82d6-11e7-ad95-9bb52fbec2f2'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'port_pair_group_parameters': {},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'aabba8a6-82d9-11e7-a18a-d3c7719b742d',
             'name': 'osm_sf1'},
            {'port_pairs': ['0d63799c-82d6-11e7-8deb-a746bb3ae9f5'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'port_pair_group_parameters': {},
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': 'b22892fc-82d9-11e7-ae85-0fea6a3b3757',
             'name': 'osm_sf2'}
        ]}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnConflictException,
                          self.vimconn.get_sf,
                          'b22892fc-82d9-11e7-ae85-0fea6a3b3757')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair_group.assert_called_with(
            id='b22892fc-82d9-11e7-ae85-0fea6a3b3757')

    @mock.patch.object(Client, 'list_port_pair_group')
    def test_get_sf_no_results(self, list_port_pair_group):
        # what OpenStack is assumed to return to the VIM connector
        list_port_pair_group.return_value = {'port_pair_groups': []}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnNotFoundException,
                          self.vimconn.get_sf,
                          'b22892fc-82d9-11e7-ae85-0fea6a3b3757')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_pair_group.assert_called_with(
            id='b22892fc-82d9-11e7-ae85-0fea6a3b3757')

    @mock.patch.object(Client, 'list_port_chain')
    def test_get_sfp(self, list_port_chain):
        # what OpenStack is assumed to return to the VIM connector
        list_port_chain.return_value = {'port_chains': [
            {'port_pair_groups': ['7d8e3bf8-82d6-11e7-a032-8ff028839d25'],
             'flow_classifiers': ['1333c2f4-82d7-11e7-a5df-9327f33d104e'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'chain_parameters': {'correlation': 'nsh'},
             'chain_id': 40,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': '821bc9be-82d7-11e7-8ce3-23a08a27ab47',
             'name': 'osm_sfp1'}]}

        # call the VIM connector
        result = self.vimconn.get_sfp('821bc9be-82d7-11e7-8ce3-23a08a27ab47')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_chain.assert_called_with(
            id='821bc9be-82d7-11e7-8ce3-23a08a27ab47')
        # assert that VIM connector successfully returned the OpenStack result
        self.assertEqual(result,
                         {'service_functions': [
                             '7d8e3bf8-82d6-11e7-a032-8ff028839d25'],
                          'classifications': [
                              '1333c2f4-82d7-11e7-a5df-9327f33d104e'],
                          'description': '',
                          'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
                          'sfc_encap': True,
                          'spi': 40,
                          'id': '821bc9be-82d7-11e7-8ce3-23a08a27ab47',
                          'name': 'osm_sfp1'})

    @mock.patch.object(Client, 'list_port_chain')
    def test_get_sfp_many_results(self, list_port_chain):
        # what OpenStack is assumed to return to the VIM connector
        list_port_chain.return_value = {'port_chains': [
            {'port_pair_groups': ['7d8e3bf8-82d6-11e7-a032-8ff028839d25'],
             'flow_classifiers': ['1333c2f4-82d7-11e7-a5df-9327f33d104e'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'chain_parameters': {'correlation': 'nsh'},
             'chain_id': 40,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': '821bc9be-82d7-11e7-8ce3-23a08a27ab47',
             'name': 'osm_sfp1'},
            {'port_pair_groups': ['7d8e3bf8-82d6-11e7-a032-8ff028839d25'],
             'flow_classifiers': ['1333c2f4-82d7-11e7-a5df-9327f33d104e'],
             'description': '',
             'tenant_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'chain_parameters': {'correlation': 'nsh'},
             'chain_id': 50,
             'project_id': '8f3019ef06374fa880a0144ad4bc1d7b',
             'id': '5d002f38-82de-11e7-a770-f303f11ce66a',
             'name': 'osm_sfp2'}
        ]}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnConflictException,
                          self.vimconn.get_sfp,
                          '5d002f38-82de-11e7-a770-f303f11ce66a')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_chain.assert_called_with(
            id='5d002f38-82de-11e7-a770-f303f11ce66a')

    @mock.patch.object(Client, 'list_port_chain')
    def test_get_sfp_no_results(self, list_port_chain):
        # what OpenStack is assumed to return to the VIM connector
        list_port_chain.return_value = {'port_chains': []}

        # call the VIM connector
        self.assertRaises(vimconn.vimconnNotFoundException,
                          self.vimconn.get_sfp,
                          '5d002f38-82de-11e7-a770-f303f11ce66a')

        # assert that VIM connector called OpenStack with the expected filter
        list_port_chain.assert_called_with(
            id='5d002f38-82de-11e7-a770-f303f11ce66a')

    @mock.patch.object(Client, 'delete_flow_classifier')
    def test_delete_classification(self, delete_flow_classifier):
        result = self.vimconn.delete_classification(
            '638f957c-82df-11e7-b7c8-132706021464')
        delete_flow_classifier.assert_called_with(
            '638f957c-82df-11e7-b7c8-132706021464')
        self.assertEqual(result, '638f957c-82df-11e7-b7c8-132706021464')

    @mock.patch.object(Client, 'delete_port_pair')
    def test_delete_sfi(self, delete_port_pair):
        result = self.vimconn.delete_sfi(
            '638f957c-82df-11e7-b7c8-132706021464')
        delete_port_pair.assert_called_with(
            '638f957c-82df-11e7-b7c8-132706021464')
        self.assertEqual(result, '638f957c-82df-11e7-b7c8-132706021464')

    @mock.patch.object(Client, 'delete_port_pair_group')
    def test_delete_sf(self, delete_port_pair_group):
        result = self.vimconn.delete_sf('638f957c-82df-11e7-b7c8-132706021464')
        delete_port_pair_group.assert_called_with(
            '638f957c-82df-11e7-b7c8-132706021464')
        self.assertEqual(result, '638f957c-82df-11e7-b7c8-132706021464')

    @mock.patch.object(Client, 'delete_port_chain')
    def test_delete_sfp(self, delete_port_chain):
        result = self.vimconn.delete_sfp(
            '638f957c-82df-11e7-b7c8-132706021464')
        delete_port_chain.assert_called_with(
            '638f957c-82df-11e7-b7c8-132706021464')
        self.assertEqual(result, '638f957c-82df-11e7-b7c8-132706021464')


if __name__ == '__main__':
    unittest.main()
