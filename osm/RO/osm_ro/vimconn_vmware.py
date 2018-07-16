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

"""
vimconn_vmware implementation an Abstract class in order to interact with VMware  vCloud Director.
mbayramov@vmware.com
"""
from progressbar import Percentage, Bar, ETA, FileTransferSpeed, ProgressBar

import vimconn
import os
import traceback
import itertools
import requests
import ssl
import atexit

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

from xml.etree import ElementTree as XmlElementTree
from lxml import etree as lxmlElementTree

import yaml
from pyvcloud.vcd.client import BasicLoginCredentials,Client,VcdTaskException
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.org import Org
import re
from pyvcloud.vcd.vapp import VApp
from xml.sax.saxutils import escape
import logging
import json
import time
import uuid
import httplib
#For python3
#import http.client
import hashlib
import socket
import struct
import netaddr
import random

# global variable for vcd connector type
STANDALONE = 'standalone'

# key for flavor dicts
FLAVOR_RAM_KEY = 'ram'
FLAVOR_VCPUS_KEY = 'vcpus'
FLAVOR_DISK_KEY = 'disk'
DEFAULT_IP_PROFILE = {'dhcp_count':50,
                      'dhcp_enabled':True,
                      'ip_version':"IPv4"
                      }
# global variable for wait time
INTERVAL_TIME = 5
MAX_WAIT_TIME = 1800

API_VERSION = '5.9'

__author__ = "Mustafa Bayramov, Arpita Kate, Sachin Bhangare, Prakash Kasar"
__date__ = "$09-Mar-2018 11:09:29$"
__version__ = '0.2'

#     -1: "Could not be created",
#     0: "Unresolved",
#     1: "Resolved",
#     2: "Deployed",
#     3: "Suspended",
#     4: "Powered on",
#     5: "Waiting for user input",
#     6: "Unknown state",
#     7: "Unrecognized state",
#     8: "Powered off",
#     9: "Inconsistent state",
#     10: "Children do not all have the same status",
#     11: "Upload initiated, OVF descriptor pending",
#     12: "Upload initiated, copying contents",
#     13: "Upload initiated , disk contents pending",
#     14: "Upload has been quarantined",
#     15: "Upload quarantine period has expired"

# mapping vCD status to MANO
vcdStatusCode2manoFormat = {4: 'ACTIVE',
                            7: 'PAUSED',
                            3: 'SUSPENDED',
                            8: 'INACTIVE',
                            12: 'BUILD',
                            -1: 'ERROR',
                            14: 'DELETED'}

#
netStatus2manoFormat = {'ACTIVE': 'ACTIVE', 'PAUSED': 'PAUSED', 'INACTIVE': 'INACTIVE', 'BUILD': 'BUILD',
                        'ERROR': 'ERROR', 'DELETED': 'DELETED'
                        }

class vimconnector(vimconn.vimconnector):
    # dict used to store flavor in memory
    flavorlist = {}

    def __init__(self, uuid=None, name=None, tenant_id=None, tenant_name=None,
                 url=None, url_admin=None, user=None, passwd=None, log_level=None, config={}, persistent_info={}):
        """
        Constructor create vmware connector to vCloud director.

        By default construct doesn't validate connection state. So client can create object with None arguments.
        If client specified username , password and host and VDC name.  Connector initialize other missing attributes.

        a) It initialize organization UUID
        b) Initialize tenant_id/vdc ID.   (This information derived from tenant name)

        Args:
            uuid - is organization uuid.
            name - is organization name that must be presented in vCloud director.
            tenant_id - is VDC uuid it must be presented in vCloud director
            tenant_name - is VDC name.
            url - is hostname or ip address of vCloud director
            url_admin - same as above.
            user - is user that administrator for organization. Caller must make sure that
                    username has right privileges.

            password - is password for a user.

            VMware connector also requires PVDC administrative privileges and separate account.
            This variables must be passed via config argument dict contains keys

            dict['admin_username']
            dict['admin_password']
            config - Provide NSX and vCenter information

            Returns:
                Nothing.
        """

        vimconn.vimconnector.__init__(self, uuid, name, tenant_id, tenant_name, url,
                                      url_admin, user, passwd, log_level, config)

        self.logger = logging.getLogger('openmano.vim.vmware')
        self.logger.setLevel(10)
        self.persistent_info = persistent_info

        self.name = name
        self.id = uuid
        self.url = url
        self.url_admin = url_admin
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.user = user
        self.passwd = passwd
        self.config = config
        self.admin_password = None
        self.admin_user = None
        self.org_name = ""
        self.nsx_manager = None
        self.nsx_user = None
        self.nsx_password = None

        # Disable warnings from self-signed certificates.
        requests.packages.urllib3.disable_warnings()

        if tenant_name is not None:
            orgnameandtenant = tenant_name.split(":")
            if len(orgnameandtenant) == 2:
                self.tenant_name = orgnameandtenant[1]
                self.org_name = orgnameandtenant[0]
            else:
                self.tenant_name = tenant_name
        if "orgname" in config:
            self.org_name = config['orgname']

        if log_level:
            self.logger.setLevel(getattr(logging, log_level))

        try:
            self.admin_user = config['admin_username']
            self.admin_password = config['admin_password']
        except KeyError:
            raise vimconn.vimconnException(message="Error admin username or admin password is empty.")

        try:
            self.nsx_manager = config['nsx_manager']
            self.nsx_user = config['nsx_user']
            self.nsx_password = config['nsx_password']
        except KeyError:
            raise vimconn.vimconnException(message="Error: nsx manager or nsx user or nsx password is empty in Config")

        self.vcenter_ip = config.get("vcenter_ip", None)
        self.vcenter_port = config.get("vcenter_port", None)
        self.vcenter_user = config.get("vcenter_user", None)
        self.vcenter_password = config.get("vcenter_password", None)

# ############# Stub code for SRIOV #################
#         try:
#             self.dvs_name = config['dv_switch_name']
#         except KeyError:
#             raise vimconn.vimconnException(message="Error: distributed virtaul switch name is empty in Config")
#
#         self.vlanID_range = config.get("vlanID_range", None)

        self.org_uuid = None
        self.client = None

        if not url:
            raise vimconn.vimconnException('url param can not be NoneType')

        if not self.url_admin:  # try to use normal url
            self.url_admin = self.url

        logging.debug("UUID: {} name: {} tenant_id: {} tenant name {}".format(self.id, self.org_name,
                                                                              self.tenant_id, self.tenant_name))
        logging.debug("vcd url {} vcd username: {} vcd password: {}".format(self.url, self.user, self.passwd))
        logging.debug("vcd admin username {} vcd admin passowrd {}".format(self.admin_user, self.admin_password))

        # initialize organization
        if self.user is not None and self.passwd is not None and self.url:
            self.init_organization()

    def __getitem__(self, index):
        if index == 'name':
            return self.name
        if index == 'tenant_id':
            return self.tenant_id
        if index == 'tenant_name':
            return self.tenant_name
        elif index == 'id':
            return self.id
        elif index == 'org_name':
            return self.org_name
        elif index == 'org_uuid':
            return self.org_uuid
        elif index == 'user':
            return self.user
        elif index == 'passwd':
            return self.passwd
        elif index == 'url':
            return self.url
        elif index == 'url_admin':
            return self.url_admin
        elif index == "config":
            return self.config
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    def __setitem__(self, index, value):
        if index == 'name':
            self.name = value
        if index == 'tenant_id':
            self.tenant_id = value
        if index == 'tenant_name':
            self.tenant_name = value
        elif index == 'id':
            self.id = value
        elif index == 'org_name':
            self.org_name = value
        elif index == 'org_uuid':
            self.org_uuid = value
        elif index == 'user':
            self.user = value
        elif index == 'passwd':
            self.passwd = value
        elif index == 'url':
            self.url = value
        elif index == 'url_admin':
            self.url_admin = value
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    def connect_as_admin(self):
        """ Method connect as pvdc admin user to vCloud director.
            There are certain action that can be done only by provider vdc admin user.
            Organization creation / provider network creation etc.

            Returns:
                The return client object that latter can be used to connect to vcloud director as admin for provider vdc
        """

        self.logger.debug("Logging into vCD {} as admin.".format(self.org_name))

        try:
            host = self.url
            org = 'System'
            client_as_admin = Client(host, verify_ssl_certs=False)
            client_as_admin.set_credentials(BasicLoginCredentials(self.admin_user, org, self.admin_password))
        except Exception as e:
            raise vimconn.vimconnException(
                  "Can't connect to a vCloud director as: {} with exception {}".format(self.admin_user, e))

        return client_as_admin

    def connect(self):
        """ Method connect as normal user to vCloud director.

            Returns:
                The return client object that latter can be used to connect to vCloud director as admin for VDC
        """

        try:
            self.logger.debug("Logging into vCD {} as {} to datacenter {}.".format(self.org_name,
                                                                                      self.user,
                                                                                      self.org_name))
            host = self.url
            client = Client(host, verify_ssl_certs=False)
            client.set_credentials(BasicLoginCredentials(self.user, self.org_name, self.passwd))
        except:
            raise vimconn.vimconnConnectionException("Can't connect to a vCloud director org: "
                                                     "{} as user: {}".format(self.org_name, self.user))

        return client

    def init_organization(self):
        """ Method initialize organization UUID and VDC parameters.

            At bare minimum client must provide organization name that present in vCloud director and VDC.

            The VDC - UUID ( tenant_id) will be initialized at the run time if client didn't call constructor.
            The Org - UUID will be initialized at the run time if data center present in vCloud director.

            Returns:
                The return vca object that letter can be used to connect to vcloud direct as admin
        """
        client = self.connect()
        if not client:
            raise vimconn.vimconnConnectionException("Failed to connect vCD.")

        self.client = client
        try:
            if self.org_uuid is None:
                org_list = client.get_org_list()
                for org in org_list.Org:
                    # we set org UUID at the init phase but we can do it only when we have valid credential.
                    if org.get('name') == self.org_name:
                        self.org_uuid = org.get('href').split('/')[-1]
                        self.logger.debug("Setting organization UUID {}".format(self.org_uuid))
                        break
                else:
                    raise vimconn.vimconnException("Vcloud director organization {} not found".format(self.org_name))

                # if well good we require for org details
                org_details_dict = self.get_org(org_uuid=self.org_uuid)

                # we have two case if we want to initialize VDC ID or VDC name at run time
                # tenant_name provided but no tenant id
                if self.tenant_id is None and self.tenant_name is not None and 'vdcs' in org_details_dict:
                    vdcs_dict = org_details_dict['vdcs']
                    for vdc in vdcs_dict:
                        if vdcs_dict[vdc] == self.tenant_name:
                            self.tenant_id = vdc
                            self.logger.debug("Setting vdc uuid {} for organization UUID {}".format(self.tenant_id,
                                                                                                    self.org_name))
                            break
                    else:
                        raise vimconn.vimconnException("Tenant name indicated but not present in vcloud director.")
                    # case two we have tenant_id but we don't have tenant name so we find and set it.
                    if self.tenant_id is not None and self.tenant_name is None and 'vdcs' in org_details_dict:
                        vdcs_dict = org_details_dict['vdcs']
                        for vdc in vdcs_dict:
                            if vdc == self.tenant_id:
                                self.tenant_name = vdcs_dict[vdc]
                                self.logger.debug("Setting vdc uuid {} for organization UUID {}".format(self.tenant_id,
                                                                                                        self.org_name))
                                break
                        else:
                            raise vimconn.vimconnException("Tenant id indicated but not present in vcloud director")
            self.logger.debug("Setting organization uuid {}".format(self.org_uuid))
        except:
            self.logger.debug("Failed initialize organization UUID for org {}".format(self.org_name))
            self.logger.debug(traceback.format_exc())
            self.org_uuid = None

    def new_tenant(self, tenant_name=None, tenant_description=None):
        """ Method adds a new tenant to VIM with this name.
            This action requires access to create VDC action in vCloud director.

            Args:
                tenant_name is tenant_name to be created.
                tenant_description not used for this call

            Return:
                returns the tenant identifier in UUID format.
                If action is failed method will throw vimconn.vimconnException method
            """
        vdc_task = self.create_vdc(vdc_name=tenant_name)
        if vdc_task is not None:
            vdc_uuid, value = vdc_task.popitem()
            self.logger.info("Created new vdc {} and uuid: {}".format(tenant_name, vdc_uuid))
            return vdc_uuid
        else:
            raise vimconn.vimconnException("Failed create tenant {}".format(tenant_name))

    def delete_tenant(self, tenant_id=None):
        """ Delete a tenant from VIM
             Args:
                tenant_id is tenant_id to be deleted.

            Return:
                returns the tenant identifier in UUID format.
                If action is failed method will throw exception
        """
        vca = self.connect_as_admin()
        if not vca:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")

        if tenant_id is not None:
            if vca._session:
                #Get OrgVDC
                url_list = [self.url, '/api/vdc/', tenant_id]
                orgvdc_herf = ''.join(url_list)

                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']}
                response = self.perform_request(req_type='GET',
                                                url=orgvdc_herf,
                                                headers=headers)

                if response.status_code != requests.codes.ok:
                    self.logger.debug("delete_tenant():GET REST API call {} failed. "\
                                      "Return status code {}".format(orgvdc_herf,
                                                                     response.status_code))
                    raise vimconn.vimconnNotFoundException("Fail to get tenant {}".format(tenant_id))

                lxmlroot_respond = lxmlElementTree.fromstring(response.content)
                namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.iteritems() if prefix}
                #For python3
                #namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.items() if prefix}
                namespaces["xmlns"]= "http://www.vmware.com/vcloud/v1.5"
                vdc_remove_href = lxmlroot_respond.find("xmlns:Link[@rel='remove']",namespaces).attrib['href']
                vdc_remove_href = vdc_remove_href + '?recursive=true&force=true'

                response = self.perform_request(req_type='DELETE',
                                                url=vdc_remove_href,
                                                headers=headers)

                if response.status_code == 202:
                    time.sleep(5)
                    return tenant_id
                else:
                    self.logger.debug("delete_tenant(): DELETE REST API call {} failed. "\
                                      "Return status code {}".format(vdc_remove_href,
                                                                     response.status_code))
                    raise vimconn.vimconnException("Fail to delete tenant with ID {}".format(tenant_id))
        else:
            self.logger.debug("delete_tenant():Incorrect tenant ID  {}".format(tenant_id))
            raise vimconn.vimconnNotFoundException("Fail to get tenant {}".format(tenant_id))


    def get_tenant_list(self, filter_dict={}):
        """Obtain tenants of VIM
        filter_dict can contain the following keys:
            name: filter by tenant name
            id: filter by tenant uuid/id
            <other VIM specific>
        Returns the tenant list of dictionaries:
            [{'name':'<name>, 'id':'<id>, ...}, ...]

        """
        org_dict = self.get_org(self.org_uuid)
        vdcs_dict = org_dict['vdcs']

        vdclist = []
        try:
            for k in vdcs_dict:
                entry = {'name': vdcs_dict[k], 'id': k}
                # if caller didn't specify dictionary we return all tenants.
                if filter_dict is not None and filter_dict:
                    filtered_entry = entry.copy()
                    filtered_dict = set(entry.keys()) - set(filter_dict)
                    for unwanted_key in filtered_dict: del entry[unwanted_key]
                    if filter_dict == entry:
                        vdclist.append(filtered_entry)
                else:
                    vdclist.append(entry)
        except:
            self.logger.debug("Error in get_tenant_list()")
            self.logger.debug(traceback.format_exc())
            raise vimconn.vimconnException("Incorrect state. {}")

        return vdclist

    def new_network(self, net_name, net_type, ip_profile=None, shared=False):
        """Adds a tenant network to VIM
            net_name is the name
            net_type can be 'bridge','data'.'ptp'.
            ip_profile is a dict containing the IP parameters of the network
            shared is a boolean
        Returns the network identifier"""

        self.logger.debug("new_network tenant {} net_type {} ip_profile {} shared {}"
                          .format(net_name, net_type, ip_profile, shared))

        isshared = 'false'
        if shared:
            isshared = 'true'

# ############# Stub code for SRIOV #################
#         if net_type == "data" or net_type == "ptp":
#             if self.config.get('dv_switch_name') == None:
#                  raise vimconn.vimconnConflictException("You must provide 'dv_switch_name' at config value")
#             network_uuid = self.create_dvPort_group(net_name)

        network_uuid = self.create_network(network_name=net_name, net_type=net_type,
                                           ip_profile=ip_profile, isshared=isshared)
        if network_uuid is not None:
            return network_uuid
        else:
            raise vimconn.vimconnUnexpectedResponse("Failed create a new network {}".format(net_name))

    def get_vcd_network_list(self):
        """ Method available organization for a logged in tenant

            Returns:
                The return vca object that letter can be used to connect to vcloud direct as admin
        """

        self.logger.debug("get_vcd_network_list(): retrieving network list for vcd {}".format(self.tenant_name))

        if not self.tenant_name:
            raise vimconn.vimconnConnectionException("Tenant name is empty.")

        org, vdc = self.get_vdc_details()
        if vdc is None:
            raise vimconn.vimconnConnectionException("Can't retrieve information for a VDC {}".format(self.tenant_name))

        vdc_uuid = vdc.get('id').split(":")[3]
        if self.client._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
                response = self.perform_request(req_type='GET',
                                           url=vdc.get('href'),
                                               headers=headers)
        if response.status_code != 200:
            self.logger.error("Failed to get vdc content")
            raise vimconn.vimconnNotFoundException("Failed to get vdc content")
        else:
            content = XmlElementTree.fromstring(response.content)
 
        network_list = []
        try:
            for item in content:
                if item.tag.split('}')[-1] == 'AvailableNetworks':
                    for net in item:
                        response = self.perform_request(req_type='GET',
                                                   url=net.get('href'),
                                                       headers=headers)

                        if response.status_code != 200:
                            self.logger.error("Failed to get network content")
                            raise vimconn.vimconnNotFoundException("Failed to get network content")
                        else:
                            net_details = XmlElementTree.fromstring(response.content)

                            filter_dict = {}
                            net_uuid = net_details.get('id').split(":")
                            if len(net_uuid) != 4:
                                continue
                            else:
                                net_uuid = net_uuid[3]
                                # create dict entry
                                self.logger.debug("Adding  {} to a list vcd id {} network {}".format(net_uuid,
                                                                                                        vdc_uuid,
                                                                                         net_details.get('name')))
                                filter_dict["name"] = net_details.get('name')
                                filter_dict["id"] = net_uuid
                                if [i.text for i in net_details if i.tag.split('}')[-1] == 'IsShared'][0] == 'true':
                                    shared = True
                                else:
                                    shared = False
                                filter_dict["shared"] = shared
                                filter_dict["tenant_id"] = vdc_uuid
                                if net_details.get('status') == 1:
                                    filter_dict["admin_state_up"] = True
                                else:
                                    filter_dict["admin_state_up"] = False
                                filter_dict["status"] = "ACTIVE"
                                filter_dict["type"] = "bridge"
                                network_list.append(filter_dict)
                                self.logger.debug("get_vcd_network_list adding entry {}".format(filter_dict))
        except:
            self.logger.debug("Error in get_vcd_network_list", exc_info=True)
            pass

        self.logger.debug("get_vcd_network_list returning {}".format(network_list))
        return network_list

    def get_network_list(self, filter_dict={}):
        """Obtain tenant networks of VIM
        Filter_dict can be:
            name: network name  OR/AND
            id: network uuid    OR/AND
            shared: boolean     OR/AND
            tenant_id: tenant   OR/AND
            admin_state_up: boolean
            status: 'ACTIVE'

        [{key : value , key : value}]

        Returns the network list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        """

        self.logger.debug("get_network_list(): retrieving network list for vcd {}".format(self.tenant_name))

        if not self.tenant_name:
            raise vimconn.vimconnConnectionException("Tenant name is empty.")

        org, vdc = self.get_vdc_details()
        if vdc is None:
            raise vimconn.vimconnConnectionException("Can't retrieve information for a VDC {}.".format(self.tenant_name))

        try:
            vdcid = vdc.get('id').split(":")[3]

            if self.client._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
                response = self.perform_request(req_type='GET',
                                           url=vdc.get('href'),
                                               headers=headers)
            if response.status_code != 200:
                self.logger.error("Failed to get vdc content")
                raise vimconn.vimconnNotFoundException("Failed to get vdc content")
            else:
                content = XmlElementTree.fromstring(response.content)

            network_list = []
            for item in content:
                if item.tag.split('}')[-1] == 'AvailableNetworks':
                    for net in item:
                        response = self.perform_request(req_type='GET',
                                                   url=net.get('href'),
                                                       headers=headers)

                        if response.status_code != 200:
                            self.logger.error("Failed to get network content")
                            raise vimconn.vimconnNotFoundException("Failed to get network content")
                        else:
                            net_details = XmlElementTree.fromstring(response.content)

                            filter_entry = {}
                            net_uuid = net_details.get('id').split(":")
                            if len(net_uuid) != 4:
                                continue
                            else:
                                net_uuid = net_uuid[3] 
                                # create dict entry
                                self.logger.debug("Adding  {} to a list vcd id {} network {}".format(net_uuid,
                                                                                                        vdcid,
                                                                                         net_details.get('name')))
                                filter_entry["name"] = net_details.get('name')
                                filter_entry["id"] = net_uuid
                                if [i.text for i in net_details if i.tag.split('}')[-1] == 'IsShared'][0] == 'true':
                                    shared = True
                                else:
                                    shared = False
                                filter_entry["shared"] = shared
                                filter_entry["tenant_id"] = vdcid
                                if net_details.get('status') == 1:
                                    filter_entry["admin_state_up"] = True
                                else:
                                    filter_entry["admin_state_up"] = False
                                filter_entry["status"] = "ACTIVE"
                                filter_entry["type"] = "bridge"
                                filtered_entry = filter_entry.copy()

                                if filter_dict is not None and filter_dict:
                                    # we remove all the key : value we don't care and match only
                                    # respected field
                                    filtered_dict = set(filter_entry.keys()) - set(filter_dict)
                                    for unwanted_key in filtered_dict: del filter_entry[unwanted_key]
                                    if filter_dict == filter_entry:
                                        network_list.append(filtered_entry)
                                else:
                                    network_list.append(filtered_entry)
        except Exception as e:
            self.logger.debug("Error in get_network_list",exc_info=True)
            if isinstance(e, vimconn.vimconnException):
                raise
            else:
                raise vimconn.vimconnNotFoundException("Failed : Networks list not found {} ".format(e))

        self.logger.debug("Returning {}".format(network_list))
        return network_list

    def get_network(self, net_id):
        """Method obtains network details of net_id VIM network
           Return a dict with  the fields at filter_dict (see get_network_list) plus some VIM specific>}, ...]"""

        try:
            org, vdc = self.get_vdc_details()
            vdc_id = vdc.get('id').split(":")[3]
            if self.client._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
                response = self.perform_request(req_type='GET',
                                           url=vdc.get('href'),
                                               headers=headers)
            if response.status_code != 200:
                self.logger.error("Failed to get vdc content")
                raise vimconn.vimconnNotFoundException("Failed to get vdc content")
            else:
                content = XmlElementTree.fromstring(response.content)

            filter_dict = {}

            for item in content:
                if item.tag.split('}')[-1] == 'AvailableNetworks':
                    for net in item:
                        response = self.perform_request(req_type='GET',
                                                   url=net.get('href'),
                                                       headers=headers)

                        if response.status_code != 200:
                            self.logger.error("Failed to get network content")
                            raise vimconn.vimconnNotFoundException("Failed to get network content")
                        else:
                            net_details = XmlElementTree.fromstring(response.content)

                            vdc_network_id = net_details.get('id').split(":")
                            if len(vdc_network_id) == 4 and vdc_network_id[3] == net_id:
                                filter_dict["name"] = net_details.get('name')
                                filter_dict["id"] = vdc_network_id[3]
                                if [i.text for i in net_details if i.tag.split('}')[-1] == 'IsShared'][0] == 'true':
                                    shared = True
                                else:
                                    shared = False
                                filter_dict["shared"] = shared
                                filter_dict["tenant_id"] = vdc_id
                                if net_details.get('status') == 1:
                                    filter_dict["admin_state_up"] = True
                                else:
                                    filter_dict["admin_state_up"] = False
                                filter_dict["status"] = "ACTIVE"
                                filter_dict["type"] = "bridge"
                                self.logger.debug("Returning {}".format(filter_dict))
                                return filter_dict
                    else:
                        raise vimconn.vimconnNotFoundException("Network {} not found".format(net_id))
        except Exception as e:
            self.logger.debug("Error in get_network")
            self.logger.debug(traceback.format_exc())
            if isinstance(e, vimconn.vimconnException):
                raise
            else:
                raise vimconn.vimconnNotFoundException("Failed : Network not found {} ".format(e))

        return filter_dict

    def delete_network(self, net_id):
        """
            Method Deletes a tenant network from VIM, provide the network id.

            Returns the network identifier or raise an exception
        """

        # ############# Stub code for SRIOV #################
