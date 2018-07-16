#!/usr/bin/env python2
# -*- coding: utf-8 -*-

##
# Copyright 2017
# This file is part of openmano
# All Rights Reserved.
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
##

"""
Module for testing openmano functionality. It uses openmanoclient.py for invoking openmano
"""

import logging
import os
import argcomplete
import unittest
import string
import inspect
import random
# import traceback
import glob
import yaml
import sys
import time
import uuid
import json
from argparse import ArgumentParser

__author__ = "Pablo Montes, Alfonso Tierno"
__date__ = "$16-Feb-2017 17:08:16$"
__version__ = "0.1.0"
version_date = "Oct 2017"

test_config = {}    # used for global variables with the test configuration


class test_base(unittest.TestCase):
    test_index = 1
    test_text = None

    @classmethod
    def setUpClass(cls):
        logger.info("{}. {}".format(test_config["test_number"], cls.__name__))

    @classmethod
    def tearDownClass(cls):
        test_config["test_number"] += 1

    def tearDown(self):
        exec_info = sys.exc_info()
        if exec_info == (None, None, None):
            logger.info(self.__class__.test_text+" -> TEST OK")
        else:
            logger.warning(self.__class__.test_text+" -> TEST NOK")
            logger.critical("Traceback error",exc_info=True)


def check_instance_scenario_active(uuid):
    instance = test_config["client"].get_instance(uuid=uuid)

    for net in instance['nets']:
        status = net['status']
        if status != 'ACTIVE':
            return (False, status)

    for vnf in instance['vnfs']:
        for vm in vnf['vms']:
            status = vm['status']
            if status != 'ACTIVE':
                return (False, status)

    return (True, None)


