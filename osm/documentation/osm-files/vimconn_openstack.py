# -*- coding: utf-8 -*-

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
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
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

'''
osconnector implements all the methods to interact with openstack using the python-neutronclient.

For the VNF forwarding graph, The OpenStack VIM connector calls the
networking-sfc Neutron extension methods, whose resources are mapped
to the VIM connector's SFC resources as follows:
- Classification (OSM) -> Flow Classifier (Neutron)
- Service Function Instance (OSM) -> Port Pair (Neutron)
- Service Function (OSM) -> Port Pair Group (Neutron)
- Service Function Path (OSM) -> Port Chain (Neutron)
'''
__author__ = "Alfonso Tierno, Gerardo Garcia, Pablo Montes, xFlow Research, Igor D.C."
__date__  = "$22-sep-2017 23:59:59$"

import vimconn
# import json
import logging
import netaddr
import time
import yaml
import random
import re
import copy

from novaclient import client as nClient, exceptions as nvExceptions
from keystoneauth1.identity import v2, v3
from keystoneauth1 import session
import keystoneclient.exceptions as ksExceptions
import keystoneclient.v3.client as ksClient_v3
import keystoneclient.v2_0.client as ksClient_v2
from glanceclient import client as glClient
import glanceclient.client as gl1Client
import glanceclient.exc as gl1Exceptions
from  cinderclient import client as cClient
from httplib import HTTPException
from neutronclient.neutron import client as neClient
from neutronclient.common import exceptions as neExceptions
from requests.exceptions import ConnectionError


"""contain the openstack virtual machine status to openmano status"""
vmStatus2manoFormat={'ACTIVE':'ACTIVE',
                     'PAUSED':'PAUSED',
                     'SUSPENDED': 'SUSPENDED',
                     'SHUTOFF':'INACTIVE',
                     'BUILD':'BUILD',
                     'ERROR':'ERROR','DELETED':'DELETED'
                     }
netStatus2manoFormat={'ACTIVE':'ACTIVE','PAUSED':'PAUSED','INACTIVE':'INACTIVE','BUILD':'BUILD','ERROR':'ERROR','DELETED':'DELETED'
                     }

supportedClassificationTypes = ['legacy_flow_classifier']

#global var to have a timeout creating and deleting volumes
volume_timeout = 600
server_timeout = 600