#         dvport_group = self.get_dvport_group(net_id)
#         if dvport_group:
#             #delete portgroup
#             status = self.destroy_dvport_group(net_id)
#             if status:
#                 # Remove vlanID from persistent info
#                 if net_id in self.persistent_info["used_vlanIDs"]:
#                     del self.persistent_info["used_vlanIDs"][net_id]
#
#                 return net_id

        vcd_network = self.get_vcd_network(network_uuid=net_id)
        if vcd_network is not None and vcd_network:
            if self.delete_network_action(network_uuid=net_id):
                return net_id
        else:
            raise vimconn.vimconnNotFoundException("Network {} not found".format(net_id))

    def refresh_nets_status(self, net_list):
        """Get the status of the networks
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

        """

        dict_entry = {}
        try:
            for net in net_list:
                errormsg = ''
                vcd_network = self.get_vcd_network(network_uuid=net)
                if vcd_network is not None and vcd_network:
                    if vcd_network['status'] == '1':
                        status = 'ACTIVE'
                    else:
                        status = 'DOWN'
                else:
                    status = 'DELETED'
                    errormsg = 'Network not found.'

                dict_entry[net] = {'status': status, 'error_msg': errormsg,
                                   'vim_info': yaml.safe_dump(vcd_network)}
        except:
            self.logger.debug("Error in refresh_nets_status")
            self.logger.debug(traceback.format_exc())

        return dict_entry

    def get_flavor(self, flavor_id):
        """Obtain flavor details from the  VIM
            Returns the flavor dict details {'id':<>, 'name':<>, other vim specific } #TODO to concrete
        """
        if flavor_id not in vimconnector.flavorlist:
            raise vimconn.vimconnNotFoundException("Flavor not found.")
        return vimconnector.flavorlist[flavor_id]

    def new_flavor(self, flavor_data):
        """Adds a tenant flavor to VIM
            flavor_data contains a dictionary with information, keys:
                name: flavor name
                ram: memory (cloud type) in MBytes
                vpcus: cpus (cloud type)
                extended: EPA parameters
                  - numas: #items requested in same NUMA
                        memory: number of 1G huge pages memory
                        paired-threads|cores|threads: number of paired hyperthreads, complete cores OR individual threads
                        interfaces: # passthrough(PT) or SRIOV interfaces attached to this numa
                          - name: interface name
                            dedicated: yes|no|yes:sriov;  for PT, SRIOV or only one SRIOV for the physical NIC
                            bandwidth: X Gbps; requested guarantee bandwidth
                            vpci: requested virtual PCI address
                disk: disk size
                is_public:
                 #TODO to concrete
        Returns the flavor identifier"""

        # generate a new uuid put to internal dict and return it.
        self.logger.debug("Creating new flavor - flavor_data: {}".format(flavor_data))
        new_flavor=flavor_data
        ram = flavor_data.get(FLAVOR_RAM_KEY, 1024)
        cpu = flavor_data.get(FLAVOR_VCPUS_KEY, 1)
        disk = flavor_data.get(FLAVOR_DISK_KEY, 0)

        if not isinstance(ram, int):
            raise vimconn.vimconnException("Non-integer value for ram")
        elif not isinstance(cpu, int):
            raise vimconn.vimconnException("Non-integer value for cpu")
        elif not isinstance(disk, int):
            raise vimconn.vimconnException("Non-integer value for disk")

        extended_flv = flavor_data.get("extended")
        if extended_flv:
            numas=extended_flv.get("numas")
            if numas:
                for numa in numas:
                    #overwrite ram and vcpus
                    ram = numa['memory']*1024
                    if 'paired-threads' in numa:
                        cpu = numa['paired-threads']*2
                    elif 'cores' in numa:
                        cpu = numa['cores']
                    elif 'threads' in numa:
                        cpu = numa['threads']

        new_flavor[FLAVOR_RAM_KEY] = ram
        new_flavor[FLAVOR_VCPUS_KEY] = cpu
        new_flavor[FLAVOR_DISK_KEY] = disk
        # generate a new uuid put to internal dict and return it.
        flavor_id = uuid.uuid4()
        vimconnector.flavorlist[str(flavor_id)] = new_flavor
        self.logger.debug("Created flavor - {} : {}".format(flavor_id, new_flavor))

        return str(flavor_id)

    def delete_flavor(self, flavor_id):
        """Deletes a tenant flavor from VIM identify by its id

           Returns the used id or raise an exception
        """
        if flavor_id not in vimconnector.flavorlist:
            raise vimconn.vimconnNotFoundException("Flavor not found.")

        vimconnector.flavorlist.pop(flavor_id, None)
        return flavor_id

    def new_image(self, image_dict):
        """
        Adds a tenant image to VIM
        Returns:
            200, image-id        if the image is created
            <0, message          if there is an error
        """

        return self.get_image_id_from_path(image_dict['location'])

    def delete_image(self, image_id):
        """
            Deletes a tenant image from VIM
            Args:
                image_id is ID of Image to be deleted
            Return:
                returns the image identifier in UUID format or raises an exception on error
        """
        conn = self.connect_as_admin()
        if not conn:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")
        # Get Catalog details
        url_list = [self.url, '/api/catalog/', image_id]
        catalog_herf = ''.join(url_list)

        headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                  'x-vcloud-authorization': conn._session.headers['x-vcloud-authorization']}

        response = self.perform_request(req_type='GET',
                                        url=catalog_herf,
                                        headers=headers) 

        if response.status_code != requests.codes.ok:
            self.logger.debug("delete_image():GET REST API call {} failed. "\
                              "Return status code {}".format(catalog_herf,
                                                             response.status_code))
            raise vimconn.vimconnNotFoundException("Fail to get image {}".format(image_id))

        lxmlroot_respond = lxmlElementTree.fromstring(response.content)
        namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.iteritems() if prefix}
        #For python3
        #namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.items() if prefix}
        namespaces["xmlns"]= "http://www.vmware.com/vcloud/v1.5"

        catalogItems_section = lxmlroot_respond.find("xmlns:CatalogItems",namespaces)
        catalogItems = catalogItems_section.iterfind("xmlns:CatalogItem",namespaces)
        for catalogItem in catalogItems:
            catalogItem_href = catalogItem.attrib['href']

            response = self.perform_request(req_type='GET',
                                        url=catalogItem_href,
                                        headers=headers)

            if response.status_code != requests.codes.ok:
                self.logger.debug("delete_image():GET REST API call {} failed. "\
                                  "Return status code {}".format(catalog_herf,
                                                                 response.status_code))
                raise vimconn.vimconnNotFoundException("Fail to get catalogItem {} for catalog {}".format(
                                                                                    catalogItem,
                                                                                    image_id))

            lxmlroot_respond = lxmlElementTree.fromstring(response.content)
            namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.iteritems() if prefix}
            #For python3
            #namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.items() if prefix}
            namespaces["xmlns"]= "http://www.vmware.com/vcloud/v1.5"
            catalogitem_remove_href = lxmlroot_respond.find("xmlns:Link[@rel='remove']",namespaces).attrib['href']

            #Remove catalogItem
            response = self.perform_request(req_type='DELETE',
                                        url=catalogitem_remove_href,
                                        headers=headers) 
            if response.status_code == requests.codes.no_content:
                self.logger.debug("Deleted Catalog item {}".format(catalogItem))
            else:
                raise vimconn.vimconnException("Fail to delete Catalog Item {}".format(catalogItem))

        #Remove catalog
        url_list = [self.url, '/api/admin/catalog/', image_id]
        catalog_remove_herf = ''.join(url_list)
        response = self.perform_request(req_type='DELETE',
                                        url=catalog_remove_herf,
                                        headers=headers)

        if response.status_code == requests.codes.no_content:
            self.logger.debug("Deleted Catalog {}".format(image_id))
            return image_id
        else:
            raise vimconn.vimconnException("Fail to delete Catalog {}".format(image_id))


    def catalog_exists(self, catalog_name, catalogs):
        """

        :param catalog_name:
        :param catalogs:
        :return:
        """
        for catalog in catalogs:
            if catalog['name'] == catalog_name:
                return True
        return False

    def create_vimcatalog(self, vca=None, catalog_name=None):
        """ Create new catalog entry in vCloud director.

            Args
                vca:  vCloud director.
                catalog_name catalog that client wish to create.   Note no validation done for a name.
                Client must make sure that provide valid string representation.

             Return (bool) True if catalog created.

        """
        try:
            result = vca.create_catalog(catalog_name, catalog_name)
            if result is not None:
                return True 
            catalogs = vca.list_catalogs()
        except:
            return False
        return self.catalog_exists(catalog_name, catalogs)

    # noinspection PyIncorrectDocstring
    def upload_ovf(self, vca=None, catalog_name=None, image_name=None, media_file_name=None,
                   description='', progress=False, chunk_bytes=128 * 1024):
        """
        Uploads a OVF file to a vCloud catalog

        :param chunk_bytes:
        :param progress:
        :param description:
        :param image_name:
        :param vca:
        :param catalog_name: (str): The name of the catalog to upload the media.
        :param media_file_name: (str): The name of the local media file to upload.
        :return: (bool) True if the media file was successfully uploaded, false otherwise.
        """
        os.path.isfile(media_file_name)
        statinfo = os.stat(media_file_name)

        #  find a catalog entry where we upload OVF.
        #  create vApp Template and check the status if vCD able to read OVF it will respond with appropirate
        #  status change.
        #  if VCD can parse OVF we upload VMDK file
        try:
            for catalog in vca.list_catalogs():
                if catalog_name != catalog['name']:
                    continue
                catalog_href = "{}/api/catalog/{}/action/upload".format(self.url, catalog['id'])
                data = """
                <UploadVAppTemplateParams name="{}" xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"><Description>{} vApp Template</Description></UploadVAppTemplateParams>
                """.format(catalog_name, description)

                if self.client:
                    headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
                    headers['Content-Type'] = 'application/vnd.vmware.vcloud.uploadVAppTemplateParams+xml'

                response = self.perform_request(req_type='POST',
                                                url=catalog_href,
                                                headers=headers,
                                                data=data)

                if response.status_code == requests.codes.created:
                    catalogItem = XmlElementTree.fromstring(response.content)
                    entity = [child for child in catalogItem if
                              child.get("type") == "application/vnd.vmware.vcloud.vAppTemplate+xml"][0]
                    href = entity.get('href')
                    template = href

                    response = self.perform_request(req_type='GET',
                                                    url=href,
                                                    headers=headers)

                    if response.status_code == requests.codes.ok:
                        headers['Content-Type'] = 'Content-Type text/xml'
                        result = re.search('rel="upload:default"\shref="(.*?\/descriptor.ovf)"',response.content)
                        if result:
                            transfer_href = result.group(1)

                        response = self.perform_request(req_type='PUT',
                                                    url=transfer_href,
                                                    headers=headers,
                                                    data=open(media_file_name, 'rb'))
                        if response.status_code != requests.codes.ok:
                            self.logger.debug(
                                "Failed create vApp template for catalog name {} and image {}".format(catalog_name,
                                                                                                      media_file_name))
                            return False

                    # TODO fix this with aync block
                    time.sleep(5)

                    self.logger.debug("vApp template for catalog name {} and image {}".format(catalog_name, media_file_name))

                    # uploading VMDK file
                    # check status of OVF upload and upload remaining files.
                    response = self.perform_request(req_type='GET',
                                                    url=template,
                                                    headers=headers)

                    if response.status_code == requests.codes.ok:
                        result = re.search('rel="upload:default"\s*href="(.*?vmdk)"',response.content)
                        if result:
                            link_href = result.group(1)
                        # we skip ovf since it already uploaded.
                        if 'ovf' in link_href:
                            continue
                        # The OVF file and VMDK must be in a same directory
                        head, tail = os.path.split(media_file_name)
                        file_vmdk = head + '/' + link_href.split("/")[-1]
                        if not os.path.isfile(file_vmdk):
                            return False
                        statinfo = os.stat(file_vmdk)
                        if statinfo.st_size == 0:
                            return False
                        hrefvmdk = link_href

                        if progress:
                            widgets = ['Uploading file: ', Percentage(), ' ', Bar(), ' ', ETA(), ' ',
                                           FileTransferSpeed()]
                            progress_bar = ProgressBar(widgets=widgets, maxval=statinfo.st_size).start()

                        bytes_transferred = 0
                        f = open(file_vmdk, 'rb')
                        while bytes_transferred < statinfo.st_size:
                            my_bytes = f.read(chunk_bytes)
                            if len(my_bytes) <= chunk_bytes:
                                headers['Content-Range'] = 'bytes %s-%s/%s' % (
                                    bytes_transferred, len(my_bytes) - 1, statinfo.st_size)
                                headers['Content-Length'] = str(len(my_bytes))
                                response = requests.put(url=hrefvmdk,
                                                         headers=headers,
                                                         data=my_bytes,
                                                         verify=False)
                                if response.status_code == requests.codes.ok:
                                    bytes_transferred += len(my_bytes)
                                    if progress:
                                        progress_bar.update(bytes_transferred)
                                else:
                                    self.logger.debug(
                                        'file upload failed with error: [%s] %s' % (response.status_code,
                                                                                        response.content))

                                    f.close()
                                    return False
                        f.close()
                        if progress:
                            progress_bar.finish()
                            time.sleep(10)
                    return True
                else:
                    self.logger.debug("Failed retrieve vApp template for catalog name {} for OVF {}".
                                      format(catalog_name, media_file_name))
                    return False
        except Exception as exp:
            self.logger.debug("Failed while uploading OVF to catalog {} for OVF file {} with Exception {}"
                .format(catalog_name,media_file_name, exp))
            raise vimconn.vimconnException(
                "Failed while uploading OVF to catalog {} for OVF file {} with Exception {}"
                .format(catalog_name,media_file_name, exp))

        self.logger.debug("Failed retrieve catalog name {} for OVF file {}".format(catalog_name, media_file_name))
        return False

    def upload_vimimage(self, vca=None, catalog_name=None, media_name=None, medial_file_name=None, progress=False):
        """Upload media file"""
        # TODO add named parameters for readability

        return self.upload_ovf(vca=vca, catalog_name=catalog_name, image_name=media_name.split(".")[0],
                               media_file_name=medial_file_name, description='medial_file_name', progress=progress)

    def validate_uuid4(self, uuid_string=None):
        """  Method validate correct format of UUID.

        Return: true if string represent valid uuid
        """
        try:
            val = uuid.UUID(uuid_string, version=4)
        except ValueError:
            return False
        return True

    def get_catalogid(self, catalog_name=None, catalogs=None):
        """  Method check catalog and return catalog ID in UUID format.

        Args
            catalog_name: catalog name as string
            catalogs:  list of catalogs.

        Return: catalogs uuid
        """

        for catalog in catalogs:
            if catalog['name'] == catalog_name:
                catalog_id = catalog['id']
                return catalog_id
        return None

    def get_catalogbyid(self, catalog_uuid=None, catalogs=None):
        """  Method check catalog and return catalog name lookup done by catalog UUID.

        Args
            catalog_name: catalog name as string
            catalogs:  list of catalogs.

        Return: catalogs name or None
        """

        if not self.validate_uuid4(uuid_string=catalog_uuid):
            return None

        for catalog in catalogs:
            catalog_id = catalog.get('id')
            if catalog_id == catalog_uuid:
                return catalog.get('name')
        return None

    def get_catalog_obj(self, catalog_uuid=None, catalogs=None):
        """  Method check catalog and return catalog name lookup done by catalog UUID.

        Args
            catalog_name: catalog name as string
            catalogs:  list of catalogs.

        Return: catalogs name or None
        """

        if not self.validate_uuid4(uuid_string=catalog_uuid):
            return None

        for catalog in catalogs:
            catalog_id = catalog.get('id')
            if catalog_id == catalog_uuid:
                return catalog
        return None

    def get_image_id_from_path(self, path=None, progress=False):
        """  Method upload OVF image to vCloud director.

        Each OVF image represented as single catalog entry in vcloud director.
        The method check for existing catalog entry.  The check done by file name without file extension.

        if given catalog name already present method will respond with existing catalog uuid otherwise
        it will create new catalog entry and upload OVF file to newly created catalog.

        If method can't create catalog entry or upload a file it will throw exception.

        Method accept boolean flag progress that will output progress bar. It useful method
        for standalone upload use case. In case to test large file upload.

        Args
            path: - valid path to OVF file.
            progress - boolean progress bar show progress bar.

        Return: if image uploaded correct method will provide image catalog UUID.
        """

        if not path:
            raise vimconn.vimconnException("Image path can't be None.")

        if not os.path.isfile(path):
            raise vimconn.vimconnException("Can't read file. File not found.")

        if not os.access(path, os.R_OK):
            raise vimconn.vimconnException("Can't read file. Check file permission to read.")

        self.logger.debug("get_image_id_from_path() client requesting {} ".format(path))

        dirpath, filename = os.path.split(path)
        flname, file_extension = os.path.splitext(path)
        if file_extension != '.ovf':
            self.logger.debug("Wrong file extension {} connector support only OVF container.".format(file_extension))
            raise vimconn.vimconnException("Wrong container.  vCloud director supports only OVF.")

        catalog_name = os.path.splitext(filename)[0]
        catalog_md5_name = hashlib.md5(path).hexdigest()
        self.logger.debug("File name {} Catalog Name {} file path {} "
                          "vdc catalog name {}".format(filename, catalog_name, path, catalog_md5_name))

        try:
            org,vdc = self.get_vdc_details()
            catalogs = org.list_catalogs()
        except Exception as exp:
            self.logger.debug("Failed get catalogs() with Exception {} ".format(exp))
            raise vimconn.vimconnException("Failed get catalogs() with Exception {} ".format(exp))

        if len(catalogs) == 0:
            self.logger.info("Creating a new catalog entry {} in vcloud director".format(catalog_name))
            result = self.create_vimcatalog(org, catalog_md5_name)
            if not result:
                raise vimconn.vimconnException("Failed create new catalog {} ".format(catalog_md5_name))

            result = self.upload_vimimage(vca=org, catalog_name=catalog_md5_name,
                                          media_name=filename, medial_file_name=path, progress=progress)
            if not result:
                raise vimconn.vimconnException("Failed create vApp template for catalog {} ".format(catalog_name))
            return self.get_catalogid(catalog_name, catalogs)
        else:
            for catalog in catalogs:
                # search for existing catalog if we find same name we return ID
                # TODO optimize this
                if catalog['name'] == catalog_md5_name:
                    self.logger.debug("Found existing catalog entry for {} "
                                      "catalog id {}".format(catalog_name,
                                                             self.get_catalogid(catalog_md5_name, catalogs)))
                    return self.get_catalogid(catalog_md5_name, catalogs)

        # if we didn't find existing catalog we create a new one and upload image.
        self.logger.debug("Creating new catalog entry {} - {}".format(catalog_name, catalog_md5_name))
        result = self.create_vimcatalog(org, catalog_md5_name)
        if not result:
            raise vimconn.vimconnException("Failed create new catalog {} ".format(catalog_md5_name))

        result = self.upload_vimimage(vca=org, catalog_name=catalog_md5_name,
                                      media_name=filename, medial_file_name=path, progress=progress)
        if not result:
            raise vimconn.vimconnException("Failed create vApp template for catalog {} ".format(catalog_md5_name))

        return self.get_catalogid(catalog_md5_name, org.list_catalogs())

    def get_image_list(self, filter_dict={}):
        '''Obtain tenant images from VIM
        Filter_dict can be:
            name: image name
            id: image uuid
            checksum: image checksum
            location: image path
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        '''

        try:
            org, vdc = self.get_vdc_details()
            image_list = []
            catalogs = org.list_catalogs()
            if len(catalogs) == 0:
                return image_list
            else:
                for catalog in catalogs:
                    catalog_uuid = catalog.get('id')
                    name = catalog.get('name')
                    filtered_dict = {}
                    if filter_dict.get("name") and filter_dict["name"] != name:
                        continue
                    if filter_dict.get("id") and filter_dict["id"] != catalog_uuid:
                        continue
                    filtered_dict ["name"] = name
                    filtered_dict ["id"] = catalog_uuid
                    image_list.append(filtered_dict)

                self.logger.debug("List of already created catalog items: {}".format(image_list))
                return image_list
        except Exception as exp:
            raise vimconn.vimconnException("Exception occured while retriving catalog items {}".format(exp))

    def get_vappid(self, vdc=None, vapp_name=None):
        """ Method takes vdc object and vApp name and returns vapp uuid or None

        Args:
            vdc: The VDC object.
            vapp_name: is application vappp name identifier

        Returns:
                The return vApp name otherwise None
        """
        if vdc is None or vapp_name is None:
            return None
        # UUID has following format https://host/api/vApp/vapp-30da58a3-e7c7-4d09-8f68-d4c8201169cf
        try:
            refs = filter(lambda ref: ref.name == vapp_name and ref.type_ == 'application/vnd.vmware.vcloud.vApp+xml',
                          vdc.ResourceEntities.ResourceEntity)
            #For python3
            #refs = [ref for ref in vdc.ResourceEntities.ResourceEntity\
            #         if ref.name == vapp_name and ref.type_ == 'application/vnd.vmware.vcloud.vApp+xml']
            if len(refs) == 1:
                return refs[0].href.split("vapp")[1][1:]
        except Exception as e:
            self.logger.exception(e)
            return False
        return None

    def check_vapp(self, vdc=None, vapp_uuid=None):
        """ Method Method returns True or False if vapp deployed in vCloud director

            Args:
                vca: Connector to VCA
                vdc: The VDC object.
                vappid: vappid is application identifier

            Returns:
                The return True if vApp deployed
                :param vdc:
                :param vapp_uuid:
        """
        try:
            refs = filter(lambda ref:
                          ref.type_ == 'application/vnd.vmware.vcloud.vApp+xml',
                          vdc.ResourceEntities.ResourceEntity)
            #For python3
            #refs = [ref for ref in vdc.ResourceEntities.ResourceEntity\
            #         if ref.type_ == 'application/vnd.vmware.vcloud.vApp+xml']
            for ref in refs:
                vappid = ref.href.split("vapp")[1][1:]
                # find vapp with respected vapp uuid
                if vappid == vapp_uuid:
                    return True
        except Exception as e:
            self.logger.exception(e)
            return False
        return False

    def get_namebyvappid(self, vapp_uuid=None):
        """Method returns vApp name from vCD and lookup done by vapp_id.

        Args:
            vapp_uuid: vappid is application identifier

        Returns:
            The return vApp name otherwise None
        """
        try:
            if self.client and vapp_uuid:
                vapp_call = "{}/api/vApp/vapp-{}".format(self.url, vapp_uuid)
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                     'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}

                response = self.perform_request(req_type='GET',
                                                url=vapp_call,
                                                headers=headers) 
                #Retry login if session expired & retry sending request
                if response.status_code == 403:
                    response = self.retry_rest('GET', vapp_call)

                tree = XmlElementTree.fromstring(response.content)
                return tree.attrib['name']
        except Exception as e:
            self.logger.exception(e)
            return None
        return None

    def new_vminstance(self, name=None, description="", start=False, image_id=None, flavor_id=None, net_list=[],
                       cloud_config=None, disk_list=None, availability_zone_index=None, availability_zone_list=None):
        """Adds a VM instance to VIM
        Params:
            'start': (boolean) indicates if VM must start or created in pause mode.
            'image_id','flavor_id': image and flavor VIM id to use for the VM
            'net_list': list of interfaces, each one is a dictionary with:
                'name': (optional) name for the interface.
                'net_id': VIM network id where this interface must be connect to. Mandatory for type==virtual
                'vpci': (optional) virtual vPCI address to assign at the VM. Can be ignored depending on VIM capabilities
                'model': (optional and only have sense for type==virtual) interface model: virtio, e2000, ...
                'mac_address': (optional) mac address to assign to this interface
                #TODO: CHECK if an optional 'vlan' parameter is needed for VIMs when type if VF and net_id is not provided,
                    the VLAN tag to be used. In case net_id is provided, the internal network vlan is used for tagging VF
                'type': (mandatory) can be one of:
                    'virtual', in this case always connected to a network of type 'net_type=bridge'
                     'PCI-PASSTHROUGH' or 'PF' (passthrough): depending on VIM capabilities it can be connected to a data/ptp network ot it
                           can created unconnected
                     'SR-IOV' or 'VF' (SRIOV with VLAN tag): same as PF for network connectivity.
                     'VFnotShared'(SRIOV without VLAN tag) same as PF for network connectivity. VF where no other VFs
                            are allocated on the same physical NIC
                'bw': (optional) only for PF/VF/VFnotShared. Minimal Bandwidth required for the interface in GBPS
                'port_security': (optional) If False it must avoid any traffic filtering at this interface. If missing
                                or True, it must apply the default VIM behaviour
                After execution the method will add the key:
                'vim_id': must be filled/added by this method with the VIM identifier generated by the VIM for this
                        interface. 'net_list' is modified
            'cloud_config': (optional) dictionary with:
                'key-pairs': (optional) list of strings with the public key to be inserted to the default user
                'users': (optional) list of users to be inserted, each item is a dict with:
                    'name': (mandatory) user name,
                    'key-pairs': (optional) list of strings with the public key to be inserted to the user
                'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                    or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
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
        Returns a tuple with the instance identifier and created_items or raises an exception on error
            created_items can be None or a dictionary where this method can include key-values that will be passed to
            the method delete_vminstance and action_vminstance. Can be used to store created ports, volumes, etc.
            Format is vimconnector dependent, but do not use nested dictionaries and a value of None should be the same
            as not present.
        """
        self.logger.info("Creating new instance for entry {}".format(name))
        self.logger.debug("desc {} boot {} image_id: {} flavor_id: {} net_list: {} cloud_config {} disk_list {}".format(
                                    description, start, image_id, flavor_id, net_list, cloud_config, disk_list))

        #new vm name = vmname + tenant_id + uuid
        new_vm_name = [name, '-', str(uuid.uuid4())]
        vmname_andid = ''.join(new_vm_name)

        for net in net_list:
            if net['type'] == "SR-IOV" or net['type'] == "PCI-PASSTHROUGH":
                raise vimconn.vimconnNotSupportedException(
                      "Current vCD version does not support type : {}".format(net['type']))

        if len(net_list) > 10:
            raise vimconn.vimconnNotSupportedException(
                      "The VM hardware versions 7 and above support upto 10 NICs only")

        # if vm already deployed we return existing uuid
        # we check for presence of VDC, Catalog entry and Flavor.
        org, vdc = self.get_vdc_details()
        if vdc is None:
            raise vimconn.vimconnNotFoundException(
                "new_vminstance(): Failed create vApp {}: (Failed retrieve VDC information)".format(name))
        catalogs = org.list_catalogs()
        if catalogs is None:
            #Retry once, if failed by refreshing token
            self.get_token()
            org = Org(self.client, resource=self.client.get_org())
            catalogs = org.list_catalogs()
        if catalogs is None:
            raise vimconn.vimconnNotFoundException(
                "new_vminstance(): Failed create vApp {}: (Failed retrieve catalogs list)".format(name))

        catalog_hash_name = self.get_catalogbyid(catalog_uuid=image_id, catalogs=catalogs)
        if catalog_hash_name:
            self.logger.info("Found catalog entry {} for image id {}".format(catalog_hash_name, image_id))
        else:
            raise vimconn.vimconnNotFoundException("new_vminstance(): Failed create vApp {}: "
                                                   "(Failed retrieve catalog information {})".format(name, image_id))


        # Set vCPU and Memory based on flavor.
        vm_cpus = None
        vm_memory = None
        vm_disk = None
        numas = None

        if flavor_id is not None:
            if flavor_id not in vimconnector.flavorlist:
                raise vimconn.vimconnNotFoundException("new_vminstance(): Failed create vApp {}: "
                                                       "Failed retrieve flavor information "
                                                       "flavor id {}".format(name, flavor_id))
            else:
                try:
                    flavor = vimconnector.flavorlist[flavor_id]
                    vm_cpus = flavor[FLAVOR_VCPUS_KEY]
                    vm_memory = flavor[FLAVOR_RAM_KEY]
                    vm_disk = flavor[FLAVOR_DISK_KEY]
                    extended = flavor.get("extended", None)
                    if extended:
                        numas=extended.get("numas", None)

                except Exception as exp:
                    raise vimconn.vimconnException("Corrupted flavor. {}.Exception: {}".format(flavor_id, exp))

        # image upload creates template name as catalog name space Template.
        templateName = self.get_catalogbyid(catalog_uuid=image_id, catalogs=catalogs)
        power_on = 'false'
        if start:
            power_on = 'true'

        # client must provide at least one entry in net_list if not we report error
        #If net type is mgmt, then configure it as primary net & use its NIC index as primary NIC
        #If no mgmt, then the 1st NN in netlist is considered as primary net. 
        primary_net = None
        primary_netname = None
        network_mode = 'bridged'
        if net_list is not None and len(net_list) > 0:
            for net in net_list:
                if 'use' in net and net['use'] == 'mgmt' and not primary_net:
                    primary_net = net
            if primary_net is None:
                primary_net = net_list[0]

            try:
                primary_net_id = primary_net['net_id']
                network_dict = self.get_vcd_network(network_uuid=primary_net_id)
                if 'name' in network_dict:
                    primary_netname = network_dict['name']

            except KeyError:
                raise vimconn.vimconnException("Corrupted flavor. {}".format(primary_net))
        else:
            raise vimconn.vimconnUnexpectedResponse("new_vminstance(): Failed network list is empty.".format(name))

        # use: 'data', 'bridge', 'mgmt'
        # create vApp.  Set vcpu and ram based on flavor id.
        try:
            vdc_obj = VDC(self.client, resource=org.get_vdc(self.tenant_name))
            if not vdc_obj:
                raise vimconn.vimconnNotFoundException("new_vminstance(): Failed to get VDC object") 

            for retry in (1,2):
                items = org.get_catalog_item(catalog_hash_name, catalog_hash_name)
                catalog_items = [items.attrib]

                if len(catalog_items) == 1:
                    if self.client:
                        headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}

                    response = self.perform_request(req_type='GET',
                                                url=catalog_items[0].get('href'),
                                                headers=headers)
                    catalogItem = XmlElementTree.fromstring(response.content)
                    entity = [child for child in catalogItem if child.get("type") == "application/vnd.vmware.vcloud.vAppTemplate+xml"][0]
                    vapp_tempalte_href = entity.get("href")
        
                response = self.perform_request(req_type='GET',
                                                    url=vapp_tempalte_href,
                                                    headers=headers)    
                if response.status_code != requests.codes.ok:
                    self.logger.debug("REST API call {} failed. Return status code {}".format(vapp_tempalte_href,
                                                                                           response.status_code))
                else:
                    result = (response.content).replace("\n"," ")

                src = re.search('<Vm goldMaster="false"\sstatus="\d+"\sname="(.*?)"\s'
                                               'id="(\w+:\w+:vm:.*?)"\shref="(.*?)"\s'
                              'type="application/vnd\.vmware\.vcloud\.vm\+xml',result)
                if src:
                    vm_name = src.group(1)
                    vm_id = src.group(2)
                    vm_href = src.group(3)

                cpus = re.search('<rasd:Description>Number of Virtual CPUs</.*?>(\d+)</rasd:VirtualQuantity>',result).group(1)
                memory_mb = re.search('<rasd:Description>Memory Size</.*?>(\d+)</rasd:VirtualQuantity>',result).group(1)
                cores = re.search('<vmw:CoresPerSocket ovf:required.*?>(\d+)</vmw:CoresPerSocket>',result).group(1)

                headers['Content-Type'] = 'application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml' 
                vdc_id = vdc.get('id').split(':')[-1]
                instantiate_vapp_href = "{}/api/vdc/{}/action/instantiateVAppTemplate".format(self.url,
                                                                                                vdc_id) 
                data = """<?xml version="1.0" encoding="UTF-8"?>
                <InstantiateVAppTemplateParams
                xmlns="http://www.vmware.com/vcloud/v1.5"
                name="{}"
                deploy="false"
                powerOn="false"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1">
                <Description>Vapp instantiation</Description>
                <InstantiationParams>
                     <NetworkConfigSection>
                         <ovf:Info>Configuration parameters for logical networks</ovf:Info>
                         <NetworkConfig networkName="None">
                             <Configuration>
                                 <ParentNetwork href=""/>
                                 <FenceMode>bridged</FenceMode>
                             </Configuration>
                         </NetworkConfig>
                     </NetworkConfigSection>
                <LeaseSettingsSection
                type="application/vnd.vmware.vcloud.leaseSettingsSection+xml">
                <ovf:Info>Lease Settings</ovf:Info>
                <StorageLeaseInSeconds>172800</StorageLeaseInSeconds>
                <StorageLeaseExpiration>2014-04-25T08:08:16.438-07:00</StorageLeaseExpiration>
                </LeaseSettingsSection>
                </InstantiationParams>
                <Source href="{}"/> 
                <SourcedItem>
                <Source href="{}" id="{}" name="{}"
                type="application/vnd.vmware.vcloud.vm+xml"/>
                <VmGeneralParams>
                    <NeedsCustomization>false</NeedsCustomization>
                </VmGeneralParams>
                <InstantiationParams>
                      <NetworkConnectionSection>
                      <ovf:Info>Specifies the available VM network connections</ovf:Info>
                      <NetworkConnection network="{}">
                      <NetworkConnectionIndex>0</NetworkConnectionIndex>
                      <IsConnected>true</IsConnected>
                      <IpAddressAllocationMode>DHCP</IpAddressAllocationMode>     
                      </NetworkConnection> 
                      </NetworkConnectionSection><ovf:VirtualHardwareSection>
                      <ovf:Info>Virtual hardware requirements</ovf:Info>
                      <ovf:Item xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"
                      xmlns:vmw="http://www.vmware.com/schema/ovf">
                      <rasd:AllocationUnits>hertz * 10^6</rasd:AllocationUnits>
                      <rasd:Description>Number of Virtual CPUs</rasd:Description>
                      <rasd:ElementName xmlns:py="http://codespeak.net/lxml/objectify/pytype" py:pytype="str">{cpu} virtual CPU(s)</rasd:ElementName>
                      <rasd:InstanceID>4</rasd:InstanceID>      
                      <rasd:Reservation>0</rasd:Reservation>
                      <rasd:ResourceType>3</rasd:ResourceType>
                      <rasd:VirtualQuantity xmlns:py="http://codespeak.net/lxml/objectify/pytype" py:pytype="int">{cpu}</rasd:VirtualQuantity>
                      <rasd:Weight>0</rasd:Weight>
                      <vmw:CoresPerSocket ovf:required="false">{core}</vmw:CoresPerSocket>
                      </ovf:Item><ovf:Item xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData">
                      <rasd:AllocationUnits>byte * 2^20</rasd:AllocationUnits>
                      <rasd:Description>Memory Size</rasd:Description>
                      <rasd:ElementName xmlns:py="http://codespeak.net/lxml/objectify/pytype" py:pytype="str">{memory} MB of memory</rasd:ElementName>
                      <rasd:InstanceID>5</rasd:InstanceID>
                      <rasd:Reservation>0</rasd:Reservation>
                      <rasd:ResourceType>4</rasd:ResourceType>
                      <rasd:VirtualQuantity xmlns:py="http://codespeak.net/lxml/objectify/pytype" py:pytype="int">{memory}</rasd:VirtualQuantity>
                      <rasd:Weight>0</rasd:Weight>
                      </ovf:Item>
                </ovf:VirtualHardwareSection> 
                </InstantiationParams>
                </SourcedItem>
                <AllEULAsAccepted>false</AllEULAsAccepted>
                </InstantiateVAppTemplateParams>""".format(vmname_andid,
                                                     vapp_tempalte_href,
                                                                vm_href,
                                                                  vm_id,
                                                                vm_name,
                                                        primary_netname,
                                                               cpu=cpus,
                                                             core=cores,
                                                       memory=memory_mb)

                response = self.perform_request(req_type='POST',
                                                url=instantiate_vapp_href,
                                                headers=headers,
                                                data=data)

                if response.status_code != 201:
                    self.logger.error("REST call {} failed reason : {}"\
                         "status code : {}".format(instantiate_vapp_href,
                                                        response.content,
                                                   response.status_code))
                    raise vimconn.vimconnException("new_vminstance(): Failed to create"\
                                                        "vAapp {}".format(vmname_andid))
                else:
                    vapptask = self.get_task_from_response(response.content)

                if vapptask is None and retry==1:
                    self.get_token() # Retry getting token
                    continue
                else:
                    break

            if vapptask is None or vapptask is False:
                raise vimconn.vimconnUnexpectedResponse(
                    "new_vminstance(): failed to create vApp {}".format(vmname_andid))

            # wait for task to complete   
            result = self.client.get_task_monitor().wait_for_success(task=vapptask)

            if result.get('status') == 'success':
                self.logger.debug("new_vminstance(): Sucessfully created Vapp {}".format(vmname_andid))
            else:
                raise vimconn.vimconnUnexpectedResponse(
                    "new_vminstance(): failed to create vApp {}".format(vmname_andid))

        except Exception as exp:
            raise vimconn.vimconnUnexpectedResponse(
                "new_vminstance(): failed to create vApp {} with Exception:{}".format(vmname_andid, exp))

        # we should have now vapp in undeployed state.
        try:
            vdc_obj = VDC(self.client, href=vdc.get('href'))
            vapp_resource = vdc_obj.get_vapp(vmname_andid)
            vapp_uuid = vapp_resource.get('id').split(':')[-1]
            vapp = VApp(self.client, resource=vapp_resource)

        except Exception as exp:
            raise vimconn.vimconnUnexpectedResponse(
                    "new_vminstance(): Failed to retrieve vApp {} after creation: Exception:{}"
                    .format(vmname_andid, exp))

        if vapp_uuid is None:
            raise vimconn.vimconnUnexpectedResponse(
                "new_vminstance(): Failed to retrieve vApp {} after creation".format(
                                                                            vmname_andid))

        #Add PCI passthrough/SRIOV configrations
        vm_obj = None
        pci_devices_info = []
        sriov_net_info = []
        reserve_memory = False

        for net in net_list:
            if net["type"] == "PF" or net["type"] == "PCI-PASSTHROUGH":
                pci_devices_info.append(net)
            elif (net["type"] == "VF" or net["type"] == "SR-IOV" or net["type"] == "VFnotShared") and 'net_id'in net:
                sriov_net_info.append(net)

        #Add PCI
        if len(pci_devices_info) > 0:
            self.logger.info("Need to add PCI devices {} into VM {}".format(pci_devices_info,
                                                                        vmname_andid ))
            PCI_devices_status, vm_obj, vcenter_conect = self.add_pci_devices(vapp_uuid,
                                                                            pci_devices_info,
                                                                            vmname_andid)
            if PCI_devices_status:
                self.logger.info("Added PCI devives {} to VM {}".format(
                                                            pci_devices_info,
                                                            vmname_andid)
                                 )
                reserve_memory = True
            else:
                self.logger.info("Fail to add PCI devives {} to VM {}".format(
                                                            pci_devices_info,
                                                            vmname_andid)
                                 )

        # Modify vm disk
        if vm_disk:
            #Assuming there is only one disk in ovf and fast provisioning in organization vDC is disabled
            result = self.modify_vm_disk(vapp_uuid, vm_disk)
            if result :
                self.logger.debug("Modified Disk size of VM {} ".format(vmname_andid))

        #Add new or existing disks to vApp
        if disk_list:
            added_existing_disk = False
            for disk in disk_list:
                if 'device_type' in disk and disk['device_type'] == 'cdrom':
                    image_id = disk['image_id']
                    # Adding CD-ROM to VM
                    # will revisit code once specification ready to support this feature
                    self.insert_media_to_vm(vapp, image_id)
                elif "image_id" in disk and disk["image_id"] is not None:
                    self.logger.debug("Adding existing disk from image {} to vm {} ".format(
                                                                    disk["image_id"] , vapp_uuid))
                    self.add_existing_disk(catalogs=catalogs,
                                           image_id=disk["image_id"],
                                           size = disk["size"],
                                           template_name=templateName,
                                           vapp_uuid=vapp_uuid
                                           )
                    added_existing_disk = True
                else:
                    #Wait till added existing disk gets reflected into vCD database/API
                    if added_existing_disk:
                        time.sleep(5)
                        added_existing_disk = False
                    self.add_new_disk(vapp_uuid, disk['size'])

        if numas:
            # Assigning numa affinity setting
            for numa in numas:
                if 'paired-threads-id' in numa:
                    paired_threads_id = numa['paired-threads-id']
                    self.set_numa_affinity(vapp_uuid, paired_threads_id)

        # add NICs & connect to networks in netlist
        try:
            self.logger.info("Request to connect VM to a network: {}".format(net_list))
            nicIndex = 0
            primary_nic_index = 0
            for net in net_list:
                # openmano uses network id in UUID format.
                # vCloud Director need a name so we do reverse operation from provided UUID we lookup a name
                # [{'use': 'bridge', 'net_id': '527d4bf7-566a-41e7-a9e7-ca3cdd9cef4f', 'type': 'virtual',
                #   'vpci': '0000:00:11.0', 'name': 'eth0'}]

                if 'net_id' not in net:
                    continue

                #Using net_id as a vim_id i.e. vim interface id, as do not have saperate vim interface id
                #Same will be returned in refresh_vms_status() as vim_interface_id
                net['vim_id'] = net['net_id']  # Provide the same VIM identifier as the VIM network

                interface_net_id = net['net_id']
                interface_net_name = self.get_network_name_by_id(network_uuid=interface_net_id)
                interface_network_mode = net['use']

                if interface_network_mode == 'mgmt':
                    primary_nic_index = nicIndex

                """- POOL (A static IP address is allocated automatically from a pool of addresses.)
                                  - DHCP (The IP address is obtained from a DHCP service.)
                                  - MANUAL (The IP address is assigned manually in the IpAddress element.)
                                  - NONE (No IP addressing mode specified.)"""

                if primary_netname is not None:
                    nets = filter(lambda n: n.get('name') == interface_net_name, self.get_network_list())
                    #For python3
                    #nets = [n for n in self.get_network_list() if n.get('name') == interface_net_name]
                    if len(nets) == 1:
                        self.logger.info("new_vminstance(): Found requested network: {}".format(nets[0].get('name')))

                        vdc_obj = VDC(self.client, href=vdc.get('href'))
                        vapp_resource = vdc_obj.get_vapp(vmname_andid)
                        vapp = VApp(self.client, resource=vapp_resource)
                        # connect network to VM - with all DHCP by default
                        task = vapp.connect_org_vdc_network(nets[0].get('name'))

                        self.client.get_task_monitor().wait_for_success(task=task)

                        type_list = ('PF', 'PCI-PASSTHROUGH', 'VF', 'SR-IOV', 'VFnotShared')
                        if 'type' in net and net['type'] not in type_list:
                            # fetching nic type from vnf
                            if 'model' in net:
                                if net['model'] is not None and net['model'].lower() == 'virtio':
                                    nic_type = 'VMXNET3'
                                else:
                                    nic_type = net['model']

                                self.logger.info("new_vminstance(): adding network adapter "\
                                                          "to a network {}".format(nets[0].get('name')))
                                self.add_network_adapter_to_vms(vapp, nets[0].get('name'),
                                                                primary_nic_index,
                                                                nicIndex,
                                                                net,
                                                                nic_type=nic_type)
                            else:
                                self.logger.info("new_vminstance(): adding network adapter "\
                                                         "to a network {}".format(nets[0].get('name')))
                                self.add_network_adapter_to_vms(vapp, nets[0].get('name'),
                                                                primary_nic_index,
                                                                nicIndex,
                                                                net)
                nicIndex += 1

            # cloud-init for ssh-key injection
            if cloud_config:
                self.cloud_init(vapp,cloud_config)

        # ############# Stub code for SRIOV #################
        #Add SRIOV