'''
IMPORTANT NOTE
All unittest classes for code based tests must have prefix 'test_' in order to be taken into account for tests
'''
class test_VIM_datacenter_tenant_operations(test_base):
    tenant_name = None

    def test_000_create_RO_tenant(self):
        self.__class__.tenant_name = _get_random_string(20)
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        tenant = test_config["client"].create_tenant(name=self.__class__.tenant_name,
                                                     description=self.__class__.tenant_name)
        logger.debug("{}".format(tenant))
        self.assertEqual(tenant.get('tenant', {}).get('name', ''), self.__class__.tenant_name)

    def test_010_list_RO_tenant(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        tenant = test_config["client"].get_tenant(name=self.__class__.tenant_name)
        logger.debug("{}".format(tenant))
        self.assertEqual(tenant.get('tenant', {}).get('name', ''), self.__class__.tenant_name)

    def test_020_delete_RO_tenant(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        tenant = test_config["client"].delete_tenant(name=self.__class__.tenant_name)
        logger.debug("{}".format(tenant))
        assert('deleted' in tenant.get('result',""))


class test_VIM_datacenter_operations(test_base):
    datacenter_name = None

    def test_000_create_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.datacenter_name = _get_random_string(20)
        self.__class__.test_index += 1
        self.datacenter = test_config["client"].create_datacenter(name=self.__class__.datacenter_name,
                                                                  vim_url="http://fakeurl/fake")
        logger.debug("{}".format(self.datacenter))
        self.assertEqual (self.datacenter.get('datacenter', {}).get('name',''), self.__class__.datacenter_name)

    def test_010_list_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        self.datacenter = test_config["client"].get_datacenter(all_tenants=True, name=self.__class__.datacenter_name)
        logger.debug("{}".format(self.datacenter))
        self.assertEqual (self.datacenter.get('datacenter', {}).get('name', ''), self.__class__.datacenter_name)

    def test_020_attach_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        self.datacenter = test_config["client"].attach_datacenter(name=self.__class__.datacenter_name,
                                                                  vim_tenant_name='fake')
        logger.debug("{}".format(self.datacenter))
        assert ('vim_tenants' in self.datacenter.get('datacenter', {}))

    def test_030_list_attached_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        self.datacenter = test_config["client"].get_datacenter(all_tenants=False, name=self.__class__.datacenter_name)
        logger.debug("{}".format(self.datacenter))
        self.assertEqual (self.datacenter.get('datacenter', {}).get('name', ''), self.__class__.datacenter_name)

    def test_040_detach_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        self.datacenter = test_config["client"].detach_datacenter(name=self.__class__.datacenter_name)
        logger.debug("{}".format(self.datacenter))
        assert ('detached' in self.datacenter.get('result', ""))

    def test_050_delete_datacenter(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        self.datacenter = test_config["client"].delete_datacenter(name=self.__class__.datacenter_name)
        logger.debug("{}".format(self.datacenter))
        assert('deleted' in self.datacenter.get('result',""))


class test_VIM_network_operations(test_base):
    vim_network_name = None
    vim_network_uuid = None

    def test_000_create_VIM_network(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.vim_network_name = _get_random_string(20)
        self.__class__.test_index += 1
        network = test_config["client"].vim_action("create", "networks", name=self.__class__.vim_network_name)
        logger.debug("{}".format(network))
        self.__class__.vim_network_uuid = network["network"]["id"]
        self.assertEqual(network.get('network', {}).get('name', ''), self.__class__.vim_network_name)

    def test_010_list_VIM_networks(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        networks = test_config["client"].vim_action("list", "networks")
        logger.debug("{}".format(networks))

    def test_020_get_VIM_network_by_uuid(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        network = test_config["client"].vim_action("show", "networks", uuid=self.__class__.vim_network_uuid)
        logger.debug("{}".format(network))
        self.assertEqual(network.get('network', {}).get('name', ''), self.__class__.vim_network_name)

    def test_030_delete_VIM_network_by_uuid(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        network = test_config["client"].vim_action("delete", "networks", uuid=self.__class__.vim_network_uuid)
        logger.debug("{}".format(network))
        assert ('deleted' in network.get('result', ""))


class test_VIM_image_operations(test_base):

    def test_000_list_VIM_images(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        images = test_config["client"].vim_action("list", "images")
        logger.debug("{}".format(images))

'''
The following is a non critical test that will fail most of the times.
In case of OpenStack datacenter these tests will only success if RO has access to the admin endpoint
This test will only be executed in case it is specifically requested by the user
'''
class test_VIM_tenant_operations(test_base):
    vim_tenant_name = None
    vim_tenant_uuid = None

    @classmethod
    def setUpClass(cls):
        test_base.setUpClass(cls)
        logger.warning("In case of OpenStack datacenter these tests will only success "
                       "if RO has access to the admin endpoint")

    def test_000_create_VIM_tenant(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.vim_tenant_name = _get_random_string(20)
        self.__class__.test_index += 1
        tenant = test_config["client"].vim_action("create", "tenants", name=self.__class__.vim_tenant_name)
        logger.debug("{}".format(tenant))
        self.__class__.vim_tenant_uuid = tenant["tenant"]["id"]
        self.assertEqual(tenant.get('tenant', {}).get('name', ''), self.__class__.vim_tenant_name)

    def test_010_list_VIM_tenants(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        tenants = test_config["client"].vim_action("list", "tenants")
        logger.debug("{}".format(tenants))

    def test_020_get_VIM_tenant_by_uuid(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        tenant = test_config["client"].vim_action("show", "tenants", uuid=self.__class__.vim_tenant_uuid)
        logger.debug("{}".format(tenant))
        self.assertEqual(tenant.get('tenant', {}).get('name', ''), self.__class__.vim_tenant_name)

    def test_030_delete_VIM_tenant_by_uuid(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        tenant = test_config["client"].vim_action("delete", "tenants", uuid=self.__class__.vim_tenant_uuid)
        logger.debug("{}".format(tenant))
        assert ('deleted' in tenant.get('result', ""))


class test_vimconn_connect(test_base):

    def test_000_connect(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)

        self.__class__.test_index += 1
        if test_config['vimtype'] == 'vmware':
            vca_object = test_config["vim_conn"].connect()
            logger.debug("{}".format(vca_object))
            self.assertIsNotNone(vca_object)

class test_vimconn_new_network(test_base):
    network_name = None

    def test_000_new_network(self):
        self.__class__.network_name = _get_random_string(20)
        network_type = 'bridge'

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                     self.__class__.test_index, inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                          net_type=network_type)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

        network_list = test_config["vim_conn"].get_network_list()
        for net in network_list:
            if self.__class__.network_name in net.get('name'):
                self.assertIn(self.__class__.network_name, net.get('name'))
                self.assertEqual(net.get('type'), network_type)

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_010_new_network_by_types(self):
        delete_net_ids = []
        network_types = ['data','bridge','mgmt']
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        for net_type in network_types:
            self.__class__.network_name = _get_random_string(20)
            network_id = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                                                net_type=net_type)

            delete_net_ids.append(network_id)
            logger.debug("{}".format(network_id))

            network_list = test_config["vim_conn"].get_network_list()
            for net in network_list:
                if self.__class__.network_name in net.get('name'):
                    self.assertIn(self.__class__.network_name, net.get('name'))
                if net_type in net.get('type'):
                    self.assertEqual(net.get('type'), net_type)
                else:
                    self.assertNotEqual(net.get('type'), net_type)

        # Deleting created network
        for net_id in delete_net_ids:
            result = test_config["vim_conn"].delete_network(net_id)
            if result:
                logger.info("Network id {} sucessfully deleted".format(net_id))
            else:
                logger.info("Failed to delete network id {}".format(net_id))

    def test_020_new_network_by_ipprofile(self):
        test_directory_content = os.listdir(test_config["test_directory"])

        for dir_name in test_directory_content:
            if dir_name == 'simple_multi_vnfc':
                self.__class__.scenario_test_path = test_config["test_directory"] + '/'+ dir_name
                vnfd_files = glob.glob(self.__class__.scenario_test_path+'/vnfd_*.yaml')
                break

        for vnfd in vnfd_files:
            with open(vnfd, 'r') as stream:
                vnf_descriptor = yaml.load(stream)

            internal_connections_list = vnf_descriptor['vnf']['internal-connections']
            for item in internal_connections_list:
                if 'ip-profile' in item:
                    version = item['ip-profile']['ip-version']
                    dhcp_count = item['ip-profile']['dhcp']['count']
                    dhcp_enabled = item['ip-profile']['dhcp']['enabled']

        self.__class__.network_name = _get_random_string(20)
        ip_profile = {'dhcp_count': dhcp_count,
                      'dhcp_enabled': dhcp_enabled,
                      'ip_version': version
                     }
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                                           net_type='mgmt',
                                                                     ip_profile=ip_profile)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

        network_list = test_config["vim_conn"].get_network_list()
        for net in network_list:
            if self.__class__.network_name in net.get('name'):
                self.assertIn(self.__class__.network_name, net.get('name'))

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_030_new_network_by_isshared(self):
        self.__class__.network_name = _get_random_string(20)
        shared = True
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                                         net_type='bridge',
                                                                             shared=shared)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

        network_list = test_config["vim_conn"].get_network_list()
        for net in network_list:
            if self.__class__.network_name in net.get('name'):
                self.assertIn(self.__class__.network_name, net.get('name'))
                self.assertEqual(net.get('shared'), shared)

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_040_new_network_by_negative(self):
        self.__class__.network_name = _get_random_string(20)
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                                    net_type='unknowntype')
        self.__class__.network_id = network
        logger.debug("{}".format(network))
        network_list = test_config["vim_conn"].get_network_list()
        for net in network_list:
            if self.__class__.network_name in net.get('name'):
                self.assertIn(self.__class__.network_name, net.get('name'))

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_050_refresh_nets_status(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        # creating new network
        network_name = _get_random_string(20)
        net_type = 'bridge'
        network_id = test_config["vim_conn"].new_network(net_name=network_name,
                                                          net_type=net_type)
        # refresh net status
        net_dict = test_config["vim_conn"].refresh_nets_status([network_id])
        for attr in net_dict[network_id]:
            if attr == 'status':
                self.assertEqual(net_dict[network_id][attr], 'ACTIVE')

        # Deleting created network
        result = test_config["vim_conn"].delete_network(network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(network_id))
        else:
            logger.info("Failed to delete network id {}".format(network_id))

    def test_060_refresh_nets_status_negative(self):
        unknown_net_id = str(uuid.uuid4())
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # refresh net status
        net_dict = test_config["vim_conn"].refresh_nets_status([unknown_net_id])
        self.assertEqual(net_dict, {})

class test_vimconn_get_network_list(test_base):
    network_name = None

    def setUp(self):
        # creating new network
        self.__class__.network_name = _get_random_string(20)
        self.__class__.net_type = 'bridge'
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                          net_type=self.__class__.net_type)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

    def tearDown(self):
        test_base.tearDown(self)

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_000_get_network_list(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network_list = test_config["vim_conn"].get_network_list()
        for net in network_list:
            if self.__class__.network_name in net.get('name'):
                self.assertIn(self.__class__.network_name, net.get('name'))
                self.assertEqual(net.get('type'), self.__class__.net_type)
                self.assertEqual(net.get('status'), 'ACTIVE')
                self.assertEqual(net.get('shared'), False)

    def test_010_get_network_list_by_name(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network_name = test_config['vim_conn'].get_network_name_by_id(self.__class__.network_id)

        # find network from list by it's name
        new_network_list = test_config["vim_conn"].get_network_list({'name': network_name})
        for list_item in new_network_list:
            if self.__class__.network_name in list_item.get('name'):
                self.assertEqual(network_name, list_item.get('name'))
                self.assertEqual(list_item.get('type'), self.__class__.net_type)
                self.assertEqual(list_item.get('status'), 'ACTIVE')

    def test_020_get_network_list_by_id(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # find network from list by it's id
        new_network_list = test_config["vim_conn"].get_network_list({'id':self.__class__.network_id})
        for list_item in new_network_list:
            if self.__class__.network_id in list_item.get('id'):
                self.assertEqual(self.__class__.network_id, list_item.get('id'))
                self.assertEqual(list_item.get('type'), self.__class__.net_type)
                self.assertEqual(list_item.get('status'), 'ACTIVE')

    def test_030_get_network_list_by_shared(self):
        Shared = False
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network_name = test_config['vim_conn'].get_network_name_by_id(self.__class__.network_id)
        # find network from list by it's shared value
        new_network_list = test_config["vim_conn"].get_network_list({'shared':Shared,
                                                                'name':network_name})
        for list_item in new_network_list:
            if list_item.get('shared') == Shared:
                self.assertEqual(list_item.get('shared'), Shared)
                self.assertEqual(list_item.get('type'), self.__class__.net_type)
                self.assertEqual(network_name, list_item.get('name'))

    def test_040_get_network_list_by_tenant_id(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        tenant_list = test_config["vim_conn"].get_tenant_list()
        network_name = test_config['vim_conn'].get_network_name_by_id(self.__class__.network_id)

        for tenant_item in tenant_list:
            if test_config['tenant'] == tenant_item.get('name'):
                # find network from list by it's tenant id
                tenant_id = tenant_item.get('id')
                new_network_list = test_config["vim_conn"].get_network_list({'tenant_id':tenant_id,
                                                                              'name':network_name})
                for list_item in new_network_list:
                    self.assertEqual(tenant_id, list_item.get('tenant_id'))
                    self.assertEqual(network_name, list_item.get('name'))
                    self.assertEqual(list_item.get('type'), self.__class__.net_type)
                    self.assertEqual(list_item.get('status'), 'ACTIVE')

    def test_050_get_network_list_by_status(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        status = 'ACTIVE'

        network_name = test_config['vim_conn'].get_network_name_by_id(self.__class__.network_id)

        # find network from list by it's status
        new_network_list = test_config["vim_conn"].get_network_list({'status':status,
                                                               'name': network_name})
        for list_item in new_network_list:
            self.assertIn(self.__class__.network_name, list_item.get('name'))
            self.assertEqual(list_item.get('type'), self.__class__.net_type)
            self.assertEqual(list_item.get('status'), status)

    def test_060_get_network_list_by_negative(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network_list = test_config["vim_conn"].get_network_list({'name': 'unknown_name'})
        self.assertEqual(network_list, [])

class test_vimconn_get_network(test_base):
    network_name = None

    def setUp(self):
        # creating new network
        self.__class__.network_name = _get_random_string(20)
        self.__class__.net_type = 'bridge'
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                          net_type=self.__class__.net_type)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

    def tearDown(self):
        test_base.tearDown(self)

        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_000_get_network(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        network_info = test_config["vim_conn"].get_network(self.__class__.network_id)
        self.assertEqual(network_info.get('status'), 'ACTIVE')
        self.assertIn(self.__class__.network_name, network_info.get('name'))
        self.assertEqual(network_info.get('type'), self.__class__.net_type)
        self.assertEqual(network_info.get('id'), self.__class__.network_id)

    def test_010_get_network_negative(self):
        Non_exist_id = str(uuid.uuid4())
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].get_network(Non_exist_id)

        self.assertEqual((context.exception).http_code, 404)

class test_vimconn_delete_network(test_base):
    network_name = None

    def test_000_delete_network(self):
        # Creating network
        self.__class__.network_name = _get_random_string(20)
        self.__class__.net_type = 'bridge'
        network = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                          net_type=self.__class__.net_type)
        self.__class__.network_id = network
        logger.debug("{}".format(network))

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))
        time.sleep(5)
        # after deleting network we check in network list
        network_list = test_config["vim_conn"].get_network_list({ 'id':self.__class__.network_id })
        self.assertEqual(network_list, [])

    def test_010_delete_network_negative(self):
        Non_exist_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].delete_network(Non_exist_id)

        self.assertEqual((context.exception).http_code, 400)

class test_vimconn_get_flavor(test_base):

    def test_000_get_flavor(self):
        test_directory_content = os.listdir(test_config["test_directory"])

        for dir_name in test_directory_content:
            if dir_name == 'simple_linux':
                self.__class__.scenario_test_path = test_config["test_directory"] + '/'+ dir_name
                vnfd_files = glob.glob(self.__class__.scenario_test_path+'/vnfd_*.yaml')
                break

        for vnfd in vnfd_files:
            with open(vnfd, 'r') as stream:
                vnf_descriptor = yaml.load(stream)

            vnfc_list = vnf_descriptor['vnf']['VNFC']
            for item in vnfc_list:
                if 'ram' in item and 'vcpus' in item and 'disk' in item:
                    ram = item['ram']
                    vcpus = item['vcpus']
                    disk = item['disk']

        flavor_data = {'ram': ram,
                      'vcpus': vcpus,
                      'disk': disk
                      }

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)
        # get flavor by id
        result = test_config["vim_conn"].get_flavor(flavor_id)
        self.assertEqual(ram, result['ram'])
        self.assertEqual(vcpus, result['vcpus'])
        self.assertEqual(disk, result['disk'])

        # delete flavor
        result = test_config["vim_conn"].delete_flavor(flavor_id)
        if result:
            logger.info("Flavor id {} sucessfully deleted".format(result))
        else:
            logger.info("Failed to delete flavor id {}".format(result))

    def test_010_get_flavor_negative(self):
        Non_exist_flavor_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].get_flavor(Non_exist_flavor_id)

        self.assertEqual((context.exception).http_code, 404)

class test_vimconn_new_flavor(test_base):
    flavor_id = None

    def test_000_new_flavor(self):
        flavor_data = {'ram': 1024, 'vpcus': 1, 'disk': 10}

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # create new flavor
        self.__class__.flavor_id = test_config["vim_conn"].new_flavor(flavor_data)
        self.assertEqual(type(self.__class__.flavor_id),str)
        self.assertIsInstance(uuid.UUID(self.__class__.flavor_id),uuid.UUID)

    def test_010_delete_flavor(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # delete flavor
        result = test_config["vim_conn"].delete_flavor(self.__class__.flavor_id)
        if result:
            logger.info("Flavor id {} sucessfully deleted".format(result))
        else:
            logger.error("Failed to delete flavor id {}".format(result))
            raise Exception ("Failed to delete created flavor")

    def test_020_new_flavor_negative(self):
        Invalid_flavor_data = {'ram': '1024', 'vcpus': 2.0, 'disk': 2.0}

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].new_flavor(Invalid_flavor_data)

        self.assertEqual((context.exception).http_code, 400)

    def test_030_delete_flavor_negative(self):
        Non_exist_flavor_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].delete_flavor(Non_exist_flavor_id)

        self.assertEqual((context.exception).http_code, 404)

class test_vimconn_new_image(test_base):

    def test_000_new_image(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        image_path = test_config['image_path']
        if image_path:
            self.__class__.image_id = test_config["vim_conn"].new_image({ 'name': 'TestImage', 'location' : image_path })
            time.sleep(20)
            self.assertEqual(type(self.__class__.image_id),str)
            self.assertIsInstance(uuid.UUID(self.__class__.image_id),uuid.UUID)
        else:
            self.skipTest("Skipping test as image file not present at RO container")

    def test_010_new_image_negative(self):
        Non_exist_image_path = '/temp1/cirros.ovf'

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].new_image({ 'name': 'TestImage', 'location' : Non_exist_image_path })

        self.assertEqual((context.exception).http_code, 400)

    def test_020_delete_image(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        image_id = test_config["vim_conn"].delete_image(self.__class__.image_id)
        self.assertEqual(type(image_id),str)

    def test_030_delete_image_negative(self):
        Non_exist_image_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].delete_image(Non_exist_image_id)

        self.assertEqual((context.exception).http_code, 404)

class test_vimconn_get_image_id_from_path(test_base):

    def test_000_get_image_id_from_path(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        image_path = test_config['image_path']
        if image_path:
            image_id = test_config["vim_conn"].get_image_id_from_path( image_path )
            self.assertEqual(type(image_id),str)
        else:
            self.skipTest("Skipping test as image file not present at RO container")

    def test_010_get_image_id_from_path_negative(self):
        Non_exist_image_path = '/temp1/cirros.ovf'

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].new_image({ 'name': 'TestImage', 'location' : Non_exist_image_path })

        self.assertEqual((context.exception).http_code, 400)

class test_vimconn_get_image_list(test_base):
    image_name = None
    image_id = None

    def test_000_get_image_list(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        image_list = test_config["vim_conn"].get_image_list()

        for item in image_list:
            if 'name' in item:
                self.__class__.image_name = item['name']
                self.__class__.image_id = item['id']
                self.assertEqual(type(self.__class__.image_name),str)
                self.assertEqual(type(self.__class__.image_id),str)

    def test_010_get_image_list_by_name(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        image_list = test_config["vim_conn"].get_image_list({'name': self.__class__.image_name})

        for item in image_list:
            self.assertEqual(type(item['id']), str)
            self.assertEqual(item['id'], self.__class__.image_id)
            self.assertEqual(type(item['name']), str)
            self.assertEqual(item['name'], self.__class__.image_name)

    def test_020_get_image_list_by_id(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        filter_image_list = test_config["vim_conn"].get_image_list({'id': self.__class__.image_id})

        for item1 in filter_image_list:
            self.assertEqual(type(item1.get('id')), str)
            self.assertEqual(item1.get('id'), self.__class__.image_id)
            self.assertEqual(type(item1.get('name')), str)
            self.assertEqual(item1.get('name'), self.__class__.image_name)

    def test_030_get_image_list_negative(self):
        Non_exist_image_id = uuid.uuid4()
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        image_list = test_config["vim_conn"].get_image_list({'name': 'Unknown_name', 'id': Non_exist_image_id})

        self.assertIsNotNone(image_list, None)
        self.assertEqual(image_list, [])

class test_vimconn_new_vminstance(test_base):
    network_name = None
    net_type = None
    network_id = None
    image_id = None
    instance_id = None

    def setUp(self):
        # create network
        self.__class__.network_name = _get_random_string(20)
        self.__class__.net_type = 'bridge'

        self.__class__.network_id = test_config["vim_conn"].new_network(net_name=self.__class__.network_name,
                                                                            net_type=self.__class__.net_type)

    def tearDown(self):
        test_base.tearDown(self)
        # Deleting created network
        result = test_config["vim_conn"].delete_network(self.__class__.network_id)
        if result:
            logger.info("Network id {} sucessfully deleted".format(self.__class__.network_id))
        else:
            logger.info("Failed to delete network id {}".format(self.__class__.network_id))

    def test_000_new_vminstance(self):
        vpci = "0000:00:11.0"
        name = "eth0"

        flavor_data = {'ram': 1024, 'vcpus': 1, 'disk': 10}

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        # find image name and image id
        if test_config['image_name']:
            image_list = test_config['vim_conn'].get_image_list({'name': test_config['image_name']})
            if len(image_list) == 0:
                raise Exception("Image {} is not found at VIM".format(test_config['image_name']))
            else:
                self.__class__.image_id = image_list[0]['id']
        else:
            image_list = test_config['vim_conn'].get_image_list()
            if len(image_list) == 0:
                raise Exception("Not found any image at VIM")
            else:
                self.__class__.image_id = image_list[0]['id']

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'vpci': vpci, 'port_security': True, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        self.__class__.instance_id, _ = test_config["vim_conn"].new_vminstance(name='Test1_vm', image_id=self.__class__.image_id, flavor_id=flavor_id, net_list=net_list)

        self.assertEqual(type(self.__class__.instance_id),str)

    def test_010_new_vminstance_by_model(self):
        flavor_data = {'ram': 1024, 'vcpus': 2, 'disk': 10}
        model_name = 'e1000'
        name = 'eth0'

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'port_security': True, 'model': model_name, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        instance_id, _ = test_config["vim_conn"].new_vminstance(name='Test1_vm', image_id=self.__class__.image_id,
                                                                                           flavor_id=flavor_id,
                                                                                             net_list=net_list)
        self.assertEqual(type(instance_id),str)
        # Deleting created vm instance
        logger.info("Deleting created vm intance")
        test_config["vim_conn"].delete_vminstance(instance_id)
        time.sleep(10)

    def test_020_new_vminstance_by_net_use(self):
        flavor_data = {'ram': 1024, 'vcpus': 2, 'disk': 10}
        net_use = 'data'
        name = 'eth0'

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': net_use, 'name': name, 'floating_ip': False, 'port_security': True, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        instance_id, _ = test_config["vim_conn"].new_vminstance(name='Test1_vm', image_id=self.__class__.image_id,
                                                                                           flavor_id=flavor_id,
                                                                                             net_list=net_list)
        self.assertEqual(type(instance_id),str)
        # Deleting created vm instance
        logger.info("Deleting created vm intance")
        test_config["vim_conn"].delete_vminstance(instance_id)
        time.sleep(10)

    def test_030_new_vminstance_by_net_type(self):
        flavor_data = {'ram': 1024, 'vcpus': 2, 'disk': 10}
        _type = 'VF'
        name = 'eth0'

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'port_security': True, 'type': _type, 'net_id': self.__class__.network_id}]

        instance_id, _ = test_config["vim_conn"].new_vminstance(name='Test1_vm', image_id=self.__class__.image_id,
                                                                                           flavor_id=flavor_id,
                                                                                             net_list=net_list)
        self.assertEqual(type(instance_id),str)
        # Deleting created vm instance
        logger.info("Deleting created vm intance")
        test_config["vim_conn"].delete_vminstance(instance_id)
        time.sleep(10)

    def test_040_new_vminstance_by_cloud_config(self):
        flavor_data = {'ram': 1024, 'vcpus': 2, 'disk': 10}
        name = 'eth0'
        user_name = 'test_user'

        key_pairs = ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy2w9GHMKKNkpCmrDK2ovc3XBYDETuLWwaW24S+feHhLBQiZlzh3gSQoINlA+2ycM9zYbxl4BGzEzpTVyCQFZv5PidG4m6ox7LR+KYkDcITMyjsVuQJKDvt6oZvRt6KbChcCi0n2JJD/oUiJbBFagDBlRslbaFI2mmqmhLlJ5TLDtmYxzBLpjuX4m4tv+pdmQVfg7DYHsoy0hllhjtcDlt1nn05WgWYRTu7mfQTWfVTavu+OjIX3e0WN6NW7yIBWZcE/Q9lC0II3W7PZDE3QaT55se4SPIO2JTdqsx6XGbekdG1n6adlduOI27sOU5m4doiyJ8554yVbuDB/z5lRBD alfonso.tiernosepulveda@telefonica.com']

        users_data = [{'key-pairs': ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy2w9GHMKKNkpCmrDK2ovc3XBYDETuLWwaW24S+feHhLBQiZlzh3gSQoINlA+2ycM9zYbxl4BGzEzpTVyCQFZv5PidG4m6ox7LR+KYkDcITMyjsVuQJKDvt6oZvRt6KbChcCi0n2JJD/oUiJbBFagDBlRslbaFI2mmqmhLlJ5TLDtmYxzBLpjuX4m4tv+pdmQVfg7DYHsoy0hllhjtcDlt1nn05WgWYRTu7mfQTWfVTavu+OjIX3e0WN6NW7yIBWZcE/Q9lC0II3W7PZDE3QaT55se4SPIO2JTdqsx6XGbekdG1n6adlduOI27sOU5m4doiyJ8554yVbuDB/z5lRBD alfonso.tiernosepulveda@telefonica.com'], 'name': user_name}]

        cloud_data = {'config-files': [{'content': 'auto enp0s3\niface enp0s3 inet dhcp\n', 'dest': '/etc/network/interfaces.d/enp0s3.cfg', 'owner': 'root:root', 'permissions': '0644'}, {'content': '#! /bin/bash\nls -al >> /var/log/osm.log\n', 'dest': '/etc/rc.local', 'permissions': '0755'}, {'content': 'file content', 'dest': '/etc/test_delete'}], 'boot-data-drive': True, 'key-pairs': key_pairs, 'users': users_data }

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'port_security': True, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        instance_id, _ = test_config["vim_conn"].new_vminstance(name='Cloud_vm', image_id=self.__class__.image_id,
                                                                                           flavor_id=flavor_id,
                                                                                             net_list=net_list,
                                                                                       cloud_config=cloud_data)
        self.assertEqual(type(instance_id),str)
        # Deleting created vm instance
        logger.info("Deleting created vm intance")
        test_config["vim_conn"].delete_vminstance(instance_id)
        time.sleep(10)

    def test_050_new_vminstance_by_disk_list(self):
        flavor_data = {'ram': 1024, 'vcpus': 2, 'disk': 10}
        name = 'eth0'

        device_data = [{'image_id': self.__class__.image_id, 'size': '5'}]

        # create new flavor
        flavor_id = test_config["vim_conn"].new_flavor(flavor_data)

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'port_security': True, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        instance_id, _ = test_config["vim_conn"].new_vminstance(name='VM_test1', image_id=self.__class__.image_id,
                                                                                           flavor_id=flavor_id,
                                                                                             net_list=net_list,
                                                                                         disk_list=device_data)
        self.assertEqual(type(instance_id),str)
        # Deleting created vm instance
        logger.info("Deleting created vm intance")
        test_config["vim_conn"].delete_vminstance(instance_id)
        time.sleep(10)

    def test_060_new_vminstance_negative(self):
        unknown_flavor_id = str(uuid.uuid4())
        unknown_image_id = str(uuid.uuid4())
        name = 'eth2'

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        net_list = [{'use': self.__class__.net_type, 'name': name, 'floating_ip': False, 'port_security': True, 'type': 'virtual', 'net_id': self.__class__.network_id}]

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].new_vminstance(name='Test1_vm', image_id=unknown_image_id,
                                                                  flavor_id=unknown_flavor_id,
                                                                            net_list=net_list)
        self.assertEqual((context.exception).http_code, 404)

    def test_070_get_vminstance(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Get instance by its id
        vm_info = test_config["vim_conn"].get_vminstance(self.__class__.instance_id)

        if test_config['vimtype'] == 'vmware':
            for attr in vm_info:
                if attr == 'status':
                    self.assertEqual(vm_info[attr], 'ACTIVE')
                if attr == 'hostId':
                    self.assertEqual(type(vm_info[attr]), str)
                if attr == 'interfaces':
                    self.assertEqual(type(vm_info[attr]), list)
                    self.assertEqual(vm_info[attr][0]['IsConnected'], 'true')
                if attr == 'IsEnabled':
                    self.assertEqual(vm_info[attr], 'true')

    def test_080_get_vminstance_negative(self):
        unknown_instance_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].get_vminstance(unknown_instance_id)

        self.assertEqual((context.exception).http_code, 404)

    def test_090_refresh_vms_status(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1
        vm_list = []
        vm_list.append(self.__class__.instance_id)

        # refresh vm status
        vm_info = test_config["vim_conn"].refresh_vms_status(vm_list)
        for attr in vm_info[self.__class__.instance_id]:
            if attr == 'status':
                self.assertEqual(vm_info[self.__class__.instance_id][attr], 'ACTIVE')
            if attr == 'interfaces':
                self.assertEqual(type(vm_info[self.__class__.instance_id][attr]), list)

    def test_100_refresh_vms_status_negative(self):
        unknown_id = str(uuid.uuid4())

        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        vm_dict = test_config["vim_conn"].refresh_vms_status([unknown_id])
        self.assertEqual(vm_dict, {})

    def test_110_action_vminstance(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        action_list = ['shutdown','start','shutoff','rebuild','pause','resume']
        # various action on vminstace
        for action in action_list:
            instance_id = test_config["vim_conn"].action_vminstance(self.__class__.instance_id,
                                                                               { action: None})
            self.assertEqual(instance_id, self.__class__.instance_id)

    def test_120_action_vminstance_negative(self):
        non_exist_id = str(uuid.uuid4())
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        action = 'start'
        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].action_vminstance(non_exist_id, { action: None})

        self.assertEqual((context.exception).http_code, 400)

    def test_130_delete_vminstance(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Deleting created vm instance
        logger.info("Deleting created vm instance")
        test_config["vim_conn"].delete_vminstance(self.__class__.instance_id)
        time.sleep(10)

class test_vimconn_get_tenant_list(test_base):
    tenant_id = None

    def test_000_get_tenant_list(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Getting tenant list
        tenant_list = test_config["vim_conn"].get_tenant_list()

        for item in tenant_list:
            if test_config['tenant'] == item['name']:
                self.__class__.tenant_id = item['id']
                self.assertEqual(type(item['name']), str)
                self.assertEqual(type(item['id']), str)

    def test_010_get_tenant_list_by_id(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Getting filter tenant list by its id
        filter_tenant_list = test_config["vim_conn"].get_tenant_list({'id': self.__class__.tenant_id})

        for item in filter_tenant_list:
            self.assertEqual(type(item['id']), str)
            self.assertEqual(item['id'], self.__class__.tenant_id)

    def test_020_get_tenant_list_by_name(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Getting filter tenant list by its name
        filter_tenant_list = test_config["vim_conn"].get_tenant_list({'name': test_config['tenant']})

        for item in filter_tenant_list:
            self.assertEqual(type(item['name']), str)
            self.assertEqual(item['name'], test_config['tenant'])

    def test_030_get_tenant_list_by_name_and_id(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        # Getting filter tenant list by its name and id
        filter_tenant_list = test_config["vim_conn"].get_tenant_list({'name': test_config['tenant'],
                                                                    'id': self.__class__.tenant_id})

        for item in filter_tenant_list:
            self.assertEqual(type(item['name']), str)
            self.assertEqual(type(item['id']), str)
            self.assertEqual(item['name'], test_config['tenant'])
            self.assertEqual(item['id'], self.__class__.tenant_id)

    def test_040_get_tenant_list_negative(self):
        non_exist_tenant_name = "Tenant_123"
        non_exist_tenant_id = "kjhgrt456-45345kjhdfgnbdk-34dsfjdfg"
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        filter_tenant_list = test_config["vim_conn"].get_tenant_list({'name': non_exist_tenant_name,
                                                                         'id': non_exist_tenant_id})

        self.assertEqual(filter_tenant_list, [])

class test_vimconn_new_tenant(test_base):
    tenant_id = None

    def test_000_new_tenant(self):
        tenant_name = _get_random_string(20)
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        self.__class__.tenant_id = test_config["vim_conn"].new_tenant(tenant_name)
        time.sleep(15)

        self.assertEqual(type(self.__class__.tenant_id), str)

    def test_010_new_tenant_negative(self):
        Invalid_tenant_name = 10121
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].new_tenant(Invalid_tenant_name)

        self.assertEqual((context.exception).http_code, 400)

    def test_020_delete_tenant(self):
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        tenant_id = test_config["vim_conn"].delete_tenant(self.__class__.tenant_id)
        self.assertEqual(type(tenant_id), str)

    def test_030_delete_tenant_negative(self):
        Non_exist_tenant_name = 'Test_30_tenant'
        self.__class__.test_text = "{}.{}. TEST {}".format(test_config["test_number"],
                                                            self.__class__.test_index,
                                                inspect.currentframe().f_code.co_name)
        self.__class__.test_index += 1

        with self.assertRaises(Exception) as context:
            test_config["vim_conn"].delete_tenant(Non_exist_tenant_name)

        self.assertEqual((context.exception).http_code, 404)


'''
IMPORTANT NOTE
The following unittest class does not have the 'test_' on purpose. This test is the one used for the
scenario based tests.
'''
class descriptor_based_scenario_test(test_base):
    test_index = 0
    scenario_test_path = None

    @classmethod
    def setUpClass(cls):
        cls.test_index = 1
        cls.to_delete_list = []
        cls.scenario_uuids = []
        cls.instance_scenario_uuids = []
        cls.scenario_test_path = test_config["test_directory"] + '/' + test_config["test_folder"]
        logger.info("{}. {} {}".format(test_config["test_number"], cls.__name__, test_config["test_folder"]))

    @classmethod
    def tearDownClass(cls):
         test_config["test_number"] += 1

    def test_000_load_scenario(self):
        self.__class__.test_text = "{}.{}. TEST {} {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name,
                                                           test_config["test_folder"])
        self.__class__.test_index += 1
        # load VNFD and NSD
        descriptor_files = glob.glob(self.__class__.scenario_test_path+'/*.yaml')
        vnf_descriptors = []
        scenario_descriptors = []
        for descriptor_file in descriptor_files:
            with open(descriptor_file, 'r') as stream:
                descriptor = yaml.load(stream)
                if "vnf" in descriptor or "vnfd:vnfd-catalog" in descriptor or "vnfd-catalog" in descriptor:
                    vnf_descriptors.append(descriptor)
                else:
                    scenario_descriptors.append(descriptor)

        scenario_file = glob.glob(self.__class__.scenario_test_path + '/scenario_*.yaml')
        if not vnf_descriptors or not scenario_descriptors or len(scenario_descriptors) > 1:
            raise Exception("Test '{}' not valid. It must contain an scenario file and at least one vnfd file'".format(
                test_config["test_folder"]))

        # load all vnfd
        for vnf_descriptor in vnf_descriptors:
            logger.debug("VNF descriptor: {}".format(vnf_descriptor))
            vnf = test_config["client"].create_vnf(descriptor=vnf_descriptor, image_name=test_config["image_name"])
            logger.debug(vnf)
            if 'vnf' in vnf:
                vnf_uuid = vnf['vnf']['uuid']
            else:
                vnf_uuid = vnf['vnfd'][0]['uuid']
            self.__class__.to_delete_list.insert(0, {"item": "vnf", "function": test_config["client"].delete_vnf,
                                                     "params": {"uuid": vnf_uuid}})

        # load the scenario definition
        for scenario_descriptor in scenario_descriptors:
            # networks = scenario_descriptor['scenario']['networks']
            # networks[test_config["mgmt_net"]] = networks.pop('mgmt')
            logger.debug("Scenario descriptor: {}".format(scenario_descriptor))
            scenario = test_config["client"].create_scenario(descriptor=scenario_descriptor)
            logger.debug(scenario)
            if 'scenario' in scenario:
                scenario_uuid = scenario['scenario']['uuid']
            else:
                scenario_uuid = scenario['nsd'][0]['uuid']
            self.__class__.to_delete_list.insert(0, {"item": "scenario",
                                                     "function": test_config["client"].delete_scenario,
                                                     "params": {"uuid": scenario_uuid}})
            self.__class__.scenario_uuids.append(scenario_uuid)

    def test_010_instantiate_scenario(self):
        self.__class__.test_text = "{}.{}. TEST {} {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name,
                                                           test_config["test_folder"])
        self.__class__.test_index += 1
        for scenario_uuid in self.__class__.scenario_uuids:
            instance_descriptor = {
                "instance":{
                    "name": self.__class__.test_text,
                    "scenario": scenario_uuid,
                    "networks":{
                        "mgmt": {"sites": [ { "netmap-use": test_config["mgmt_net"]} ]}
                    }
                }
            }
            instance = test_config["client"].create_instance(instance_descriptor)
            self.__class__.instance_scenario_uuids.append(instance['uuid'])
            logger.debug(instance)
            self.__class__.to_delete_list.insert(0, {"item": "instance",
                                                     "function": test_config["client"].delete_instance,
                                                     "params": {"uuid": instance['uuid']}})

    def test_020_check_deployent(self):
        self.__class__.test_text = "{}.{}. TEST {} {}".format(test_config["test_number"], self.__class__.test_index,
                                                           inspect.currentframe().f_code.co_name,
                                                           test_config["test_folder"])
        self.__class__.test_index += 1

        if test_config["manual"]:
            raw_input('Scenario has been deployed. Perform manual check and press any key to resume')
            return

        keep_waiting = test_config["timeout"]
        pending_instance_scenario_uuids = list(self.__class__.instance_scenario_uuids)   # make a copy
        while pending_instance_scenario_uuids:
            index = 0
            while index < len(pending_instance_scenario_uuids):
                result = check_instance_scenario_active(pending_instance_scenario_uuids[index])
                if result[0]:
                    del pending_instance_scenario_uuids[index]
                    break
                elif 'ERROR' in result[1]:
                    msg = 'Got error while waiting for the instance to get active: '+result[1]
                    logging.error(msg)
                    raise Exception(msg)
                index += 1

            if keep_waiting >= 5:
                time.sleep(5)
                keep_waiting -= 5
            elif keep_waiting > 0:
                time.sleep(keep_waiting)
                keep_waiting = 0
            else:
                msg = 'Timeout reached while waiting instance scenario to get active'
                logging.error(msg)
                raise Exception(msg)

    def test_030_clean_deployment(self):
        self.__class__.test_text = "{}.{}. TEST {} {}".format(test_config["test_number"], self.__class__.test_index,
                                                              inspect.currentframe().f_code.co_name,
                                                              test_config["test_folder"])
        self.__class__.test_index += 1
        #At the moment if you delete an scenario right after creating it, in openstack datacenters
        #sometimes scenario ports get orphaned. This sleep is just a dirty workaround
        time.sleep(5)
        for item in self.__class__.to_delete_list:
            response = item["function"](**item["params"])
            logger.debug(response)


def _get_random_string(maxLength):
    '''generates a string with random characters string.letters and string.digits
    with a random length up to maxLength characters. If maxLength is <15 it will be changed automatically to 15
    '''
    prefix = 'testing_'
    min_string = 15
    minLength = min_string - len(prefix)
    if maxLength < min_string: maxLength = min_string
    maxLength -= len(prefix)
    length = random.randint(minLength,maxLength)
    return 'testing_'+"".join([random.choice(string.letters+string.digits) for i in xrange(length)])


def test_vimconnector(args):
    global test_config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/osm_ro")
    test_config['vimtype'] = args.vimtype
    if args.vimtype == "vmware":
        import vimconn_vmware as vim

        test_config["test_directory"] = os.path.dirname(__file__) + "/RO_tests"

        tenant_name = args.tenant_name
        test_config['tenant'] = tenant_name
        config_params = json.loads(args.config_param)
        org_name = config_params.get('orgname')
        org_user = config_params.get('user')
        org_passwd = config_params.get('passwd')
        vim_url = args.endpoint_url
        test_config['image_path'] = args.image_path
        test_config['image_name'] = args.image_name

        # vmware connector obj
        test_config['vim_conn'] = vim.vimconnector(name=org_name, tenant_name=tenant_name, user=org_user,passwd=org_passwd, url=vim_url, config=config_params)

    elif args.vimtype == "aws":
        import vimconn_aws as vim
    elif args.vimtype == "openstack":
        import vimconn_openstack as vim
    elif args.vimtype == "openvim":
        import vimconn_openvim as vim
    else:
        logger.critical("vimtype '{}' not supported".format(args.vimtype))
        sys.exit(1)
    executed = 0
    failed = 0
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    # If only want to obtain a tests list print it and exit
    if args.list_tests:
        tests_names = []
        for cls in clsmembers:
            if cls[0].startswith('test_vimconnector'):
                tests_names.append(cls[0])

        msg = "The 'vim' set tests are:\n\t" + ', '.join(sorted(tests_names))
        print(msg)
        logger.info(msg)
        sys.exit(0)

    # Create the list of tests to be run
    code_based_tests = []
    if args.tests:
        for test in args.tests:
            for t in test.split(','):
                matches_code_based_tests = [item for item in clsmembers if item[0] == t]
                if len(matches_code_based_tests) > 0:
                    code_based_tests.append(matches_code_based_tests[0][1])
                else:
                    logger.critical("Test '{}' is not among the possible ones".format(t))
                    sys.exit(1)
    if not code_based_tests:
        # include all tests
        for cls in clsmembers:
            # We exclude 'test_VIM_tenant_operations' unless it is specifically requested by the user
            if cls[0].startswith('test_vimconnector'):
                code_based_tests.append(cls[1])

    logger.debug("tests to be executed: {}".format(code_based_tests))

    # TextTestRunner stream is set to /dev/null in order to avoid the method to directly print the result of tests.
    # This is handled in the tests using logging.
    stream = open('/dev/null', 'w')

    # Run code based tests
    basic_tests_suite = unittest.TestSuite()
    for test in code_based_tests:
        basic_tests_suite.addTest(unittest.makeSuite(test))
    result = unittest.TextTestRunner(stream=stream, failfast=failfast).run(basic_tests_suite)
    executed += result.testsRun
    failed += len(result.failures) + len(result.errors)
    if failfast and failed:
        sys.exit(1)
    if len(result.failures) > 0:
        logger.debug("failures : {}".format(result.failures))
    if len(result.errors) > 0:
        logger.debug("errors : {}".format(result.errors))
    return executed, failed


def test_vim(args):
    global test_config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/osm_ro")
    import openmanoclient
    executed = 0
    failed = 0
    test_config["client"] = openmanoclient.openmanoclient(
        endpoint_url=args.endpoint_url,
        tenant_name=args.tenant_name,
        datacenter_name=args.datacenter,
        debug=args.debug, logger=test_config["logger_name"])
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    # If only want to obtain a tests list print it and exit
    if args.list_tests:
        tests_names = []
        for cls in clsmembers:
            if cls[0].startswith('test_VIM'):
                tests_names.append(cls[0])

        msg = "The 'vim' set tests are:\n\t" + ', '.join(sorted(tests_names)) +\
              "\nNOTE: The test test_VIM_tenant_operations will fail in case the used datacenter is type OpenStack " \
              "unless RO has access to the admin endpoint. Therefore this test is excluded by default"
        print(msg)
        logger.info(msg)
        sys.exit(0)

    # Create the list of tests to be run
    code_based_tests = []
    if args.tests:
        for test in args.tests:
            for t in test.split(','):
                matches_code_based_tests = [item for item in clsmembers if item[0] == t]
                if len(matches_code_based_tests) > 0:
                    code_based_tests.append(matches_code_based_tests[0][1])
                else:
                    logger.critical("Test '{}' is not among the possible ones".format(t))
                    sys.exit(1)
    if not code_based_tests:
        # include all tests
        for cls in clsmembers:
            # We exclude 'test_VIM_tenant_operations' unless it is specifically requested by the user
            if cls[0].startswith('test_VIM') and cls[0] != 'test_VIM_tenant_operations':
                code_based_tests.append(cls[1])

    logger.debug("tests to be executed: {}".format(code_based_tests))

    # TextTestRunner stream is set to /dev/null in order to avoid the method to directly print the result of tests.
    # This is handled in the tests using logging.
    stream = open('/dev/null', 'w')

    # Run code based tests
    basic_tests_suite = unittest.TestSuite()
    for test in code_based_tests:
        basic_tests_suite.addTest(unittest.makeSuite(test))
    result = unittest.TextTestRunner(stream=stream, failfast=failfast).run(basic_tests_suite)
    executed += result.testsRun
    failed += len(result.failures) + len(result.errors)
    if failfast and failed:
        sys.exit(1)
    if len(result.failures) > 0:
        logger.debug("failures : {}".format(result.failures))
    if len(result.errors) > 0:
        logger.debug("errors : {}".format(result.errors))
    return executed, failed


def test_deploy(args):
    global test_config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/osm_ro")
    import openmanoclient
    executed = 0
    failed = 0
    test_config["test_directory"] = os.path.dirname(__file__) + "/RO_tests"
    test_config["image_name"] = args.image_name
    test_config["mgmt_net"] = args.mgmt_net
    test_config["manual"] = args.manual
    test_directory_content = os.listdir(test_config["test_directory"])
    # If only want to obtain a tests list print it and exit
    if args.list_tests:
        msg = "the 'deploy' set tests are:\n\t" + ', '.join(sorted(test_directory_content))
        print(msg)
        # logger.info(msg)
        sys.exit(0)

    descriptor_based_tests = []
    # Create the list of tests to be run
    code_based_tests = []
    if args.tests:
        for test in args.tests:
            for t in test.split(','):
                if t in test_directory_content:
                    descriptor_based_tests.append(t)
                else:
                    logger.critical("Test '{}' is not among the possible ones".format(t))
                    sys.exit(1)
    if not descriptor_based_tests:
        # include all tests
        descriptor_based_tests = test_directory_content

    logger.debug("tests to be executed: {}".format(code_based_tests))

    # import openmanoclient from relative path
    test_config["client"] = openmanoclient.openmanoclient(
        endpoint_url=args.endpoint_url,
        tenant_name=args.tenant_name,
        datacenter_name=args.datacenter,
        debug=args.debug, logger=test_config["logger_name"])

    # TextTestRunner stream is set to /dev/null in order to avoid the method to directly print the result of tests.
    # This is handled in the tests using logging.
    stream = open('/dev/null', 'w')
    # This scenario based tests are defined as directories inside the directory defined in 'test_directory'
    for test in descriptor_based_tests:
        test_config["test_folder"] = test
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(descriptor_based_scenario_test))
        result = unittest.TextTestRunner(stream=stream, failfast=False).run(test_suite)
        executed += result.testsRun
        failed += len(result.failures) + len(result.errors)
        if failfast and failed:
            sys.exit(1)
        if len(result.failures) > 0:
            logger.debug("failures : {}".format(result.failures))
        if len(result.errors) > 0:
            logger.debug("errors : {}".format(result.errors))

    return executed, failed

if __name__=="__main__":

    parser = ArgumentParser(description='Test RO module')
    parser.add_argument('-v','--version', action='version', help="Show current version",
                             version='%(prog)s version ' + __version__  + ' ' + version_date)

    # Common parameters
    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument('--failfast', help='Stop when a test fails rather than execute all tests',
                      dest='failfast', action="store_true", default=False)
    parent_parser.add_argument('--failed', help='Set logs to show only failed tests. --debug disables this option',
                      dest='failed', action="store_true", default=False)
    default_logger_file = os.path.dirname(__file__)+'/'+os.path.splitext(os.path.basename(__file__))[0]+'.log'
    parent_parser.add_argument('--list-tests', help='List all available tests', dest='list_tests', action="store_true",
                      default=False)
    parent_parser.add_argument('--logger_file', dest='logger_file', default=default_logger_file,
                               help='Set the logger file. By default '+default_logger_file)
    parent_parser.add_argument("-t", '--tenant', dest='tenant_name', default="osm",
                               help="Set the openmano tenant to use for the test. By default 'osm'")
    parent_parser.add_argument('--debug', help='Set logs to debug level', dest='debug', action="store_true")
    parent_parser.add_argument('--timeout', help='Specify the instantiation timeout in seconds. By default 300',
                          dest='timeout', type=int, default=300)
    parent_parser.add_argument('--test', '--tests', help='Specify the tests to run', dest='tests', action="append")

    subparsers = parser.add_subparsers(help='test sets')

    # Deployment test set
    # -------------------
    deploy_parser = subparsers.add_parser('deploy', parents=[parent_parser],
                                          help="test deployment using descriptors at RO_test folder ")
    deploy_parser.set_defaults(func=test_deploy)

    # Mandatory arguments
    mandatory_arguments = deploy_parser.add_argument_group('mandatory arguments')
    mandatory_arguments.add_argument('-d', '--datacenter', required=True, help='Set the datacenter to test')
    mandatory_arguments.add_argument("-i", '--image-name', required=True, dest="image_name",
                                     help='Image name available at datacenter used for the tests')
    mandatory_arguments.add_argument("-n", '--mgmt-net-name', required=True, dest='mgmt_net',
                                     help='Set the vim management network to use for tests')

    # Optional arguments
    deploy_parser.add_argument('-m', '--manual-check', dest='manual', action="store_true", default=False,
                               help='Pause execution once deployed to allow manual checking of the '
                                    'deployed instance scenario')
    deploy_parser.add_argument('-u', '--url', dest='endpoint_url', default='http://localhost:9090/openmano',
                               help="Set the openmano server url. By default 'http://localhost:9090/openmano'")

    # Vimconn test set
    # -------------------
    vimconn_parser = subparsers.add_parser('vimconn', parents=[parent_parser], help="test vimconnector plugin")
    vimconn_parser.set_defaults(func=test_vimconnector)
    # Mandatory arguments
    mandatory_arguments = vimconn_parser.add_argument_group('mandatory arguments')
    mandatory_arguments.add_argument('--vimtype', choices=['vmware', 'aws', 'openstack', 'openvim'], required=True,
                                     help='Set the vimconnector type to test')
    mandatory_arguments.add_argument('-c', '--config', dest='config_param', required=True,
                                    help='Set the vimconnector specific config parameters in dictionary format')
    mandatory_arguments.add_argument('-u', '--url', dest='endpoint_url',required=True, help="Set the vim connector url or Host IP")
    # Optional arguments
    vimconn_parser.add_argument('-i', '--image-path', dest='image_path', help="Provide image path present at RO container")
    vimconn_parser.add_argument('-n', '--image-name', dest='image_name', help="Provide image name for test")
    # TODO add optional arguments for vimconn tests
    # vimconn_parser.add_argument("-i", '--image-name', dest='image_name', help='<HELP>'))

    # Datacenter test set
    # -------------------
    vimconn_parser = subparsers.add_parser('vim', parents=[parent_parser], help="test vim")
    vimconn_parser.set_defaults(func=test_vim)

    # Mandatory arguments
    mandatory_arguments = vimconn_parser.add_argument_group('mandatory arguments')
    mandatory_arguments.add_argument('-d', '--datacenter', required=True, help='Set the datacenter to test')

    # Optional arguments
    vimconn_parser.add_argument('-u', '--url', dest='endpoint_url', default='http://localhost:9090/openmano',
                               help="Set the openmano server url. By default 'http://localhost:9090/openmano'")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    # print str(args)
    test_config = {}

    # default logger level is INFO. Options --debug and --failed override this, being --debug prioritary
    logger_level = 'INFO'
    if args.debug:
        logger_level = 'DEBUG'
    elif args.failed:
        logger_level = 'WARNING'
    logger_name = os.path.basename(__file__)
    test_config["logger_name"] = logger_name
    logger = logging.getLogger(logger_name)
    logger.setLevel(logger_level)
    failfast = args.failfast

    # Configure a logging handler to store in a logging file
    if args.logger_file:
        fileHandler = logging.FileHandler(args.logger_file)
        formatter_fileHandler = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        fileHandler.setFormatter(formatter_fileHandler)
        logger.addHandler(fileHandler)

    # Configure a handler to print to stdout
    consoleHandler = logging.StreamHandler(sys.stdout)
    formatter_consoleHandler = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    consoleHandler.setFormatter(formatter_consoleHandler)
    logger.addHandler(consoleHandler)

    logger.debug('Program started with the following arguments: ' + str(args))

    # set test config parameters
    test_config["timeout"] = args.timeout
    test_config["test_number"] = 1

    executed, failed = args.func(args)

    # Log summary
    logger.warning("Total number of tests: {}; Total number of failures/errors: {}".format(executed, failed))
    sys.exit(1 if failed else 0)