class vimconnector(vimconn.vimconnector):
    def __init__(self, uuid, name, tenant_id, tenant_name, url, url_admin=None, user=None, passwd=None,
                 log_level=None, config={}, persistent_info={}):
        '''using common constructor parameters. In this case
        'url' is the keystone authorization url,
        'url_admin' is not use
        '''
        api_version = config.get('APIversion')
        if api_version and api_version not in ('v3.3', 'v2.0', '2', '3'):
            raise vimconn.vimconnException("Invalid value '{}' for config:APIversion. "
                                           "Allowed values are 'v3.3', 'v2.0', '2' or '3'".format(api_version))
        vim_type = config.get('vim_type')
        if vim_type and vim_type not in ('vio', 'VIO'):
            raise vimconn.vimconnException("Invalid value '{}' for config:vim_type."
                            "Allowed values are 'vio' or 'VIO'".format(vim_type))

        if config.get('dataplane_net_vlan_range') is not None:
            #validate vlan ranges provided by user
            self._validate_vlan_ranges(config.get('dataplane_net_vlan_range'))

        vimconn.vimconnector.__init__(self, uuid, name, tenant_id, tenant_name, url, url_admin, user, passwd, log_level,
                                      config)

        if self.config.get("insecure") and self.config.get("ca_cert"):
            raise vimconn.vimconnException("options insecure and ca_cert are mutually exclusive")
        self.verify = True
        if self.config.get("insecure"):
            self.verify = False
        if self.config.get("ca_cert"):
            self.verify = self.config.get("ca_cert")
        self.verify = self.config.get("insecure", False)

        if not url:
            raise TypeError('url param can not be NoneType')
        self.persistent_info = persistent_info
        self.availability_zone = persistent_info.get('availability_zone', None)
        self.session = persistent_info.get('session', {'reload_client': True})
        self.nova = self.session.get('nova')
        self.neutron = self.session.get('neutron')
        self.cinder = self.session.get('cinder')
        self.glance = self.session.get('glance')
        self.glancev1 = self.session.get('glancev1')
        self.keystone = self.session.get('keystone')
        self.api_version3 = self.session.get('api_version3')
        self.vim_type = self.config.get("vim_type")
        if self.vim_type:
            self.vim_type = self.vim_type.upper()
        if self.config.get("use_internal_endpoint"):
            self.endpoint_type = "internalURL"
        else:
            self.endpoint_type = None

        self.logger = logging.getLogger('openmano.vim.openstack')

        ####### VIO Specific Changes #########
        if self.vim_type == "VIO":
            self.logger = logging.getLogger('openmano.vim.vio')

        if log_level:
            self.logger.setLevel( getattr(logging, log_level))

        if self.config.get("public_network"):
            self.public_network = self.config.get("public_network")

    def __getitem__(self, index):
        """Get individuals parameters.
        Throw KeyError"""
        if index == 'project_domain_id':
            return self.config.get("project_domain_id")
        elif index == 'user_domain_id':
            return self.config.get("user_domain_id")
        else:
            return vimconn.vimconnector.__getitem__(self, index)

    def __setitem__(self, index, value):
        """Set individuals parameters and it is marked as dirty so to force connection reload.
        Throw KeyError"""
        if index == 'project_domain_id':
            self.config["project_domain_id"] = value
        elif index == 'user_domain_id':
                self.config["user_domain_id"] = value
        else:
            vimconn.vimconnector.__setitem__(self, index, value)
        self.session['reload_client'] = True

    def _reload_connection(self):
        '''Called before any operation, it check if credentials has changed
        Throw keystoneclient.apiclient.exceptions.AuthorizationFailure
        '''
        #TODO control the timing and possible token timeout, but it seams that python client does this task for us :-) 
        if self.session['reload_client']:
            if self.config.get('APIversion'):
                self.api_version3 = self.config['APIversion'] == 'v3.3' or self.config['APIversion'] == '3'
            else:  # get from ending auth_url that end with v3 or with v2.0
                self.api_version3 =  self.url.endswith("/v3") or self.url.endswith("/v3/")
            self.session['api_version3'] = self.api_version3
            if self.api_version3:
                if self.config.get('project_domain_id') or self.config.get('project_domain_name'):
                    project_domain_id_default = None
                else:
                    project_domain_id_default = 'default'
                if self.config.get('user_domain_id') or self.config.get('user_domain_name'):
                    user_domain_id_default = None
                else:
                    user_domain_id_default = 'default'
                auth = v3.Password(auth_url=self.url,
                                   username=self.user,
                                   password=self.passwd,
                                   project_name=self.tenant_name,
                                   project_id=self.tenant_id,
                                   project_domain_id=self.config.get('project_domain_id', project_domain_id_default),
                                   user_domain_id=self.config.get('user_domain_id', user_domain_id_default),
                                   project_domain_name=self.config.get('project_domain_name'),
                                   user_domain_name=self.config.get('user_domain_name'))
            else:
                auth = v2.Password(auth_url=self.url,
                                   username=self.user,
                                   password=self.passwd,
                                   tenant_name=self.tenant_name,
                                   tenant_id=self.tenant_id)
            sess = session.Session(auth=auth, verify=self.verify)
            if self.api_version3:
                self.keystone = ksClient_v3.Client(session=sess, endpoint_type=self.endpoint_type)
            else:
                self.keystone = ksClient_v2.Client(session=sess, endpoint_type=self.endpoint_type)
            self.session['keystone'] = self.keystone
            # In order to enable microversion functionality an explicit microversion must be specified in 'config'.
            # This implementation approach is due to the warning message in
            # https://developer.openstack.org/api-guide/compute/microversions.html
            # where it is stated that microversion backwards compatibility is not guaranteed and clients should
            # always require an specific microversion.
            # To be able to use 'device role tagging' functionality define 'microversion: 2.32' in datacenter config
            version = self.config.get("microversion")
            if not version:
                version = "2.1"
            self.nova = self.session['nova'] = nClient.Client(str(version), session=sess, endpoint_type=self.endpoint_type)
            self.neutron = self.session['neutron'] = neClient.Client('2.0', session=sess, endpoint_type=self.endpoint_type)
            self.cinder = self.session['cinder'] = cClient.Client(2, session=sess, endpoint_type=self.endpoint_type)
            if self.endpoint_type == "internalURL":
                glance_service_id = self.keystone.services.list(name="glance")[0].id
                glance_endpoint = self.keystone.endpoints.list(glance_service_id, interface="internal")[0].url
            else:
                glance_endpoint = None
            self.glance = self.session['glance'] = glClient.Client(2, session=sess, endpoint=glance_endpoint)
            #using version 1 of glance client in new_image()
            self.glancev1 = self.session['glancev1'] = glClient.Client('1', session=sess,
                                                                       endpoint=glance_endpoint)
            self.session['reload_client'] = False
            self.persistent_info['session'] = self.session
            # add availablity zone info inside  self.persistent_info
            self._set_availablity_zones()
            self.persistent_info['availability_zone'] = self.availability_zone

    def __net_os2mano(self, net_list_dict):
        '''Transform the net openstack format to mano format
        net_list_dict can be a list of dict or a single dict'''
        if type(net_list_dict) is dict:
            net_list_=(net_list_dict,)
        elif type(net_list_dict) is list:
            net_list_=net_list_dict
        else:
            raise TypeError("param net_list_dict must be a list or a dictionary")
        for net in net_list_:
            if net.get('provider:network_type') == "vlan":
                net['type']='data'
            else:
                net['type']='bridge'

    def __classification_os2mano(self, class_list_dict):
        """Transform the openstack format (Flow Classifier) to mano format
        (Classification) class_list_dict can be a list of dict or a single dict
        """
        if isinstance(class_list_dict, dict):
            class_list_ = [class_list_dict]
        elif isinstance(class_list_dict, list):
            class_list_ = class_list_dict
        else:
            raise TypeError(
                "param class_list_dict must be a list or a dictionary")
        for classification in class_list_:
            id = classification.pop('id')
            name = classification.pop('name')
            description = classification.pop('description')
            project_id = classification.pop('project_id')
            tenant_id = classification.pop('tenant_id')
            original_classification = copy.deepcopy(classification)
            classification.clear()
            classification['ctype'] = 'legacy_flow_classifier'
            classification['definition'] = original_classification
            classification['id'] = id
            classification['name'] = name
            classification['description'] = description
            classification['project_id'] = project_id
            classification['tenant_id'] = tenant_id

    def __sfi_os2mano(self, sfi_list_dict):
        """Transform the openstack format (Port Pair) to mano format (SFI)
        sfi_list_dict can be a list of dict or a single dict
        """
        if isinstance(sfi_list_dict, dict):
            sfi_list_ = [sfi_list_dict]
        elif isinstance(sfi_list_dict, list):
            sfi_list_ = sfi_list_dict
        else:
            raise TypeError(
                "param sfi_list_dict must be a list or a dictionary")
        for sfi in sfi_list_:
            sfi['ingress_ports'] = []
            sfi['egress_ports'] = []
            if sfi.get('ingress'):
                sfi['ingress_ports'].append(sfi['ingress'])
            if sfi.get('egress'):
                sfi['egress_ports'].append(sfi['egress'])
            del sfi['ingress']
            del sfi['egress']
            params = sfi.get('service_function_parameters')
            sfc_encap = False
            if params:
                correlation = params.get('correlation')
                if correlation:
                    sfc_encap = True
            sfi['sfc_encap'] = sfc_encap
            del sfi['service_function_parameters']

    def __sf_os2mano(self, sf_list_dict):
        """Transform the openstack format (Port Pair Group) to mano format (SF)
        sf_list_dict can be a list of dict or a single dict
        """
        if isinstance(sf_list_dict, dict):
            sf_list_ = [sf_list_dict]
        elif isinstance(sf_list_dict, list):
            sf_list_ = sf_list_dict
        else:
            raise TypeError(
                "param sf_list_dict must be a list or a dictionary")
        for sf in sf_list_:
            del sf['port_pair_group_parameters']
            sf['sfis'] = sf['port_pairs']
            del sf['port_pairs']

    def __sfp_os2mano(self, sfp_list_dict):
        """Transform the openstack format (Port Chain) to mano format (SFP)
        sfp_list_dict can be a list of dict or a single dict
        """
        if isinstance(sfp_list_dict, dict):
            sfp_list_ = [sfp_list_dict]
        elif isinstance(sfp_list_dict, list):
            sfp_list_ = sfp_list_dict
        else:
            raise TypeError(
                "param sfp_list_dict must be a list or a dictionary")
        for sfp in sfp_list_:
            params = sfp.pop('chain_parameters')
            sfc_encap = False
            if params:
                correlation = params.get('correlation')
                if correlation:
                    sfc_encap = True
            sfp['sfc_encap'] = sfc_encap
            sfp['spi'] = sfp.pop('chain_id')
            sfp['classifications'] = sfp.pop('flow_classifiers')
            sfp['service_functions'] = sfp.pop('port_pair_groups')

    # placeholder for now; read TODO note below
    def _validate_classification(self, type, definition):
        # only legacy_flow_classifier Type is supported at this point
        return True
        # TODO(igordcard): this method should be an abstract method of an
        # abstract Classification class to be implemented by the specific
        # Types. Also, abstract vimconnector should call the validation
        # method before the implemented VIM connectors are called.

    def _format_exception(self, exception):
        '''Transform a keystone, nova, neutron  exception into a vimconn exception'''
        if isinstance(exception, (HTTPException, gl1Exceptions.HTTPException, gl1Exceptions.CommunicationError,
                                  ConnectionError, ksExceptions.ConnectionError, neExceptions.ConnectionFailed
                                  )):
            raise vimconn.vimconnConnectionException(type(exception).__name__ + ": " + str(exception))
        elif isinstance(exception, (nvExceptions.ClientException, ksExceptions.ClientException,
                                    neExceptions.NeutronException, nvExceptions.BadRequest)):
            raise vimconn.vimconnUnexpectedResponse(type(exception).__name__ + ": " + str(exception))
        elif isinstance(exception, (neExceptions.NetworkNotFoundClient, nvExceptions.NotFound)):
            raise vimconn.vimconnNotFoundException(type(exception).__name__ + ": " + str(exception))
        elif isinstance(exception, nvExceptions.Conflict):
            raise vimconn.vimconnConflictException(type(exception).__name__ + ": " + str(exception))
        elif isinstance(exception, vimconn.vimconnException):
            raise exception
        else:  # ()
            self.logger.error("General Exception " + str(exception), exc_info=True)
            raise vimconn.vimconnConnectionException(type(exception).__name__ + ": " + str(exception))

    def get_tenant_list(self, filter_dict={}):
        '''Obtain tenants of VIM
        filter_dict can contain the following keys:
            name: filter by tenant name
            id: filter by tenant uuid/id
            <other VIM specific>
        Returns the tenant list of dictionaries: [{'name':'<name>, 'id':'<id>, ...}, ...]
        '''
        self.logger.debug("Getting tenants from VIM filter: '%s'", str(filter_dict))
        try:
            self._reload_connection()
            if self.api_version3:
                project_class_list = self.keystone.projects.list(name=filter_dict.get("name"))
            else:
                project_class_list = self.keystone.tenants.findall(**filter_dict)
            project_list=[]
            for project in project_class_list:
                if filter_dict.get('id') and filter_dict["id"] != project.id:
                    continue
                project_list.append(project.to_dict())
            return project_list
        except (ksExceptions.ConnectionError, ksExceptions.ClientException, ConnectionError) as e:
            self._format_exception(e)

    def new_tenant(self, tenant_name, tenant_description):
        '''Adds a new tenant to openstack VIM. Returns the tenant identifier'''
        self.logger.debug("Adding a new tenant name: %s", tenant_name)
        try:
            self._reload_connection()
            if self.api_version3:
                project = self.keystone.projects.create(tenant_name, self.config.get("project_domain_id", "default"),
                                                        description=tenant_description, is_domain=False)
            else:
                project = self.keystone.tenants.create(tenant_name, tenant_description)
            return project.id
        except (ksExceptions.ConnectionError, ksExceptions.ClientException, ConnectionError)  as e:
            self._format_exception(e)

    def delete_tenant(self, tenant_id):
        '''Delete a tenant from openstack VIM. Returns the old tenant identifier'''
        self.logger.debug("Deleting tenant %s from VIM", tenant_id)
        try:
            self._reload_connection()
            if self.api_version3:
                self.keystone.projects.delete(tenant_id)
            else:
                self.keystone.tenants.delete(tenant_id)
            return tenant_id
        except (ksExceptions.ConnectionError, ksExceptions.ClientException, ConnectionError)  as e:
            self._format_exception(e)

    def new_network(self,net_name, net_type, ip_profile=None, shared=False, vlan=None):
        '''Adds a tenant network to VIM. Returns the network identifier'''
        self.logger.debug("Adding a new network to VIM name '%s', type '%s'", net_name, net_type)
        #self.logger.debug(">>>>>>>>>>>>>>>>>> IP profile %s", str(ip_profile))
        try:
            new_net = None
            self._reload_connection()
            network_dict = {'name': net_name, 'admin_state_up': True}
            if net_type=="data" or net_type=="ptp":
                if self.config.get('dataplane_physical_net') == None:
                    raise vimconn.vimconnConflictException("You must provide a 'dataplane_physical_net' at config value before creating sriov network")
                network_dict["provider:physical_network"] = self.config['dataplane_physical_net'] #"physnet_sriov" #TODO physical
                network_dict["provider:network_type"]     = "vlan"
                if vlan!=None:
                    network_dict["provider:network_type"] = vlan

                ####### VIO Specific Changes #########
                if self.vim_type == "VIO":
                    if vlan is not None:
                        network_dict["provider:segmentation_id"] = vlan
                    else:
                        if self.config.get('dataplane_net_vlan_range') is None:
                            raise vimconn.vimconnConflictException("You must provide "\
                                "'dataplane_net_vlan_range' in format [start_ID - end_ID]"\
                                "at config value before creating sriov network with vlan tag")

                        network_dict["provider:segmentation_id"] = self._genrate_vlanID()

            network_dict["shared"]=shared
            new_net=self.neutron.create_network({'network':network_dict})
            #print new_net
            #create subnetwork, even if there is no profile
            if not ip_profile:
                ip_profile = {}
            if not ip_profile.get('subnet_address'):
                #Fake subnet is required
                subnet_rand = random.randint(0, 255)
                ip_profile['subnet_address'] = "192.168.{}.0/24".format(subnet_rand)
            if 'ip_version' not in ip_profile:
                ip_profile['ip_version'] = "IPv4"
            subnet = {"name":net_name+"-subnet",
                    "network_id": new_net["network"]["id"],
                    "ip_version": 4 if ip_profile['ip_version']=="IPv4" else 6,
                    "cidr": ip_profile['subnet_address']
                    }
            # Gateway should be set to None if not needed. Otherwise openstack assigns one by default
            if ip_profile.get('gateway_address'):
                subnet['gateway_ip'] = ip_profile.get('gateway_address')
            if ip_profile.get('dns_address'):
                subnet['dns_nameservers'] = ip_profile['dns_address'].split(";")
            if 'dhcp_enabled' in ip_profile:
                subnet['enable_dhcp'] = False if \
                    ip_profile['dhcp_enabled']=="false" or ip_profile['dhcp_enabled']==False else True
            if ip_profile.get('dhcp_start_address'):
                subnet['allocation_pools'] = []
                subnet['allocation_pools'].append(dict())
                subnet['allocation_pools'][0]['start'] = ip_profile['dhcp_start_address']
            if ip_profile.get('dhcp_count'):
                #parts = ip_profile['dhcp_start_address'].split('.')
                #ip_int = (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
                ip_int = int(netaddr.IPAddress(ip_profile['dhcp_start_address']))
                ip_int += ip_profile['dhcp_count'] - 1
                ip_str = str(netaddr.IPAddress(ip_int))
                subnet['allocation_pools'][0]['end'] = ip_str
            #self.logger.debug(">>>>>>>>>>>>>>>>>> Subnet: %s", str(subnet))
            new_subnet=self.neutron.create_subnet({"subnet": subnet} )

            # Connect network to 'public' network to allow internet access
            if self.public_network is not None:
                router_id=self.neutron.create_router({'router': {'name': net_name+'-router', 'admin_state_up': True}})['router']['id']
                self.neutron.add_gateway_router(router=router_id, body={'network_id': self.public_network})
                self.neutron.add_interface_router(router=router_id, body={'subnet_id': new_subnet['subnet']['id']})


            return new_net["network"]["id"]
        except Exception as e:
            if new_net:
                self.neutron.delete_network(new_net['network']['id'])
            self._format_exception(e)

    def get_network_list(self, filter_dict={}):
        '''Obtain tenant networks of VIM
        Filter_dict can be:
            name: network name
            id: network uuid
            shared: boolean
            tenant_id: tenant
            admin_state_up: boolean
            status: 'ACTIVE'
        Returns the network list of dictionaries
        '''
        self.logger.debug("Getting network from VIM filter: '%s'", str(filter_dict))
        try:
            self._reload_connection()
            filter_dict_os = filter_dict.copy()
            if self.api_version3 and "tenant_id" in filter_dict_os:
                filter_dict_os['project_id'] = filter_dict_os.pop('tenant_id')  #T ODO check
            net_dict = self.neutron.list_networks(**filter_dict_os)
            net_list = net_dict["networks"]
            self.__net_os2mano(net_list)
            return net_list
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException, neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def get_network(self, net_id):
        '''Obtain details of network from VIM
        Returns the network information from a network id'''
        self.logger.debug(" Getting tenant network %s from VIM", net_id)
        filter_dict={"id": net_id}
        net_list = self.get_network_list(filter_dict)
        if len(net_list)==0:
            raise vimconn.vimconnNotFoundException("Network '{}' not found".format(net_id))
        elif len(net_list)>1:
            raise vimconn.vimconnConflictException("Found more than one network with this criteria")
        net = net_list[0]
        subnets=[]
        for subnet_id in net.get("subnets", () ):
            try:
                subnet = self.neutron.show_subnet(subnet_id)
            except Exception as e:
                self.logger.error("osconnector.get_network(): Error getting subnet %s %s" % (net_id, str(e)))
                subnet = {"id": subnet_id, "fault": str(e)}
            subnets.append(subnet)
        net["subnets"] = subnets
        net["encapsulation"] = net.get('provider:network_type')
        net["segmentation_id"] = net.get('provider:segmentation_id')
        return net

    def delete_network(self, net_id):
        '''Deletes a tenant network from VIM. Returns the old network identifier'''
        self.logger.debug("Deleting network '%s' from VIM", net_id)
        try:
            self._reload_connection()

            # delete router ports and router connecting tenant and public network
            for port in self.neutron.list_ports(network_id=net_id)['ports']:
                if port['device_owner'] =='network:router_interface' or port['device_owner'] == 'network:dhcp':
                    self.neutron.update_port(port=port['id'], body={'port': {'device_owner': 'None'}})
                    self.neutron.delete_port(port['id'])
            self.neutron.delete_router(self.neutron.list_routers(name=self.neutron.list_networks(id=net_id)['networks'][0]['name']+'-router')['routers'][0]['id'])

            #delete VM ports attached to this networks before the network
            ports = self.neutron.list_ports(network_id=net_id)
            for p in ports['ports']:
                try:
                    self.neutron.delete_port(p["id"])
                except Exception as e:
                    self.logger.error("Error deleting port %s: %s", p["id"], str(e))
            self.neutron.delete_network(net_id)
            return net_id
        except (neExceptions.ConnectionFailed, neExceptions.NetworkNotFoundClient, neExceptions.NeutronException,
                ksExceptions.ClientException, neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def refresh_nets_status(self, net_list):
        '''Get the status of the networks
           Params: the list of network identifiers
           Returns a dictionary with:
                net_id:         #VIM id of this network
                    status:     #Mandatory. Text with one of:
                                #  DELETED (not found at vim)
                                #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...) 
                                #  OTHER (Vim reported other status not understood)
                                #  ERROR (VIM indicates an ERROR status)
                                #  ACTIVE, INACTIVE, DOWN (admin down), 
                                #  BUILD (on building process)
                                #
                    error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR 
                    vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)

        '''
        net_dict={}
        for net_id in net_list:
            net = {}
            try:
                net_vim = self.get_network(net_id)
                if net_vim['status'] in netStatus2manoFormat:
                    net["status"] = netStatus2manoFormat[ net_vim['status'] ]
                else:
                    net["status"] = "OTHER"
                    net["error_msg"] = "VIM status reported " + net_vim['status']

                if net['status'] == "ACTIVE" and not net_vim['admin_state_up']:
                    net['status'] = 'DOWN'
                try:
                    net['vim_info'] = yaml.safe_dump(net_vim, default_flow_style=True, width=256)
                except yaml.representer.RepresenterError:
                    net['vim_info'] = str(net_vim)
                if net_vim.get('fault'):  #TODO
                    net['error_msg'] = str(net_vim['fault'])
            except vimconn.vimconnNotFoundException as e:
                self.logger.error("Exception getting net status: %s", str(e))
                net['status'] = "DELETED"
                net['error_msg'] = str(e)
            except vimconn.vimconnException as e:
                self.logger.error("Exception getting net status: %s", str(e))
                net['status'] = "VIM_ERROR"
                net['error_msg'] = str(e)
            net_dict[net_id] = net
        return net_dict

    def get_flavor(self, flavor_id):
        '''Obtain flavor details from the  VIM. Returns the flavor dict details'''
        self.logger.debug("Getting flavor '%s'", flavor_id)
        try:
            self._reload_connection()
            flavor = self.nova.flavors.find(id=flavor_id)
            #TODO parse input and translate to VIM format (openmano_schemas.new_vminstance_response_schema)
            return flavor.to_dict()
        except (nvExceptions.NotFound, nvExceptions.ClientException, ksExceptions.ClientException, ConnectionError) as e:
            self._format_exception(e)

    def get_flavor_id_from_data(self, flavor_dict):
        """Obtain flavor id that match the flavor description
           Returns the flavor_id or raises a vimconnNotFoundException
           flavor_dict: contains the required ram, vcpus, disk
           If 'use_existing_flavors' is set to True at config, the closer flavor that provides same or more ram, vcpus
                and disk is returned. Otherwise a flavor with exactly same ram, vcpus and disk is returned or a
                vimconnNotFoundException is raised
        """
        exact_match = False if self.config.get('use_existing_flavors') else True
        try:
            self._reload_connection()
            flavor_candidate_id = None
            flavor_candidate_data = (10000, 10000, 10000)
            flavor_target = (flavor_dict["ram"], flavor_dict["vcpus"], flavor_dict["disk"])
            # numa=None
            numas = flavor_dict.get("extended", {}).get("numas")
            if numas:
                #TODO
                raise vimconn.vimconnNotFoundException("Flavor with EPA still not implemted")
                # if len(numas) > 1:
                #     raise vimconn.vimconnNotFoundException("Cannot find any flavor with more than one numa")
                # numa=numas[0]
                # numas = extended.get("numas")
            for flavor in self.nova.flavors.list():
                epa = flavor.get_keys()
                if epa:
                    continue
                    # TODO
                flavor_data = (flavor.ram, flavor.vcpus, flavor.disk)
                if flavor_data == flavor_target:
                    return flavor.id
                elif not exact_match and flavor_target < flavor_data < flavor_candidate_data:
                    flavor_candidate_id = flavor.id
                    flavor_candidate_data = flavor_data
            if not exact_match and flavor_candidate_id:
                return flavor_candidate_id
            raise vimconn.vimconnNotFoundException("Cannot find any flavor matching '{}'".format(str(flavor_dict)))
        except (nvExceptions.NotFound, nvExceptions.ClientException, ksExceptions.ClientException, ConnectionError) as e:
            self._format_exception(e)

    def new_flavor(self, flavor_data, change_name_if_used=True):
        '''Adds a tenant flavor to openstack VIM
        if change_name_if_used is True, it will change name in case of conflict, because it is not supported name repetition
        Returns the flavor identifier
        '''
        self.logger.debug("Adding flavor '%s'", str(flavor_data))
        retry=0
        max_retries=3
        name_suffix = 0
        name=flavor_data['name']
        while retry<max_retries:
            retry+=1
            try:
                self._reload_connection()
                if change_name_if_used:
                    #get used names
                    fl_names=[]
                    fl=self.nova.flavors.list()
                    for f in fl:
                        fl_names.append(f.name)
                    while name in fl_names:
                        name_suffix += 1
                        name = flavor_data['name']+"-" + str(name_suffix)

                ram = flavor_data.get('ram',64)
                vcpus = flavor_data.get('vcpus',1)
                numa_properties=None

                extended = flavor_data.get("extended")
                if extended:
                    numas=extended.get("numas")
                    if numas:
                        numa_nodes = len(numas)
                        if numa_nodes > 1:
                            return -1, "Can not add flavor with more than one numa"
                        numa_properties = {"hw:numa_nodes":str(numa_nodes)}
                        numa_properties["hw:mem_page_size"] = "large"
                        numa_properties["hw:cpu_policy"] = "dedicated"
                        numa_properties["hw:numa_mempolicy"] = "strict"
                        if self.vim_type == "VIO":
                            numa_properties["vmware:extra_config"] = '{"numa.nodeAffinity":"0"}'
                            numa_properties["vmware:latency_sensitivity_level"] = "high"
                        for numa in numas:
                            #overwrite ram and vcpus
                            #check if key 'memory' is present in numa else use ram value at flavor
                            if 'memory' in numa:
                                ram = numa['memory']*1024
                            #See for reference: https://specs.openstack.org/openstack/nova-specs/specs/mitaka/implemented/virt-driver-cpu-thread-pinning.html
                            if 'paired-threads' in numa:
                                vcpus = numa['paired-threads']*2
                                #cpu_thread_policy "require" implies that the compute node must have an STM architecture
                                numa_properties["hw:cpu_thread_policy"] = "require"
                                numa_properties["hw:cpu_policy"] = "dedicated"
                            elif 'cores' in numa:
                                vcpus = numa['cores']
                                # cpu_thread_policy "prefer" implies that the host must not have an SMT architecture, or a non-SMT architecture will be emulated
                                numa_properties["hw:cpu_thread_policy"] = "isolate"
                                numa_properties["hw:cpu_policy"] = "dedicated"
                            elif 'threads' in numa:
                                vcpus = numa['threads']
                                # cpu_thread_policy "prefer" implies that the host may or may not have an SMT architecture
                                numa_properties["hw:cpu_thread_policy"] = "prefer"
                                numa_properties["hw:cpu_policy"] = "dedicated"
                            # for interface in numa.get("interfaces",() ):
                            #     if interface["dedicated"]=="yes":
                            #         raise vimconn.vimconnException("Passthrough interfaces are not supported for the openstack connector", http_code=vimconn.HTTP_Service_Unavailable)
                            #     #TODO, add the key 'pci_passthrough:alias"="<label at config>:<number ifaces>"' when a way to connect it is available

                #create flavor                 
                new_flavor=self.nova.flavors.create(name,
                                ram,
                                vcpus,
                                flavor_data.get('disk',0),
                                is_public=flavor_data.get('is_public', True)
                            )
                #add metadata
                if numa_properties:
                    new_flavor.set_keys(numa_properties)
                return new_flavor.id
            except nvExceptions.Conflict as e:
                if change_name_if_used and retry < max_retries:
                    continue
                self._format_exception(e)
            #except nvExceptions.BadRequest as e:
            except (ksExceptions.ClientException, nvExceptions.ClientException, ConnectionError) as e:
                self._format_exception(e)

    def delete_flavor(self,flavor_id):
        '''Deletes a tenant flavor from openstack VIM. Returns the old flavor_id
        '''
        try:
            self._reload_connection()
            self.nova.flavors.delete(flavor_id)
            return flavor_id
        #except nvExceptions.BadRequest as e:
        except (nvExceptions.NotFound, ksExceptions.ClientException, nvExceptions.ClientException, ConnectionError) as e:
            self._format_exception(e)

    def new_image(self,image_dict):
        '''
        Adds a tenant image to VIM. imge_dict is a dictionary with:
            name: name
            disk_format: qcow2, vhd, vmdk, raw (by default), ...
            location: path or URI
            public: "yes" or "no"
            metadata: metadata of the image
        Returns the image_id
        '''
        retry=0
        max_retries=3
        while retry<max_retries:
            retry+=1
            try:
                self._reload_connection()
                #determine format  http://docs.openstack.org/developer/glance/formats.html
                if "disk_format" in image_dict:
                    disk_format=image_dict["disk_format"]
                else: #autodiscover based on extension
                    if image_dict['location'][-6:]==".qcow2":
                        disk_format="qcow2"
                    elif image_dict['location'][-4:]==".vhd":
                        disk_format="vhd"
                    elif image_dict['location'][-5:]==".vmdk":
                        disk_format="vmdk"
                    elif image_dict['location'][-4:]==".vdi":
                        disk_format="vdi"
                    elif image_dict['location'][-4:]==".iso":
                        disk_format="iso"
                    elif image_dict['location'][-4:]==".aki":
                        disk_format="aki"
                    elif image_dict['location'][-4:]==".ari":
                        disk_format="ari"
                    elif image_dict['location'][-4:]==".ami":
                        disk_format="ami"
                    else:
                        disk_format="raw"
                self.logger.debug("new_image: '%s' loading from '%s'", image_dict['name'], image_dict['location'])
                if image_dict['location'][0:4]=="http":
                    new_image = self.glancev1.images.create(name=image_dict['name'], is_public=image_dict.get('public',"yes")=="yes",
                            container_format="bare", location=image_dict['location'], disk_format=disk_format)
                else: #local path
                    with open(image_dict['location']) as fimage:
                        new_image = self.glancev1.images.create(name=image_dict['name'], is_public=image_dict.get('public',"yes")=="yes",
                            container_format="bare", data=fimage, disk_format=disk_format)
                #insert metadata. We cannot use 'new_image.properties.setdefault' 
                #because nova and glance are "INDEPENDENT" and we are using nova for reading metadata
                new_image_nova=self.nova.images.find(id=new_image.id)
                new_image_nova.metadata.setdefault('location',image_dict['location'])
                metadata_to_load = image_dict.get('metadata')
                if metadata_to_load:
                    for k,v in yaml.load(metadata_to_load).iteritems():
                        new_image_nova.metadata.setdefault(k,v)
                return new_image.id
            except (nvExceptions.Conflict, ksExceptions.ClientException, nvExceptions.ClientException) as e:
                self._format_exception(e)
            except (HTTPException, gl1Exceptions.HTTPException, gl1Exceptions.CommunicationError, ConnectionError) as e:
                if retry==max_retries:
                    continue
                self._format_exception(e)
            except IOError as e:  #can not open the file
                raise vimconn.vimconnConnectionException(type(e).__name__ + ": " + str(e)+ " for " + image_dict['location'],
                                                         http_code=vimconn.HTTP_Bad_Request)

    def delete_image(self, image_id):
        '''Deletes a tenant image from openstack VIM. Returns the old id
        '''
        try:
            self._reload_connection()
            self.nova.images.delete(image_id)
            return image_id
        except (nvExceptions.NotFound, ksExceptions.ClientException, nvExceptions.ClientException, gl1Exceptions.CommunicationError, ConnectionError) as e: #TODO remove
            self._format_exception(e)

    def get_image_id_from_path(self, path):
        '''Get the image id from image path in the VIM database. Returns the image_id'''
        try:
            self._reload_connection()
            images = self.nova.images.list()
            for image in images:
                if image.metadata.get("location")==path:
                    return image.id
            raise vimconn.vimconnNotFoundException("image with location '{}' not found".format( path))
        except (ksExceptions.ClientException, nvExceptions.ClientException, gl1Exceptions.CommunicationError, ConnectionError) as e:
            self._format_exception(e)

    def get_image_list(self, filter_dict={}):
        '''Obtain tenant images from VIM
        Filter_dict can be:
            id: image id
            name: image name
            checksum: image checksum
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        '''
        self.logger.debug("Getting image list from VIM filter: '%s'", str(filter_dict))
        try:
            self._reload_connection()
            filter_dict_os = filter_dict.copy()
            #First we filter by the available filter fields: name, id. The others are removed.
            filter_dict_os.pop('checksum', None)
            image_list = self.nova.images.findall(**filter_dict_os)
            if len(image_list) == 0:
                return []
            #Then we filter by the rest of filter fields: checksum
            filtered_list = []
            for image in image_list:
                try:
                    image_class = self.glance.images.get(image.id)
                    if 'checksum' not in filter_dict or image_class['checksum'] == filter_dict.get('checksum'):
                        filtered_list.append(image_class.copy())
                except gl1Exceptions.HTTPNotFound:
                    pass
            return filtered_list
        except (ksExceptions.ClientException, nvExceptions.ClientException, gl1Exceptions.CommunicationError, ConnectionError) as e:
            self._format_exception(e)

    def __wait_for_vm(self, vm_id, status):
        """wait until vm is in the desired status and return True.
        If the VM gets in ERROR status, return false.
        If the timeout is reached generate an exception"""
        elapsed_time = 0
        while elapsed_time < server_timeout:
            vm_status = self.nova.servers.get(vm_id).status
            if vm_status == status:
                return True
            if vm_status == 'ERROR':
                return False
            time.sleep(1)
            elapsed_time += 1

        # if we exceeded the timeout rollback
        if elapsed_time >= server_timeout:
            raise vimconn.vimconnException('Timeout waiting for instance ' + vm_id + ' to get ' + status,
                                           http_code=vimconn.HTTP_Request_Timeout)

    def _get_openstack_availablity_zones(self):
        """
        Get from openstack availability zones available
        :return:
        """
        try:
            openstack_availability_zone = self.nova.availability_zones.list()
            openstack_availability_zone = [str(zone.zoneName) for zone in openstack_availability_zone
                                           if zone.zoneName != 'internal']
            return openstack_availability_zone
        except Exception as e:
            return None

    def _set_availablity_zones(self):
        """
        Set vim availablity zone
        :return:
        """

        if 'availability_zone' in self.config:
            vim_availability_zones = self.config.get('availability_zone')
            if isinstance(vim_availability_zones, str):
                self.availability_zone = [vim_availability_zones]
            elif isinstance(vim_availability_zones, list):
                self.availability_zone = vim_availability_zones
        else:
            self.availability_zone = self._get_openstack_availablity_zones()

    def _get_vm_availability_zone(self, availability_zone_index, availability_zone_list):
        """
        Return thge availability zone to be used by the created VM.
        :return: The VIM availability zone to be used or None
        """
        if availability_zone_index is None:
            if not self.config.get('availability_zone'):
                return None
            elif isinstance(self.config.get('availability_zone'), str):
                return self.config['availability_zone']
            else:
                # TODO consider using a different parameter at config for default AV and AV list match
                return self.config['availability_zone'][0]

        vim_availability_zones = self.availability_zone
        # check if VIM offer enough availability zones describe in the VNFD
        if vim_availability_zones and len(availability_zone_list) <= len(vim_availability_zones):
            # check if all the names of NFV AV match VIM AV names
            match_by_index = False
            for av in availability_zone_list:
                if av not in vim_availability_zones:
                    match_by_index = True
                    break
            if match_by_index:
                return vim_availability_zones[availability_zone_index]
            else:
                return availability_zone_list[availability_zone_index]
        else:
            raise vimconn.vimconnConflictException("No enough availability zones at VIM for this deployment")

    def new_vminstance(self, name, description, start, image_id, flavor_id, net_list, cloud_config=None, disk_list=None,
                       availability_zone_index=None, availability_zone_list=None):
        """Adds a VM instance to VIM
        Params:
            start: indicates if VM must start or boot in pause mode. Ignored
            image_id,flavor_id: iamge and flavor uuid
            net_list: list of interfaces, each one is a dictionary with:
                name:
                net_id: network uuid to connect
                vpci: virtual vcpi to assign, ignored because openstack lack #TODO
                model: interface model, ignored #TODO
                mac_address: used for  SR-IOV ifaces #TODO for other types
                use: 'data', 'bridge',  'mgmt'
                type: 'virtual', 'PCI-PASSTHROUGH'('PF'), 'SR-IOV'('VF'), 'VFnotShared'
                vim_id: filled/added by this function
                floating_ip: True/False (or it can be None)
            'cloud_config': (optional) dictionary with:
            'key-pairs': (optional) list of strings with the public key to be inserted to the default user
            'users': (optional) list of users to be inserted, each item is a dict with:
                'name': (mandatory) user name,
                'key-pairs': (optional) list of strings with the public key to be inserted to the user
            'user-data': (optional) string is a text script to be passed directly to cloud-init
            'config-files': (optional). List of files to be transferred. Each item is a dict with:
                'dest': (mandatory) string with the destination absolute path
                'encoding': (optional, by default text). Can be one of:
                    'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                'content' (mandatory): string with the content of the file
                'permissions': (optional) string with file permissions, typically octal notation '0644'
                'owner': (optional) file owner, string with the format 'owner:group'
            'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
            'disk_list': (optional) list with additional disks to the VM. Each item is a dict with:
                'image_id': (optional). VIM id of an existing image. If not provided an empty disk must be mounted
                'size': (mandatory) string with the size of the disk in GB
            availability_zone_index: Index of availability_zone_list to use for this this VM. None if not AV required
            availability_zone_list: list of availability zones given by user in the VNFD descriptor.  Ignore if
                availability_zone_index is None
                #TODO ip, security groups
        Returns a tuple with the instance identifier and created_items or raises an exception on error
            created_items can be None or a dictionary where this method can include key-values that will be passed to
            the method delete_vminstance and action_vminstance. Can be used to store created ports, volumes, etc.
            Format is vimconnector dependent, but do not use nested dictionaries and a value of None should be the same
            as not present.
        """
        self.logger.debug("new_vminstance input: image='%s' flavor='%s' nics='%s'",image_id, flavor_id,str(net_list))
        try:
            server = None
            created_items = {}
            # metadata = {}
            net_list_vim = []
            external_network = []   # list of external networks to be connected to instance, later on used to create floating_ip
            no_secured_ports = []   # List of port-is with port-security disabled
            self._reload_connection()
            # metadata_vpci = {}   # For a specific neutron plugin
            block_device_mapping = None
            for net in net_list:
                if not net.get("net_id"):   # skip non connected iface
                    continue

                port_dict={
                    "network_id": net["net_id"],
                    "name": net.get("name"),
                    "admin_state_up": True
                }
                if net["type"]=="virtual":
                    pass
                    # if "vpci" in net:
                    #     metadata_vpci[ net["net_id"] ] = [[ net["vpci"], "" ]]
                elif net["type"] == "VF" or net["type"] == "SR-IOV":  # for VF
                    # if "vpci" in net:
                    #     if "VF" not in metadata_vpci:
                    #         metadata_vpci["VF"]=[]
                    #     metadata_vpci["VF"].append([ net["vpci"], "" ])
                    port_dict["binding:vnic_type"]="direct"
                    # VIO specific Changes
                    if self.vim_type == "VIO":
                        # Need to create port with port_security_enabled = False and no-security-groups
                        port_dict["port_security_enabled"]=False
                        port_dict["provider_security_groups"]=[]
                        port_dict["security_groups"]=[]
                else:   # For PT PCI-PASSTHROUGH
                    # VIO specific Changes
                    # Current VIO release does not support port with type 'direct-physical'
                    # So no need to create virtual port in case of PCI-device.
                    # Will update port_dict code when support gets added in next VIO release
                    if self.vim_type == "VIO":
                        raise vimconn.vimconnNotSupportedException(
                            "Current VIO release does not support full passthrough (PT)")
                    # if "vpci" in net:
                    #     if "PF" not in metadata_vpci:
                    #         metadata_vpci["PF"]=[]
                    #     metadata_vpci["PF"].append([ net["vpci"], "" ])
                    port_dict["binding:vnic_type"]="direct-physical"
                if not port_dict["name"]:
                    port_dict["name"]=name
                if net.get("mac_address"):
                    port_dict["mac_address"]=net["mac_address"]
                if net.get("ip_address"):
                    port_dict["fixed_ips"] = [{'ip_address': net["ip_address"]}]
                    # TODO add 'subnet_id': <subnet_id>
                new_port = self.neutron.create_port({"port": port_dict })
                created_items["port:" + str(new_port["port"]["id"])] = True
                net["mac_adress"] = new_port["port"]["mac_address"]
                net["vim_id"] = new_port["port"]["id"]
                # if try to use a network without subnetwork, it will return a emtpy list
                fixed_ips = new_port["port"].get("fixed_ips")
                if fixed_ips:
                    net["ip"] = fixed_ips[0].get("ip_address")
                else:
                    net["ip"] = None

                port = {"port-id": new_port["port"]["id"]}
                if float(self.nova.api_version.get_string()) >= 2.32:
                    port["tag"] = new_port["port"]["name"]
                net_list_vim.append(port)

                if net.get('floating_ip', False):
                    net['exit_on_floating_ip_error'] = True
                    external_network.append(net)
                elif net['use'] == 'mgmt' and self.config.get('use_floating_ip'):
                    net['exit_on_floating_ip_error'] = False
                    external_network.append(net)
                    net['floating_ip'] = self.config.get('use_floating_ip')

                # If port security is disabled when the port has not yet been attached to the VM, then all vm traffic is dropped.
                # As a workaround we wait until the VM is active and then disable the port-security
                if net.get("port_security") == False and not self.config.get("no_port_security_extension"):
                    no_secured_ports.append(new_port["port"]["id"])

            # if metadata_vpci:
            #     metadata = {"pci_assignement": json.dumps(metadata_vpci)}
            #     if len(metadata["pci_assignement"]) >255:
            #         #limit the metadata size
            #         #metadata["pci_assignement"] = metadata["pci_assignement"][0:255]
            #         self.logger.warn("Metadata deleted since it exceeds the expected length (255) ")
            #         metadata = {}

            self.logger.debug("name '%s' image_id '%s'flavor_id '%s' net_list_vim '%s' description '%s'",
                              name, image_id, flavor_id, str(net_list_vim), description)

            security_groups = self.config.get('security_groups')
            if type(security_groups) is str:
                security_groups = ( security_groups, )
            # cloud config
            config_drive, userdata = self._create_user_data(cloud_config)

            # Create additional volumes in case these are present in disk_list
            base_disk_index = ord('b')
            if disk_list != None:
                block_device_mapping = {}
                for disk in disk_list:
                    if 'image_id' in disk:
                        volume = self.cinder.volumes.create(size = disk['size'],name = name + '_vd' +
                                    chr(base_disk_index), imageRef = disk['image_id'])
                    else:
                        volume = self.cinder.volumes.create(size=disk['size'], name=name + '_vd' +
                                    chr(base_disk_index))
                    created_items["volume:" + str(volume.id)] = True
                    block_device_mapping['_vd' +  chr(base_disk_index)] = volume.id
                    base_disk_index += 1

                # Wait until volumes are with status available
                keep_waiting = True
                elapsed_time = 0
                while keep_waiting and elapsed_time < volume_timeout:
                    keep_waiting = False
                    for volume_id in block_device_mapping.itervalues():
                        if self.cinder.volumes.get(volume_id).status != 'available':
                            keep_waiting = True
                    if keep_waiting:
                        time.sleep(1)
                        elapsed_time += 1

                # If we exceeded the timeout rollback
                if elapsed_time >= volume_timeout:
                    raise vimconn.vimconnException('Timeout creating volumes for instance ' + name,
                                                   http_code=vimconn.HTTP_Request_Timeout)
            # get availability Zone
            vm_av_zone = self._get_vm_availability_zone(availability_zone_index, availability_zone_list)

            self.logger.debug("nova.servers.create({}, {}, {}, nics={}, security_groups={}, "
                              "availability_zone={}, key_name={}, userdata={}, config_drive={}, "
                              "block_device_mapping={})".format(name, image_id, flavor_id, net_list_vim,
                                                                security_groups, vm_av_zone, self.config.get('keypair'),
                                                                userdata, config_drive, block_device_mapping))
            server = self.nova.servers.create(name, image_id, flavor_id, nics=net_list_vim,
                                              security_groups=security_groups,
                                              availability_zone=vm_av_zone,
                                              key_name=self.config.get('keypair'),
                                              userdata=userdata,
                                              config_drive=config_drive,
                                              block_device_mapping=block_device_mapping
                                              )  # , description=description)

            vm_start_time = time.time()
            # Previously mentioned workaround to wait until the VM is active and then disable the port-security
            if no_secured_ports:
                self.__wait_for_vm(server.id, 'ACTIVE')

            for port_id in no_secured_ports:
                try:
                    self.neutron.update_port(port_id,
                                             {"port": {"port_security_enabled": False, "security_groups": None}})
                except Exception as e:
                    raise vimconn.vimconnException("It was not possible to disable port security for port {}".format(
                        port_id))
            # print "DONE :-)", server

            # pool_id = None
            if external_network:
                floating_ips = self.neutron.list_floatingips().get("floatingips", ())
            for floating_network in external_network:
                try:
                    assigned = False
                    while not assigned:
                        if floating_ips:
                            ip = floating_ips.pop(0)
                            if ip.get("port_id", False) or ip.get('tenant_id') != server.tenant_id:
                                continue
                            if isinstance(floating_network['floating_ip'], str):
                                if ip.get("floating_network_id") != floating_network['floating_ip']:
                                    continue
                            free_floating_ip = ip.get("floating_ip_address")
                        else:
                            if isinstance(floating_network['floating_ip'], str):
                                pool_id = floating_network['floating_ip']
                            else:
                                # Find the external network
                                external_nets = list()
                                for net in self.neutron.list_networks()['networks']:
                                    if net['router:external']:
                                            external_nets.append(net)

                                if len(external_nets) == 0:
                                    raise vimconn.vimconnException("Cannot create floating_ip automatically since no external "
                                                                   "network is present",
                                                                    http_code=vimconn.HTTP_Conflict)
                                if len(external_nets) > 1:
                                    raise vimconn.vimconnException("Cannot create floating_ip automatically since multiple "
                                                                   "external networks are present",
                                                                   http_code=vimconn.HTTP_Conflict)

                                pool_id = external_nets[0].get('id')
                            param = {'floatingip': {'floating_network_id': pool_id, 'tenant_id': server.tenant_id}}
                            try:
                                # self.logger.debug("Creating floating IP")
                                new_floating_ip = self.neutron.create_floatingip(param)
                                free_floating_ip = new_floating_ip['floatingip']['floating_ip_address']
                            except Exception as e:
                                raise vimconn.vimconnException(type(e).__name__ + ": Cannot create new floating_ip " +
                                                               str(e), http_code=vimconn.HTTP_Conflict)

                        fix_ip = floating_network.get('ip')
                        while not assigned:
                            try:
                                server.add_floating_ip(free_floating_ip, fix_ip)
                                assigned = True
                            except Exception as e:
                                # openstack need some time after VM creation to asign an IP. So retry if fails
                                vm_status = self.nova.servers.get(server.id).status
                                if vm_status != 'ACTIVE' and vm_status != 'ERROR':
                                    if time.time() - vm_start_time < server_timeout:
                                        time.sleep(5)
                                        continue
                                raise vimconn.vimconnException(
                                    "Cannot create floating_ip: {} {}".format(type(e).__name__, e),
                                    http_code=vimconn.HTTP_Conflict)

                except Exception as e:
                    if not floating_network['exit_on_floating_ip_error']:
                        self.logger.warn("Cannot create floating_ip. %s", str(e))
                        continue
                    raise

            return server.id, created_items
#        except nvExceptions.NotFound as e:
#            error_value=-vimconn.HTTP_Not_Found
#            error_text= "vm instance %s not found" % vm_id
#        except TypeError as e:
#            raise vimconn.vimconnException(type(e).__name__ + ": "+  str(e), http_code=vimconn.HTTP_Bad_Request)

        except Exception as e:
            server_id = None
            if server:
                server_id = server.id
            try:
                self.delete_vminstance(server_id, created_items)
            except Exception as e2:
                self.logger.error("new_vminstance rollback fail {}".format(e2))

            self._format_exception(e)

    def get_vminstance(self,vm_id):
        '''Returns the VM instance information from VIM'''
        #self.logger.debug("Getting VM from VIM")
        try:
            self._reload_connection()
            server = self.nova.servers.find(id=vm_id)
            #TODO parse input and translate to VIM format (openmano_schemas.new_vminstance_response_schema)
            return server.to_dict()
        except (ksExceptions.ClientException, nvExceptions.ClientException, nvExceptions.NotFound, ConnectionError) as e:
            self._format_exception(e)

    def get_vminstance_console(self,vm_id, console_type="vnc"):
        '''
        Get a console for the virtual machine
        Params:
            vm_id: uuid of the VM
            console_type, can be:
                "novnc" (by default), "xvpvnc" for VNC types, 
                "rdp-html5" for RDP types, "spice-html5" for SPICE types
        Returns dict with the console parameters:
                protocol: ssh, ftp, http, https, ...
                server:   usually ip address 
                port:     the http, ssh, ... port 
                suffix:   extra text, e.g. the http path and query string   
        '''
        self.logger.debug("Getting VM CONSOLE from VIM")
        try:
            self._reload_connection()
            server = self.nova.servers.find(id=vm_id)
            if console_type == None or console_type == "novnc":
                console_dict = server.get_vnc_console("novnc")
            elif console_type == "xvpvnc":
                console_dict = server.get_vnc_console(console_type)
            elif console_type == "rdp-html5":
                console_dict = server.get_rdp_console(console_type)
            elif console_type == "spice-html5":
                console_dict = server.get_spice_console(console_type)
            else:
                raise vimconn.vimconnException("console type '{}' not allowed".format(console_type), http_code=vimconn.HTTP_Bad_Request)

            console_dict1 = console_dict.get("console")
            if console_dict1:
                console_url = console_dict1.get("url")
                if console_url:
                    #parse console_url
                    protocol_index = console_url.find("//")
                    suffix_index = console_url[protocol_index+2:].find("/") + protocol_index+2
                    port_index = console_url[protocol_index+2:suffix_index].find(":") + protocol_index+2
                    if protocol_index < 0 or port_index<0 or suffix_index<0:
                        return -vimconn.HTTP_Internal_Server_Error, "Unexpected response from VIM"
                    console_dict={"protocol": console_url[0:protocol_index],
                                  "server":   console_url[protocol_index+2:port_index],
                                  "port":     console_url[port_index:suffix_index],
                                  "suffix":   console_url[suffix_index+1:]
                                  }
                    protocol_index += 2
                    return console_dict
            raise vimconn.vimconnUnexpectedResponse("Unexpected response from VIM")

        except (nvExceptions.NotFound, ksExceptions.ClientException, nvExceptions.ClientException, nvExceptions.BadRequest, ConnectionError) as e:
            self._format_exception(e)

    def delete_vminstance(self, vm_id, created_items=None):
        '''Removes a VM instance from VIM. Returns the old identifier
        '''
        #print "osconnector: Getting VM from VIM"
        if created_items == None:
            created_items = {}
        try:
            self._reload_connection()
            # delete VM ports attached to this networks before the virtual machine
            for k, v in created_items.items():
                if not v:  # skip already deleted
                    continue
                try:
                    k_item, _, k_id = k.partition(":")
                    if k_item == "port":
                        self.neutron.delete_port(k_id)
                except Exception as e:
                    self.logger.error("Error deleting port: {}: {}".format(type(e).__name__, e))

            # #commented because detaching the volumes makes the servers.delete not work properly ?!?
            # #dettach volumes attached
            # server = self.nova.servers.get(vm_id)
            # volumes_attached_dict = server._info['os-extended-volumes:volumes_attached']   #volume['id']
            # #for volume in volumes_attached_dict:
            # #    self.cinder.volumes.detach(volume['id'])

            if vm_id:
                self.nova.servers.delete(vm_id)

            # delete volumes. Although having detached, they should have in active status before deleting
            # we ensure in this loop
            keep_waiting = True
            elapsed_time = 0
            while keep_waiting and elapsed_time < volume_timeout:
                keep_waiting = False
                for k, v in created_items.items():
                    if not v:  # skip already deleted
                        continue
                    try:
                        k_item, _, k_id = k.partition(":")
                        if k_item == "volume":
                            if self.cinder.volumes.get(k_id).status != 'available':
                                keep_waiting = True
                            else:
                                self.cinder.volumes.delete(k_id)
                    except Exception as e:
                        self.logger.error("Error deleting volume: {}: {}".format(type(e).__name__, e))
                if keep_waiting:
                    time.sleep(1)
                    elapsed_time += 1
            return None
        except (nvExceptions.NotFound, ksExceptions.ClientException, nvExceptions.ClientException, ConnectionError) as e:
            self._format_exception(e)

    def refresh_vms_status(self, vm_list):
        '''Get the status of the virtual machines and their interfaces/ports
           Params: the list of VM identifiers
           Returns a dictionary with:
                vm_id:          #VIM id of this Virtual Machine
                    status:     #Mandatory. Text with one of:
                                #  DELETED (not found at vim)
                                #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...) 
                                #  OTHER (Vim reported other status not understood)
                                #  ERROR (VIM indicates an ERROR status)
                                #  ACTIVE, PAUSED, SUSPENDED, INACTIVE (not running), 
                                #  CREATING (on building process), ERROR
                                #  ACTIVE:NoMgmtIP (Active but any of its interface has an IP address
                                #
                    error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR 
                    vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
                    interfaces:
                     -  vim_info:         #Text with plain information obtained from vim (yaml.safe_dump)
                        mac_address:      #Text format XX:XX:XX:XX:XX:XX
                        vim_net_id:       #network id where this interface is connected
                        vim_interface_id: #interface/port VIM id
                        ip_address:       #null, or text with IPv4, IPv6 address
                        compute_node:     #identification of compute node where PF,VF interface is allocated
                        pci:              #PCI address of the NIC that hosts the PF,VF
                        vlan:             #physical VLAN used for VF
        '''
        vm_dict={}
        self.logger.debug("refresh_vms status: Getting tenant VM instance information from VIM")
        for vm_id in vm_list:
            vm={}
            try:
                vm_vim = self.get_vminstance(vm_id)
                if vm_vim['status'] in vmStatus2manoFormat:
                    vm['status']    =  vmStatus2manoFormat[ vm_vim['status'] ]
                else:
                    vm['status']    = "OTHER"
                    vm['error_msg'] = "VIM status reported " + vm_vim['status']
                try:
                    vm['vim_info']  = yaml.safe_dump(vm_vim, default_flow_style=True, width=256)
                except yaml.representer.RepresenterError:
                    vm['vim_info'] = str(vm_vim)
                vm["interfaces"] = []
                if vm_vim.get('fault'):
                    vm['error_msg'] = str(vm_vim['fault'])
                #get interfaces
                try:
                    self._reload_connection()
                    port_dict=self.neutron.list_ports(device_id=vm_id)
                    for port in port_dict["ports"]:
                        interface={}
                        try:
                            interface['vim_info'] = yaml.safe_dump(port, default_flow_style=True, width=256)
                        except yaml.representer.RepresenterError:
                            interface['vim_info'] = str(port)
                        interface["mac_address"] = port.get("mac_address")
                        interface["vim_net_id"] = port["network_id"]
                        interface["vim_interface_id"] = port["id"]
                        # check if OS-EXT-SRV-ATTR:host is there, 
                        # in case of non-admin credentials, it will be missing
                        if vm_vim.get('OS-EXT-SRV-ATTR:host'):
                            interface["compute_node"] = vm_vim['OS-EXT-SRV-ATTR:host']
                        interface["pci"] = None

                        # check if binding:profile is there, 
                        # in case of non-admin credentials, it will be missing
                        if port.get('binding:profile'):
                            if port['binding:profile'].get('pci_slot'):
                                # TODO: At the moment sr-iov pci addresses are converted to PF pci addresses by setting the slot to 0x00
                                # TODO: This is just a workaround valid for niantinc. Find a better way to do so
                                #   CHANGE DDDD:BB:SS.F to DDDD:BB:00.(F%2)   assuming there are 2 ports per nic
                                pci = port['binding:profile']['pci_slot']
                                # interface["pci"] = pci[:-4] + "00." + str(int(pci[-1]) % 2)
                                interface["pci"] = pci
                        interface["vlan"] = None
                        #if network is of type vlan and port is of type direct (sr-iov) then set vlan id
                        network = self.neutron.show_network(port["network_id"])
                        if network['network'].get('provider:network_type') == 'vlan' and \
                            port.get("binding:vnic_type") == "direct":
                            interface["vlan"] = network['network'].get('provider:segmentation_id')
                        ips=[]
                        #look for floating ip address
                        floating_ip_dict = self.neutron.list_floatingips(port_id=port["id"])
                        if floating_ip_dict.get("floatingips"):
                            ips.append(floating_ip_dict["floatingips"][0].get("floating_ip_address") )

                        for subnet in port["fixed_ips"]:
                            ips.append(subnet["ip_address"])
                        interface["ip_address"] = ";".join(ips)
                        vm["interfaces"].append(interface)
                except Exception as e:
                    self.logger.error("Error getting vm interface information " + type(e).__name__ + ": "+  str(e))
            except vimconn.vimconnNotFoundException as e:
                self.logger.error("Exception getting vm status: %s", str(e))
                vm['status'] = "DELETED"
                vm['error_msg'] = str(e)
            except vimconn.vimconnException as e:
                self.logger.error("Exception getting vm status: %s", str(e))
                vm['status'] = "VIM_ERROR"
                vm['error_msg'] = str(e)
            vm_dict[vm_id] = vm
        return vm_dict

    def action_vminstance(self, vm_id, action_dict, created_items={}):
        '''Send and action over a VM instance from VIM
        Returns None or the console dict if the action was successfully sent to the VIM'''
        self.logger.debug("Action over VM '%s': %s", vm_id, str(action_dict))
        try:
            self._reload_connection()
            server = self.nova.servers.find(id=vm_id)
            if "start" in action_dict:
                if action_dict["start"]=="rebuild":
                    server.rebuild()
                else:
                    if server.status=="PAUSED":
                        server.unpause()
                    elif server.status=="SUSPENDED":
                        server.resume()
                    elif server.status=="SHUTOFF":
                        server.start()
            elif "pause" in action_dict:
                server.pause()
            elif "resume" in action_dict:
                server.resume()
            elif "shutoff" in action_dict or "shutdown" in action_dict:
                server.stop()
            elif "forceOff" in action_dict:
                server.stop() #TODO
            elif "terminate" in action_dict:
                server.delete()
            elif "createImage" in action_dict:
                server.create_image()
                #"path":path_schema,
                #"description":description_schema,
                #"name":name_schema,
                #"metadata":metadata_schema,
                #"imageRef": id_schema,
                #"disk": {"oneOf":[{"type": "null"}, {"type":"string"}] },
            elif "rebuild" in action_dict:
                server.rebuild(server.image['id'])
            elif "reboot" in action_dict:
                server.reboot() #reboot_type='SOFT'
            elif "console" in action_dict:
                console_type = action_dict["console"]
                if console_type == None or console_type == "novnc":
                    console_dict = server.get_vnc_console("novnc")
                elif console_type == "xvpvnc":
                    console_dict = server.get_vnc_console(console_type)
                elif console_type == "rdp-html5":
                    console_dict = server.get_rdp_console(console_type)
                elif console_type == "spice-html5":
                    console_dict = server.get_spice_console(console_type)
                else:
                    raise vimconn.vimconnException("console type '{}' not allowed".format(console_type),
                                                   http_code=vimconn.HTTP_Bad_Request)
                try:
                    console_url = console_dict["console"]["url"]
                    #parse console_url
                    protocol_index = console_url.find("//")
                    suffix_index = console_url[protocol_index+2:].find("/") + protocol_index+2
                    port_index = console_url[protocol_index+2:suffix_index].find(":") + protocol_index+2
                    if protocol_index < 0 or port_index<0 or suffix_index<0:
                        raise vimconn.vimconnException("Unexpected response from VIM " + str(console_dict))
                    console_dict2={"protocol": console_url[0:protocol_index],
                                  "server":   console_url[protocol_index+2 : port_index],
                                  "port":     int(console_url[port_index+1 : suffix_index]),
                                  "suffix":   console_url[suffix_index+1:]
                                  }
                    return console_dict2
                except Exception as e:
                    raise vimconn.vimconnException("Unexpected response from VIM " + str(console_dict))

            return None
        except (ksExceptions.ClientException, nvExceptions.ClientException, nvExceptions.NotFound, ConnectionError) as e:
            self._format_exception(e)
        #TODO insert exception vimconn.HTTP_Unauthorized

    ####### VIO Specific Changes #########
    def _genrate_vlanID(self):
        """
         Method to get unused vlanID
            Args:
                None
            Returns:
                vlanID
        """
        #Get used VLAN IDs
        usedVlanIDs = []
        networks = self.get_network_list()
        for net in networks:
            if net.get('provider:segmentation_id'):
                usedVlanIDs.append(net.get('provider:segmentation_id'))
        used_vlanIDs = set(usedVlanIDs)

        #find unused VLAN ID
        for vlanID_range in self.config.get('dataplane_net_vlan_range'):
            try:
                start_vlanid , end_vlanid = map(int, vlanID_range.replace(" ", "").split("-"))
                for vlanID in xrange(start_vlanid, end_vlanid + 1):
                    if vlanID not in used_vlanIDs:
                        return vlanID
            except Exception as exp:
                raise vimconn.vimconnException("Exception {} occurred while generating VLAN ID.".format(exp))
        else:
            raise vimconn.vimconnConflictException("Unable to create the SRIOV VLAN network."\
                " All given Vlan IDs {} are in use.".format(self.config.get('dataplane_net_vlan_range')))


    def _validate_vlan_ranges(self, dataplane_net_vlan_range):
        """
        Method to validate user given vlanID ranges
            Args:  None
            Returns: None
        """
        for vlanID_range in dataplane_net_vlan_range:
            vlan_range = vlanID_range.replace(" ", "")
            #validate format
            vlanID_pattern = r'(\d)*-(\d)*$'
            match_obj = re.match(vlanID_pattern, vlan_range)
            if not match_obj:
                raise vimconn.vimconnConflictException("Invalid dataplane_net_vlan_range {}.You must provide "\
                "'dataplane_net_vlan_range' in format [start_ID - end_ID].".format(vlanID_range))

            start_vlanid , end_vlanid = map(int,vlan_range.split("-"))
            if start_vlanid <= 0 :
                raise vimconn.vimconnConflictException("Invalid dataplane_net_vlan_range {}."\
                "Start ID can not be zero. For VLAN "\
                "networks valid IDs are 1 to 4094 ".format(vlanID_range))
            if end_vlanid > 4094 :
                raise vimconn.vimconnConflictException("Invalid dataplane_net_vlan_range {}."\
                "End VLAN ID can not be greater than 4094. For VLAN "\
                "networks valid IDs are 1 to 4094 ".format(vlanID_range))

            if start_vlanid > end_vlanid:
                raise vimconn.vimconnConflictException("Invalid dataplane_net_vlan_range {}."\
                    "You must provide a 'dataplane_net_vlan_range' in format start_ID - end_ID and "\
                    "start_ID < end_ID ".format(vlanID_range))

#NOT USED FUNCTIONS

    def new_external_port(self, port_data):
        #TODO openstack if needed
        '''Adds a external port to VIM'''
        '''Returns the port identifier'''
        return -vimconn.HTTP_Internal_Server_Error, "osconnector.new_external_port() not implemented"

    def connect_port_network(self, port_id, network_id, admin=False):
        #TODO openstack if needed
        '''Connects a external port to a network'''
        '''Returns status code of the VIM response'''
        return -vimconn.HTTP_Internal_Server_Error, "osconnector.connect_port_network() not implemented"

    def new_user(self, user_name, user_passwd, tenant_id=None):
        '''Adds a new user to openstack VIM'''
        '''Returns the user identifier'''
        self.logger.debug("osconnector: Adding a new user to VIM")
        try:
            self._reload_connection()
            user=self.keystone.users.create(user_name, user_passwd, tenant_id=tenant_id)
            #self.keystone.tenants.add_user(self.k_creds["username"], #role)
            return user.id
        except ksExceptions.ConnectionError as e:
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        except ksExceptions.ClientException as e: #TODO remove
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        #TODO insert exception vimconn.HTTP_Unauthorized
        #if reaching here is because an exception
        self.logger.debug("new_user " + error_text)
        return error_value, error_text

    def delete_user(self, user_id):
        '''Delete a user from openstack VIM'''
        '''Returns the user identifier'''
        if self.debug:
            print("osconnector: Deleting  a  user from VIM")
        try:
            self._reload_connection()
            self.keystone.users.delete(user_id)
            return 1, user_id
        except ksExceptions.ConnectionError as e:
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        except ksExceptions.NotFound as e:
            error_value=-vimconn.HTTP_Not_Found
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        except ksExceptions.ClientException as e: #TODO remove
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        #TODO insert exception vimconn.HTTP_Unauthorized
        #if reaching here is because an exception
            self.logger.debug("delete_tenant " + error_text)
        return error_value, error_text

    def get_hosts_info(self):
        '''Get the information of deployed hosts
        Returns the hosts content'''
        if self.debug:
            print("osconnector: Getting Host info from VIM")
        try:
            h_list=[]
            self._reload_connection()
            hypervisors = self.nova.hypervisors.list()
            for hype in hypervisors:
                h_list.append( hype.to_dict() )
            return 1, {"hosts":h_list}
        except nvExceptions.NotFound as e:
            error_value=-vimconn.HTTP_Not_Found
            error_text= (str(e) if len(e.args)==0 else str(e.args[0]))
        except (ksExceptions.ClientException, nvExceptions.ClientException) as e:
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        #TODO insert exception vimconn.HTTP_Unauthorized
        #if reaching here is because an exception
        self.logger.debug("get_hosts_info " + error_text)
        return error_value, error_text

    def get_hosts(self, vim_tenant):
        '''Get the hosts and deployed instances
        Returns the hosts content'''
        r, hype_dict = self.get_hosts_info()
        if r<0:
            return r, hype_dict
        hypervisors = hype_dict["hosts"]
        try:
            servers = self.nova.servers.list()
            for hype in hypervisors:
                for server in servers:
                    if server.to_dict()['OS-EXT-SRV-ATTR:hypervisor_hostname']==hype['hypervisor_hostname']:
                        if 'vm' in hype:
                            hype['vm'].append(server.id)
                        else:
                            hype['vm'] = [server.id]
            return 1, hype_dict
        except nvExceptions.NotFound as e:
            error_value=-vimconn.HTTP_Not_Found
            error_text= (str(e) if len(e.args)==0 else str(e.args[0]))
        except (ksExceptions.ClientException, nvExceptions.ClientException) as e:
            error_value=-vimconn.HTTP_Bad_Request
            error_text= type(e).__name__ + ": "+  (str(e) if len(e.args)==0 else str(e.args[0]))
        #TODO insert exception vimconn.HTTP_Unauthorized
        #if reaching here is because an exception
        self.logger.debug("get_hosts " + error_text)
        return error_value, error_text

    def new_classification(self, name, ctype, definition):
        self.logger.debug(
            'Adding a new (Traffic) Classification to VIM, named %s', name)
        try:
            new_class = None
            self._reload_connection()
            if ctype not in supportedClassificationTypes:
                raise vimconn.vimconnNotSupportedException(
                        'OpenStack VIM connector doesn\'t support provided '
                        'Classification Type {}, supported ones are: '
                        '{}'.format(ctype, supportedClassificationTypes))
            if not self._validate_classification(ctype, definition):
                raise vimconn.vimconnException(
                    'Incorrect Classification definition '
                    'for the type specified.')
            classification_dict = definition
            classification_dict['name'] = name

            new_class = self.neutron.create_sfc_flow_classifier(
                {'flow_classifier': classification_dict})
            return new_class['flow_classifier']['id']
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            self.logger.error(
                'Creation of Classification failed.')
            self._format_exception(e)

    def get_classification(self, class_id):
        self.logger.debug(" Getting Classification %s from VIM", class_id)
        filter_dict = {"id": class_id}
        class_list = self.get_classification_list(filter_dict)
        if len(class_list) == 0:
            raise vimconn.vimconnNotFoundException(
                "Classification '{}' not found".format(class_id))
        elif len(class_list) > 1:
            raise vimconn.vimconnConflictException(
                "Found more than one Classification with this criteria")
        classification = class_list[0]
        return classification

    def get_classification_list(self, filter_dict={}):
        self.logger.debug("Getting Classifications from VIM filter: '%s'",
                          str(filter_dict))
        try:
            filter_dict_os = filter_dict.copy()
            self._reload_connection()
            if self.api_version3 and "tenant_id" in filter_dict_os:
                filter_dict_os['project_id'] = filter_dict_os.pop('tenant_id')
            classification_dict = self.neutron.list_sfc_flow_classifiers(
                **filter_dict_os)
            classification_list = classification_dict["flow_classifiers"]
            self.__classification_os2mano(classification_list)
            return classification_list
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def delete_classification(self, class_id):
        self.logger.debug("Deleting Classification '%s' from VIM", class_id)
        try:
            self._reload_connection()
            self.neutron.delete_sfc_flow_classifier(class_id)
            return class_id
        except (neExceptions.ConnectionFailed, neExceptions.NeutronException,
                ksExceptions.ClientException, neExceptions.NeutronException,
                ConnectionError) as e:
            self._format_exception(e)

    def new_sfi(self, name, ingress_ports, egress_ports, sfc_encap=True):
        self.logger.debug(
            "Adding a new Service Function Instance to VIM, named '%s'", name)
        try:
            new_sfi = None
            self._reload_connection()
            correlation = None
            if sfc_encap:
                correlation = 'nsh'
            if len(ingress_ports) != 1:
                raise vimconn.vimconnNotSupportedException(
                    "OpenStack VIM connector can only have "
                    "1 ingress port per SFI")
            if len(egress_ports) != 1:
                raise vimconn.vimconnNotSupportedException(
                    "OpenStack VIM connector can only have "
                    "1 egress port per SFI")
            sfi_dict = {'name': name,
                        'ingress': ingress_ports[0],
                        'egress': egress_ports[0],
                        'service_function_parameters': {
                            'correlation': correlation}}
            new_sfi = self.neutron.create_sfc_port_pair({'port_pair': sfi_dict})
            return new_sfi['port_pair']['id']
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            if new_sfi:
                try:
                    self.neutron.delete_sfc_port_pair(
                        new_sfi['port_pair']['id'])
                except Exception:
                    self.logger.error(
                        'Creation of Service Function Instance failed, with '
                        'subsequent deletion failure as well.')
            self._format_exception(e)

    def get_sfi(self, sfi_id):
        self.logger.debug(
            'Getting Service Function Instance %s from VIM', sfi_id)
        filter_dict = {"id": sfi_id}
        sfi_list = self.get_sfi_list(filter_dict)
        if len(sfi_list) == 0:
            raise vimconn.vimconnNotFoundException(
                "Service Function Instance '{}' not found".format(sfi_id))
        elif len(sfi_list) > 1:
            raise vimconn.vimconnConflictException(
                'Found more than one Service Function Instance '
                'with this criteria')
        sfi = sfi_list[0]
        return sfi

    def get_sfi_list(self, filter_dict={}):
        self.logger.debug("Getting Service Function Instances from "
                          "VIM filter: '%s'", str(filter_dict))
        try:
            self._reload_connection()
            filter_dict_os = filter_dict.copy()
            if self.api_version3 and "tenant_id" in filter_dict_os:
                filter_dict_os['project_id'] = filter_dict_os.pop('tenant_id')
            sfi_dict = self.neutron.list_sfc_port_pairs(**filter_dict_os)
            sfi_list = sfi_dict["port_pairs"]
            self.__sfi_os2mano(sfi_list)
            return sfi_list
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def delete_sfi(self, sfi_id):
        self.logger.debug("Deleting Service Function Instance '%s' "
                          "from VIM", sfi_id)
        try:
            self._reload_connection()
            self.neutron.delete_sfc_port_pair(sfi_id)
            return sfi_id
        except (neExceptions.ConnectionFailed, neExceptions.NeutronException,
                ksExceptions.ClientException, neExceptions.NeutronException,
                ConnectionError) as e:
            self._format_exception(e)

    def new_sf(self, name, sfis, sfc_encap=True):
        self.logger.debug("Adding a new Service Function to VIM, "
                          "named '%s'", name)
        try:
            new_sf = None
            self._reload_connection()
            # correlation = None
            # if sfc_encap:
            #     correlation = 'nsh'
            for instance in sfis:
                sfi = self.get_sfi(instance)
                if sfi.get('sfc_encap') != sfc_encap:
                    raise vimconn.vimconnNotSupportedException(
                        "OpenStack VIM connector requires all SFIs of the "
                        "same SF to share the same SFC Encapsulation")
            sf_dict = {'name': name,
                       'port_pairs': sfis}
            new_sf = self.neutron.create_sfc_port_pair_group({
                'port_pair_group': sf_dict})
            return new_sf['port_pair_group']['id']
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            if new_sf:
                try:
                    self.neutron.delete_sfc_port_pair_group(
                        new_sf['port_pair_group']['id'])
                except Exception:
                    self.logger.error(
                        'Creation of Service Function failed, with '
                        'subsequent deletion failure as well.')
            self._format_exception(e)

    def get_sf(self, sf_id):
        self.logger.debug("Getting Service Function %s from VIM", sf_id)
        filter_dict = {"id": sf_id}
        sf_list = self.get_sf_list(filter_dict)
        if len(sf_list) == 0:
            raise vimconn.vimconnNotFoundException(
                "Service Function '{}' not found".format(sf_id))
        elif len(sf_list) > 1:
            raise vimconn.vimconnConflictException(
                "Found more than one Service Function with this criteria")
        sf = sf_list[0]
        return sf

    def get_sf_list(self, filter_dict={}):
        self.logger.debug("Getting Service Function from VIM filter: '%s'",
                          str(filter_dict))
        try:
            self._reload_connection()
            filter_dict_os = filter_dict.copy()
            if self.api_version3 and "tenant_id" in filter_dict_os:
                filter_dict_os['project_id'] = filter_dict_os.pop('tenant_id')
            sf_dict = self.neutron.list_sfc_port_pair_groups(**filter_dict_os)
            sf_list = sf_dict["port_pair_groups"]
            self.__sf_os2mano(sf_list)
            return sf_list
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def delete_sf(self, sf_id):
        self.logger.debug("Deleting Service Function '%s' from VIM", sf_id)
        try:
            self._reload_connection()
            self.neutron.delete_sfc_port_pair_group(sf_id)
            return sf_id
        except (neExceptions.ConnectionFailed, neExceptions.NeutronException,
                ksExceptions.ClientException, neExceptions.NeutronException,
                ConnectionError) as e:
            self._format_exception(e)

    def new_sfp(self, name, classifications, sfs, sfc_encap=True, spi=None):
        self.logger.debug("Adding a new Service Function Path to VIM, "
                          "named '%s'", name)
        try:
            new_sfp = None
            self._reload_connection()
            # In networking-sfc the MPLS encapsulation is legacy
            # should be used when no full SFC Encapsulation is intended
            sfc_encap = 'mpls'
            if sfc_encap:
                correlation = 'nsh'
            sfp_dict = {'name': name,
                        'flow_classifiers': classifications,
                        'port_pair_groups': sfs,
                        'chain_parameters': {'correlation': correlation}}
            if spi:
                sfp_dict['chain_id'] = spi
            new_sfp = self.neutron.create_sfc_port_chain({'port_chain': sfp_dict})
            return new_sfp["port_chain"]["id"]
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            if new_sfp:
                try:
                    self.neutron.delete_sfc_port_chain(new_sfp['port_chain']['id'])
                except Exception:
                    self.logger.error(
                        'Creation of Service Function Path failed, with '
                        'subsequent deletion failure as well.')
            self._format_exception(e)

    def get_sfp(self, sfp_id):
        self.logger.debug(" Getting Service Function Path %s from VIM", sfp_id)
        filter_dict = {"id": sfp_id}
        sfp_list = self.get_sfp_list(filter_dict)
        if len(sfp_list) == 0:
            raise vimconn.vimconnNotFoundException(
                "Service Function Path '{}' not found".format(sfp_id))
        elif len(sfp_list) > 1:
            raise vimconn.vimconnConflictException(
                "Found more than one Service Function Path with this criteria")
        sfp = sfp_list[0]
        return sfp

    def get_sfp_list(self, filter_dict={}):
        self.logger.debug("Getting Service Function Paths from VIM filter: "
                          "'%s'", str(filter_dict))
        try:
            self._reload_connection()
            filter_dict_os = filter_dict.copy()
            if self.api_version3 and "tenant_id" in filter_dict_os:
                filter_dict_os['project_id'] = filter_dict_os.pop('tenant_id')
            sfp_dict = self.neutron.list_sfc_port_chains(**filter_dict_os)
            sfp_list = sfp_dict["port_chains"]
            self.__sfp_os2mano(sfp_list)
            return sfp_list
        except (neExceptions.ConnectionFailed, ksExceptions.ClientException,
                neExceptions.NeutronException, ConnectionError) as e:
            self._format_exception(e)

    def delete_sfp(self, sfp_id):
        self.logger.debug(
            "Deleting Service Function Path '%s' from VIM", sfp_id)
        try:
            self._reload_connection()
            self.neutron.delete_sfc_port_chain(sfp_id)
            return sfp_id
        except (neExceptions.ConnectionFailed, neExceptions.NeutronException,
                ksExceptions.ClientException, neExceptions.NeutronException,
                ConnectionError) as e:
            self._format_exception(e)
