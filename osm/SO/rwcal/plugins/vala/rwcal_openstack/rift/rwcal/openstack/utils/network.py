#!/usr/bin/python

#
#   Copyright 2017 RIFT.IO Inc
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
import gi
gi.require_version('RwcalYang', '1.0')
from gi.repository import RwcalYang
import neutronclient.common.exceptions as NeutronException


class NetworkUtils(object):
    """
    Utility class for network operations
    """
    def __init__(self, driver):
        """
        Constructor for class
        Arguments:
          driver: object of OpenstackDriver()
        """
        self._driver = driver
        self.log = driver.log

    @property
    def driver(self):
        return self._driver

    def _parse_cp(self, cp_info):
        """
        Parse the port_info dictionary returned by neutronclient
        Arguments:
          cp_info: A dictionary object representing port attributes

        Returns:
          Protobuf GI oject of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList_ConnectionPoints()
        """
        cp = RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList_ConnectionPoints()
        if 'name' in cp_info and cp_info['name']:
            cp.name = cp_info['name']

        if 'id' in cp_info and cp_info['id']:
            cp.connection_point_id = cp_info['id']

        if ('fixed_ips' in cp_info) and (len(cp_info['fixed_ips']) >= 1):
            if 'ip_address' in cp_info['fixed_ips'][0]:
                cp.ip_address = cp_info['fixed_ips'][0]['ip_address']

        if 'mac_address' in cp_info and cp_info['mac_address']:
            cp.mac_addr = cp_info['mac_address']

        if cp_info['status'] == 'ACTIVE':
            cp.state = 'active'
        else:
            cp.state = 'inactive'

        if 'network_id' in cp_info and cp_info['network_id']:
            cp.virtual_link_id = cp_info['network_id']

        if 'device_id' in cp_info and cp_info['device_id']:
            cp.vdu_id = cp_info['device_id']

        if 'allowed_address_pairs' in cp_info and cp_info['allowed_address_pairs']:
            for vcp in cp_info['allowed_address_pairs']:
                vcp_info = cp.virtual_cp_info.add()
                if 'ip_address' in vcp and vcp['ip_address']:
                    vcp_info.ip_address = vcp['ip_address']
                if 'mac_address' in vcp and vcp['mac_address']:
                    vcp_info.mac_address = vcp['mac_address']
        return cp

    def _parse_virtual_cp(self, cp_info):
        """
        Parse the port_info dictionary returned by neutronclient
        Arguments:
          cp_info: A dictionary object representing port attributes

        Returns:
          Protobuf GI oject of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList_VirtualConnectionPoints()
        """
        cp = RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList_VirtualConnectionPoints()

        if 'id' in cp_info and cp_info['id']:
            cp.connection_point_id = cp_info['id']

        if 'name' in cp_info and cp_info['name']:
            cp.name = cp_info['name']

        if ('fixed_ips' in cp_info) and (len(cp_info['fixed_ips']) >= 1):
            if 'ip_address' in cp_info['fixed_ips'][0]:
                cp.ip_address = cp_info['fixed_ips'][0]['ip_address']

        if 'mac_address' in cp_info and cp_info['mac_address']:
            cp.mac_address = cp_info['mac_address']

        return cp

    def parse_cloud_virtual_link_info(self, vlink_info, port_list, subnet):
        """
        Parse vlink_info dictionary (return by python-client) and put values in GI object for Virtual Link

        Arguments:
        vlink_info : A dictionary object return by neutronclient library listing network attributes

        Returns:
        Protobuf GI Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList()
        """
        link = RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList()
        link.name  = vlink_info['name']
        if 'status' in vlink_info and vlink_info['status'] == 'ACTIVE':
            link.state = 'active'
        else:
            link.state = 'inactive'

        link.virtual_link_id = vlink_info['id']
        for port in port_list:
            if ('device_owner' in port) and (port['device_owner'] in ['compute:nova', 'compute:None']):
                link.connection_points.append(self._parse_cp(port))
            if ('device_owner' in port) and (port['device_owner'] == ''):
                link.virtual_connection_points.append(self._parse_virtual_cp(port))

        if subnet is not None:
            link.subnet = subnet['cidr']

        if ('provider:network_type' in vlink_info) and (vlink_info['provider:network_type'] != None):
            link.provider_network.overlay_type = vlink_info['provider:network_type'].upper()
        if ('provider:segmentation_id' in vlink_info) and (vlink_info['provider:segmentation_id']):
            link.provider_network.segmentation_id = vlink_info['provider:segmentation_id']
        if ('provider:physical_network' in vlink_info) and (vlink_info['provider:physical_network']):
            link.provider_network.physical_network = vlink_info['provider:physical_network'].upper()

        return link

    def setup_vdu_networking(self, vdu_params):
        """
        This function validates the networking/connectivity setup.

        Arguments:
          vdu_params: object of RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
          A list of port_ids and network_ids for VDU

        """
        port_args = list()
        network_ids = list()
        add_mgmt_net = False

        # Sorting Connection Points by given 'port_order'. If 'port_order' is not given then sorting by name.
        # Please note that the GI Object (vdu_params.connection_points) has been converted into a dictionary object for sorting purposes.

        sorted_connection_points = []
        if vdu_params.has_field('connection_points'):
            sorted_connection_points = sorted(vdu_params.as_dict().get('connection_points'), key=lambda k: ("port_order" not in k,
                                                                                                            k.get("port_order", None), k['name']))

        if vdu_params.mgmt_network is not None:
            # Setting the mgmt network as found in vdu params.
            mgmt_network = self.driver.neutron_drv.network_get(network_name=vdu_params.mgmt_network)['id']
        else:
            mgmt_network = self.driver._mgmt_network_id

        for cp in sorted_connection_points:
            if cp['virtual_link_id'] == mgmt_network:
                ### Remove mgmt_network_id from net_ids
                add_mgmt_net = True
            port_args.append(self._create_cp_args(cp))
        if not add_mgmt_net:
            network_ids.append(mgmt_network)

        ### Create ports and collect port ids
        if port_args:
            port_ids = self.driver.neutron_multi_port_create(port_args)
        else:
            port_ids = list()
        return port_ids, network_ids


    def _create_cp_args(self, cp):
        """
        Creates a request dictionary for port create call
        Arguments:
           cp: Object of Python Dictionary
        Returns:
           dict() of request params
        """
        args = dict()
        args['name'] = cp['name']

        args['network_id'] = cp['virtual_link_id']
        args['admin_state_up'] = True

        if cp['type_yang'] in ['VIRTIO', 'E1000', 'VPORT']:
            args['binding:vnic_type'] = 'normal'
        elif cp['type_yang'] == 'SR_IOV':
            args['binding:vnic_type'] = 'direct'
        else:
            raise NotImplementedError("Port Type: %s not supported" %(cp['type_yang']))

        try:
            if cp['static_ip_address']:
                args["fixed_ips"] = [{"ip_address" : cp['static_ip_address']}]
        except Exception as e:
            pass

        if 'port_security_enabled' in cp:
            args['port_security_enabled'] = cp['port_security_enabled']

        if 'security_group' in cp:
            if self.driver._neutron_security_groups:
                gid = self.driver._neutron_security_groups[0]['id']
                args['security_groups'] = [ gid ]

        if 'virtual_cps' in cp:
            args['allowed_address_pairs'] = [ {'ip_address': vcp['ip_address'],
                                               'mac_address': vcp['mac_address']}
                                              for vcp in cp['virtual_cps'] ]

        return args

    def make_virtual_link_args(self, link_params):
        """
        Function to create kwargs required for neutron_network_create API

        Arguments:
         link_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VirtualLinkReqParams()

        Returns:
          A kwargs dictionary for network operation
        """
        kwargs = dict()
        kwargs['name']            = link_params.name
        kwargs['admin_state_up']  = True
        kwargs['external_router'] = False
        kwargs['shared']          = False

        if link_params.has_field('provider_network'):
            if link_params.provider_network.has_field('physical_network'):
                kwargs['physical_network'] = link_params.provider_network.physical_network
            if link_params.provider_network.has_field('overlay_type'):
                kwargs['network_type'] = link_params.provider_network.overlay_type.lower()
            if link_params.provider_network.has_field('segmentation_id'):
                kwargs['segmentation_id'] = link_params.provider_network.segmentation_id

        return kwargs

    def make_subnet_args(self, link_params, network_id):
        """
        Function to create kwargs required for neutron_subnet_create API

        Arguments:
         link_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VirtualLinkReqParams()

        Returns:
          A kwargs dictionary for subnet operation
        """
        kwargs = {'network_id' : network_id,
                  'dhcp_params': {'enable_dhcp': True},
                  'gateway_ip' : None,}

        if link_params.ip_profile_params.has_field('ip_version'):
            kwargs['ip_version'] = 6 if link_params.ip_profile_params.ip_version == 'ipv6' else 4
        else:
            kwargs['ip_version'] = 4

        if link_params.ip_profile_params.has_field('subnet_address'):
            kwargs['cidr'] = link_params.ip_profile_params.subnet_address
        elif link_params.ip_profile_params.has_field('subnet_prefix_pool'):
            name = link_params.ip_profile_params.subnet_prefix_pool
            pools = [ p['id']  for p in self.driver._neutron_subnet_prefix_pool if p['name'] == name ]
            if not pools:
                self.log.error("Could not find subnet pool with name :%s to be used for network: %s",
                               link_params.ip_profile_params.subnet_prefix_pool,
                               link_params.name)
                raise NeutronException.NotFound("SubnetPool with name %s not found"%(link_params.ip_profile_params.subnet_prefix_pool))

            kwargs['subnetpool_id'] = pools[0]

        elif link_params.has_field('subnet'):
            kwargs['cidr'] = link_params.subnet
        else:
            raise NeutronException.NeutronException("No IP Prefix or Pool name specified")

        if link_params.ip_profile_params.has_field('dhcp_params'):
            if link_params.ip_profile_params.dhcp_params.has_field('enabled'):
                kwargs['dhcp_params']['enable_dhcp'] = link_params.ip_profile_params.dhcp_params.enabled
            if link_params.ip_profile_params.dhcp_params.has_field('start_address'):
                kwargs['dhcp_params']['start_address']  = link_params.ip_profile_params.dhcp_params.start_address
            if link_params.ip_profile_params.dhcp_params.has_field('count'):
                kwargs['dhcp_params']['count']  = link_params.ip_profile_params.dhcp_params.count

        if link_params.ip_profile_params.has_field('dns_server'):
            kwargs['dns_server'] = []
            for server in link_params.ip_profile_params.dns_server:
                kwargs['dns_server'].append(server.address)

        if link_params.ip_profile_params.has_field('gateway_address'):
            kwargs['gateway_ip'] = link_params.ip_profile_params.gateway_address

        return kwargs

    def prepare_virtual_link(self, link_params, network_id):
        """
        Function to create additional resources in the network during
        network-creation process. It involves following steps
           - Create subnets
           - Create any virtual ports in network

        Arguments:
         link_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VirtualLinkReqParams()
         network_id: string

        Returns:
          None
        """
        ### Create subnet
        kwargs = self.make_subnet_args(link_params, network_id)
        self.driver.neutron_subnet_create(**kwargs)

        ### Create Virtual connection point
        if link_params.has_field('virtual_cps'):
            port_args = list()
            for vcp in link_params.virtual_cps:
                cp = RwcalYang.YangData_RwProject_Project_VduInitParams_ConnectionPoints()
                cp.from_dict({k:v for k,v in vcp.as_dict().items()
                              if k in ['name','security_group', 'port_security_enabled', 'static_ip_address', 'type_yang']})
                cp.virtual_link_id = network_id
                port_args.append(self._create_cp_args(cp.as_dict()))
            if port_args:
                ### Create ports
                self.driver.neutron_multi_port_create(port_args)
        return
