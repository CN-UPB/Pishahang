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
import logging
import ipaddress
from neutronclient.neutron import client as ntclient

import neutronclient.common.exceptions as NeutronException


class NeutronAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(NeutronAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during Neutron API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg


class NeutronDriver(object):
    """
    NeutronDriver Class for network orchestration
    """
    ### List of supported API versions in prioritized order 
    supported_versions = ["2"]
    
    def __init__(self,
                 sess_handle,
                 region_name  = 'RegionOne',
                 service_type = 'network',
                 logger = None):
        """
        Constructor for NeutronDriver class
        Arguments:
        sess_handle (instance of class SessionDriver)
        region_name (string): Region Name
        service_type(string): Type of service in service catalog
        logger (instance of logging.Logger)
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.neutron')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self._sess_handle = sess_handle

        #### Attempt to use API versions in prioritized order defined in
        #### NeutronDriver.supported_versions
        def select_version(version):
            try:
                self.log.info("Attempting to use Neutron v%s APIs", version)
                ntdrv = ntclient.Client(api_version = version,
                                        region_name = region_name,
                                        service_type = service_type,
                                        session = self._sess_handle.session,
                                        logger = self.log)
            except Exception as e:
                self.log.info(str(e))
                raise
            else:
                self.log.info("Neutron API v%s selected", version)
                return (version, ntdrv)

        errors = []
        for v in NeutronDriver.supported_versions:
            try:
                (self._version, self._nt_drv) = select_version(v)
            except Exception as e:
                errors.append(e)
            else:
                break
        else:
            raise NeutronAPIVersionException(errors)

    @property
    def neutron_endpoint(self):
        return self._nt_drv.get_auth_info()['endpoint_url']

    @property
    def project_id(self):
        return self._sess_handle.project_id
    
    @property
    def neutron_quota(self):
        """
        Returns Neutron Quota (a dictionary) for project
        """
        try:
            quota = self._nt_drv.show_quota(self.project_id)
        except Exception as e:
            self.log.exception("Get Neutron quota operation failed. Exception: %s", str(e))
            raise
        return quota
    
    def extensions_list(self):
        """
        Returns a list of available neutron extensions.
        Arguments:
           None
        Returns:
           A list of dictionaries. Each dictionary contains attributes for a single Neutron extension
        """
        try:
            extensions = self._nt_drv.list_extensions()
        except Exception as e:
            self.log.exception("List extension operation failed. Exception: %s", str(e))
            raise
        if 'extensions' in extensions:
            return extensions['extensions']
        return list()

    
    def _get_neutron_connection(self):
        """
        Returns instance of object neutronclient.neutron.client.Client
        Use for DEBUG ONLY
        """
        return self._nt_drv

    def _network_find(self, **kwargs):
        """
        Returns a network object dictionary based on the filters provided in kwargs 
        
        Arguments:
        kwargs (dictionary): A dictionary of key-value pair filters

        Returns:
        One or more dictionary object associated with network
        """
        try:
            networks = self._nt_drv.list_networks(**kwargs)['networks']
        except Exception as e:
            self.log.exception("List network operation failed. Exception: %s", str(e))
            raise
        return networks

    def network_list(self):
        """
        Returns list of dictionaries. Each dictionary contains the attributes for a network
        under project

        Arguments: None

        Returns:
          A list of dictionaries
        """
        return self._network_find(**{'tenant_id':self.project_id}) + self._network_find(**{'shared':True})
    
    
    def network_create(self, **kwargs):
        """
        Creates a new network for the project

        Arguments:
          A dictionary with following key-values
        {
          name (string)              : Name of the network
          admin_state_up(Boolean)    : True/False (Defaults: True)
          external_router(Boolean)   : Connectivity with external router. True/False (Defaults: False)
          shared(Boolean)            : Shared among tenants. True/False (Defaults: False)
          physical_network(string)   : The physical network where this network object is implemented (optional).
          network_type               : The type of physical network that maps to this network resource (optional).
                                       Possible values are: 'flat', 'vlan', 'vxlan', 'gre'
          segmentation_id            : An isolated segment on the physical network. The network_type attribute
                                       defines the segmentation model. For example, if the network_type value
                                       is vlan, this ID is a vlan identifier. If the network_type value is gre,
                                       this ID is a gre key.
        }
        """
        params = {'network':
                  {'name'                 : kwargs['name'],
                   'admin_state_up'       : kwargs['admin_state_up'],
                   'tenant_id'            : self.project_id,
                   'shared'               : kwargs['shared'],
                   #'port_security_enabled': port_security_enabled,
                   'router:external'      : kwargs['external_router']}}

        if 'physical_network' in kwargs:
            params['network']['provider:physical_network'] = kwargs['physical_network']
        if 'network_type' in kwargs:
            params['network']['provider:network_type'] = kwargs['network_type']
        if 'segmentation_id' in kwargs:
            params['network']['provider:segmentation_id'] = kwargs['segmentation_id']

        try:
            self.log.debug("Calling neutron create_network() with params: %s", str(params))
            net = self._nt_drv.create_network(params)
        except Exception as e:
            self.log.exception("Create Network operation failed. Exception: %s", str(e))
            raise
        
        network_id = net['network']['id']
        if not network_id:
            raise Exception("Empty network id returned from create_network. (params: %s)" % str(params))

        return network_id

    def network_delete(self, network_id):
        """
        Deletes a network identified by network_id

        Arguments:
          network_id (string): UUID of the network

        Returns: None
        """
        try:
            self._nt_drv.delete_network(network_id)
        except Exception as e:
            self.log.exception("Delete Network operation failed. Exception: %s",str(e))
            raise


    def network_get(self, network_id='', network_name=''):
        """
        Returns a dictionary object describing the attributes of the network

        Arguments:
           network_id (string): UUID of the network

        Returns:
           A dictionary object of the network attributes
        """
        networks = self._network_find(**{'id': network_id, 'name': network_name})
        if not networks:
            return None
        return networks[0]
    

    def subnet_create(self, **kwargs):
        """
        Creates a subnet on the network

        Arguments:
        A dictionary with following key value pairs
        {
          network_id(string)  : UUID of the network where subnet needs to be created
          subnet_cidr(string) : IPv4 address prefix (e.g. '1.1.1.0/24') for the subnet
          ip_version (integer): 4 for IPv4 and 6 for IPv6
        
        }

        Returns:
           subnet_id (string): UUID of the created subnet
        """
        params = {}
        params['network_id'] = kwargs['network_id']
        params['ip_version'] = kwargs['ip_version']

        # if params['ip_version'] == 6:
        #     assert 0, "IPv6 is not supported"
        
        if 'subnetpool_id' in kwargs:
            params['subnetpool_id'] = kwargs['subnetpool_id']
        else:
            params['cidr'] = kwargs['cidr']

        if 'gateway_ip' in kwargs:
            params['gateway_ip'] = kwargs['gateway_ip']
        else:
            params['gateway_ip'] = None

        if 'dhcp_params' in kwargs:
            params['enable_dhcp'] = kwargs['dhcp_params']['enable_dhcp']
            if 'start_address' in kwargs['dhcp_params'] and 'count' in kwargs['dhcp_params']:
                end_address = (ipaddress.IPv4Address(kwargs['dhcp_params']['start_address']) + kwargs['dhcp_params']['count']).compressed
                params['allocation_pools'] = [ {'start': kwargs['dhcp_params']['start_address'] ,
                                                'end' : end_address} ]
                
        if 'dns_server' in kwargs:
            params['dns_nameservers'] = []
            for server in kwargs['dns_server']:
                params['dns_nameservers'].append(server)

        try:
            subnet = self._nt_drv.create_subnet({'subnets': [params]})
        except Exception as e:
            self.log.exception("Create Subnet operation failed. Exception: %s",str(e))
            raise

        return subnet['subnets'][0]['id']

    def subnet_list(self, **kwargs):
        """
        Returns a list of dictionaries. Each dictionary contains attributes describing the subnet

        Arguments: None

        Returns:
           A dictionary of the objects of subnet attributes
        """
        try:
            subnets = self._nt_drv.list_subnets(**kwargs)['subnets']
        except Exception as e:
            self.log.exception("List Subnet operation failed. Exception: %s", str(e))
            raise
        return subnets

    def _subnet_get(self, subnet_id):
        """
        Returns a dictionary object describing the attributes of a subnet.

        Arguments:
           subnet_id (string): UUID of the subnet

        Returns:
           A dictionary object of the subnet attributes
        """
        subnets = self._nt_drv.list_subnets(id=subnet_id)
        if not subnets['subnets']:
            self.log.error("Get subnet operation failed for subnet_id: %s", subnet_id)
            #raise NeutronException.NotFound("Could not find subnet_id %s" %(subnet_id))
            return {'cidr': ''}
        else:
            return subnets['subnets'][0]

    def subnet_get(self, subnet_id):
        """
        Returns a dictionary object describing the attributes of a subnet.

        Arguments:
           subnet_id (string): UUID of the subnet

        Returns:
           A dictionary object of the subnet attributes
        """
        return self._subnet_get(subnet_id)

    def subnet_delete(self, subnet_id):
        """
        Deletes a subnet identified by subnet_id

        Arguments:
           subnet_id (string): UUID of the subnet to be deleted

        Returns: None
        """
        assert subnet_id == self._subnet_get(self,subnet_id)
        try:
            self._nt_drv.delete_subnet(subnet_id)
        except Exception as e:
            self.log.exception("Delete Subnet operation failed for subnet_id : %s. Exception: %s", subnet_id, str(e))
            raise

    def port_list(self, **kwargs):
        """
        Returns a list of dictionaries. Each dictionary contains attributes describing the port

        Arguments:
            kwargs (dictionary): A dictionary for filters for port_list operation

        Returns:
           A dictionary of the objects of port attributes

        """
        ports  = []

        kwargs['tenant_id'] = self.project_id

        try:
            ports  = self._nt_drv.list_ports(**kwargs)
        except Exception as e:
            self.log.exception("List Port operation failed. Exception: %s",str(e))
            raise
        return ports['ports']

    def port_create(self, ports):
        """
        Create a port in network

        Arguments:
           Ports
           List of dictionaries of following
           {
              name (string)          : Name of the port
              network_id(string)     : UUID of the network_id identifying the network to which port belongs
              ip_address(string)     : (Optional) Static IP address to assign to the port
              vnic_type(string)      : Possible values are "normal", "direct", "macvtap"
              admin_state_up         : True/False
              port_security_enabled  : True/False
              security_groups        : A List of Neutron security group Ids
           }
        Returns:
           A list of ports { port_id (string), tag (connection_name, string) }   
        """
        params = dict()
        params['ports'] = ports 
        self.log.debug("Port create params: {}".format(params))
        try:
            ports  = self._nt_drv.create_port(params)
        except Exception as e:
            self.log.exception("Ports Create operation failed. Exception: %s",str(e))
            raise
        return [ { "id": p['id'], "tag": p['name'] } for p in ports['ports'] ] 

    
    def port_update(self, port_id, no_security_groups=None,port_security_enabled=None):
        """
        Update a port in network
        """
        params = {}
        params["port"] = {}
        if no_security_groups:
            params["port"]["security_groups"] = []
        if port_security_enabled == False:
            params["port"]["port_security_enabled"] = False
        elif  port_security_enabled == True:
            params["port"]["port_security_enabled"] = True

        try:
            port  = self._nt_drv.update_port(port_id,params)
        except Exception as e:
            self.log.exception("Port Update operation failed. Exception: %s", str(e))
            raise
        return port['port']['id']

    def _port_get(self, port_id):
        """
        Returns a dictionary object describing the attributes of the port

        Arguments:
           port_id (string): UUID of the port

        Returns:
           A dictionary object of the port attributes
        """
        port   = self._nt_drv.list_ports(id=port_id)['ports']
        if not port:
            raise NeutronException.NotFound("Could not find port_id %s" %(port_id))
        return port[0]

    def port_get(self, port_id):
        """
        Returns a dictionary object describing the attributes of the port

        Arguments:
           port_id (string): UUID of the port

        Returns:
           A dictionary object of the port attributes
        """
        return self._port_get(port_id)

    def port_delete(self, port_id):
        """
        Deletes a port identified by port_id

        Arguments:
           port_id (string) : UUID of the port

        Returns: None
        """
        assert port_id == self._port_get(port_id)['id']
        try:
            self._nt_drv.delete_port(port_id)
        except Exception as e:
            self.log.exception("Port Delete operation failed for port_id : %s. Exception: %s",port_id, str(e))
            raise

    def security_group_list(self, **kwargs):
        """
        Returns a list of dictionaries. Each dictionary contains attributes describing the security group

        Arguments:
           None

        Returns:
           A dictionary of the objects of security group attributes
        """
        try:
            kwargs['tenant_id'] = self.project_id
            group_list = self._nt_drv.list_security_groups(**kwargs)
        except Exception as e:
            self.log.exception("List Security group operation, Exception: %s", str(e))
            raise
        return group_list['security_groups']
    

    def subnetpool_list(self, **kwargs):
        """
        Returns a list of dictionaries. Each dictionary contains attributes describing a subnet prefix pool

        Arguments:
           None

        Returns:
           A dictionary of the objects of subnet prefix pool
        """
        try:
            pool_list = self._nt_drv.list_subnetpools(**kwargs)
        except Exception as e:
            self.log.exception("List SubnetPool operation, Exception: %s",str(e))
            raise

        if 'subnetpools' in pool_list:
            return pool_list['subnetpools']
        else:
            return []