#         if len(sriov_net_info) > 0:
#             self.logger.info("Need to add SRIOV adapters {} into VM {}".format(sriov_net_info,
#                                                                         vmname_andid ))
#             sriov_status, vm_obj, vcenter_conect = self.add_sriov(vapp_uuid,
#                                                                   sriov_net_info,
#                                                                   vmname_andid)
#             if sriov_status:
#                 self.logger.info("Added SRIOV {} to VM {}".format(
#                                                             sriov_net_info,
#                                                             vmname_andid)
#                                  )
#                 reserve_memory = True
#             else:
#                 self.logger.info("Fail to add SRIOV {} to VM {}".format(
#                                                             sriov_net_info,
#                                                             vmname_andid)
#                                  )

            # If VM has PCI devices or SRIOV reserve memory for VM
            if reserve_memory:
                memReserve = vm_obj.config.hardware.memoryMB
                spec = vim.vm.ConfigSpec()
                spec.memoryAllocation = vim.ResourceAllocationInfo(reservation=memReserve)
                task = vm_obj.ReconfigVM_Task(spec=spec)
                if task:
                    result = self.wait_for_vcenter_task(task, vcenter_conect)
                    self.logger.info("Reserved memory {} MB for "
                                     "VM VM status: {}".format(str(memReserve), result))
                else:
                    self.logger.info("Fail to reserved memory {} to VM {}".format(
                                                                str(memReserve), str(vm_obj)))

            self.logger.debug("new_vminstance(): starting power on vApp {} ".format(vmname_andid))

            vapp_id = vapp_resource.get('id').split(':')[-1]
            poweron_task = self.power_on_vapp(vapp_id, vmname_andid)
            result = self.client.get_task_monitor().wait_for_success(task=poweron_task)
            if result.get('status') == 'success':
                self.logger.info("new_vminstance(): Successfully power on "\
                                             "vApp {}".format(vmname_andid))
            else:
                self.logger.error("new_vminstance(): failed to power on vApp "\
                                                     "{}".format(vmname_andid))

        except Exception as exp :
            # it might be a case if specific mandatory entry in dict is empty or some other pyVcloud exception
            self.logger.error("new_vminstance(): Failed create new vm instance {} with exception {}"
                              .format(name, exp))
            raise vimconn.vimconnException("new_vminstance(): Failed create new vm instance {} with exception {}"
                                           .format(name, exp))

        # check if vApp deployed and if that the case return vApp UUID otherwise -1
        wait_time = 0
        vapp_uuid = None
        while wait_time <= MAX_WAIT_TIME:
            try:
                vapp_resource = vdc_obj.get_vapp(vmname_andid)
                vapp = VApp(self.client, resource=vapp_resource) 
            except Exception as exp:
                raise vimconn.vimconnUnexpectedResponse(
                        "new_vminstance(): Failed to retrieve vApp {} after creation: Exception:{}"
                        .format(vmname_andid, exp))

            #if vapp and vapp.me.deployed:
            if vapp and vapp_resource.get('deployed') == 'true':
                vapp_uuid = vapp_resource.get('id').split(':')[-1]
                break
            else:
                self.logger.debug("new_vminstance(): Wait for vApp {} to deploy".format(name))
                time.sleep(INTERVAL_TIME)

            wait_time +=INTERVAL_TIME

        if vapp_uuid is not None:
            return vapp_uuid, None
        else:
            raise vimconn.vimconnUnexpectedResponse("new_vminstance(): Failed create new vm instance {}".format(name))

    ##
    ##
    ##  based on current discussion
    ##
    ##
    ##  server:
    #   created: '2016-09-08T11:51:58'
    #   description: simple-instance.linux1.1
    #   flavor: ddc6776e-75a9-11e6-ad5f-0800273e724c
    #   hostId: e836c036-74e7-11e6-b249-0800273e724c
    #   image: dde30fe6-75a9-11e6-ad5f-0800273e724c
    #   status: ACTIVE
    #   error_msg:
    #   interfaces: …
    #
    def get_vminstance(self, vim_vm_uuid=None):
        """Returns the VM instance information from VIM"""

        self.logger.debug("Client requesting vm instance {} ".format(vim_vm_uuid))

        org, vdc = self.get_vdc_details()
        if vdc is None:
            raise vimconn.vimconnConnectionException(
                "Failed to get a reference of VDC for a tenant {}".format(self.tenant_name))

        vm_info_dict = self.get_vapp_details_rest(vapp_uuid=vim_vm_uuid)
        if not vm_info_dict:
            self.logger.debug("get_vminstance(): Failed to get vApp name by UUID {}".format(vim_vm_uuid))
            raise vimconn.vimconnNotFoundException("Failed to get vApp name by UUID {}".format(vim_vm_uuid))

        status_key = vm_info_dict['status']
        error = ''
        try:
            vm_dict = {'created': vm_info_dict['created'],
                       'description': vm_info_dict['name'],
                       'status': vcdStatusCode2manoFormat[int(status_key)],
                       'hostId': vm_info_dict['vmuuid'],
                       'error_msg': error,
                       'vim_info': yaml.safe_dump(vm_info_dict), 'interfaces': []}

            if 'interfaces' in vm_info_dict:
                vm_dict['interfaces'] = vm_info_dict['interfaces']
            else:
                vm_dict['interfaces'] = []
        except KeyError:
            vm_dict = {'created': '',
                       'description': '',
                       'status': vcdStatusCode2manoFormat[int(-1)],
                       'hostId': vm_info_dict['vmuuid'],
                       'error_msg': "Inconsistency state",
                       'vim_info': yaml.safe_dump(vm_info_dict), 'interfaces': []}

        return vm_dict

    def delete_vminstance(self, vm__vim_uuid, created_items=None):
        """Method poweroff and remove VM instance from vcloud director network.

        Args:
            vm__vim_uuid: VM UUID

        Returns:
            Returns the instance identifier
        """

        self.logger.debug("Client requesting delete vm instance {} ".format(vm__vim_uuid))

        org, vdc = self.get_vdc_details()
        vdc_obj = VDC(self.client, href=vdc.get('href')) 
        if vdc_obj is None:
            self.logger.debug("delete_vminstance(): Failed to get a reference of VDC for a tenant {}".format(
                self.tenant_name))
            raise vimconn.vimconnException(
                "delete_vminstance(): Failed to get a reference of VDC for a tenant {}".format(self.tenant_name))

        try:
            vapp_name = self.get_namebyvappid(vm__vim_uuid)
            vapp_resource = vdc_obj.get_vapp(vapp_name)
            vapp = VApp(self.client, resource=vapp_resource)
            if vapp_name is None:
                self.logger.debug("delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid))
                return -1, "delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid)
            else:
                self.logger.info("Deleting vApp {} and UUID {}".format(vapp_name, vm__vim_uuid))

            # Delete vApp and wait for status change if task executed and vApp is None.

            if vapp:
                if vapp_resource.get('deployed') == 'true':
                    self.logger.info("Powering off vApp {}".format(vapp_name))
                    #Power off vApp
                    powered_off = False
                    wait_time = 0
                    while wait_time <= MAX_WAIT_TIME:
                        power_off_task = vapp.power_off()
                        result = self.client.get_task_monitor().wait_for_success(task=power_off_task)

                        if result.get('status') == 'success':
                            powered_off = True
                            break
                        else:
                            self.logger.info("Wait for vApp {} to power off".format(vapp_name))
                            time.sleep(INTERVAL_TIME)

                        wait_time +=INTERVAL_TIME
                    if not powered_off:
                        self.logger.debug("delete_vminstance(): Failed to power off VM instance {} ".format(vm__vim_uuid))
                    else:
                        self.logger.info("delete_vminstance(): Powered off VM instance {} ".format(vm__vim_uuid))

                    #Undeploy vApp
                    self.logger.info("Undeploy vApp {}".format(vapp_name))
                    wait_time = 0
                    undeployed = False
                    while wait_time <= MAX_WAIT_TIME:
                        vapp = VApp(self.client, resource=vapp_resource) 
                        if not vapp:
                            self.logger.debug("delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid))
                            return -1, "delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid)
                        undeploy_task = vapp.undeploy()

                        result = self.client.get_task_monitor().wait_for_success(task=undeploy_task)
                        if result.get('status') == 'success':
                            undeployed = True
                            break
                        else:
                            self.logger.debug("Wait for vApp {} to undeploy".format(vapp_name))
                            time.sleep(INTERVAL_TIME)

                        wait_time +=INTERVAL_TIME

                    if not undeployed:
                        self.logger.debug("delete_vminstance(): Failed to undeploy vApp {} ".format(vm__vim_uuid)) 

                # delete vapp
                self.logger.info("Start deletion of vApp {} ".format(vapp_name))

                if vapp is not None:
                    wait_time = 0
                    result = False

                    while wait_time <= MAX_WAIT_TIME:
                        vapp = VApp(self.client, resource=vapp_resource)
                        if not vapp:
                            self.logger.debug("delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid))
                            return -1, "delete_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid)

                        delete_task = vdc_obj.delete_vapp(vapp.name, force=True)

                        result = self.client.get_task_monitor().wait_for_success(task=delete_task)
                        if result.get('status') == 'success':     
                            break
                        else:
                            self.logger.debug("Wait for vApp {} to delete".format(vapp_name))
                            time.sleep(INTERVAL_TIME)

                        wait_time +=INTERVAL_TIME

                    if result is None:
                        self.logger.debug("delete_vminstance(): Failed delete uuid {} ".format(vm__vim_uuid))
                    else:
                        self.logger.info("Deleted vm instance {} sccessfully".format(vm__vim_uuid))
                        return vm__vim_uuid
        except:
            self.logger.debug(traceback.format_exc())
            raise vimconn.vimconnException("delete_vminstance(): Failed delete vm instance {}".format(vm__vim_uuid))


    def refresh_vms_status(self, vm_list):
        """Get the status of the virtual machines and their interfaces/ports
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
        """

        self.logger.debug("Client requesting refresh vm status for {} ".format(vm_list))

        org,vdc = self.get_vdc_details()
        if vdc is None:
            raise vimconn.vimconnException("Failed to get a reference of VDC for a tenant {}".format(self.tenant_name))

        vms_dict = {}
        nsx_edge_list = []
        for vmuuid in vm_list:
            vapp_name = self.get_namebyvappid(vmuuid)
            if vapp_name is not None:

                try:
                    vm_pci_details = self.get_vm_pci_details(vmuuid)
                    vdc_obj = VDC(self.client, href=vdc.get('href'))
                    vapp_resource = vdc_obj.get_vapp(vapp_name)
                    the_vapp = VApp(self.client, resource=vapp_resource)

                    vm_details = {}
                    for vm in the_vapp.get_all_vms():
                        headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}    
                        response = self.perform_request(req_type='GET',
                                                        url=vm.get('href'),
                                                        headers=headers)

                        if response.status_code != 200:
                            self.logger.error("refresh_vms_status : REST call {} failed reason : {}"\
                                                            "status code : {}".format(vm.get('href'),
                                                                                    response.content,
                                                                               response.status_code))
                            raise vimconn.vimconnException("refresh_vms_status : Failed to get "\
                                                                         "VM details")
                        xmlroot = XmlElementTree.fromstring(response.content)

                        result = response.content.replace("\n"," ")
                        hdd_mb = re.search('vcloud:capacity="(\d+)"\svcloud:storageProfileOverrideVmDefault=',result).group(1)
                        vm_details['hdd_mb'] = int(hdd_mb) if hdd_mb else None
                        cpus = re.search('<rasd:Description>Number of Virtual CPUs</.*?>(\d+)</rasd:VirtualQuantity>',result).group(1)
                        vm_details['cpus'] = int(cpus) if cpus else None
                        memory_mb = re.search('<rasd:Description>Memory Size</.*?>(\d+)</rasd:VirtualQuantity>',result).group(1)
                        vm_details['memory_mb'] = int(memory_mb) if memory_mb else None
                        vm_details['status'] = vcdStatusCode2manoFormat[int(xmlroot.get('status'))]
                        vm_details['id'] = xmlroot.get('id')
                        vm_details['name'] = xmlroot.get('name')
                        vm_info = [vm_details]
                        if vm_pci_details:
                            vm_info[0].update(vm_pci_details)  

                        vm_dict = {'status': vcdStatusCode2manoFormat[int(vapp_resource.get('status'))],
                                   'error_msg': vcdStatusCode2manoFormat[int(vapp_resource.get('status'))],
                                   'vim_info': yaml.safe_dump(vm_info), 'interfaces': []}

                        # get networks
                        vm_ip = None
                        vm_mac = None   
                        if vm.NetworkConnectionSection.NetworkConnection:
                            vm_mac = vm.NetworkConnectionSection.NetworkConnection.MACAddress
                        if vm_ip is None:
                            if not nsx_edge_list:
                                nsx_edge_list = self.get_edge_details()
                                if nsx_edge_list is None:
                                    raise vimconn.vimconnException("refresh_vms_status:"\
                                                                      "Failed to get edge details from NSX Manager")
                            if vm_mac is not None:
                                vm_ip = self.get_ipaddr_from_NSXedge(nsx_edge_list, vm_mac)

                        network_name = vm.NetworkConnectionSection.NetworkConnection.get('network')    
                        vm_net_id = self.get_network_id_by_name(network_name)
                        interface = {"mac_address": vm_mac,
                                     "vim_net_id": vm_net_id,
                                     "vim_interface_id": vm_net_id,
                                     'ip_address': vm_ip}

                        vm_dict["interfaces"].append(interface)

                    # add a vm to vm dict
                    vms_dict.setdefault(vmuuid, vm_dict)
                    self.logger.debug("refresh_vms_status : vm info {}".format(vm_dict))
                except Exception as exp:
                    self.logger.debug("Error in response {}".format(exp))
                    self.logger.debug(traceback.format_exc())

        return vms_dict


    def get_edge_details(self):
        """Get the NSX edge list from NSX Manager
           Returns list of NSX edges
        """
        edge_list = []
        rheaders = {'Content-Type': 'application/xml'}
        nsx_api_url = '/api/4.0/edges'

        self.logger.debug("Get edge details from NSX Manager {} {}".format(self.nsx_manager, nsx_api_url))

        try:
            resp = requests.get(self.nsx_manager + nsx_api_url,
                                auth = (self.nsx_user, self.nsx_password),
                                verify = False, headers = rheaders)
            if resp.status_code == requests.codes.ok:
                paged_Edge_List = XmlElementTree.fromstring(resp.text)
                for edge_pages in paged_Edge_List:
                    if edge_pages.tag == 'edgePage':
                        for edge_summary in edge_pages:
                            if edge_summary.tag == 'pagingInfo':
                                for element in edge_summary:
                                    if element.tag == 'totalCount' and element.text == '0':
                                        raise vimconn.vimconnException("get_edge_details: No NSX edges details found: {}"
                                                                       .format(self.nsx_manager))

                            if edge_summary.tag == 'edgeSummary':
                                for element in edge_summary:
                                    if element.tag == 'id':
                                        edge_list.append(element.text)
                    else:
                        raise vimconn.vimconnException("get_edge_details: No NSX edge details found: {}"
                                                       .format(self.nsx_manager))

                if not edge_list:
                    raise vimconn.vimconnException("get_edge_details: "\
                                                   "No NSX edge details found: {}"
                                                   .format(self.nsx_manager))
                else:
                    self.logger.debug("get_edge_details: Found NSX edges {}".format(edge_list))
                    return edge_list
            else:
                self.logger.debug("get_edge_details: "
                                  "Failed to get NSX edge details from NSX Manager: {}"
                                  .format(resp.content))
                return None

        except Exception as exp:
            self.logger.debug("get_edge_details: "\
                              "Failed to get NSX edge details from NSX Manager: {}"
                              .format(exp))
            raise vimconn.vimconnException("get_edge_details: "\
                                           "Failed to get NSX edge details from NSX Manager: {}"
                                           .format(exp))


    def get_ipaddr_from_NSXedge(self, nsx_edges, mac_address):
        """Get IP address details from NSX edges, using the MAC address
           PARAMS: nsx_edges : List of NSX edges
                   mac_address : Find IP address corresponding to this MAC address
           Returns: IP address corrresponding to the provided MAC address
        """

        ip_addr = None
        rheaders = {'Content-Type': 'application/xml'}

        self.logger.debug("get_ipaddr_from_NSXedge: Finding IP addr from NSX edge")

        try:
            for edge in nsx_edges:
                nsx_api_url = '/api/4.0/edges/'+ edge +'/dhcp/leaseInfo'

                resp = requests.get(self.nsx_manager + nsx_api_url,
                                    auth = (self.nsx_user, self.nsx_password),
                                    verify = False, headers = rheaders)

                if resp.status_code == requests.codes.ok:
                    dhcp_leases = XmlElementTree.fromstring(resp.text)
                    for child in dhcp_leases:
                        if child.tag == 'dhcpLeaseInfo':
                            dhcpLeaseInfo = child
                            for leaseInfo in dhcpLeaseInfo:
                                for elem in leaseInfo:
                                    if (elem.tag)=='macAddress':
                                        edge_mac_addr = elem.text
                                    if (elem.tag)=='ipAddress':
                                        ip_addr = elem.text
                                if edge_mac_addr is not None:
                                    if edge_mac_addr == mac_address:
                                        self.logger.debug("Found ip addr {} for mac {} at NSX edge {}"
                                                          .format(ip_addr, mac_address,edge))
                                        return ip_addr
                else:
                    self.logger.debug("get_ipaddr_from_NSXedge: "\
                                      "Error occurred while getting DHCP lease info from NSX Manager: {}"
                                      .format(resp.content))

            self.logger.debug("get_ipaddr_from_NSXedge: No IP addr found in any NSX edge")
            return None

        except XmlElementTree.ParseError as Err:
            self.logger.debug("ParseError in response from NSX Manager {}".format(Err.message), exc_info=True)


    def action_vminstance(self, vm__vim_uuid=None, action_dict=None, created_items={}):
        """Send and action over a VM instance from VIM
        Returns the vm_id if the action was successfully sent to the VIM"""

        self.logger.debug("Received action for vm {} and action dict {}".format(vm__vim_uuid, action_dict))
        if vm__vim_uuid is None or action_dict is None:
            raise vimconn.vimconnException("Invalid request. VM id or action is None.")

        org, vdc = self.get_vdc_details()
        if vdc is None:
            raise  vimconn.vimconnException("Failed to get a reference of VDC for a tenant {}".format(self.tenant_name))

        vapp_name = self.get_namebyvappid(vm__vim_uuid)
        if vapp_name is None:
            self.logger.debug("action_vminstance(): Failed to get vm by given {} vm uuid".format(vm__vim_uuid))
            raise vimconn.vimconnException("Failed to get vm by given {} vm uuid".format(vm__vim_uuid))
        else:
            self.logger.info("Action_vminstance vApp {} and UUID {}".format(vapp_name, vm__vim_uuid))

        try:
            vdc_obj = VDC(self.client, href=vdc.get('href'))
            vapp_resource = vdc_obj.get_vapp(vapp_name)
            vapp = VApp(self.client, resource=vapp_resource)  
            if "start" in action_dict:
                self.logger.info("action_vminstance: Power on vApp: {}".format(vapp_name))
                poweron_task = self.power_on_vapp(vm__vim_uuid, vapp_name)   
                result = self.client.get_task_monitor().wait_for_success(task=poweron_task) 
                self.instance_actions_result("start", result, vapp_name)
            elif "rebuild" in action_dict:
                self.logger.info("action_vminstance: Rebuild vApp: {}".format(vapp_name))
                rebuild_task = vapp.deploy(power_on=True)
                result = self.client.get_task_monitor().wait_for_success(task=rebuild_task) 
                self.instance_actions_result("rebuild", result, vapp_name)
            elif "pause" in action_dict:
                self.logger.info("action_vminstance: pause vApp: {}".format(vapp_name))
                pause_task = vapp.undeploy(action='suspend')
                result = self.client.get_task_monitor().wait_for_success(task=pause_task) 
                self.instance_actions_result("pause", result, vapp_name)
            elif "resume" in action_dict:
                self.logger.info("action_vminstance: resume vApp: {}".format(vapp_name))
                poweron_task = self.power_on_vapp(vm__vim_uuid, vapp_name)
                result = self.client.get_task_monitor().wait_for_success(task=poweron_task)
                self.instance_actions_result("resume", result, vapp_name)
            elif "shutoff" in action_dict or "shutdown" in action_dict:
                action_name , value = action_dict.items()[0]
                #For python3
                #action_name , value = list(action_dict.items())[0]
                self.logger.info("action_vminstance: {} vApp: {}".format(action_name, vapp_name))
                shutdown_task = vapp.shutdown()
                result = self.client.get_task_monitor().wait_for_success(task=shutdown_task)
                if action_name == "shutdown":
                    self.instance_actions_result("shutdown", result, vapp_name)
                else:
                    self.instance_actions_result("shutoff", result, vapp_name)
            elif "forceOff" in action_dict:
                result = vapp.undeploy(action='powerOff')
                self.instance_actions_result("forceOff", result, vapp_name)
            elif "reboot" in action_dict:
                self.logger.info("action_vminstance: reboot vApp: {}".format(vapp_name))
                reboot_task = vapp.reboot()
                self.client.get_task_monitor().wait_for_success(task=reboot_task)  
            else:
                raise vimconn.vimconnException("action_vminstance: Invalid action {} or action is None.".format(action_dict))
            return vm__vim_uuid
        except Exception as exp :
            self.logger.debug("action_vminstance: Failed with Exception {}".format(exp))
            raise vimconn.vimconnException("action_vminstance: Failed with Exception {}".format(exp))

    def instance_actions_result(self, action, result, vapp_name):
        if result.get('status') == 'success':
            self.logger.info("action_vminstance: Sucessfully {} the vApp: {}".format(action, vapp_name))
        else:
            self.logger.error("action_vminstance: Failed to {} vApp: {}".format(action, vapp_name))

    def get_vminstance_console(self, vm_id, console_type="vnc"):
        """
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
        """
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    # NOT USED METHODS in current version

    def host_vim2gui(self, host, server_dict):
        """Transform host dictionary from VIM format to GUI format,
        and append to the server_dict
        """
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def get_hosts_info(self):
        """Get the information of deployed hosts
        Returns the hosts content"""
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def get_hosts(self, vim_tenant):
        """Get the hosts and deployed instances
        Returns the hosts content"""
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def get_processor_rankings(self):
        """Get the processor rankings in the VIM database"""
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def new_host(self, host_data):
        """Adds a new host to VIM"""
        '''Returns status code of the VIM response'''
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def new_external_port(self, port_data):
        """Adds a external port to VIM"""
        '''Returns the port identifier'''
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def new_external_network(self, net_name, net_type):
        """Adds a external network to VIM (shared)"""
        '''Returns the network identifier'''
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def connect_port_network(self, port_id, network_id, admin=False):
        """Connects a external port to a network"""
        '''Returns status code of the VIM response'''
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def new_vminstancefromJSON(self, vm_data):
        """Adds a VM instance to VIM"""
        '''Returns the instance identifier'''
        raise vimconn.vimconnNotImplemented("Should have implemented this")

    def get_network_name_by_id(self, network_uuid=None):
        """Method gets vcloud director network named based on supplied uuid.

        Args:
            network_uuid: network_id

        Returns:
            The return network name.
        """

        if not network_uuid:
            return None

        try:
            org_dict = self.get_org(self.org_uuid)
            if 'networks' in org_dict:
                org_network_dict = org_dict['networks']
                for net_uuid in org_network_dict:
                    if net_uuid == network_uuid:
                        return org_network_dict[net_uuid]
        except:
            self.logger.debug("Exception in get_network_name_by_id")
            self.logger.debug(traceback.format_exc())

        return None

    def get_network_id_by_name(self, network_name=None):
        """Method gets vcloud director network uuid based on supplied name.

        Args:
            network_name: network_name
        Returns:
            The return network uuid.
            network_uuid: network_id
        """

        if not network_name:
            self.logger.debug("get_network_id_by_name() : Network name is empty")
            return None

        try:
            org_dict = self.get_org(self.org_uuid)
            if org_dict and 'networks' in org_dict:
                org_network_dict = org_dict['networks']
                for net_uuid,net_name in org_network_dict.iteritems():
                #For python3
                #for net_uuid,net_name in org_network_dict.items():
                    if net_name == network_name:
                        return net_uuid

        except KeyError as exp:
            self.logger.debug("get_network_id_by_name() : KeyError- {} ".format(exp))

        return None

    def list_org_action(self):
        """
        Method leverages vCloud director and query for available organization for particular user

        Args:
            vca - is active VCA connection.
            vdc_name - is a vdc name that will be used to query vms action

            Returns:
                The return XML respond
        """
        url_list = [self.url, '/api/org']
        vm_list_rest_call = ''.join(url_list)

        if self.client._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                       'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}

            response = self.perform_request(req_type='GET',
                                     url=vm_list_rest_call,
                                           headers=headers)

            if response.status_code == 403:
                response = self.retry_rest('GET', vm_list_rest_call)

            if response.status_code == requests.codes.ok:
                return response.content

        return None

    def get_org_action(self, org_uuid=None):
        """
        Method leverages vCloud director and retrieve available object for organization.

        Args:
            org_uuid - vCD organization uuid
            self.client - is active connection.

            Returns:
                The return XML respond
        """

        if org_uuid is None:
            return None

        url_list = [self.url, '/api/org/', org_uuid]
        vm_list_rest_call = ''.join(url_list)

        if self.client._session: 
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                     'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']} 

            #response = requests.get(vm_list_rest_call, headers=headers, verify=False)
            response = self.perform_request(req_type='GET',
                                            url=vm_list_rest_call,
                                            headers=headers)
            if response.status_code == 403:
                response = self.retry_rest('GET', vm_list_rest_call)

            if response.status_code == requests.codes.ok:
                return response.content 
        return None

    def get_org(self, org_uuid=None):
        """
        Method retrieves available organization in vCloud Director

        Args:
            org_uuid - is a organization uuid.

            Returns:
                The return dictionary with following key
                    "network" - for network list under the org
                    "catalogs" - for network list under the org
                    "vdcs" - for vdc list under org
        """

        org_dict = {}

        if org_uuid is None:
            return org_dict

        content = self.get_org_action(org_uuid=org_uuid)
        try:
            vdc_list = {}
            network_list = {}
            catalog_list = {}
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            for child in vm_list_xmlroot:
                if child.attrib['type'] == 'application/vnd.vmware.vcloud.vdc+xml':
                    vdc_list[child.attrib['href'].split("/")[-1:][0]] = child.attrib['name']
                    org_dict['vdcs'] = vdc_list
                if child.attrib['type'] == 'application/vnd.vmware.vcloud.orgNetwork+xml':
                    network_list[child.attrib['href'].split("/")[-1:][0]] = child.attrib['name']
                    org_dict['networks'] = network_list
                if child.attrib['type'] == 'application/vnd.vmware.vcloud.catalog+xml':
                    catalog_list[child.attrib['href'].split("/")[-1:][0]] = child.attrib['name']
                    org_dict['catalogs'] = catalog_list
        except:
            pass

        return org_dict

    def get_org_list(self):
        """
        Method retrieves available organization in vCloud Director

        Args:
            vca - is active VCA connection.

            Returns:
                The return dictionary and key for each entry VDC UUID
        """

        org_dict = {}

        content = self.list_org_action()
        try:
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            for vm_xml in vm_list_xmlroot:
                if vm_xml.tag.split("}")[1] == 'Org':
                    org_uuid = vm_xml.attrib['href'].split('/')[-1:]
                    org_dict[org_uuid[0]] = vm_xml.attrib['name']
        except:
            pass

        return org_dict

    def vms_view_action(self, vdc_name=None):
        """ Method leverages vCloud director vms query call

        Args:
            vca - is active VCA connection.
            vdc_name - is a vdc name that will be used to query vms action

            Returns:
                The return XML respond
        """
        vca = self.connect()
        if vdc_name is None:
            return None

        url_list = [vca.host, '/api/vms/query']
        vm_list_rest_call = ''.join(url_list)

        if not (not vca.vcloud_session or not vca.vcloud_session.organization):
            refs = filter(lambda ref: ref.name == vdc_name and ref.type_ == 'application/vnd.vmware.vcloud.vdc+xml',
                          vca.vcloud_session.organization.Link)
            #For python3
            #refs = [ref for ref in vca.vcloud_session.organization.Link if ref.name == vdc_name and\
            #        ref.type_ == 'application/vnd.vmware.vcloud.vdc+xml']
            if len(refs) == 1:
                response = Http.get(url=vm_list_rest_call,
                                    headers=vca.vcloud_session.get_vcloud_headers(),
                                    verify=vca.verify,
                                    logger=vca.logger)
                if response.status_code == requests.codes.ok:
                    return response.content

        return None

    def get_vapp_list(self, vdc_name=None):
        """
        Method retrieves vApp list deployed vCloud director and returns a dictionary
        contains a list of all vapp deployed for queried VDC.
        The key for a dictionary is vApp UUID


        Args:
            vca - is active VCA connection.
            vdc_name - is a vdc name that will be used to query vms action

            Returns:
                The return dictionary and key for each entry vapp UUID
        """

        vapp_dict = {}
        if vdc_name is None:
            return vapp_dict

        content = self.vms_view_action(vdc_name=vdc_name)
        try:
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            for vm_xml in vm_list_xmlroot:
                if vm_xml.tag.split("}")[1] == 'VMRecord':
                    if vm_xml.attrib['isVAppTemplate'] == 'true':
                        rawuuid = vm_xml.attrib['container'].split('/')[-1:]
                        if 'vappTemplate-' in rawuuid[0]:
                            # vm in format vappTemplate-e63d40e7-4ff5-4c6d-851f-96c1e4da86a5 we remove
                            # vm and use raw UUID as key
                            vapp_dict[rawuuid[0][13:]] = vm_xml.attrib
        except:
            pass

        return vapp_dict

    def get_vm_list(self, vdc_name=None):
        """
        Method retrieves VM's list deployed vCloud director. It returns a dictionary
        contains a list of all VM's deployed for queried VDC.
        The key for a dictionary is VM UUID


        Args:
            vca - is active VCA connection.
            vdc_name - is a vdc name that will be used to query vms action

            Returns:
                The return dictionary and key for each entry vapp UUID
        """
        vm_dict = {}

        if vdc_name is None:
            return vm_dict

        content = self.vms_view_action(vdc_name=vdc_name)
        try:
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            for vm_xml in vm_list_xmlroot:
                if vm_xml.tag.split("}")[1] == 'VMRecord':
                    if vm_xml.attrib['isVAppTemplate'] == 'false':
                        rawuuid = vm_xml.attrib['href'].split('/')[-1:]
                        if 'vm-' in rawuuid[0]:
                            # vm in format vm-e63d40e7-4ff5-4c6d-851f-96c1e4da86a5 we remove
                            #  vm and use raw UUID as key
                            vm_dict[rawuuid[0][3:]] = vm_xml.attrib
        except:
            pass

        return vm_dict

    def get_vapp(self, vdc_name=None, vapp_name=None, isuuid=False):
        """
        Method retrieves VM deployed vCloud director. It returns VM attribute as dictionary
        contains a list of all VM's deployed for queried VDC.
        The key for a dictionary is VM UUID


        Args:
            vca - is active VCA connection.
            vdc_name - is a vdc name that will be used to query vms action

            Returns:
                The return dictionary and key for each entry vapp UUID
        """
        vm_dict = {}
        vca = self.connect()
        if not vca:
            raise vimconn.vimconnConnectionException("self.connect() is failed")

        if vdc_name is None:
            return vm_dict

        content = self.vms_view_action(vdc_name=vdc_name)
        try:
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            for vm_xml in vm_list_xmlroot:
                if vm_xml.tag.split("}")[1] == 'VMRecord' and vm_xml.attrib['isVAppTemplate'] == 'false':
                    # lookup done by UUID
                    if isuuid:
                        if vapp_name in vm_xml.attrib['container']:
                            rawuuid = vm_xml.attrib['href'].split('/')[-1:]
                            if 'vm-' in rawuuid[0]:
                                vm_dict[rawuuid[0][3:]] = vm_xml.attrib
                                break
                    # lookup done by Name
                    else:
                        if vapp_name in vm_xml.attrib['name']:
                            rawuuid = vm_xml.attrib['href'].split('/')[-1:]
                            if 'vm-' in rawuuid[0]:
                                vm_dict[rawuuid[0][3:]] = vm_xml.attrib
                                break
        except:
            pass

        return vm_dict

    def get_network_action(self, network_uuid=None):
        """
        Method leverages vCloud director and query network based on network uuid

        Args:
            vca - is active VCA connection.
            network_uuid - is a network uuid

            Returns:
                The return XML respond
        """

        if network_uuid is None:
            return None

        url_list = [self.url, '/api/network/', network_uuid]
        vm_list_rest_call = ''.join(url_list)

        if self.client._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                     'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}

            response = self.perform_request(req_type='GET',
                                            url=vm_list_rest_call,
                                            headers=headers)
            #Retry login if session expired & retry sending request
            if response.status_code == 403:
                response = self.retry_rest('GET', vm_list_rest_call)

            if response.status_code == requests.codes.ok:
                return response.content

        return None

    def get_vcd_network(self, network_uuid=None):
        """
        Method retrieves available network from vCloud Director

        Args:
            network_uuid - is VCD network UUID

        Each element serialized as key : value pair

        Following keys available for access.    network_configuration['Gateway'}
        <Configuration>
          <IpScopes>
            <IpScope>
                <IsInherited>true</IsInherited>
                <Gateway>172.16.252.100</Gateway>
                <Netmask>255.255.255.0</Netmask>
                <Dns1>172.16.254.201</Dns1>
                <Dns2>172.16.254.202</Dns2>
                <DnsSuffix>vmwarelab.edu</DnsSuffix>
                <IsEnabled>true</IsEnabled>
                <IpRanges>
                    <IpRange>
                        <StartAddress>172.16.252.1</StartAddress>
                        <EndAddress>172.16.252.99</EndAddress>
                    </IpRange>
                </IpRanges>
            </IpScope>
        </IpScopes>
        <FenceMode>bridged</FenceMode>

        Returns:
                The return dictionary and key for each entry vapp UUID
        """

        network_configuration = {}
        if network_uuid is None:
            return network_uuid

        try:
            content = self.get_network_action(network_uuid=network_uuid)
            vm_list_xmlroot = XmlElementTree.fromstring(content)

            network_configuration['status'] = vm_list_xmlroot.get("status")
            network_configuration['name'] = vm_list_xmlroot.get("name")
            network_configuration['uuid'] = vm_list_xmlroot.get("id").split(":")[3]

            for child in vm_list_xmlroot:
                if child.tag.split("}")[1] == 'IsShared':
                    network_configuration['isShared'] = child.text.strip()
                if child.tag.split("}")[1] == 'Configuration':
                    for configuration in child.iter():
                        tagKey = configuration.tag.split("}")[1].strip()
                        if tagKey != "":
                            network_configuration[tagKey] = configuration.text.strip()
            return network_configuration
        except Exception as exp :
            self.logger.debug("get_vcd_network: Failed with Exception {}".format(exp))
            raise vimconn.vimconnException("get_vcd_network: Failed with Exception {}".format(exp))

        return network_configuration

    def delete_network_action(self, network_uuid=None):
        """
        Method delete given network from vCloud director

        Args:
            network_uuid - is a network uuid that client wish to delete

            Returns:
                The return None or XML respond or false
        """
        client = self.connect_as_admin()
        if not client:
            raise vimconn.vimconnConnectionException("Failed to connect vCD as admin")
        if network_uuid is None:
            return False

        url_list = [self.url, '/api/admin/network/', network_uuid]
        vm_list_rest_call = ''.join(url_list)

        if client._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                     'x-vcloud-authorization': client._session.headers['x-vcloud-authorization']} 
            response = self.perform_request(req_type='DELETE',
                                            url=vm_list_rest_call,
                                            headers=headers)
            if response.status_code == 202:
                return True

        return False

    def create_network(self, network_name=None, net_type='bridge', parent_network_uuid=None,
                       ip_profile=None, isshared='true'):
        """
        Method create network in vCloud director

        Args:
            network_name - is network name to be created.
            net_type - can be 'bridge','data','ptp','mgmt'.
            ip_profile is a dict containing the IP parameters of the network
            isshared - is a boolean
            parent_network_uuid - is parent provider vdc network that will be used for mapping.
            It optional attribute. by default if no parent network indicate the first available will be used.

            Returns:
                The return network uuid or return None
        """

        new_network_name = [network_name, '-', str(uuid.uuid4())]
        content = self.create_network_rest(network_name=''.join(new_network_name),
                                           ip_profile=ip_profile,
                                           net_type=net_type,
                                           parent_network_uuid=parent_network_uuid,
                                           isshared=isshared)
        if content is None:
            self.logger.debug("Failed create network {}.".format(network_name))
            return None

        try:
            vm_list_xmlroot = XmlElementTree.fromstring(content)
            vcd_uuid = vm_list_xmlroot.get('id').split(":")
            if len(vcd_uuid) == 4:
                self.logger.info("Created new network name: {} uuid: {}".format(network_name, vcd_uuid[3]))
                return vcd_uuid[3]
        except:
            self.logger.debug("Failed create network {}".format(network_name))
            return None

    def create_network_rest(self, network_name=None, net_type='bridge', parent_network_uuid=None,
                            ip_profile=None, isshared='true'):
        """
        Method create network in vCloud director

        Args:
            network_name - is network name to be created.
            net_type - can be 'bridge','data','ptp','mgmt'.
            ip_profile is a dict containing the IP parameters of the network
            isshared - is a boolean
            parent_network_uuid - is parent provider vdc network that will be used for mapping.
            It optional attribute. by default if no parent network indicate the first available will be used.

            Returns:
                The return network uuid or return None
        """
        client_as_admin = self.connect_as_admin()
        if not client_as_admin:
            raise vimconn.vimconnConnectionException("Failed to connect vCD.")
        if network_name is None:
            return None

        url_list = [self.url, '/api/admin/vdc/', self.tenant_id]
        vm_list_rest_call = ''.join(url_list)

        if client_as_admin._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                     'x-vcloud-authorization': client_as_admin._session.headers['x-vcloud-authorization']}

            response = self.perform_request(req_type='GET',
                                            url=vm_list_rest_call,
                                            headers=headers)

            provider_network = None
            available_networks = None
            add_vdc_rest_url = None

            if response.status_code != requests.codes.ok:
                self.logger.debug("REST API call {} failed. Return status code {}".format(vm_list_rest_call,
                                                                                          response.status_code))
                return None
            else:
                try:
                    vm_list_xmlroot = XmlElementTree.fromstring(response.content)
                    for child in vm_list_xmlroot:
                        if child.tag.split("}")[1] == 'ProviderVdcReference':
                            provider_network = child.attrib.get('href')
                            # application/vnd.vmware.admin.providervdc+xml
                        if child.tag.split("}")[1] == 'Link':
                            if child.attrib.get('type') == 'application/vnd.vmware.vcloud.orgVdcNetwork+xml' \
                                    and child.attrib.get('rel') == 'add':
                                add_vdc_rest_url = child.attrib.get('href')
                except:
                    self.logger.debug("Failed parse respond for rest api call {}".format(vm_list_rest_call))
                    self.logger.debug("Respond body {}".format(response.content))
                    return None

            # find  pvdc provided available network
            response = self.perform_request(req_type='GET',
                                            url=provider_network,
                                            headers=headers)
            if response.status_code != requests.codes.ok:
                self.logger.debug("REST API call {} failed. Return status code {}".format(vm_list_rest_call,
                                                                                          response.status_code))
                return None

            if parent_network_uuid is None:
                try:
                    vm_list_xmlroot = XmlElementTree.fromstring(response.content)
                    for child in vm_list_xmlroot.iter():
                        if child.tag.split("}")[1] == 'AvailableNetworks':
                            for networks in child.iter():
                                # application/vnd.vmware.admin.network+xml
                                if networks.attrib.get('href') is not None:
                                    available_networks = networks.attrib.get('href')
                                    break
                except:
                    return None

            try:
                #Configure IP profile of the network
                ip_profile = ip_profile if ip_profile is not None else DEFAULT_IP_PROFILE

                if 'subnet_address' not in ip_profile or ip_profile['subnet_address'] is None:
                    subnet_rand = random.randint(0, 255)
                    ip_base = "192.168.{}.".format(subnet_rand)
                    ip_profile['subnet_address'] = ip_base + "0/24"
                else:
                    ip_base = ip_profile['subnet_address'].rsplit('.',1)[0] + '.'

                if 'gateway_address' not in ip_profile or ip_profile['gateway_address'] is None:
                    ip_profile['gateway_address']=ip_base + "1"
                if 'dhcp_count' not in ip_profile or ip_profile['dhcp_count'] is None:
                    ip_profile['dhcp_count']=DEFAULT_IP_PROFILE['dhcp_count']
                if 'dhcp_enabled' not in ip_profile or ip_profile['dhcp_enabled'] is None:
                    ip_profile['dhcp_enabled']=DEFAULT_IP_PROFILE['dhcp_enabled']
                if 'dhcp_start_address' not in ip_profile or ip_profile['dhcp_start_address'] is None:
                    ip_profile['dhcp_start_address']=ip_base + "3"
                if 'ip_version' not in ip_profile or ip_profile['ip_version'] is None:
                    ip_profile['ip_version']=DEFAULT_IP_PROFILE['ip_version']
                if 'dns_address' not in ip_profile or ip_profile['dns_address'] is None:
                    ip_profile['dns_address']=ip_base + "2"

                gateway_address=ip_profile['gateway_address']
                dhcp_count=int(ip_profile['dhcp_count'])
                subnet_address=self.convert_cidr_to_netmask(ip_profile['subnet_address'])

                if ip_profile['dhcp_enabled']==True:
                    dhcp_enabled='true'
                else:
                    dhcp_enabled='false'
                dhcp_start_address=ip_profile['dhcp_start_address']

                #derive dhcp_end_address from dhcp_start_address & dhcp_count
                end_ip_int = int(netaddr.IPAddress(dhcp_start_address))
                end_ip_int += dhcp_count - 1
                dhcp_end_address = str(netaddr.IPAddress(end_ip_int))

                ip_version=ip_profile['ip_version']
                dns_address=ip_profile['dns_address']
            except KeyError as exp:
                self.logger.debug("Create Network REST: Key error {}".format(exp))
                raise vimconn.vimconnException("Create Network REST: Key error{}".format(exp))

            # either use client provided UUID or search for a first available
            #  if both are not defined we return none
            if parent_network_uuid is not None:
                url_list = [self.url, '/api/admin/network/', parent_network_uuid]
                add_vdc_rest_url = ''.join(url_list)

            #Creating all networks as Direct Org VDC type networks.
            #Unused in case of Underlay (data/ptp) network interface.
            fence_mode="bridged"
            is_inherited='false'
            dns_list = dns_address.split(";")
            dns1 = dns_list[0]
            dns2_text = ""
            if len(dns_list) >= 2:
                dns2_text = "\n                                                <Dns2>{}</Dns2>\n".format(dns_list[1])
            data = """ <OrgVdcNetwork name="{0:s}" xmlns="http://www.vmware.com/vcloud/v1.5">
                            <Description>Openmano created</Description>
                                    <Configuration>
                                        <IpScopes>
                                            <IpScope>
                                                <IsInherited>{1:s}</IsInherited>
                                                <Gateway>{2:s}</Gateway>
                                                <Netmask>{3:s}</Netmask>
                                                <Dns1>{4:s}</Dns1>{5:s}
                                                <IsEnabled>{6:s}</IsEnabled>
                                                <IpRanges>
                                                    <IpRange>
                                                        <StartAddress>{7:s}</StartAddress>
                                                        <EndAddress>{8:s}</EndAddress>
                                                    </IpRange>
                                                </IpRanges>
                                            </IpScope>
                                        </IpScopes>
                                        <ParentNetwork href="{9:s}"/>
                                        <FenceMode>{10:s}</FenceMode>
                                    </Configuration>
                                    <IsShared>{11:s}</IsShared>
                        </OrgVdcNetwork> """.format(escape(network_name), is_inherited, gateway_address,
                                                    subnet_address, dns1, dns2_text, dhcp_enabled,
                                                    dhcp_start_address, dhcp_end_address, available_networks,
                                                    fence_mode, isshared)

            headers['Content-Type'] = 'application/vnd.vmware.vcloud.orgVdcNetwork+xml'
            try:
                response = self.perform_request(req_type='POST',
                                           url=add_vdc_rest_url,
                                           headers=headers,
                                           data=data)

                if response.status_code != 201:
                    self.logger.debug("Create Network POST REST API call failed. Return status code {}, Response content: {}"
                                      .format(response.status_code,response.content))
                else:
                    network_task = self.get_task_from_response(response.content)
                    self.logger.debug("Create Network REST : Waiting for Network creation complete")
                    time.sleep(5)
                    result = self.client.get_task_monitor().wait_for_success(task=network_task)
                    if result.get('status') == 'success':   
                        return response.content
                    else:
                        self.logger.debug("create_network_rest task failed. Network Create response : {}"
                                          .format(response.content))
            except Exception as exp:
                self.logger.debug("create_network_rest : Exception : {} ".format(exp))

        return None

    def convert_cidr_to_netmask(self, cidr_ip=None):
        """
        Method sets convert CIDR netmask address to normal IP format
        Args:
            cidr_ip : CIDR IP address
            Returns:
                netmask : Converted netmask
        """
        if cidr_ip is not None:
            if '/' in cidr_ip:
                network, net_bits = cidr_ip.split('/')
                netmask = socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - int(net_bits))) & 0xffffffff))
            else:
                netmask = cidr_ip
            return netmask
        return None

    def get_provider_rest(self, vca=None):
        """
        Method gets provider vdc view from vcloud director

        Args:
            network_name - is network name to be created.
            parent_network_uuid - is parent provider vdc network that will be used for mapping.
            It optional attribute. by default if no parent network indicate the first available will be used.

            Returns:
                The return xml content of respond or None
        """

        url_list = [self.url, '/api/admin']
        if vca:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                       'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
            response = self.perform_request(req_type='GET',
                                            url=''.join(url_list),
                                            headers=headers)

        if response.status_code == requests.codes.ok:
            return response.content
        return None

    def create_vdc(self, vdc_name=None):

        vdc_dict = {}

        xml_content = self.create_vdc_from_tmpl_rest(vdc_name=vdc_name)
        if xml_content is not None:
            try:
                task_resp_xmlroot = XmlElementTree.fromstring(xml_content)
                for child in task_resp_xmlroot:
                    if child.tag.split("}")[1] == 'Owner':
                        vdc_id = child.attrib.get('href').split("/")[-1]
                        vdc_dict[vdc_id] = task_resp_xmlroot.get('href')
                        return vdc_dict
            except:
                self.logger.debug("Respond body {}".format(xml_content))

        return None

    def create_vdc_from_tmpl_rest(self, vdc_name=None):
        """
        Method create vdc in vCloud director based on VDC template.
        it uses pre-defined template.

        Args:
            vdc_name -  name of a new vdc.

            Returns:
                The return xml content of respond or None
        """
        # pre-requesite atleast one vdc template should be available in vCD
        self.logger.info("Creating new vdc {}".format(vdc_name))
        vca = self.connect_as_admin()
        if not vca:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")
        if vdc_name is None:
            return None

        url_list = [self.url, '/api/vdcTemplates']
        vm_list_rest_call = ''.join(url_list)

        headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                    'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']}
        response = self.perform_request(req_type='GET',
                                        url=vm_list_rest_call,
                                        headers=headers)

        # container url to a template
        vdc_template_ref = None
        try:
            vm_list_xmlroot = XmlElementTree.fromstring(response.content)
            for child in vm_list_xmlroot:
                # application/vnd.vmware.admin.providervdc+xml
                # we need find a template from witch we instantiate VDC
                if child.tag.split("}")[1] == 'VdcTemplate':
                    if child.attrib.get('type') == 'application/vnd.vmware.admin.vdcTemplate+xml':
                        vdc_template_ref = child.attrib.get('href')
        except:
            self.logger.debug("Failed parse respond for rest api call {}".format(vm_list_rest_call))
            self.logger.debug("Respond body {}".format(response.content))
            return None

        # if we didn't found required pre defined template we return None
        if vdc_template_ref is None:
            return None

        try:
            # instantiate vdc
            url_list = [self.url, '/api/org/', self.org_uuid, '/action/instantiate']
            vm_list_rest_call = ''.join(url_list)
            data = """<InstantiateVdcTemplateParams name="{0:s}" xmlns="http://www.vmware.com/vcloud/v1.5">
                                        <Source href="{1:s}"></Source>
                                        <Description>opnemano</Description>
                                        </InstantiateVdcTemplateParams>""".format(vdc_name, vdc_template_ref)

            headers['Content-Type'] = 'application/vnd.vmware.vcloud.instantiateVdcTemplateParams+xml'

            response = self.perform_request(req_type='POST',
                                            url=vm_list_rest_call,
                                            headers=headers,
                                            data=data)

            vdc_task = self.get_task_from_response(response.content)
            self.client.get_task_monitor().wait_for_success(task=vdc_task)

            # if we all ok we respond with content otherwise by default None
            if response.status_code >= 200 and response.status_code < 300:
                return response.content
            return None
        except:
            self.logger.debug("Failed parse respond for rest api call {}".format(vm_list_rest_call))
            self.logger.debug("Respond body {}".format(response.content))

        return None

    def create_vdc_rest(self, vdc_name=None):
        """
        Method create network in vCloud director

        Args:
            vdc_name - vdc name to be created
            Returns:
                The return response
        """

        self.logger.info("Creating new vdc {}".format(vdc_name))

        vca = self.connect_as_admin()
        if not vca:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")
        if vdc_name is None:
            return None

        url_list = [self.url, '/api/admin/org/', self.org_uuid]
        vm_list_rest_call = ''.join(url_list)

        if vca._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                      'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
            response = self.perform_request(req_type='GET',
                                            url=vm_list_rest_call,
                                            headers=headers)

            provider_vdc_ref = None
            add_vdc_rest_url = None
            available_networks = None

            if response.status_code != requests.codes.ok:
                self.logger.debug("REST API call {} failed. Return status code {}".format(vm_list_rest_call,
                                                                                          response.status_code))
                return None
            else:
                try:
                    vm_list_xmlroot = XmlElementTree.fromstring(response.content)
                    for child in vm_list_xmlroot:
                        # application/vnd.vmware.admin.providervdc+xml
                        if child.tag.split("}")[1] == 'Link':
                            if child.attrib.get('type') == 'application/vnd.vmware.admin.createVdcParams+xml' \
                                    and child.attrib.get('rel') == 'add':
                                add_vdc_rest_url = child.attrib.get('href')
                except:
                    self.logger.debug("Failed parse respond for rest api call {}".format(vm_list_rest_call))
                    self.logger.debug("Respond body {}".format(response.content))
                    return None

                response = self.get_provider_rest(vca=vca)
                try:
                    vm_list_xmlroot = XmlElementTree.fromstring(response)
                    for child in vm_list_xmlroot:
                        if child.tag.split("}")[1] == 'ProviderVdcReferences':
                            for sub_child in child:
                                provider_vdc_ref = sub_child.attrib.get('href')
                except:
                    self.logger.debug("Failed parse respond for rest api call {}".format(vm_list_rest_call))
                    self.logger.debug("Respond body {}".format(response))
                    return None

                if add_vdc_rest_url is not None and provider_vdc_ref is not None:
                    data = """ <CreateVdcParams name="{0:s}" xmlns="http://www.vmware.com/vcloud/v1.5"><Description>{1:s}</Description>
                            <AllocationModel>ReservationPool</AllocationModel>
                            <ComputeCapacity><Cpu><Units>MHz</Units><Allocated>2048</Allocated><Limit>2048</Limit></Cpu>
                            <Memory><Units>MB</Units><Allocated>2048</Allocated><Limit>2048</Limit></Memory>
                            </ComputeCapacity><NicQuota>0</NicQuota><NetworkQuota>100</NetworkQuota>
                            <VdcStorageProfile><Enabled>true</Enabled><Units>MB</Units><Limit>20480</Limit><Default>true</Default></VdcStorageProfile>
                            <ProviderVdcReference
                            name="Main Provider"
                            href="{2:s}" />
                    <UsesFastProvisioning>true</UsesFastProvisioning></CreateVdcParams>""".format(escape(vdc_name),
                                                                                                  escape(vdc_name),
                                                                                                  provider_vdc_ref)

                    headers['Content-Type'] = 'application/vnd.vmware.admin.createVdcParams+xml'

                    response = self.perform_request(req_type='POST',
                                                    url=add_vdc_rest_url,
                                                    headers=headers,
                                                    data=data)

                    # if we all ok we respond with content otherwise by default None
                    if response.status_code == 201:
                        return response.content
        return None

    def get_vapp_details_rest(self, vapp_uuid=None, need_admin_access=False):
        """
        Method retrieve vapp detail from vCloud director

        Args:
            vapp_uuid - is vapp identifier.

            Returns:
                The return network uuid or return None
        """

        parsed_respond = {}
        vca = None

        if need_admin_access:
            vca = self.connect_as_admin()
        else:
            vca = self.client 

        if not vca:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")
        if vapp_uuid is None:
            return None

        url_list = [self.url, '/api/vApp/vapp-', vapp_uuid]
        get_vapp_restcall = ''.join(url_list)

        if vca._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                       'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']}  
            response = self.perform_request(req_type='GET',
                                            url=get_vapp_restcall,
                                            headers=headers)

            if response.status_code == 403:
                if need_admin_access == False:
                    response = self.retry_rest('GET', get_vapp_restcall)

            if response.status_code != requests.codes.ok:
                self.logger.debug("REST API call {} failed. Return status code {}".format(get_vapp_restcall,
                                                                                          response.status_code))
                return parsed_respond

            try:
                xmlroot_respond = XmlElementTree.fromstring(response.content)
                parsed_respond['ovfDescriptorUploaded'] = xmlroot_respond.attrib['ovfDescriptorUploaded']

                namespaces = {"vssd":"http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData" ,
                              'ovf': 'http://schemas.dmtf.org/ovf/envelope/1',
                              'vmw': 'http://www.vmware.com/schema/ovf',
                              'vm': 'http://www.vmware.com/vcloud/v1.5',
                              'rasd':"http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData",
                              "vmext":"http://www.vmware.com/vcloud/extension/v1.5",
                              "xmlns":"http://www.vmware.com/vcloud/v1.5"
                             }

                created_section = xmlroot_respond.find('vm:DateCreated', namespaces)
                if created_section is not None:
                    parsed_respond['created'] = created_section.text

                network_section = xmlroot_respond.find('vm:NetworkConfigSection/vm:NetworkConfig', namespaces)
                if network_section is not None and 'networkName' in network_section.attrib:
                    parsed_respond['networkname'] = network_section.attrib['networkName']

                ipscopes_section = \
                    xmlroot_respond.find('vm:NetworkConfigSection/vm:NetworkConfig/vm:Configuration/vm:IpScopes',
                                         namespaces)
                if ipscopes_section is not None:
                    for ipscope in ipscopes_section:
                        for scope in ipscope:
                            tag_key = scope.tag.split("}")[1]
                            if tag_key == 'IpRanges':
                                ip_ranges = scope.getchildren()
                                for ipblock in ip_ranges:
                                    for block in ipblock:
                                        parsed_respond[block.tag.split("}")[1]] = block.text
                            else:
                                parsed_respond[tag_key] = scope.text

                # parse children section for other attrib
                children_section = xmlroot_respond.find('vm:Children/', namespaces)
                if children_section is not None:
                    parsed_respond['name'] = children_section.attrib['name']
                    parsed_respond['nestedHypervisorEnabled'] = children_section.attrib['nestedHypervisorEnabled'] \
                     if  "nestedHypervisorEnabled" in children_section.attrib else None
                    parsed_respond['deployed'] = children_section.attrib['deployed']
                    parsed_respond['status'] = children_section.attrib['status']
                    parsed_respond['vmuuid'] = children_section.attrib['id'].split(":")[-1]
                    network_adapter = children_section.find('vm:NetworkConnectionSection', namespaces)
                    nic_list = []
                    for adapters in network_adapter:
                        adapter_key = adapters.tag.split("}")[1]
                        if adapter_key == 'PrimaryNetworkConnectionIndex':
                            parsed_respond['primarynetwork'] = adapters.text
                        if adapter_key == 'NetworkConnection':
                            vnic = {}
                            if 'network' in adapters.attrib:
                                vnic['network'] = adapters.attrib['network']
                            for adapter in adapters:
                                setting_key = adapter.tag.split("}")[1]
                                vnic[setting_key] = adapter.text
                            nic_list.append(vnic)

                    for link in children_section:
                        if link.tag.split("}")[1] == 'Link' and 'rel' in link.attrib:
                            if link.attrib['rel'] == 'screen:acquireTicket':
                                parsed_respond['acquireTicket'] = link.attrib
                            if link.attrib['rel'] == 'screen:acquireMksTicket':
                                parsed_respond['acquireMksTicket'] = link.attrib

                    parsed_respond['interfaces'] = nic_list
                    vCloud_extension_section = children_section.find('xmlns:VCloudExtension', namespaces)
                    if vCloud_extension_section is not None:
                        vm_vcenter_info = {}
                        vim_info = vCloud_extension_section.find('vmext:VmVimInfo', namespaces)
                        vmext = vim_info.find('vmext:VmVimObjectRef', namespaces)
                        if vmext is not None:
                            vm_vcenter_info["vm_moref_id"] = vmext.find('vmext:MoRef', namespaces).text
                        parsed_respond["vm_vcenter_info"]= vm_vcenter_info

                    virtual_hardware_section = children_section.find('ovf:VirtualHardwareSection', namespaces)
                    vm_virtual_hardware_info = {}
                    if virtual_hardware_section is not None:
                        for item in virtual_hardware_section.iterfind('ovf:Item',namespaces):
                            if item.find("rasd:Description",namespaces).text == "Hard disk":
                                disk_size = item.find("rasd:HostResource" ,namespaces
                                                ).attrib["{"+namespaces['vm']+"}capacity"]

                                vm_virtual_hardware_info["disk_size"]= disk_size
                                break

                        for link in virtual_hardware_section:
                            if link.tag.split("}")[1] == 'Link' and 'rel' in link.attrib:
                                if link.attrib['rel'] == 'edit' and link.attrib['href'].endswith("/disks"):
                                    vm_virtual_hardware_info["disk_edit_href"] = link.attrib['href']
                                    break

                    parsed_respond["vm_virtual_hardware"]= vm_virtual_hardware_info
            except Exception as exp :
                self.logger.info("Error occurred calling rest api for getting vApp details {}".format(exp))
        return parsed_respond

    def acquire_console(self, vm_uuid=None):

        if vm_uuid is None:
            return None
        if self.client._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                       'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
            vm_dict = self.get_vapp_details_rest(vapp_uuid=vm_uuid)
            console_dict = vm_dict['acquireTicket']
            console_rest_call = console_dict['href']

            response = self.perform_request(req_type='POST',
                                            url=console_rest_call,
                                            headers=headers)

            if response.status_code == 403:
                response = self.retry_rest('POST', console_rest_call)

            if response.status_code == requests.codes.ok:
                return response.content

        return None

    def modify_vm_disk(self, vapp_uuid, flavor_disk):
        """
        Method retrieve vm disk details

        Args:
            vapp_uuid - is vapp identifier.
            flavor_disk - disk size as specified in VNFD (flavor)

            Returns:
                The return network uuid or return None
        """
        status = None
        try:
            #Flavor disk is in GB convert it into MB
            flavor_disk = int(flavor_disk) * 1024
            vm_details = self.get_vapp_details_rest(vapp_uuid)
            if vm_details:
                vm_name = vm_details["name"]
                self.logger.info("VM: {} flavor_disk :{}".format(vm_name , flavor_disk))

            if vm_details and "vm_virtual_hardware" in vm_details:
                vm_disk = int(vm_details["vm_virtual_hardware"]["disk_size"])
                disk_edit_href = vm_details["vm_virtual_hardware"]["disk_edit_href"]

                self.logger.info("VM: {} VM_disk :{}".format(vm_name , vm_disk))

                if flavor_disk > vm_disk:
                    status = self.modify_vm_disk_rest(disk_edit_href ,flavor_disk)
                    self.logger.info("Modify disk of VM {} from {} to {} MB".format(vm_name,
                                                         vm_disk,  flavor_disk ))
                else:
                    status = True
                    self.logger.info("No need to modify disk of VM {}".format(vm_name))

            return status
        except Exception as exp:
            self.logger.info("Error occurred while modifing disk size {}".format(exp))


    def modify_vm_disk_rest(self, disk_href , disk_size):
        """
        Method retrieve modify vm disk size

        Args:
            disk_href - vCD API URL to GET and PUT disk data
            disk_size - disk size as specified in VNFD (flavor)

            Returns:
                The return network uuid or return None
        """
        if disk_href is None or disk_size is None:
            return None

        if self.client._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}  
                response = self.perform_request(req_type='GET',
                                                url=disk_href,
                                                headers=headers)

        if response.status_code == 403:
            response = self.retry_rest('GET', disk_href)

        if response.status_code != requests.codes.ok:
            self.logger.debug("GET REST API call {} failed. Return status code {}".format(disk_href,
                                                                            response.status_code))
            return None
        try:
            lxmlroot_respond = lxmlElementTree.fromstring(response.content)
            namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.iteritems() if prefix}
            #For python3
            #namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.items() if prefix}
            namespaces["xmlns"]= "http://www.vmware.com/vcloud/v1.5"

            for item in lxmlroot_respond.iterfind('xmlns:Item',namespaces):
                if item.find("rasd:Description",namespaces).text == "Hard disk":
                    disk_item = item.find("rasd:HostResource" ,namespaces )
                    if disk_item is not None:
                        disk_item.attrib["{"+namespaces['xmlns']+"}capacity"] = str(disk_size)
                        break

            data = lxmlElementTree.tostring(lxmlroot_respond, encoding='utf8', method='xml',
                                             xml_declaration=True)

            #Send PUT request to modify disk size
            headers['Content-Type'] = 'application/vnd.vmware.vcloud.rasdItemsList+xml; charset=ISO-8859-1'

            response = self.perform_request(req_type='PUT',
                                                url=disk_href,
                                                headers=headers,
                                                data=data)
            if response.status_code == 403:
                add_headers = {'Content-Type': headers['Content-Type']}
                response = self.retry_rest('PUT', disk_href, add_headers, data)

            if response.status_code != 202:
                self.logger.debug("PUT REST API call {} failed. Return status code {}".format(disk_href,
                                                                            response.status_code))
            else:
                modify_disk_task = self.get_task_from_response(response.content)
                result = self.client.get_task_monitor().wait_for_success(task=modify_disk_task)
                if result.get('status') == 'success':
                    return True
                else:
                    return False   
            return None

        except Exception as exp :
                self.logger.info("Error occurred calling rest api for modifing disk size {}".format(exp))
                return None

    def add_pci_devices(self, vapp_uuid , pci_devices , vmname_andid):
        """
            Method to attach pci devices to VM

             Args:
                vapp_uuid - uuid of vApp/VM
                pci_devices - pci devices infromation as specified in VNFD (flavor)

            Returns:
                The status of add pci device task , vm object and
                vcenter_conect object
        """
        vm_obj = None
        self.logger.info("Add pci devices {} into vApp {}".format(pci_devices , vapp_uuid))
        vcenter_conect, content = self.get_vcenter_content()
        vm_moref_id = self.get_vm_moref_id(vapp_uuid)

        if vm_moref_id:
            try:
                no_of_pci_devices = len(pci_devices)
                if no_of_pci_devices > 0:
                    #Get VM and its host
                    host_obj, vm_obj = self.get_vm_obj(content, vm_moref_id)
                    self.logger.info("VM {} is currently on host {}".format(vm_obj, host_obj))
                    if host_obj and vm_obj:
                        #get PCI devies from host on which vapp is currently installed
                        avilable_pci_devices = self.get_pci_devices(host_obj, no_of_pci_devices)

                        if avilable_pci_devices is None:
                            #find other hosts with active pci devices
                            new_host_obj , avilable_pci_devices = self.get_host_and_PCIdevices(
                                                                content,
                                                                no_of_pci_devices
                                                                )

                            if new_host_obj is not None and avilable_pci_devices is not None and len(avilable_pci_devices)> 0:
                                #Migrate vm to the host where PCI devices are availble
                                self.logger.info("Relocate VM {} on new host {}".format(vm_obj, new_host_obj))
                                task = self.relocate_vm(new_host_obj, vm_obj)
                                if task is not None:
                                    result = self.wait_for_vcenter_task(task, vcenter_conect)
                                    self.logger.info("Migrate VM status: {}".format(result))
                                    host_obj = new_host_obj
                                else:
                                    self.logger.info("Fail to migrate VM : {}".format(result))
                                    raise vimconn.vimconnNotFoundException(
                                    "Fail to migrate VM : {} to host {}".format(
                                                    vmname_andid,
                                                    new_host_obj)
                                        )

                        if host_obj is not None and avilable_pci_devices is not None and len(avilable_pci_devices)> 0:
                            #Add PCI devices one by one
                            for pci_device in avilable_pci_devices:
                                task = self.add_pci_to_vm(host_obj, vm_obj, pci_device)
                                if task:
                                    status= self.wait_for_vcenter_task(task, vcenter_conect)
                                    if status:
                                        self.logger.info("Added PCI device {} to VM {}".format(pci_device,str(vm_obj)))
                                else:
                                    self.logger.error("Fail to add PCI device {} to VM {}".format(pci_device,str(vm_obj)))
                            return True, vm_obj, vcenter_conect
                        else:
                            self.logger.error("Currently there is no host with"\
                                              " {} number of avaialble PCI devices required for VM {}".format(
                                                                            no_of_pci_devices,
                                                                            vmname_andid)
                                              )
                            raise vimconn.vimconnNotFoundException(
                                    "Currently there is no host with {} "\
                                    "number of avaialble PCI devices required for VM {}".format(
                                                                            no_of_pci_devices,
                                                                            vmname_andid))
                else:
                    self.logger.debug("No infromation about PCI devices {} ",pci_devices)

            except vmodl.MethodFault as error:
                self.logger.error("Error occurred while adding PCI devices {} ",error)
        return None, vm_obj, vcenter_conect

    def get_vm_obj(self, content, mob_id):
        """
            Method to get the vsphere VM object associated with a given morf ID
             Args:
                vapp_uuid - uuid of vApp/VM
                content - vCenter content object
                mob_id - mob_id of VM

            Returns:
                    VM and host object
        """
        vm_obj = None
        host_obj = None
        try :
            container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        [vim.VirtualMachine], True
                                                        )
            for vm in container.view:
                mobID = vm._GetMoId()
                if mobID == mob_id:
                    vm_obj = vm
                    host_obj = vm_obj.runtime.host
                    break
        except Exception as exp:
            self.logger.error("Error occurred while finding VM object : {}".format(exp))
        return host_obj, vm_obj

    def get_pci_devices(self, host, need_devices):
        """
            Method to get the details of pci devices on given host
             Args:
                host - vSphere host object
                need_devices - number of pci devices needed on host

             Returns:
                array of pci devices
        """
        all_devices = []
        all_device_ids = []
        used_devices_ids = []

        try:
            if host:
                pciPassthruInfo = host.config.pciPassthruInfo
                pciDevies = host.hardware.pciDevice

            for pci_status in pciPassthruInfo:
                if pci_status.passthruActive:
                    for device in pciDevies:
                        if device.id == pci_status.id:
                            all_device_ids.append(device.id)
                            all_devices.append(device)

            #check if devices are in use
            avalible_devices = all_devices
            for vm in host.vm:
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    vm_devices = vm.config.hardware.device
                    for device in vm_devices:
                        if type(device) is vim.vm.device.VirtualPCIPassthrough:
                            if device.backing.id in all_device_ids:
                                for use_device in avalible_devices:
                                    if use_device.id == device.backing.id:
                                        avalible_devices.remove(use_device)
                                used_devices_ids.append(device.backing.id)
                                self.logger.debug("Device {} from devices {}"\
                                        "is in use".format(device.backing.id,
                                                           device)
                                            )
            if len(avalible_devices) < need_devices:
                self.logger.debug("Host {} don't have {} number of active devices".format(host,
                                                                            need_devices))
                self.logger.debug("found only {} devives {}".format(len(avalible_devices),
                                                                    avalible_devices))
                return None
            else:
                required_devices = avalible_devices[:need_devices]
                self.logger.info("Found {} PCI devivces on host {} but required only {}".format(
                                                            len(avalible_devices),
                                                            host,
                                                            need_devices))
                self.logger.info("Retruning {} devices as {}".format(need_devices,
                                                                required_devices ))
                return required_devices

        except Exception as exp:
            self.logger.error("Error {} occurred while finding pci devices on host: {}".format(exp, host))

        return None

    def get_host_and_PCIdevices(self, content, need_devices):
        """
         Method to get the details of pci devices infromation on all hosts

            Args:
                content - vSphere host object
                need_devices - number of pci devices needed on host

            Returns:
                 array of pci devices and host object
        """
        host_obj = None
        pci_device_objs = None
        try:
            if content:
                container = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.HostSystem], True)
                for host in container.view:
                    devices = self.get_pci_devices(host, need_devices)
                    if devices:
                        host_obj = host
                        pci_device_objs = devices
                        break
        except Exception as exp:
            self.logger.error("Error {} occurred while finding pci devices on host: {}".format(exp, host_obj))

        return host_obj,pci_device_objs

    def relocate_vm(self, dest_host, vm) :
        """
         Method to get the relocate VM to new host

            Args:
                dest_host - vSphere host object
                vm - vSphere VM object

            Returns:
                task object
        """
        task = None
        try:
            relocate_spec = vim.vm.RelocateSpec(host=dest_host)
            task = vm.Relocate(relocate_spec)
            self.logger.info("Migrating {} to destination host {}".format(vm, dest_host))
        except Exception as exp:
            self.logger.error("Error occurred while relocate VM {} to new host {}: {}".format(
                                                                            dest_host, vm, exp))
        return task

    def wait_for_vcenter_task(self, task, actionName='job', hideResult=False):
        """
        Waits and provides updates on a vSphere task
        """
        while task.info.state == vim.TaskInfo.State.running:
            time.sleep(2)

        if task.info.state == vim.TaskInfo.State.success:
            if task.info.result is not None and not hideResult:
                self.logger.info('{} completed successfully, result: {}'.format(
                                                            actionName,
                                                            task.info.result))
            else:
                self.logger.info('Task {} completed successfully.'.format(actionName))
        else:
            self.logger.error('{} did not complete successfully: {} '.format(
                                                            actionName,
                                                            task.info.error)
                              )

        return task.info.result

    def add_pci_to_vm(self,host_object, vm_object, host_pci_dev):
        """
         Method to add pci device in given VM

            Args:
                host_object - vSphere host object
                vm_object - vSphere VM object
                host_pci_dev -  host_pci_dev must be one of the devices from the
                                host_object.hardware.pciDevice list
                                which is configured as a PCI passthrough device

            Returns:
                task object
        """
        task = None
        if vm_object and host_object and host_pci_dev:
            try :
                #Add PCI device to VM
                pci_passthroughs = vm_object.environmentBrowser.QueryConfigTarget(host=None).pciPassthrough
                systemid_by_pciid = {item.pciDevice.id: item.systemId for item in pci_passthroughs}

                if host_pci_dev.id not in systemid_by_pciid:
                    self.logger.error("Device {} is not a passthrough device ".format(host_pci_dev))
                    return None

                deviceId = hex(host_pci_dev.deviceId % 2**16).lstrip('0x')
                backing = vim.VirtualPCIPassthroughDeviceBackingInfo(deviceId=deviceId,
                                            id=host_pci_dev.id,
                                            systemId=systemid_by_pciid[host_pci_dev.id],
                                            vendorId=host_pci_dev.vendorId,
                                            deviceName=host_pci_dev.deviceName)

                hba_object = vim.VirtualPCIPassthrough(key=-100, backing=backing)

                new_device_config = vim.VirtualDeviceConfigSpec(device=hba_object)
                new_device_config.operation = "add"
                vmConfigSpec = vim.vm.ConfigSpec()
                vmConfigSpec.deviceChange = [new_device_config]

                task = vm_object.ReconfigVM_Task(spec=vmConfigSpec)
                self.logger.info("Adding PCI device {} into VM {} from host {} ".format(
                                                            host_pci_dev, vm_object, host_object)
                                )
            except Exception as exp:
                self.logger.error("Error occurred while adding pci devive {} to VM {}: {}".format(
                                                                            host_pci_dev,
                                                                            vm_object,
                                                                             exp))
        return task

    def get_vm_vcenter_info(self):
        """
        Method to get details of vCenter and vm

            Args:
                vapp_uuid - uuid of vApp or VM

            Returns:
                Moref Id of VM and deails of vCenter
        """
        vm_vcenter_info = {}

        if self.vcenter_ip is not None:
            vm_vcenter_info["vm_vcenter_ip"] = self.vcenter_ip
        else:
            raise vimconn.vimconnException(message="vCenter IP is not provided."\
                                           " Please provide vCenter IP while attaching datacenter to tenant in --config")
        if self.vcenter_port is not None:
            vm_vcenter_info["vm_vcenter_port"] = self.vcenter_port
        else:
            raise vimconn.vimconnException(message="vCenter port is not provided."\
                                           " Please provide vCenter port while attaching datacenter to tenant in --config")
        if self.vcenter_user is not None:
            vm_vcenter_info["vm_vcenter_user"] = self.vcenter_user
        else:
            raise vimconn.vimconnException(message="vCenter user is not provided."\
                                           " Please provide vCenter user while attaching datacenter to tenant in --config")

        if self.vcenter_password is not None:
            vm_vcenter_info["vm_vcenter_password"] = self.vcenter_password
        else:
            raise vimconn.vimconnException(message="vCenter user password is not provided."\
                                           " Please provide vCenter user password while attaching datacenter to tenant in --config")

        return vm_vcenter_info


    def get_vm_pci_details(self, vmuuid):
        """
            Method to get VM PCI device details from vCenter

            Args:
                vm_obj - vSphere VM object

            Returns:
                dict of PCI devives attached to VM

        """
        vm_pci_devices_info = {}
        try:
            vcenter_conect, content = self.get_vcenter_content()
            vm_moref_id = self.get_vm_moref_id(vmuuid)
            if vm_moref_id:
                #Get VM and its host
                if content:
                    host_obj, vm_obj = self.get_vm_obj(content, vm_moref_id)
                    if host_obj and vm_obj:
                        vm_pci_devices_info["host_name"]= host_obj.name
                        vm_pci_devices_info["host_ip"]= host_obj.config.network.vnic[0].spec.ip.ipAddress
                        for device in vm_obj.config.hardware.device:
                            if type(device) == vim.vm.device.VirtualPCIPassthrough:
                                device_details={'devide_id':device.backing.id,
                                                'pciSlotNumber':device.slotInfo.pciSlotNumber,
                                            }
                                vm_pci_devices_info[device.deviceInfo.label] = device_details
                else:
                    self.logger.error("Can not connect to vCenter while getting "\
                                          "PCI devices infromationn")
                return vm_pci_devices_info
        except Exception as exp:
            self.logger.error("Error occurred while getting VM infromationn"\
                             " for VM : {}".format(exp))
            raise vimconn.vimconnException(message=exp)

    def add_network_adapter_to_vms(self, vapp, network_name, primary_nic_index, nicIndex, net, nic_type=None):
        """
            Method to add network adapter type to vm
            Args :
                network_name - name of network
                primary_nic_index - int value for primary nic index
                nicIndex - int value for nic index
                nic_type - specify model name to which add to vm
            Returns:
                None
        """

        try:
            ip_address = None
            floating_ip = False
            mac_address = None
            if 'floating_ip' in net: floating_ip = net['floating_ip']

            # Stub for ip_address feature
            if 'ip_address' in net: ip_address = net['ip_address']

            if 'mac_address' in net: mac_address = net['mac_address']

            if floating_ip:
                allocation_mode = "POOL"
            elif ip_address:
                allocation_mode = "MANUAL"
            else:
                allocation_mode = "DHCP"

            if not nic_type:
                for vms in vapp.get_all_vms():
                    vm_id = vms.get('id').split(':')[-1]

                    url_rest_call = "{}/api/vApp/vm-{}/networkConnectionSection/".format(self.url, vm_id)

                    headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}  
                    response = self.perform_request(req_type='GET',
                                                    url=url_rest_call,
                                                    headers=headers)

                    if response.status_code == 403:
                        response = self.retry_rest('GET', url_rest_call)

                    if response.status_code != 200:
                        self.logger.error("REST call {} failed reason : {}"\
                                             "status code : {}".format(url_rest_call,
                                                                    response.content,
                                                               response.status_code))
                        raise vimconn.vimconnException("add_network_adapter_to_vms : Failed to get "\
                                                                         "network connection section")

                    data = response.content
                    data = data.split('<Link rel="edit"')[0]
                    if '<PrimaryNetworkConnectionIndex>' not in data:
                        item = """<PrimaryNetworkConnectionIndex>{}</PrimaryNetworkConnectionIndex>
                                <NetworkConnection network="{}">
                                <NetworkConnectionIndex>{}</NetworkConnectionIndex>
                                <IsConnected>true</IsConnected>
                                <IpAddressAllocationMode>{}</IpAddressAllocationMode>
                                </NetworkConnection>""".format(primary_nic_index, network_name, nicIndex,
                                                                                         allocation_mode)
                        # Stub for ip_address feature
                        if ip_address:
                            ip_tag = '<IpAddress>{}</IpAddress>'.format(ip_address)
                            item =  item.replace('</NetworkConnectionIndex>\n','</NetworkConnectionIndex>\n{}\n'.format(ip_tag))

                        if mac_address:
                            mac_tag = '<MACAddress>{}</MACAddress>'.format(mac_address)
                            item =  item.replace('</IsConnected>\n','</IsConnected>\n{}\n'.format(mac_tag))

                        data = data.replace('</ovf:Info>\n','</ovf:Info>\n{}\n</NetworkConnectionSection>'.format(item))
                    else:
                        new_item = """<NetworkConnection network="{}">
                                    <NetworkConnectionIndex>{}</NetworkConnectionIndex>
                                    <IsConnected>true</IsConnected>
                                    <IpAddressAllocationMode>{}</IpAddressAllocationMode>
                                    </NetworkConnection>""".format(network_name, nicIndex,
                                                                          allocation_mode)
                        # Stub for ip_address feature
                        if ip_address:
                            ip_tag = '<IpAddress>{}</IpAddress>'.format(ip_address)
                            new_item =  new_item.replace('</NetworkConnectionIndex>\n','</NetworkConnectionIndex>\n{}\n'.format(ip_tag))

                        if mac_address:
                            mac_tag = '<MACAddress>{}</MACAddress>'.format(mac_address)
                            new_item =  new_item.replace('</IsConnected>\n','</IsConnected>\n{}\n'.format(mac_tag))

                        data = data + new_item + '</NetworkConnectionSection>'

                    headers['Content-Type'] = 'application/vnd.vmware.vcloud.networkConnectionSection+xml'

                    response = self.perform_request(req_type='PUT',
                                                    url=url_rest_call,
                                                    headers=headers,
                                                    data=data)

                    if response.status_code == 403:
                        add_headers = {'Content-Type': headers['Content-Type']}
                        response = self.retry_rest('PUT', url_rest_call, add_headers, data)

                    if response.status_code != 202:
                        self.logger.error("REST call {} failed reason : {}"\
                                            "status code : {} ".format(url_rest_call,
                                                                    response.content,
                                                               response.status_code))
                        raise vimconn.vimconnException("add_network_adapter_to_vms : Failed to update "\
                                                                            "network connection section")
                    else:
                        nic_task = self.get_task_from_response(response.content)
                        result = self.client.get_task_monitor().wait_for_success(task=nic_task)  
                        if result.get('status') == 'success':
                            self.logger.info("add_network_adapter_to_vms(): VM {} conneced to "\
                                                               "default NIC type".format(vm_id))
                        else:
                            self.logger.error("add_network_adapter_to_vms(): VM {} failed to "\
                                                              "connect NIC type".format(vm_id))
            else:
                for vms in vapp.get_all_vms():
                    vm_id = vms.get('id').split(':')[-1]


                    url_rest_call = "{}/api/vApp/vm-{}/networkConnectionSection/".format(self.url, vm_id)

                    headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
                    response = self.perform_request(req_type='GET',
                                                    url=url_rest_call,
                                                    headers=headers)

                    if response.status_code == 403:
                        response = self.retry_rest('GET', url_rest_call)

                    if response.status_code != 200:
                        self.logger.error("REST call {} failed reason : {}"\
                                            "status code : {}".format(url_rest_call,
                                                                   response.content,
                                                              response.status_code))
                        raise vimconn.vimconnException("add_network_adapter_to_vms : Failed to get "\
                                                                        "network connection section")
                    data = response.content
                    data = data.split('<Link rel="edit"')[0]
                    if '<PrimaryNetworkConnectionIndex>' not in data:
                        item = """<PrimaryNetworkConnectionIndex>{}</PrimaryNetworkConnectionIndex>
                                <NetworkConnection network="{}">
                                <NetworkConnectionIndex>{}</NetworkConnectionIndex>
                                <IsConnected>true</IsConnected>
                                <IpAddressAllocationMode>{}</IpAddressAllocationMode>
                                <NetworkAdapterType>{}</NetworkAdapterType>
                                </NetworkConnection>""".format(primary_nic_index, network_name, nicIndex,
                                                                               allocation_mode, nic_type)
                        # Stub for ip_address feature
                        if ip_address:
                            ip_tag = '<IpAddress>{}</IpAddress>'.format(ip_address)
                            item =  item.replace('</NetworkConnectionIndex>\n','</NetworkConnectionIndex>\n{}\n'.format(ip_tag))

                        if mac_address:
                            mac_tag = '<MACAddress>{}</MACAddress>'.format(mac_address)
                            item =  item.replace('</IsConnected>\n','</IsConnected>\n{}\n'.format(mac_tag)) 

                        data = data.replace('</ovf:Info>\n','</ovf:Info>\n{}\n</NetworkConnectionSection>'.format(item))
                    else:
                        new_item = """<NetworkConnection network="{}">
                                    <NetworkConnectionIndex>{}</NetworkConnectionIndex>
                                    <IsConnected>true</IsConnected>
                                    <IpAddressAllocationMode>{}</IpAddressAllocationMode>
                                    <NetworkAdapterType>{}</NetworkAdapterType>
                                    </NetworkConnection>""".format(network_name, nicIndex,
                                                                allocation_mode, nic_type)
                        # Stub for ip_address feature
                        if ip_address:
                            ip_tag = '<IpAddress>{}</IpAddress>'.format(ip_address)
                            new_item =  new_item.replace('</NetworkConnectionIndex>\n','</NetworkConnectionIndex>\n{}\n'.format(ip_tag))

                        if mac_address:
                            mac_tag = '<MACAddress>{}</MACAddress>'.format(mac_address)
                            new_item =  new_item.replace('</IsConnected>\n','</IsConnected>\n{}\n'.format(mac_tag))

                        data = data + new_item + '</NetworkConnectionSection>'

                    headers['Content-Type'] = 'application/vnd.vmware.vcloud.networkConnectionSection+xml'

                    response = self.perform_request(req_type='PUT',
                                                    url=url_rest_call,
                                                    headers=headers,
                                                    data=data)

                    if response.status_code == 403:
                        add_headers = {'Content-Type': headers['Content-Type']}
                        response = self.retry_rest('PUT', url_rest_call, add_headers, data)

                    if response.status_code != 202:
                        self.logger.error("REST call {} failed reason : {}"\
                                            "status code : {}".format(url_rest_call,
                                                                   response.content,
                                                              response.status_code))
                        raise vimconn.vimconnException("add_network_adapter_to_vms : Failed to update "\
                                                                           "network connection section")
                    else:
                        nic_task = self.get_task_from_response(response.content)
                        result = self.client.get_task_monitor().wait_for_success(task=nic_task)
                        if result.get('status') == 'success':
                            self.logger.info("add_network_adapter_to_vms(): VM {} "\
                                               "conneced to NIC type {}".format(vm_id, nic_type))
                        else:
                            self.logger.error("add_network_adapter_to_vms(): VM {} "\
                                               "failed to connect NIC type {}".format(vm_id, nic_type))
        except Exception as exp:
            self.logger.error("add_network_adapter_to_vms() : exception occurred "\
                                               "while adding Network adapter")
            raise vimconn.vimconnException(message=exp)


    def set_numa_affinity(self, vmuuid, paired_threads_id):
        """
            Method to assign numa affinity in vm configuration parammeters
            Args :
                vmuuid - vm uuid
                paired_threads_id - one or more virtual processor
                                    numbers
            Returns:
                return if True
        """
        try:
            vcenter_conect, content = self.get_vcenter_content()
            vm_moref_id = self.get_vm_moref_id(vmuuid)

            host_obj, vm_obj = self.get_vm_obj(content ,vm_moref_id)
            if vm_obj:
                config_spec = vim.vm.ConfigSpec()
                config_spec.extraConfig = []
                opt = vim.option.OptionValue()
                opt.key = 'numa.nodeAffinity'
                opt.value = str(paired_threads_id)
                config_spec.extraConfig.append(opt)
                task = vm_obj.ReconfigVM_Task(config_spec)
                if task:
                    result = self.wait_for_vcenter_task(task, vcenter_conect)
                    extra_config = vm_obj.config.extraConfig
                    flag = False
                    for opts in extra_config:
                        if 'numa.nodeAffinity' in opts.key:
                            flag = True
                            self.logger.info("set_numa_affinity: Sucessfully assign numa affinity "\
                                                     "value {} for vm {}".format(opt.value, vm_obj))
                        if flag:
                            return
            else:
                self.logger.error("set_numa_affinity: Failed to assign numa affinity")
        except Exception as exp:
            self.logger.error("set_numa_affinity : exception occurred while setting numa affinity "\
                                                       "for VM {} : {}".format(vm_obj, vm_moref_id))
            raise vimconn.vimconnException("set_numa_affinity : Error {} failed to assign numa "\
                                                                           "affinity".format(exp))


    def cloud_init(self, vapp, cloud_config):
        """
        Method to inject ssh-key
        vapp - vapp object
        cloud_config a dictionary with:
                'key-pairs': (optional) list of strings with the public key to be inserted to the default user
                'users': (optional) list of users to be inserted, each item is a dict with:
                    'name': (mandatory) user name,
                    'key-pairs': (optional) list of strings with the public key to be inserted to the user
                'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                    or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
                'config-files': (optional). List of files to be transferred. Each item is a dict with:
                    'dest': (mandatory) string with the destination absolute path
                    'encoding': (optional, by default text). Can be one of:
                        'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                    'content' (mandatory): string with the content of the file
                    'permissions': (optional) string with file permissions, typically octal notation '0644'
                    'owner': (optional) file owner, string with the format 'owner:group'
                'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk
        """
        try:
            if not isinstance(cloud_config, dict):
                raise Exception("cloud_init : parameter cloud_config is not a dictionary")
            else:
                key_pairs = []
                userdata = []
                if "key-pairs" in cloud_config:
                    key_pairs = cloud_config["key-pairs"]

                if "users" in cloud_config:
                    userdata = cloud_config["users"]

                self.logger.debug("cloud_init : Guest os customization started..")
                customize_script = self.format_script(key_pairs=key_pairs, users_list=userdata)
                customize_script = customize_script.replace("&","&amp;")
                self.guest_customization(vapp, customize_script)

        except Exception as exp:
            self.logger.error("cloud_init : exception occurred while injecting "\
                                                                       "ssh-key")
            raise vimconn.vimconnException("cloud_init : Error {} failed to inject "\
                                                               "ssh-key".format(exp))

    def format_script(self, key_pairs=[], users_list=[]):
        bash_script = """#!/bin/sh
        echo performing customization tasks with param $1 at `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"` >> /root/customization.log
        if [ "$1" = "precustomization" ];then
            echo performing precustomization tasks   on `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"` >> /root/customization.log
        """

        keys = "\n".join(key_pairs)
        if keys:
            keys_data = """
            if [ ! -d /root/.ssh ];then
                mkdir /root/.ssh
                chown root:root /root/.ssh
                chmod 700 /root/.ssh
                touch /root/.ssh/authorized_keys
                chown root:root /root/.ssh/authorized_keys
                chmod 600 /root/.ssh/authorized_keys
                # make centos with selinux happy
                which restorecon && restorecon -Rv /root/.ssh
            else
                touch /root/.ssh/authorized_keys
                chown root:root /root/.ssh/authorized_keys
                chmod 600 /root/.ssh/authorized_keys
            fi
            echo '{key}' >> /root/.ssh/authorized_keys
            """.format(key=keys)

            bash_script+= keys_data

        for user in users_list:
            if 'name' in user: user_name = user['name']
            if 'key-pairs' in user:
                user_keys = "\n".join(user['key-pairs'])
            else:
                user_keys = None

            add_user_name = """
                useradd -d /home/{user_name} -m -g users -s /bin/bash {user_name}
                """.format(user_name=user_name)

            bash_script+= add_user_name

            if user_keys:
                user_keys_data = """
                mkdir /home/{user_name}/.ssh
                chown {user_name}:{user_name} /home/{user_name}/.ssh
                chmod 700 /home/{user_name}/.ssh
                touch /home/{user_name}/.ssh/authorized_keys
                chown {user_name}:{user_name} /home/{user_name}/.ssh/authorized_keys
                chmod 600 /home/{user_name}/.ssh/authorized_keys
                # make centos with selinux happy
                which restorecon && restorecon -Rv /home/{user_name}/.ssh
                echo '{user_key}' >> /home/{user_name}/.ssh/authorized_keys
                """.format(user_name=user_name,user_key=user_keys)

                bash_script+= user_keys_data

        return bash_script+"\n\tfi"

    def guest_customization(self, vapp, customize_script):
        """
        Method to customize guest os
        vapp - Vapp object
        customize_script - Customize script to be run at first boot of VM.
        """
        for vm in vapp.get_all_vms():
            vm_id = vm.get('id').split(':')[-1]
            vm_name = vm.get('name') 
            vm_name = vm_name.replace('_','-')    
             
            vm_customization_url = "{}/api/vApp/vm-{}/guestCustomizationSection/".format(self.url, vm_id)
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}

            headers['Content-Type'] = "application/vnd.vmware.vcloud.guestCustomizationSection+xml"

            data = """<GuestCustomizationSection
                           xmlns="http://www.vmware.com/vcloud/v1.5"
                           xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"
                           ovf:required="false" href="{}" type="application/vnd.vmware.vcloud.guestCustomizationSection+xml">
                           <ovf:Info>Specifies Guest OS Customization Settings</ovf:Info>
                           <Enabled>true</Enabled>
                           <ChangeSid>false</ChangeSid>
                           <VirtualMachineId>{}</VirtualMachineId>
                           <JoinDomainEnabled>false</JoinDomainEnabled>
                           <UseOrgSettings>false</UseOrgSettings>
                           <AdminPasswordEnabled>false</AdminPasswordEnabled>
                           <AdminPasswordAuto>true</AdminPasswordAuto>
                           <AdminAutoLogonEnabled>false</AdminAutoLogonEnabled>
                           <AdminAutoLogonCount>0</AdminAutoLogonCount>
                           <ResetPasswordRequired>false</ResetPasswordRequired>
                           <CustomizationScript>{}</CustomizationScript>
                           <ComputerName>{}</ComputerName>
                           <Link href="{}" type="application/vnd.vmware.vcloud.guestCustomizationSection+xml" rel="edit"/>
                       </GuestCustomizationSection> 
                   """.format(vm_customization_url,
                                             vm_id,
                                  customize_script,
                                           vm_name,
                              vm_customization_url)  

            response = self.perform_request(req_type='PUT',
                                             url=vm_customization_url,
                                             headers=headers,
                                             data=data)
            if response.status_code == 202:
                guest_task = self.get_task_from_response(response.content)
                self.client.get_task_monitor().wait_for_success(task=guest_task)
                self.logger.info("guest_customization : customized guest os task "\
                                             "completed for VM {}".format(vm_name))
            else:
                self.logger.error("guest_customization : task for customized guest os"\
                                                    "failed for VM {}".format(vm_name))
                raise vimconn.vimconnException("guest_customization : failed to perform"\
                                       "guest os customization on VM {}".format(vm_name))

    def add_new_disk(self, vapp_uuid, disk_size):
        """
            Method to create an empty vm disk

            Args:
                vapp_uuid - is vapp identifier.
                disk_size - size of disk to be created in GB

            Returns:
                None
        """
        status = False
        vm_details = None
        try:
            #Disk size in GB, convert it into MB
            if disk_size is not None:
                disk_size_mb = int(disk_size) * 1024
                vm_details = self.get_vapp_details_rest(vapp_uuid)

            if vm_details and "vm_virtual_hardware" in vm_details:
                self.logger.info("Adding disk to VM: {} disk size:{}GB".format(vm_details["name"], disk_size))
                disk_href = vm_details["vm_virtual_hardware"]["disk_edit_href"]
                status = self.add_new_disk_rest(disk_href, disk_size_mb)

        except Exception as exp:
            msg = "Error occurred while creating new disk {}.".format(exp)
            self.rollback_newvm(vapp_uuid, msg)

        if status:
            self.logger.info("Added new disk to VM: {} disk size:{}GB".format(vm_details["name"], disk_size))
        else:
            #If failed to add disk, delete VM
            msg = "add_new_disk: Failed to add new disk to {}".format(vm_details["name"])
            self.rollback_newvm(vapp_uuid, msg)


    def add_new_disk_rest(self, disk_href, disk_size_mb):
        """
        Retrives vApp Disks section & add new empty disk

        Args:
            disk_href: Disk section href to addd disk
            disk_size_mb: Disk size in MB

            Returns: Status of add new disk task
        """
        status = False
        if self.client._session:
            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}  
            response = self.perform_request(req_type='GET',
                                            url=disk_href,
                                            headers=headers)

        if response.status_code == 403:
            response = self.retry_rest('GET', disk_href)

        if response.status_code != requests.codes.ok:
            self.logger.error("add_new_disk_rest: GET REST API call {} failed. Return status code {}"
                              .format(disk_href, response.status_code))
            return status
        try:
            #Find but type & max of instance IDs assigned to disks
            lxmlroot_respond = lxmlElementTree.fromstring(response.content)
            namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.iteritems() if prefix}
            #For python3
            #namespaces = {prefix:uri for prefix,uri in lxmlroot_respond.nsmap.items() if prefix}
            namespaces["xmlns"]= "http://www.vmware.com/vcloud/v1.5"
            instance_id = 0
            for item in lxmlroot_respond.iterfind('xmlns:Item',namespaces):
                if item.find("rasd:Description",namespaces).text == "Hard disk":
                    inst_id = int(item.find("rasd:InstanceID" ,namespaces).text)
                    if inst_id > instance_id:
                        instance_id = inst_id
                        disk_item = item.find("rasd:HostResource" ,namespaces)
                        bus_subtype = disk_item.attrib["{"+namespaces['xmlns']+"}busSubType"]
                        bus_type = disk_item.attrib["{"+namespaces['xmlns']+"}busType"]

            instance_id = instance_id + 1
            new_item =   """<Item>
                                <rasd:Description>Hard disk</rasd:Description>
                                <rasd:ElementName>New disk</rasd:ElementName>
                                <rasd:HostResource
                                    xmlns:vcloud="http://www.vmware.com/vcloud/v1.5"
                                    vcloud:capacity="{}"
                                    vcloud:busSubType="{}"
                                    vcloud:busType="{}"></rasd:HostResource>
                                <rasd:InstanceID>{}</rasd:InstanceID>
                                <rasd:ResourceType>17</rasd:ResourceType>
                            </Item>""".format(disk_size_mb, bus_subtype, bus_type, instance_id)

            new_data = response.content
            #Add new item at the bottom
            new_data = new_data.replace('</Item>\n</RasdItemsList>', '</Item>\n{}\n</RasdItemsList>'.format(new_item))

            # Send PUT request to modify virtual hardware section with new disk
            headers['Content-Type'] = 'application/vnd.vmware.vcloud.rasdItemsList+xml; charset=ISO-8859-1'

            response = self.perform_request(req_type='PUT',
                                            url=disk_href,
                                            data=new_data,
                                            headers=headers)

            if response.status_code == 403:
                add_headers = {'Content-Type': headers['Content-Type']}
                response = self.retry_rest('PUT', disk_href, add_headers, new_data)

            if response.status_code != 202:
                self.logger.error("PUT REST API call {} failed. Return status code {}. Response Content:{}"
                                  .format(disk_href, response.status_code, response.content))
            else:
                add_disk_task = self.get_task_from_response(response.content)
                result = self.client.get_task_monitor().wait_for_success(task=add_disk_task)
                if result.get('status') == 'success':  
                    status = True
                else:
                    self.logger.error("Add new disk REST task failed to add {} MB disk".format(disk_size_mb)) 

        except Exception as exp:
            self.logger.error("Error occurred calling rest api for creating new disk {}".format(exp))

        return status


    def add_existing_disk(self, catalogs=None, image_id=None, size=None, template_name=None, vapp_uuid=None):
        """
            Method to add existing disk to vm
            Args :
                catalogs - List of VDC catalogs
                image_id - Catalog ID
                template_name - Name of template in catalog
                vapp_uuid - UUID of vApp
            Returns:
                None
        """
        disk_info = None
        vcenter_conect, content = self.get_vcenter_content()
        #find moref-id of vm in image
        catalog_vm_info = self.get_vapp_template_details(catalogs=catalogs,
                                                         image_id=image_id,
                                                        )

        if catalog_vm_info and "vm_vcenter_info" in catalog_vm_info:
            if "vm_moref_id" in catalog_vm_info["vm_vcenter_info"]:
                catalog_vm_moref_id = catalog_vm_info["vm_vcenter_info"].get("vm_moref_id", None)
                if catalog_vm_moref_id:
                    self.logger.info("Moref_id of VM in catalog : {}" .format(catalog_vm_moref_id))
                    host, catalog_vm_obj = self.get_vm_obj(content, catalog_vm_moref_id)
                    if catalog_vm_obj:
                        #find existing disk
                        disk_info = self.find_disk(catalog_vm_obj)
                    else:
                        exp_msg = "No VM with image id {} found".format(image_id)
                        self.rollback_newvm(vapp_uuid, exp_msg, exp_type="NotFound")
        else:
            exp_msg = "No Image found with image ID {} ".format(image_id)
            self.rollback_newvm(vapp_uuid, exp_msg, exp_type="NotFound")

        if disk_info:
            self.logger.info("Existing disk_info : {}".format(disk_info))
            #get VM
            vm_moref_id = self.get_vm_moref_id(vapp_uuid)
            host, vm_obj = self.get_vm_obj(content, vm_moref_id)
            if vm_obj:
                status = self.add_disk(vcenter_conect=vcenter_conect,
                                       vm=vm_obj,
                                       disk_info=disk_info,
                                       size=size,
                                       vapp_uuid=vapp_uuid
                                       )
            if status:
                self.logger.info("Disk from image id {} added to {}".format(image_id,
                                                                            vm_obj.config.name)
                                 )
        else:
            msg = "No disk found with image id {} to add in VM {}".format(
                                                            image_id,
                                                            vm_obj.config.name)
            self.rollback_newvm(vapp_uuid, msg, exp_type="NotFound")


    def find_disk(self, vm_obj):
        """
         Method to find details of existing disk in VM
            Args :
                vm_obj - vCenter object of VM
                image_id - Catalog ID
            Returns:
                disk_info : dict of disk details
        """
        disk_info = {}
        if vm_obj:
            try:
                devices = vm_obj.config.hardware.device
                for device in devices:
                    if type(device) is vim.vm.device.VirtualDisk:
                        if isinstance(device.backing,vim.vm.device.VirtualDisk.FlatVer2BackingInfo) and hasattr(device.backing, 'fileName'):
                            disk_info["full_path"] = device.backing.fileName
                            disk_info["datastore"] = device.backing.datastore
                            disk_info["capacityKB"] = device.capacityInKB
                            break
            except Exception as exp:
                self.logger.error("find_disk() : exception occurred while "\
                                  "getting existing disk details :{}".format(exp))
        return disk_info


    def add_disk(self, vcenter_conect=None, vm=None, size=None, vapp_uuid=None, disk_info={}):
        """
         Method to add existing disk in VM
            Args :
                vcenter_conect - vCenter content object
                vm - vCenter vm object
                disk_info : dict of disk details
            Returns:
                status : status of add disk task
        """
        datastore = disk_info["datastore"] if "datastore" in disk_info else None
        fullpath = disk_info["full_path"] if "full_path" in disk_info else None
        capacityKB = disk_info["capacityKB"] if "capacityKB" in disk_info else None
        if size is not None:
            #Convert size from GB to KB
            sizeKB = int(size) * 1024 * 1024
            #compare size of existing disk and user given size.Assign whicherver is greater
            self.logger.info("Add Existing disk : sizeKB {} , capacityKB {}".format(
                                                                    sizeKB, capacityKB))
            if sizeKB > capacityKB:
                capacityKB = sizeKB

        if datastore and fullpath and capacityKB:
            try:
                spec = vim.vm.ConfigSpec()
                # get all disks on a VM, set unit_number to the next available
                unit_number = 0
                for dev in vm.config.hardware.device:
                    if hasattr(dev.backing, 'fileName'):
                        unit_number = int(dev.unitNumber) + 1
                        # unit_number 7 reserved for scsi controller
                        if unit_number == 7:
                            unit_number += 1
                    if isinstance(dev, vim.vm.device.VirtualDisk):
                        #vim.vm.device.VirtualSCSIController
                        controller_key = dev.controllerKey

                self.logger.info("Add Existing disk : unit number {} , controller key {}".format(
                                                                    unit_number, controller_key))
                # add disk here
                dev_changes = []
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                disk_spec.device = vim.vm.device.VirtualDisk()
                disk_spec.device.backing = \
                    vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                disk_spec.device.backing.thinProvisioned = True
                disk_spec.device.backing.diskMode = 'persistent'
                disk_spec.device.backing.datastore  = datastore
                disk_spec.device.backing.fileName  = fullpath

                disk_spec.device.unitNumber = unit_number
                disk_spec.device.capacityInKB = capacityKB
                disk_spec.device.controllerKey = controller_key
                dev_changes.append(disk_spec)
                spec.deviceChange = dev_changes
                task = vm.ReconfigVM_Task(spec=spec)
                status = self.wait_for_vcenter_task(task, vcenter_conect)
                return status
            except Exception as exp:
                exp_msg = "add_disk() : exception {} occurred while adding disk "\
                          "{} to vm {}".format(exp,
                                               fullpath,
                                               vm.config.name)
                self.rollback_newvm(vapp_uuid, exp_msg)
        else:
            msg = "add_disk() : Can not add disk to VM with disk info {} ".format(disk_info)
            self.rollback_newvm(vapp_uuid, msg)


    def get_vcenter_content(self):
        """
         Get the vsphere content object
        """
        try:
            vm_vcenter_info = self.get_vm_vcenter_info()
        except Exception as exp:
            self.logger.error("Error occurred while getting vCenter infromationn"\
                             " for VM : {}".format(exp))
            raise vimconn.vimconnException(message=exp)

        context = None
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()

        vcenter_conect = SmartConnect(
                    host=vm_vcenter_info["vm_vcenter_ip"],
                    user=vm_vcenter_info["vm_vcenter_user"],
                    pwd=vm_vcenter_info["vm_vcenter_password"],
                    port=int(vm_vcenter_info["vm_vcenter_port"]),
                    sslContext=context
                )
        atexit.register(Disconnect, vcenter_conect)
        content = vcenter_conect.RetrieveContent()
        return vcenter_conect, content


    def get_vm_moref_id(self, vapp_uuid):
        """
        Get the moref_id of given VM
        """
        try:
            if vapp_uuid:
                vm_details = self.get_vapp_details_rest(vapp_uuid, need_admin_access=True)
                if vm_details and "vm_vcenter_info" in vm_details:
                    vm_moref_id = vm_details["vm_vcenter_info"].get("vm_moref_id", None)
            return vm_moref_id

        except Exception as exp:
            self.logger.error("Error occurred while getting VM moref ID "\
                             " for VM : {}".format(exp))
            return None


    def get_vapp_template_details(self, catalogs=None, image_id=None , template_name=None):
        """
            Method to get vApp template details
                Args :
                    catalogs - list of VDC catalogs
                    image_id - Catalog ID to find
                    template_name : template name in catalog
                Returns:
                    parsed_respond : dict of vApp tempalte details
        """
        parsed_response = {}

        vca = self.connect_as_admin()
        if not vca:
            raise vimconn.vimconnConnectionException("Failed to connect vCD")

        try:
            org, vdc = self.get_vdc_details()
            catalog = self.get_catalog_obj(image_id, catalogs)
            if catalog:
                items = org.get_catalog_item(catalog.get('name'), catalog.get('name'))
                catalog_items = [items.attrib]

                if len(catalog_items) == 1:
                    headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']} 

                    response = self.perform_request(req_type='GET',
                                                    url=catalog_items[0].get('href'),
                                                    headers=headers)
                    catalogItem = XmlElementTree.fromstring(response.content)
                    entity = [child for child in catalogItem if child.get("type") == "application/vnd.vmware.vcloud.vAppTemplate+xml"][0]
                    vapp_tempalte_href = entity.get("href")
                    #get vapp details and parse moref id

                    namespaces = {"vssd":"http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData" ,
                                  'ovf': 'http://schemas.dmtf.org/ovf/envelope/1',
                                  'vmw': 'http://www.vmware.com/schema/ovf',
                                  'vm': 'http://www.vmware.com/vcloud/v1.5',
                                  'rasd':"http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData",
                                  'vmext':"http://www.vmware.com/vcloud/extension/v1.5",
                                  'xmlns':"http://www.vmware.com/vcloud/v1.5"
                                }

                    if vca._session:
                        response = self.perform_request(req_type='GET',
                                                    url=vapp_tempalte_href,
                                                    headers=headers)

                        if response.status_code != requests.codes.ok:
                            self.logger.debug("REST API call {} failed. Return status code {}".format(
                                                vapp_tempalte_href, response.status_code))

                        else:
                            xmlroot_respond = XmlElementTree.fromstring(response.content)
                            children_section = xmlroot_respond.find('vm:Children/', namespaces)
                            if children_section is not None:
                                vCloud_extension_section = children_section.find('xmlns:VCloudExtension', namespaces)
                            if vCloud_extension_section is not None:
                                vm_vcenter_info = {}
                                vim_info = vCloud_extension_section.find('vmext:VmVimInfo', namespaces)
                                vmext = vim_info.find('vmext:VmVimObjectRef', namespaces)
                                if vmext is not None:
                                    vm_vcenter_info["vm_moref_id"] = vmext.find('vmext:MoRef', namespaces).text
                                parsed_response["vm_vcenter_info"]= vm_vcenter_info

        except Exception as exp :
            self.logger.info("Error occurred calling rest api for getting vApp details {}".format(exp))

        return parsed_response


    def rollback_newvm(self, vapp_uuid, msg , exp_type="Genric"):
        """
            Method to delete vApp
                Args :
                    vapp_uuid - vApp UUID
                    msg - Error message to be logged
                    exp_type : Exception type
                Returns:
                    None
        """
        if vapp_uuid:
            status = self.delete_vminstance(vapp_uuid)
        else:
            msg = "No vApp ID"
        self.logger.error(msg)
        if exp_type == "Genric":
            raise vimconn.vimconnException(msg)
        elif exp_type == "NotFound":
            raise vimconn.vimconnNotFoundException(message=msg)

    def add_sriov(self, vapp_uuid, sriov_nets, vmname_andid):
        """
            Method to attach SRIOV adapters to VM

             Args:
                vapp_uuid - uuid of vApp/VM
                sriov_nets - SRIOV devices infromation as specified in VNFD (flavor)
                vmname_andid - vmname

            Returns:
                The status of add SRIOV adapter task , vm object and
                vcenter_conect object
        """
        vm_obj = None
        vcenter_conect, content = self.get_vcenter_content()
        vm_moref_id = self.get_vm_moref_id(vapp_uuid)

        if vm_moref_id:
            try:
                no_of_sriov_devices = len(sriov_nets)
                if no_of_sriov_devices > 0:
                    #Get VM and its host
                    host_obj, vm_obj = self.get_vm_obj(content, vm_moref_id)
                    self.logger.info("VM {} is currently on host {}".format(vm_obj, host_obj))
                    if host_obj and vm_obj:
                        #get SRIOV devies from host on which vapp is currently installed
                        avilable_sriov_devices = self.get_sriov_devices(host_obj,
                                                                no_of_sriov_devices,
                                                                )

                        if len(avilable_sriov_devices) == 0:
                            #find other hosts with active pci devices
                            new_host_obj , avilable_sriov_devices = self.get_host_and_sriov_devices(
                                                                content,
                                                                no_of_sriov_devices,
                                                                )

                            if new_host_obj is not None and len(avilable_sriov_devices)> 0:
                                #Migrate vm to the host where SRIOV devices are available
                                self.logger.info("Relocate VM {} on new host {}".format(vm_obj,
                                                                                    new_host_obj))
                                task = self.relocate_vm(new_host_obj, vm_obj)
                                if task is not None:
                                    result = self.wait_for_vcenter_task(task, vcenter_conect)
                                    self.logger.info("Migrate VM status: {}".format(result))
                                    host_obj = new_host_obj
                                else:
                                    self.logger.info("Fail to migrate VM : {}".format(result))
                                    raise vimconn.vimconnNotFoundException(
                                    "Fail to migrate VM : {} to host {}".format(
                                                    vmname_andid,
                                                    new_host_obj)
                                        )

                        if host_obj is not None and avilable_sriov_devices is not None and len(avilable_sriov_devices)> 0:
                            #Add SRIOV devices one by one
                            for sriov_net in sriov_nets:
                                network_name = sriov_net.get('net_id')
                                dvs_portgr_name = self.create_dvPort_group(network_name)
                                if sriov_net.get('type') == "VF" or sriov_net.get('type') == "SR-IOV":
                                    #add vlan ID ,Modify portgroup for vlan ID
                                    self.configure_vlanID(content, vcenter_conect, network_name)

                                task = self.add_sriov_to_vm(content,
                                                            vm_obj,
                                                            host_obj,
                                                            network_name,
                                                            avilable_sriov_devices[0]
                                                            )
                                if task:
                                    status= self.wait_for_vcenter_task(task, vcenter_conect)
                                    if status:
                                        self.logger.info("Added SRIOV {} to VM {}".format(
                                                                        no_of_sriov_devices,
                                                                        str(vm_obj)))
                                else:
                                    self.logger.error("Fail to add SRIOV {} to VM {}".format(
                                                                        no_of_sriov_devices,
                                                                        str(vm_obj)))
                                    raise vimconn.vimconnUnexpectedResponse(
                                    "Fail to add SRIOV adapter in VM ".format(str(vm_obj))
                                        )
                            return True, vm_obj, vcenter_conect
                        else:
                            self.logger.error("Currently there is no host with"\
                                              " {} number of avaialble SRIOV "\
                                              "VFs required for VM {}".format(
                                                                no_of_sriov_devices,
                                                                vmname_andid)
                                              )
                            raise vimconn.vimconnNotFoundException(
                                    "Currently there is no host with {} "\
                                    "number of avaialble SRIOV devices required for VM {}".format(
                                                                            no_of_sriov_devices,
                                                                            vmname_andid))
                else:
                    self.logger.debug("No infromation about SRIOV devices {} ",sriov_nets)

            except vmodl.MethodFault as error:
                self.logger.error("Error occurred while adding SRIOV {} ",error)
        return None, vm_obj, vcenter_conect


    def get_sriov_devices(self,host, no_of_vfs):
        """
            Method to get the details of SRIOV devices on given host
             Args:
                host - vSphere host object
                no_of_vfs - number of VFs needed on host

             Returns:
                array of SRIOV devices
        """
        sriovInfo=[]
        if host:
            for device in host.config.pciPassthruInfo:
                if isinstance(device,vim.host.SriovInfo) and device.sriovActive:
                    if device.numVirtualFunction >= no_of_vfs:
                        sriovInfo.append(device)
                        break
        return sriovInfo


    def get_host_and_sriov_devices(self, content, no_of_vfs):
        """
         Method to get the details of SRIOV devices infromation on all hosts

            Args:
                content - vSphere host object
                no_of_vfs - number of pci VFs needed on host

            Returns:
                 array of SRIOV devices and host object
        """
        host_obj = None
        sriov_device_objs = None
        try:
            if content:
                container = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.HostSystem], True)
                for host in container.view:
                    devices = self.get_sriov_devices(host, no_of_vfs)
                    if devices:
                        host_obj = host
                        sriov_device_objs = devices
                        break
        except Exception as exp:
            self.logger.error("Error {} occurred while finding SRIOV devices on host: {}".format(exp, host_obj))

        return host_obj,sriov_device_objs


    def add_sriov_to_vm(self,content, vm_obj, host_obj, network_name, sriov_device):
        """
         Method to add SRIOV adapter to vm

            Args:
                host_obj - vSphere host object
                vm_obj - vSphere vm object
                content - vCenter content object
                network_name - name of distributed virtaul portgroup
                sriov_device - SRIOV device info

            Returns:
                 task object
        """
        devices = []
        vnic_label = "sriov nic"
        try:
            dvs_portgr = self.get_dvport_group(network_name)
            network_name = dvs_portgr.name
            nic = vim.vm.device.VirtualDeviceSpec()
            # VM device
            nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic.device = vim.vm.device.VirtualSriovEthernetCard()
            nic.device.addressType = 'assigned'
            #nic.device.key = 13016
            nic.device.deviceInfo = vim.Description()
            nic.device.deviceInfo.label = vnic_label
            nic.device.deviceInfo.summary = network_name
            nic.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()

            nic.device.backing.network = self.get_obj(content, [vim.Network], network_name)
            nic.device.backing.deviceName = network_name
            nic.device.backing.useAutoDetect = False
            nic.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic.device.connectable.startConnected = True
            nic.device.connectable.allowGuestControl = True

            nic.device.sriovBacking = vim.vm.device.VirtualSriovEthernetCard.SriovBackingInfo()
            nic.device.sriovBacking.physicalFunctionBacking = vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo()
            nic.device.sriovBacking.physicalFunctionBacking.id = sriov_device.id

            devices.append(nic)
            vmconf = vim.vm.ConfigSpec(deviceChange=devices)
            task = vm_obj.ReconfigVM_Task(vmconf)
            return task
        except Exception as exp:
            self.logger.error("Error {} occurred while adding SRIOV adapter in VM: {}".format(exp, vm_obj))
            return None


    def create_dvPort_group(self, network_name):
        """
         Method to create disributed virtual portgroup

            Args:
                network_name - name of network/portgroup

            Returns:
                portgroup key
        """
        try:
            new_network_name = [network_name, '-', str(uuid.uuid4())]
            network_name=''.join(new_network_name)
            vcenter_conect, content = self.get_vcenter_content()

            dv_switch = self.get_obj(content, [vim.DistributedVirtualSwitch], self.dvs_name)
            if dv_switch:
                dv_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
                dv_pg_spec.name = network_name

                dv_pg_spec.type = vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding
                dv_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
                dv_pg_spec.defaultPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
                dv_pg_spec.defaultPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy(value=False)
                dv_pg_spec.defaultPortConfig.securityPolicy.forgedTransmits = vim.BoolPolicy(value=False)
                dv_pg_spec.defaultPortConfig.securityPolicy.macChanges = vim.BoolPolicy(value=False)

                task = dv_switch.AddDVPortgroup_Task([dv_pg_spec])
                self.wait_for_vcenter_task(task, vcenter_conect)

                dvPort_group = self.get_obj(content, [vim.dvs.DistributedVirtualPortgroup], network_name)
                if dvPort_group:
                    self.logger.info("Created disributed virtaul port group: {}".format(dvPort_group))
                    return dvPort_group.key
            else:
                self.logger.debug("No disributed virtual switch found with name {}".format(network_name))

        except Exception as exp:
            self.logger.error("Error occurred while creating disributed virtaul port group {}"\
                             " : {}".format(network_name, exp))
        return None

    def reconfig_portgroup(self, content, dvPort_group_name , config_info={}):
        """
         Method to reconfigure disributed virtual portgroup

            Args:
                dvPort_group_name - name of disributed virtual portgroup
                content - vCenter content object
                config_info - disributed virtual portgroup configuration

            Returns:
                task object
        """
        try:
            dvPort_group = self.get_dvport_group(dvPort_group_name)
            if dvPort_group:
                dv_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
                dv_pg_spec.configVersion = dvPort_group.config.configVersion
                dv_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
                if "vlanID" in config_info:
                    dv_pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
                    dv_pg_spec.defaultPortConfig.vlan.vlanId = config_info.get('vlanID')

                task = dvPort_group.ReconfigureDVPortgroup_Task(spec=dv_pg_spec)
                return task
            else:
                return None
        except Exception as exp:
            self.logger.error("Error occurred while reconfiguraing disributed virtaul port group {}"\
                             " : {}".format(dvPort_group_name, exp))
            return None


    def destroy_dvport_group(self , dvPort_group_name):
        """
         Method to destroy disributed virtual portgroup

            Args:
                network_name - name of network/portgroup

            Returns:
                True if portgroup successfully got deleted else false
        """
        vcenter_conect, content = self.get_vcenter_content()
        try:
            status = None
            dvPort_group = self.get_dvport_group(dvPort_group_name)
            if dvPort_group:
                task = dvPort_group.Destroy_Task()
                status = self.wait_for_vcenter_task(task, vcenter_conect)
            return status
        except vmodl.MethodFault as exp:
            self.logger.error("Caught vmodl fault {} while deleting disributed virtaul port group {}".format(
                                                                    exp, dvPort_group_name))
            return None


    def get_dvport_group(self, dvPort_group_name):
        """
        Method to get disributed virtual portgroup

            Args:
                network_name - name of network/portgroup

            Returns:
                portgroup object
        """
        vcenter_conect, content = self.get_vcenter_content()
        dvPort_group = None
        try:
            container = content.viewManager.CreateContainerView(content.rootFolder, [vim.dvs.DistributedVirtualPortgroup], True)
            for item in container.view:
                if item.key == dvPort_group_name:
                    dvPort_group = item
                    break
            return dvPort_group
        except vmodl.MethodFault as exp:
            self.logger.error("Caught vmodl fault {} for disributed virtaul port group {}".format(
                                                                            exp, dvPort_group_name))
            return None

    def get_vlanID_from_dvs_portgr(self, dvPort_group_name):
        """
         Method to get disributed virtual portgroup vlanID

            Args:
                network_name - name of network/portgroup

            Returns:
                vlan ID
        """
        vlanId = None
        try:
            dvPort_group = self.get_dvport_group(dvPort_group_name)
            if dvPort_group:
                vlanId = dvPort_group.config.defaultPortConfig.vlan.vlanId
        except vmodl.MethodFault as exp:
            self.logger.error("Caught vmodl fault {} for disributed virtaul port group {}".format(
                                                                            exp, dvPort_group_name))
        return vlanId


    def configure_vlanID(self, content, vcenter_conect, dvPort_group_name):
        """
         Method to configure vlanID in disributed virtual portgroup vlanID

            Args:
                network_name - name of network/portgroup

            Returns:
                None
        """
        vlanID = self.get_vlanID_from_dvs_portgr(dvPort_group_name)
        if vlanID == 0:
            #configure vlanID
            vlanID = self.genrate_vlanID(dvPort_group_name)
            config = {"vlanID":vlanID}
            task = self.reconfig_portgroup(content, dvPort_group_name,
                                    config_info=config)
            if task:
                status= self.wait_for_vcenter_task(task, vcenter_conect)
                if status:
                    self.logger.info("Reconfigured Port group {} for vlan ID {}".format(
                                                        dvPort_group_name,vlanID))
            else:
                self.logger.error("Fail reconfigure portgroup {} for vlanID{}".format(
                                        dvPort_group_name, vlanID))


    def genrate_vlanID(self, network_name):
        """
         Method to get unused vlanID
            Args:
                network_name - name of network/portgroup
            Returns:
                vlanID
        """
        vlan_id = None
        used_ids = []
        if self.config.get('vlanID_range') == None:
            raise vimconn.vimconnConflictException("You must provide a 'vlanID_range' "\
                        "at config value before creating sriov network with vlan tag")
        if "used_vlanIDs" not in self.persistent_info:
                self.persistent_info["used_vlanIDs"] = {}
        else:
            used_ids = self.persistent_info["used_vlanIDs"].values()
            #For python3
            #used_ids = list(self.persistent_info["used_vlanIDs"].values())

        for vlanID_range in self.config.get('vlanID_range'):
            start_vlanid , end_vlanid = vlanID_range.split("-")
            if start_vlanid > end_vlanid:
                raise vimconn.vimconnConflictException("Invalid vlan ID range {}".format(
                                                                        vlanID_range))

            for id in xrange(int(start_vlanid), int(end_vlanid) + 1):
            #For python3
            #for id in range(int(start_vlanid), int(end_vlanid) + 1):
                if id not in used_ids:
                    vlan_id = id
                    self.persistent_info["used_vlanIDs"][network_name] = vlan_id
                    return vlan_id
        if vlan_id is None:
            raise vimconn.vimconnConflictException("All Vlan IDs are in use")


    def get_obj(self, content, vimtype, name):
        """
         Get the vsphere object associated with a given text name
        """
        obj = None
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for item in container.view:
            if item.name == name:
                obj = item
                break
        return obj


    def insert_media_to_vm(self, vapp, image_id):
        """
        Method to insert media CD-ROM (ISO image) from catalog to vm.
        vapp - vapp object to get vm id
        Image_id - image id for cdrom to be inerted to vm
        """
        # create connection object
        vca = self.connect()
        try:
            # fetching catalog details
            rest_url = "{}/api/catalog/{}".format(self.url, image_id)
            if vca._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']}  
                response = self.perform_request(req_type='GET',
                                                url=rest_url,
                                                headers=headers)

            if response.status_code != 200:
                self.logger.error("REST call {} failed reason : {}"\
                             "status code : {}".format(url_rest_call,
                                                    response.content,
                                               response.status_code))
                raise vimconn.vimconnException("insert_media_to_vm(): Failed to get "\
                                                                    "catalog details")
            # searching iso name and id
            iso_name,media_id = self.get_media_details(vca, response.content)

            if iso_name and media_id:
                data ="""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                     <ns6:MediaInsertOrEjectParams
                     xmlns="http://www.vmware.com/vcloud/versions" xmlns:ns2="http://schemas.dmtf.org/ovf/envelope/1" xmlns:ns3="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData" xmlns:ns4="http://schemas.dmtf.org/wbem/wscim/1/common" xmlns:ns5="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData" xmlns:ns6="http://www.vmware.com/vcloud/v1.5" xmlns:ns7="http://www.vmware.com/schema/ovf" xmlns:ns8="http://schemas.dmtf.org/ovf/environment/1" xmlns:ns9="http://www.vmware.com/vcloud/extension/v1.5">
                     <ns6:Media
                        type="application/vnd.vmware.vcloud.media+xml"
                        name="{}.iso"
                        id="urn:vcloud:media:{}"
                        href="https://{}/api/media/{}"/>
                     </ns6:MediaInsertOrEjectParams>""".format(iso_name, media_id,
                                                                self.url,media_id)

                for vms in vapp.get_all_vms():
                    vm_id = vms.get('id').split(':')[-1]

                    headers['Content-Type'] = 'application/vnd.vmware.vcloud.mediaInsertOrEjectParams+xml'
                    rest_url = "{}/api/vApp/vm-{}/media/action/insertMedia".format(self.url,vm_id)

                    response = self.perform_request(req_type='POST',
                                                       url=rest_url,
                                                          data=data,
                                                    headers=headers)

                    if response.status_code != 202:
                        self.logger.error("Failed to insert CD-ROM to vm")
                        raise vimconn.vimconnException("insert_media_to_vm() : Failed to insert"\
                                                                                    "ISO image to vm")
                    else:
                        task = self.get_task_from_response(response.content)
                        result = self.client.get_task_monitor().wait_for_success(task=task)
                        if result.get('status') == 'success':
                            self.logger.info("insert_media_to_vm(): Sucessfully inserted media ISO"\
                                                                    " image to vm {}".format(vm_id))

        except Exception as exp:
            self.logger.error("insert_media_to_vm() : exception occurred "\
                                            "while inserting media CD-ROM")
            raise vimconn.vimconnException(message=exp)


    def get_media_details(self, vca, content):
        """
        Method to get catalog item details
        vca - connection object
        content - Catalog details
        Return - Media name, media id
        """
        cataloghref_list = []
        try:
            if content:
                vm_list_xmlroot = XmlElementTree.fromstring(content)
                for child in vm_list_xmlroot.iter():
                    if 'CatalogItem' in child.tag:
                        cataloghref_list.append(child.attrib.get('href'))
                if cataloghref_list is not None:
                    for href in cataloghref_list:
                        if href:
                            headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': vca._session.headers['x-vcloud-authorization']}  
                            response = self.perform_request(req_type='GET',
                                                                  url=href,
                                                           headers=headers)
                            if response.status_code != 200:
                                self.logger.error("REST call {} failed reason : {}"\
                                             "status code : {}".format(href,
                                                           response.content,
                                                      response.status_code))
                                raise vimconn.vimconnException("get_media_details : Failed to get "\
                                                                         "catalogitem details")
                            list_xmlroot = XmlElementTree.fromstring(response.content)
                            for child in list_xmlroot.iter():
                                if 'Entity' in child.tag:
                                    if 'media' in child.attrib.get('href'):
                                        name = child.attrib.get('name')
                                        media_id = child.attrib.get('href').split('/').pop()
                                        return name,media_id
                            else:
                                self.logger.debug("Media name and id not found")
                                return False,False
        except Exception as exp:
            self.logger.error("get_media_details : exception occurred "\
                                               "getting media details")
            raise vimconn.vimconnException(message=exp)


    def retry_rest(self, method, url, add_headers=None, data=None):
        """ Method to get Token & retry respective REST request
            Args:
                api - REST API - Can be one of 'GET' or 'PUT' or 'POST'
                url - request url to be used
                add_headers - Additional headers (optional)
                data - Request payload data to be passed in request
            Returns:
                response - Response of request
        """
        response = None

        #Get token
        self.get_token()

        if self.client._session:
                headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                           'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}  

        if add_headers:
            headers.update(add_headers)

        if method == 'GET':
            response = self.perform_request(req_type='GET',
                                            url=url,
                                            headers=headers)
        elif method == 'PUT':
            response = self.perform_request(req_type='PUT',
                                            url=url,
                                            headers=headers,
                                            data=data)     
        elif method == 'POST':
            response = self.perform_request(req_type='POST',
                                            url=url,
                                            headers=headers,
                                            data=data) 
        elif method == 'DELETE':
            response = self.perform_request(req_type='DELETE',
                                            url=url,
                                            headers=headers)
        return response


    def get_token(self):
        """ Generate a new token if expired

            Returns:
                The return client object that letter can be used to connect to vCloud director as admin for VDC
        """
        try:
            self.logger.debug("Generate token for vca {} as {} to datacenter {}.".format(self.org_name,
                                                                                      self.user,
                                                                                      self.org_name))
            host = self.url
            client = Client(host, verify_ssl_certs=False)
            client.set_credentials(BasicLoginCredentials(self.user, self.org_name, self.passwd))
            # connection object
            self.client = client    

        except:
            raise vimconn.vimconnConnectionException("Can't connect to a vCloud director org: "
                                                     "{} as user: {}".format(self.org_name, self.user))

        if not client:
            raise vimconn.vimconnConnectionException("Failed while reconnecting vCD")


    def get_vdc_details(self):
        """ Get VDC details using pyVcloud Lib

            Returns org and vdc object
        """
        org = Org(self.client, resource=self.client.get_org())
        vdc = org.get_vdc(self.tenant_name)

        #Retry once, if failed by refreshing token
        if vdc is None:
            self.get_token()
            vdc = org.get_vdc(self.tenant_name)

        return org, vdc


    def perform_request(self, req_type, url, headers=None, data=None):
        """Perform the POST/PUT/GET/DELETE request."""

        #Log REST request details
        self.log_request(req_type, url=url, headers=headers, data=data)
        # perform request and return its result
        if req_type == 'GET':
            response = requests.get(url=url,
                                headers=headers,
                                verify=False)
        elif req_type == 'PUT':
            response = requests.put(url=url,
                                headers=headers,
                                data=data,
                                verify=False)
        elif req_type == 'POST':
            response = requests.post(url=url,
                                 headers=headers,
                                 data=data,
                                 verify=False)
        elif req_type == 'DELETE':
            response = requests.delete(url=url,
                                 headers=headers,
                                 verify=False)
        #Log the REST response
        self.log_response(response)

        return response


    def log_request(self, req_type, url=None, headers=None, data=None):
        """Logs REST request details"""

        if req_type is not None:
            self.logger.debug("Request type: {}".format(req_type))

        if url is not None:
            self.logger.debug("Request url: {}".format(url))

        if headers is not None:
            for header in headers:
                self.logger.debug("Request header: {}: {}".format(header, headers[header]))

        if data is not None:
            self.logger.debug("Request data: {}".format(data))


    def log_response(self, response):
        """Logs REST response details"""

        self.logger.debug("Response status code: {} ".format(response.status_code))


    def get_task_from_response(self, content):
        """
        content - API response content(response.content)
        return task object 
        """
        xmlroot = XmlElementTree.fromstring(content)
        if xmlroot.tag.split('}')[1] == "Task":
            return xmlroot
        else: 
            for ele in xmlroot:
                if ele.tag.split("}")[1] == "Tasks":
                    task = ele[0]
                    break  
            return task


    def power_on_vapp(self,vapp_id, vapp_name):
        """
        vapp_id - vApp uuid
        vapp_name - vAapp name
        return - Task object 
        """
        headers = {'Accept':'application/*+xml;version=' + API_VERSION,
                   'x-vcloud-authorization': self.client._session.headers['x-vcloud-authorization']}
        
        poweron_href = "{}/api/vApp/vapp-{}/power/action/powerOn".format(self.url,
                                                                          vapp_id)
        response = self.perform_request(req_type='POST',
                                       url=poweron_href,
                                        headers=headers)

        if response.status_code != 202:
            self.logger.error("REST call {} failed reason : {}"\
                         "status code : {} ".format(poweron_href,
                                                response.content,
                                           response.status_code))
            raise vimconn.vimconnException("power_on_vapp() : Failed to power on "\
                                                      "vApp {}".format(vapp_name))
        else:
            poweron_task = self.get_task_from_response(response.content)
            return poweron_task


