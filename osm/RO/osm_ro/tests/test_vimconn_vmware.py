# -*- coding: utf-8 -*-

##
# Copyright 2016-2017 VMware Inc.
# This file is part of ETSI OSM
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
# For those usages not covered by the Apache License, Version 2.0 please
# contact:  osslegalrouting@vmware.com
##


from osm_ro.vimconn_vmware import vimconnector
from osm_ro.vimconn import vimconnUnexpectedResponse,vimconnNotFoundException
from pyvcloud.vcloudair import VCA,VCS
from pyvcloud.vapp import VAPP
from pyvcloud import Http
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import vdcType,networkType,catalogType, \
                                                    vAppType,taskType
import unittest
import mock
import test_vimconn_vmware_xml_response as xml_resp

class TestVimconn_VMware(unittest.TestCase):
    def setUp(self):
        config = { "admin_password": "admin",
                  "admin_username":"user",
                  "nsx_user": "nsx",
                  "nsx_password": "nsx",
                  "nsx_manager":"https://test-nsx" }

        self.vca = VCA(host='test',
                       username='user',
                       service_type='standalone',
                       version='5.9',
                       verify=False,
                       log=False)

        self.session = VCS('https://test/api/session',
                                               'test',
                                               'test',
                                                 None,
                          'https://test/api/org/a93c',
                          'https://test/api/org/a93c',
                                        version='5.9')

        self.vim = vimconnector(uuid='12354',
                                 name='test',
                         tenant_id='abc1234',
                          tenant_name='test',
                          url='https://test',
                               config=config)


    @mock.patch.object(vimconnector,'get_vdc_details')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(VCA,'get_networks')
    def test_get_network_not_found(self,get_networks, connect, get_vdc_details):
        vdc_xml_resp = xml_resp.vdc_xml_response
        # created vdc object
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        self.vim.vca = self.vim.connect()
        network_xml_resp = xml_resp.network_xml_response
        networks = networkType.parseString(network_xml_resp, True)
        (self.vim.vca).get_networks.return_value = [networks]
        # call to VIM connector method with invalid id
        self.assertRaises(vimconnNotFoundException,self.vim.get_network,'mgmt-net')
 
    @mock.patch.object(vimconnector,'get_vdc_details')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(VCA,'get_networks')
    def test_get_network(self,get_networks, connect, get_vdc_details):
        net_id = '5c04dc6d-6096-47c6-b72b-68f19013d491'
        vdc_xml_resp = xml_resp.vdc_xml_response
        # created vdc object
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # created network object
        network_xml_resp = xml_resp.network_xml_response
        networks = networkType.parseString(network_xml_resp, True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        self.vim.vca = self.vim.connect()
        # assumed return value from VIM connector
        (self.vim.vca).get_networks.return_value = [networks]
        # call to VIM connector method with network_id
        result = self.vim.get_network(net_id)
        # assert verified expected and return result from VIM connector
        self.assertEqual(net_id, result['id'])

    @mock.patch.object(vimconnector,'get_vdc_details')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(VCA,'get_networks')
    def test_get_network_list_not_found(self,get_networks, connect, get_vdc_details):
        vdc_xml_resp = xml_resp.vdc_xml_response
        # created vdc object
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        self.vim.vca = self.vim.connect()

        network_xml_resp = xml_resp.network_xml_response
        networks = networkType.parseString(network_xml_resp, True)
        (self.vim.vca).get_networks.return_value = [networks]
        # call to VIM connector method with network_id
        result = self.vim.get_network_list({'id':'45hdfg-345nb-345'})

        # assert verified expected and return result from VIM connector
        self.assertEqual(list(), result)

    @mock.patch.object(vimconnector,'get_vdc_details')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(VCA,'get_networks')
    def test_get_network_list(self,get_networks, connect, get_vdc_details):
        vdc_xml_resp = xml_resp.vdc_xml_response
        net_id = '5c04dc6d-6096-47c6-b72b-68f19013d491'
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # created network object
        network_xml_resp = xml_resp.network_xml_response
        networks = networkType.parseString(network_xml_resp, True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        self.vim.vca = self.vim.connect()
        # assumed return value from VIM connector
        (self.vim.vca).get_networks.return_value = [networks]

        # call to VIM connector method with network_id
        result = self.vim.get_network_list({'id': net_id})
        # assert verified expected and return result from VIM connector
        for item in result:
            self.assertEqual(item.get('id'), net_id)
            self.assertEqual(item.get('status'), 'ACTIVE')
            self.assertEqual(item.get('shared'), False)

    @mock.patch.object(vimconnector,'create_network_rest')
    def test_new_network(self, create_network_rest):
        create_net_xml_resp = xml_resp.create_network_xml_response
        net_name = 'Test_network'
        net_type = 'bridge'
        # assumed return value from VIM connector
        create_network_rest.return_value = create_net_xml_resp
        # call to VIM connector method with network_id
        result = self.vim.new_network(net_name, net_type)
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, 'df1956fa-da04-419e-a6a2-427b6f83788f')

    @mock.patch.object(vimconnector, 'create_network_rest')
    def test_new_network_not_created(self, create_network_rest):
        # assumed return value from VIM connector
        create_network_rest.return_value = """<?xml version="1.0" encoding="UTF-8"?>
                                              <OrgVdcNetwork></OrgVdcNetwork>"""

        # assert verified expected and return result from VIM connector
        self.assertRaises(vimconnUnexpectedResponse,self.vim.new_network,
                                                              'test_net',
                                                                'bridge')

    @mock.patch.object(vimconnector, 'connect')
    @mock.patch.object(vimconnector, 'get_network_action')
    @mock.patch.object(vimconnector, 'connect_as_admin')
    @mock.patch.object(vimconnector, 'delete_network_action')
    def test_delete_network(self, delete_network_action, connect_as_admin, get_network_action, connect):
        delete_net_xml_resp = xml_resp.delete_network_xml_response
        # assumed return value from VIM connector
        connect.return_value = self.vca
        self.vim.vca = self.vim.connect()
        get_network_action.return_value = delete_net_xml_resp
        connect_as_admin.return_value = self.vca
        delete_network_action.return_value = True
        # call to VIM connector method with network_id
        result = self.vim.delete_network('0a55e5d1-43a2-4688-bc92-cb304046bf87')
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, '0a55e5d1-43a2-4688-bc92-cb304046bf87')

    @mock.patch.object(vimconnector, 'get_vcd_network')
    def test_delete_network_not_found(self, get_vcd_network):
        # assumed return value from VIM connector
        get_vcd_network.return_value = False
        # assert verified expected and return result from VIM connector
        self.assertRaises(vimconnNotFoundException,self.vim.delete_network,
                                    '2a23e5d1-42a2-0648-bc92-cb508046bf87')

    def test_get_flavor(self):
        flavor_data = {'a646eb8a-95bd-4e81-8321-5413ee72b62e': {'disk': 10,
                                                                'vcpus': 1,
                                                               'ram': 1024}}
        vimconnector.flavorlist = flavor_data
        result = self.vim.get_flavor('a646eb8a-95bd-4e81-8321-5413ee72b62e')
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, flavor_data['a646eb8a-95bd-4e81-8321-5413ee72b62e'])

    def test_get_flavor_not_found(self):
        vimconnector.flavorlist = {}
        # assert verified expected and return result from VIM connector
        self.assertRaises(vimconnNotFoundException,self.vim.get_flavor,
                                'a646eb8a-95bd-4e81-8321-5413ee72b62e')

    def test_new_flavor(self):
        flavor_data = {'disk': 10, 'vcpus': 1, 'ram': 1024}
        result = self.vim.new_flavor(flavor_data)
        # assert verified expected and return result from VIM connector
        self.assertIsNotNone(result)

    def test_delete_flavor(self):
        flavor_data = {'2cb3dffb-5c51-4355-8406-28553ead28ac': {'disk': 10,
                                                                'vcpus': 1,
                                                               'ram': 1024}}
        vimconnector.flavorlist = flavor_data
        # return value from VIM connector
        result = self.vim.delete_flavor('2cb3dffb-5c51-4355-8406-28553ead28ac')
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, '2cb3dffb-5c51-4355-8406-28553ead28ac')

    @mock.patch.object(vimconnector,'connect_as_admin')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(Http,'get')
    @mock.patch.object(VCS,'get_vcloud_headers')
    def test_delete_image_not_found(self, get_vcloud_headers, get, connect, connect_as_admin):
        # assumed return value from VIM connector
        connect.return_value = self.vca
        self.vim.vca = self.vim.connect()
        # assumed return value from VIM connector
        connect_as_admin.return_value = self.vca
        self.vca.host = connect_as_admin.return_value.host
        self.vca.vcloud_session = self.session
        get_vcloud_headers.return_value = {'Accept':'application/*+xml;version=5.9',
                       'x-vcloud-authorization': '638bfee6cb5f435abc3480f480817254'}
        get_vcloud_headers.return_value = self.vca.vcloud_session.get_vcloud_headers()
        # assert verified expected and return result from VIM connector
        self.assertRaises(vimconnNotFoundException, self.vim.delete_image, 'invali3453')

    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(VCA,'get_catalogs')
    def test_get_image_list(self, get_catalogs, connect):
        catalog1 = xml_resp.catalog1_xml_response
        catalog2 = xml_resp.catalog2_xml_response

        catalogs = [catalogType.parseString(cat, True) for cat in catalog1, catalog2]
        connect.return_value = self.vca
        self.vim.vca = self.vim.connect()
        # assumed return value from VIM connector
        self.vim.vca.get_catalogs.return_value = catalogs
        result = self.vim.get_image_list({'id': '32ccb082-4a65-41f6-bcd6-38942e8a3829'})
        # assert verified expected and return result from VIM connector
        for item in result:
            self.assertEqual(item['id'], '32ccb082-4a65-41f6-bcd6-38942e8a3829')

    @mock.patch.object(vimconnector,'get_vapp_details_rest')
    @mock.patch.object(vimconnector,'get_vdc_details')
    def test_get_vminstance(self, get_vdc_details, get_vapp_details_rest):
        vapp_info = {'status': '4',
                   'acquireMksTicket': {'href': 'https://localhost/api/vApp/vm-47d12505-5968-4e16-95a7-18743edb0c8b/screen/action/acquireMksTicket',
                   'type': 'application/vnd.vmware.vcloud.mksTicket+xml', 'rel': 'screen:acquireMksTicket'},
                   'vm_virtual_hardware': {'disk_edit_href': 'https://localhost/api/vApp/vm-47d12505-5968-4e16-95a7-18743edb0c8b/virtualHardwareSection/disks', 'disk_size': '40960'},
                   'name': 'Test1_vm-69a18104-8413-4cb8-bad7-b5afaec6f9fa',
                   'created': '2017-09-21T01:15:31.627-07:00',
                    'IsEnabled': 'true',
                   'EndAddress': '12.16.24.199',
                   'interfaces': [{'MACAddress': '00:50:56:01:12:a2',
                                   'NetworkConnectionIndex': '0',
                                   'network': 'testing_T6nODiW4-68f68d93-0350-4d86-b40b-6e74dedf994d',
                                   'IpAddressAllocationMode': 'DHCP',
                                   'IsConnected': 'true',
                                   'IpAddress': '12.16.24.200'}],
                   'ovfDescriptorUploaded': 'true',
                   'nestedHypervisorEnabled': 'false',
                   'Gateway': '12.16.24.1',
                   'acquireTicket': {'href': 'https://localhost/api/vApp/vm-47d12505-5968-4e16-95a7-18743edb0c8b/screen/action/acquireTicket',
                   'rel': 'screen:acquireTicket'},
                   'vmuuid': '47d12505-5968-4e16-95a7-18743edb0c8b',
                   'Netmask': '255.255.255.0',
                   'StartAddress': '12.16.24.100',
                   'primarynetwork': '0',
                   'networkname': 'External-Network-1074',
                   'IsInherited': 'false',
                   'deployed': 'true'} 
        # created vdc object
        vdc_xml_resp = xml_resp.vdc_xml_response
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        get_vapp_details_rest.return_value = vapp_info

        result = self.vim.get_vminstance('47d12505-5968-4e16-95a7-18743edb0c8b')
        # assert verified expected and return result from VIM connector
        self.assertEqual(result['status'], 'ACTIVE')
        self.assertEqual(result['hostId'], '47d12505-5968-4e16-95a7-18743edb0c8b')

    @mock.patch.object(VCA,'get_vapp')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(vimconnector,'get_namebyvappid')
    @mock.patch.object(vimconnector,'get_vdc_details')
    def test_delete_vminstance(self, get_vdc_details, get_namebyvappid, connect, vapp):
        vm_id = '4f6a9b49-e92d-4935-87a1-0e4dc9c3a069'
        vm_name = 'Test1_vm-69a18104-8413-4cb8-bad7-b5afaec6f9fa'
        # created vdc object
        vdc_xml_resp = xml_resp.vdc_xml_response
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        connect.return_value = self.vca
        self.vim.vca = self.vim.connect()
        get_namebyvappid.return_name = vm_name
        vapp.return_value = None
        # call to VIM connector method
        result = self.vim.delete_vminstance(vm_id)
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, vm_id)

    @mock.patch.object(vimconnector,'get_network_id_by_name')
    @mock.patch.object(vimconnector,'get_vm_pci_details')
    @mock.patch.object(VCA,'get_vapp')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(vimconnector,'get_namebyvappid')
    @mock.patch.object(vimconnector,'get_vdc_details')
    def test_refresh_vms_status(self, get_vdc_details, get_namebyvappid, connect,
                                                    get_vapp, get_vm_pci_details,
                                                         get_network_id_by_name):
        headers = {'Accept':'application/*+xml;version=5.9',
                       'x-vcloud-authorization': '638bfee6cb5f435abc3480f480817254'}
        vm_id = '05e6047b-6938-4275-8940-22d1ea7245b8'

        vapp_resp = xml_resp.vapp_xml_response
        # created vdc object
        vdc_xml_resp = xml_resp.vdc_xml_response
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        connect.return_value = self.vca

        self.vim.vca = self.vim.connect()
        get_namebyvappid.return_value = 'Test1_vm-69a18104-8413-4cb8-bad7-b5afaec6f9fa'
        get_vm_pci_details.return_value = {'host_name': 'test-esx-1.corp.local', 'host_ip': '12.19.24.31'}
        get_vapp.return_value = VAPP(vAppType.parseString(vapp_resp, True), headers, False)
        get_network_id_by_name.return_value = '47d12505-5968-4e16-95a7-18743edb0c8b'
        # call to VIM connector method
        result = self.vim.refresh_vms_status([vm_id])
        for attr in result[vm_id]:
            if attr == 'status':
                # assert verified expected and return result from VIM connector
                self.assertEqual(result[vm_id][attr], 'ACTIVE')

    @mock.patch.object(vimconnector,'get_vcd_network')
    def test_refresh_nets_status(self, get_vcd_network):
        net_id = 'c2d0f28f-d38b-4588-aecc-88af3d4af58b'
        network_dict = {'status': '1','isShared': 'false','IpScope': '',
                        'EndAddress':'12.19.21.15',
                        'name': 'testing_gwyRXlvWYL1-9ebb6d7b-5c74-472f-be77-963ed050d44d',
                        'Dns1': '12.19.21.10', 'IpRanges': '',
                        'Gateway': '12.19.21.23', 'Netmask': '255.255.255.0',
                        'RetainNetInfoAcrossDeployments': 'false',
                        'IpScopes': '', 'IsEnabled': 'true', 'DnsSuffix': 'corp.local',
                        'StartAddress': '12.19.21.11', 'IpRange': '',
                        'Configuration': '', 'FenceMode': 'bridged',
                        'IsInherited': 'true', 'uuid': 'c2d0f28f-d38b-4588-aecc-88af3d4af58b'}
        # assumed return value from VIM connector
        get_vcd_network.return_value = network_dict
        result = self.vim.refresh_nets_status([net_id])
        # assert verified expected and return result from VIM connector
        for attr in result[net_id]:
            if attr == 'status':
                self.assertEqual(result[net_id][attr], 'ACTIVE')

    @mock.patch.object(VCA,'block_until_completed')
    @mock.patch.object(VCA,'get_vapp')
    @mock.patch.object(vimconnector,'connect')
    @mock.patch.object(vimconnector,'get_namebyvappid')
    @mock.patch.object(vimconnector,'get_vdc_details')
    def test_action_vminstance(self, get_vdc_details, get_namebyvappid, connect, get_vapp, block):
        task_resp = xml_resp.task_xml
        vm_id = '05e6047b-6938-4275-8940-22d1ea7245b8'
        # created vdc object
        vdc_xml_resp = xml_resp.vdc_xml_response
        vdc = vdcType.parseString(vdc_xml_resp,True)
        # assumed return value from VIM connector
        get_vdc_details.return_value = vdc
        get_namebyvappid.return_value = 'Test1_vm-69a18104-8413-4cb8-bad7-b5afaec6f9fa'
        connect.return_value = self.vca
        self.vim.vca = self.vim.connect()
        get_vapp.return_value.undeploy.return_value = taskType.parseString(task_resp, True)
        block.return_value = True
        # call to VIM connector method
        result = self.vim.action_vminstance(vm_id,{'shutdown': None})
        # assert verified expected and return result from VIM connector
        self.assertEqual(result, None)
