# -*- coding: utf-8 -*-
##
# This file is standalone vmware vcloud director util
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
# contact with: mbayramov@vmware.com
##

"""

Standalone application that leverage openmano vmware connector work with vCloud director rest api.

 - Provides capability to create and delete VDC for specific organization.
 - Create, delete and manage network for specific VDC
 - List deployed VM's , VAPPs, VDSs, Organization
 - View detail information about VM / Vapp , Organization etc
 - Operate with images upload / boot / power on etc

 Usage example.

 List organization created in vCloud director
  vmwarecli.py -u admin -p qwerty123 -c 172.16.254.206 -U Administrator -P qwerty123 -o test -v TEF list org

 List VDC for particular organization
  vmwarecli.py -u admin -p qwerty123 -c 172.16.254.206 -U Administrator -P qwerty123 -o test -v TEF list vdc

 Upload image
  python vmwarerecli.py image upload /Users/spyroot/Developer/Openmano/Ro/vnfs/cirros/cirros.ovf

 Boot Image
    python vmwarerecli.py -u admin -p qwerty123 -c 172.16.254.206 -o test -v TEF image boot cirros cirros

 View vApp
    python vmwarerecli.py -u admin -p qwerty123 -c 172.16.254.206 -o test -v TEF view vapp 90bd2b4e-f782-46cf-b5e2-c3817dcf6633 -u

 List VMS
    python vmwarerecli.py -u admin -p qwerty123 -c 172.16.254.206 -o test -v TEF list vms

 List VDC in OSM format
  python vmwarerecli.py -u admin -p qwerty123 -c 172.16.254.206 -o test -v TEF list vdc -o

Mustaafa Bayramov
mbayramov@vmware.com
"""
import os
import argparse
import traceback
import uuid

from xml.etree import ElementTree as ET

import sys
from pyvcloud import Http

import logging
import vimconn
import time
import uuid
import urllib3
import requests

from vimconn_vmware import vimconnector
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from prettytable import PrettyTable

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

__author__ = "Mustafa Bayramov"
__date__ = "$16-Sep-2016 11:09:29$"


# TODO move to main vim
def delete_network_action(vca=None, network_uuid=None):
    """
    Method leverages vCloud director and query network based on network uuid

    Args:
        vca - is active VCA connection.
        network_uuid - is a network uuid

        Returns:
            The return XML respond
    """

    if vca is None or network_uuid is None:
        return None

    url_list = [vca.host, '/api/admin/network/', network_uuid]
    vm_list_rest_call = ''.join(url_list)

    if not (not vca.vcloud_session or not vca.vcloud_session.organization):
        response = Http.get(url=vm_list_rest_call,
                            headers=vca.vcloud_session.get_vcloud_headers(),
                            verify=vca.verify,
                            logger=vca.logger)
        if response.status_code == requests.codes.ok:
            print response.content
            return response.content

    return None


def print_vapp(vapp_dict=None):
    """ Method takes vapp_dict and print in tabular format

    Args:
        vapp_dict: container vapp object.

        Returns:
            The return nothing
    """

    # following key available to print
    # {'status': 'POWERED_OFF', 'storageProfileName': '*', 'hardwareVersion': '7', 'vmToolsVersion': '0',
    #  'memoryMB': '384',
    #  'href': 'https://172.16.254.206/api/vAppTemplate/vm-129e22e8-08dc-4cb6-8358-25f635e65d3b',
    #  'isBusy': 'false', 'isDeployed': 'false', 'isInMaintenanceMode': 'false', 'isVAppTemplate': 'true',
    #  'networkName': 'nat', 'isDeleted': 'false', 'catalogName': 'Cirros',
    #  'containerName': 'Cirros Template', #  'container':
    #  'https://172.16.254.206/api/vAppTemplate/vappTemplate-b966453d-c361-4505-9e38-ccef45815e5d',
    #  'name': 'Cirros', 'pvdcHighestSupportedHardwareVersion': '11', 'isPublished': 'false',
    #  'numberOfCpus': '1', 'vdc': 'https://172.16.254.206/api/vdc/a5056f85-418c-4bfd-8041-adb0f48be9d9',
    #  'guestOs': 'Other (32-bit)', 'isVdcEnabled': 'true'}

    if vapp_dict is None:
        return

    vm_table = PrettyTable(['vm   uuid',
                            'vapp name',
                            'vapp uuid',
                            'network name',
                            'storage name',
                            'vcpu', 'memory', 'hw ver','deployed','status'])
    for k in vapp_dict:
        entry = []
        entry.append(k)
        entry.append(vapp_dict[k]['containerName'])
        # vm-b1f5cd4c-2239-4c89-8fdc-a41ff18e0d61
        entry.append(vapp_dict[k]['container'].split('/')[-1:][0][5:])
        entry.append(vapp_dict[k]['networkName'])
        entry.append(vapp_dict[k]['storageProfileName'])
        entry.append(vapp_dict[k]['numberOfCpus'])
        entry.append(vapp_dict[k]['memoryMB'])
        entry.append(vapp_dict[k]['pvdcHighestSupportedHardwareVersion'])
        entry.append(vapp_dict[k]['isDeployed'])
        entry.append(vapp_dict[k]['status'])

        vm_table.add_row(entry)

    print vm_table


def print_org(org_dict=None):
    """ Method takes vapp_dict and print in tabular format

    Args:
        org_dict:  dictionary of organization where key is org uuid.

        Returns:
            The return nothing
    """

    if org_dict is None:
        return

    org_table = PrettyTable(['org uuid', 'name'])
    for k in org_dict:
        entry = [k, org_dict[k]]
        org_table.add_row(entry)

    print org_table


def print_vm_list(vm_dict=None):
    """ Method takes vapp_dict and print in tabular format

    Args:
        vm_dict:  dictionary of organization where key is org uuid.

        Returns:
            The return nothing
    """
    if vm_dict is None:
        return

    vm_table = PrettyTable(
        ['vm uuid', 'vm name', 'vapp uuid', 'vdc uuid', 'network name', 'is deployed', 'vcpu', 'memory', 'status'])

    try:
        for k in vm_dict:
            entry = []
            entry.append(k)
            entry.append(vm_dict[k]['name'])
            entry.append(vm_dict[k]['container'].split('/')[-1:][0][5:])
            entry.append(vm_dict[k]['vdc'].split('/')[-1:][0])
            entry.append(vm_dict[k]['networkName'])
            entry.append(vm_dict[k]['isDeployed'])
            entry.append(vm_dict[k]['numberOfCpus'])
            entry.append(vm_dict[k]['memoryMB'])
            entry.append(vm_dict[k]['status'])
            vm_table.add_row(entry)
        print vm_table
    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        pass


def print_vdc_list(org_dict=None):
    """ Method takes vapp_dict and print in tabular format

    Args:
        org_dict:  dictionary of organization where key is org uuid.

        Returns:
            The return nothing
    """
    if org_dict is None:
        return
    try:
        vdcs_dict = {}
        if org_dict.has_key('vdcs'):
            vdcs_dict = org_dict['vdcs']
        vdc_table = PrettyTable(['vdc uuid', 'vdc name'])
        for k in vdcs_dict:
            entry = [k, vdcs_dict[k]]
            vdc_table.add_row(entry)

        print vdc_table
    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        logger.logger.debug(traceback.format_exc())


def print_network_list(org_dict=None):
    """ Method print network list.

    Args:
        org_dict:   dictionary of organization that contain key networks with a list of all
                    network for for specific VDC

        Returns:
            The return nothing
    """
    if org_dict is None:
        return
    try:
        network_dict = {}
        if org_dict.has_key('networks'):
            network_dict = org_dict['networks']
        network_table = PrettyTable(['network uuid', 'network name'])
        for k in network_dict:
            entry = [k, network_dict[k]]
            network_table.add_row(entry)

        print network_table

    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        logger.logger.debug(traceback.format_exc())


def print_org_details(org_dict=None):
    """ Method takes vapp_dict and print in tabular format

    Args:
        org_dict:  dictionary of organization where key is org uuid.

        Returns:
            The return nothing
    """
    if org_dict is None:
        return
    try:
        catalogs_dict = {}

        print_vdc_list(org_dict=org_dict)
        print_network_list(org_dict=org_dict)

        if org_dict.has_key('catalogs'):
            catalogs_dict = org_dict['catalogs']

        catalog_table = PrettyTable(['catalog uuid', 'catalog name'])
        for k in catalogs_dict:
            entry = [k, catalogs_dict[k]]
            catalog_table.add_row(entry)

        print catalog_table

    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        logger.logger.debug(traceback.format_exc())


def delete_actions(vim=None, action=None, namespace=None):
    if action == 'network' or namespace.action == 'network':
        logger.debug("Requesting delete for network {}".format(namespace.network_name))
        network_uuid = namespace.network_name
        # if request name based we need find UUID
        # TODO optimize it or move to external function
        if not namespace.uuid:
            org_dict = vim.get_org_list()
            for org in org_dict:
                org_net = vim.get_org(org)['networks']
                for network in org_net:
                    if org_net[network] == namespace.network_name:
                        network_uuid = network

        vim.delete_network_action(network_uuid=network_uuid)


def list_actions(vim=None, action=None, namespace=None):
    """ Method provide list object from VDC action

       Args:
           vim - is vcloud director vim connector.
           action - is action for list ( vdc / org etc)
           namespace -  must contain VDC / Org information.

           Returns:
               The return nothing
       """

    org_id = None
    myorgs = vim.get_org_list()
    for org in myorgs:
        if myorgs[org] == namespace.vcdorg:
            org_id = org
        break
    else:
        print(" Invalid organization.")
        return

    if action == 'vms' or namespace.action == 'vms':
        vm_dict = vim.get_vm_list(vdc_name=namespace.vcdvdc)
        print_vm_list(vm_dict=vm_dict)
    elif action == 'vapps' or namespace.action == 'vapps':
        vapp_dict = vim.get_vapp_list(vdc_name=namespace.vcdvdc)
        print_vapp(vapp_dict=vapp_dict)
    elif action == 'networks' or namespace.action == 'networks':
        if namespace.osm:
            osm_print(vim.get_network_list(filter_dict={}))
        else:
            print_network_list(vim.get_org(org_uuid=org_id))
    elif action == 'vdc' or namespace.action == 'vdc':
        if namespace.osm:
            osm_print(vim.get_tenant_list(filter_dict=None))
        else:
            print_vdc_list(vim.get_org(org_uuid=org_id))
    elif action == 'org' or namespace.action == 'org':
        print_org(org_dict=vim.get_org_list())
    else:
        return None


def print_network_details(network_dict=None):
    try:
        network_table = PrettyTable(network_dict.keys())
        entry = [network_dict.values()]
        network_table.add_row(entry[0])
        print network_table
    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        logger.logger.debug(traceback.format_exc())


def osm_print(generic_dict=None):

    try:
        for element in generic_dict:
            table = PrettyTable(element.keys())
            entry = [element.values()]
            table.add_row(entry[0])
        print table
    except KeyError:
        logger.error("wrong key {}".format(KeyError.message))
        logger.logger.debug(traceback.format_exc())


def view_actions(vim=None, action=None, namespace=None):
    org_id = None
    orgs = vim.get_org_list()
    for org in orgs:
        if orgs[org] == namespace.vcdorg:
            org_id = org
        break
    else:
        print(" Invalid organization.")
        return

    myorg = vim.get_org(org_uuid=org_id)

    # view org
    if action == 'org' or namespace.action == 'org':
        org_id = None
        orgs = vim.get_org_list()
        if namespace.uuid:
            if namespace.org_name in orgs:
                org_id = namespace.org_name
        else:
            # we need find UUID based on name provided
            for org in orgs:
                if orgs[org] == namespace.org_name:
                    org_id = org
                    break

        logger.debug("Requesting view for orgs {}".format(org_id))
        print_org_details(vim.get_org(org_uuid=org_id))

    # view vapp action
    if action == 'vapp' or namespace.action == 'vapp':
        if namespace.vapp_name is not None and namespace.uuid:
            logger.debug("Requesting vapp {} for vdc {}".format(namespace.vapp_name, namespace.vcdvdc))
            vapp_dict = {}
            vapp_uuid = namespace.vapp_name
            # if request based on just name we need get UUID
            if not namespace.uuid:
                vapp_uuid = vim.get_vappid(vdc=namespace.vcdvdc, vapp_name=namespace.vapp_name)
                if vapp_uuid is None:
                    print("Can't find vapp by given name {}".format(namespace.vapp_name))
                    return

            print " namespace {}".format(namespace)
            if vapp_dict is not None and namespace.osm:
                vm_info_dict = vim.get_vminstance(vim_vm_uuid=vapp_uuid)
                print vm_info_dict
            if vapp_dict is not None and namespace.osm != True:
                vapp_dict = vim.get_vapp(vdc_name=namespace.vcdvdc, vapp_name=vapp_uuid, isuuid=True)
                print_vapp(vapp_dict=vapp_dict)

    # view network
    if action == 'network' or namespace.action == 'network':
        logger.debug("Requesting view for network {}".format(namespace.network_name))
        network_uuid = namespace.network_name
        # if request name based we need find UUID
        # TODO optimize it or move to external function
        if not namespace.uuid:
            if not myorg.has_key('networks'):
                print("Network {} is undefined in vcloud director for org {} vdc {}".format(namespace.network_name,
                                                                                            vim.name,
                                                                                            vim.tenant_name))
                return

            my_org_net = myorg['networks']
            for network in my_org_net:
                if my_org_net[network] == namespace.network_name:
                    network_uuid = network
                    break

        print print_network_details(network_dict=vim.get_vcd_network(network_uuid=network_uuid))


def create_actions(vim=None, action=None, namespace=None):
    """Method gets provider vdc view from vcloud director

        Args:
            vim - is Cloud director vim connector
            action - action for create ( network / vdc etc)

        Returns:
            The return xml content of respond or None
    """
    if action == 'network' or namespace.action == 'network':
        logger.debug("Creating a network in vcloud director".format(namespace.network_name))
        network_uuid = vim.create_network(namespace.network_name)
        if network_uuid is not None:
            print ("Crated new network {} and uuid: {}".format(namespace.network_name, network_uuid))
        else:
            print ("Failed create a new network {}".format(namespace.network_name))
    elif action == 'vdc' or namespace.action == 'vdc':
        logger.debug("Creating a new vdc in vcloud director.".format(namespace.vdc_name))
        vdc_uuid = vim.create_vdc(namespace.vdc_name)
        if vdc_uuid is not None:
            print ("Crated new vdc {} and uuid: {}".format(namespace.vdc_name, vdc_uuid))
        else:
            print ("Failed create a new vdc {}".format(namespace.vdc_name))
    else:
        return None


def validate_uuid4(uuid_string):
    """Function validate that string contain valid uuid4

        Args:
            uuid_string - valid UUID string

        Returns:
            The return true if string contain valid UUID format
    """
    try:
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True


def upload_image(vim=None, image_file=None):
    """Function upload image to vcloud director

        Args:
            image_file - valid UUID string

        Returns:
            The return true if image uploaded correctly
    """
    try:
        catalog_uuid = vim.get_image_id_from_path(path=image_file, progress=True)
        if catalog_uuid is not None and validate_uuid4(catalog_uuid):
            print("Image uploaded and uuid {}".format(catalog_uuid))
            return True
    except vimconn.vimconnException as upload_exception:
        print("Failed uploaded {} image".format(image_file))
        print("Error Reason: {}".format(upload_exception.message))
    return False


def boot_image(vim=None, image_name=None, vm_name=None):
    """ Function boot image that resided in vcloud director.
        The image name can be UUID of name.

        Args:
            vim - vim connector
            image_name - image identified by UUID or text string.
            vm_name - vmname


         Returns:
             The return true if image uploaded correctly
     """

    vim_catalog = None
    try:
        catalogs = vim.vca.get_catalogs()
        if not validate_uuid4(image_name):
            vim_catalog = vim.get_catalogid(catalog_name=image_name, catalogs=catalogs)
            if vim_catalog is None:
                return None
        else:
            vim_catalog = vim.get_catalogid(catalog_name=image_name, catalogs=catalogs)
            if vim_catalog is None:
                return None

        print (" Booting {} image id {} ".format(vm_name, vim_catalog))
        vm_uuid, _ = vim.new_vminstance(name=vm_name, image_id=vim_catalog)
        if vm_uuid is not None and validate_uuid4(vm_uuid):
            print("Image booted and vm uuid {}".format(vm_uuid))
            vapp_dict = vim.get_vapp(vdc_name=namespace.vcdvdc, vapp_name=vm_uuid, isuuid=True)
            if vapp_dict is not None:
                print_vapp(vapp_dict=vapp_dict)
        return True
    except vimconn.vimconnNotFoundException as notFound:
        print("Failed boot {} image".format(image_name))
        print(notFound.message)
    except vimconn.vimconnException as vimconError:
        print("Failed boot {} image".format(image_name))
        print(vimconError.message)
    except:
        print("Failed boot {} image".format(image_name))


        return False


def image_action(vim=None, action=None, namespace=None):
    """ Function present set of action to manipulate with image.
          - upload image
          - boot image.
          - delete image ( not yet done )

        Args:
             vim - vcloud director connector
             action - string (upload/boot etc)
             namespace - contain other attributes image name etc

         Returns:
             The return nothing
     """

    if action == 'upload' or namespace.action == 'upload':
        upload_image(vim=vim, image_file=namespace.image)
    elif action == 'boot' or namespace.action == 'boot':
        boot_image(vim=vim, image_name=namespace.image, vm_name=namespace.vmname)
    else:
        return None


def vmwarecli(command=None, action=None, namespace=None):
    logger.debug("Namespace {}".format(namespace))
    urllib3.disable_warnings()

    vcduser = None
    vcdpasword = None
    vcdhost = None
    vcdorg = None

    if hasattr(__builtins__, 'raw_input'):
        input = raw_input

    if namespace.vcdvdc is None:
        while True:
            vcduser = input("Enter vcd username: ")
            if vcduser is not None and len(vcduser) > 0:
                break
    else:
        vcduser = namespace.vcduser

    if namespace.vcdpassword is None:
        while True:
            vcdpasword = input("Please enter vcd password: ")
            if vcdpasword is not None and len(vcdpasword) > 0:
                break
    else:
        vcdpasword = namespace.vcdpassword

    if namespace.vcdhost is None:
        while True:
            vcdhost = input("Please enter vcd host name or ip: ")
            if vcdhost is not None and len(vcdhost) > 0:
                break
    else:
        vcdhost = namespace.vcdhost

    if namespace.vcdorg is None:
        while True:
            vcdorg = input("Please enter vcd organization name: ")
            if vcdorg is not None and len(vcdorg) > 0:
                break
    else:
        vcdorg = namespace.vcdorg

    try:
        vim = vimconnector(uuid=None,
                           name=vcdorg,
                           tenant_id=None,
                           tenant_name=namespace.vcdvdc,
                           url=vcdhost,
                           url_admin=vcdhost,
                           user=vcduser,
                           passwd=vcdpasword,
                           log_level="DEBUG",
                           config={'admin_username': namespace.vcdamdin, 'admin_password': namespace.vcdadminpassword})
        vim.vca = vim.connect()

    except vimconn.vimconnConnectionException:
        print("Failed connect to vcloud director. Please check credential and hostname.")
        return

    # list
    if command == 'list' or namespace.command == 'list':
        logger.debug("Client requested list action")
        # route request to list actions
        list_actions(vim=vim, action=action, namespace=namespace)

    # view action
    if command == 'view' or namespace.command == 'view':
        logger.debug("Client requested view action")
        view_actions(vim=vim, action=action, namespace=namespace)

    # delete action
    if command == 'delete' or namespace.command == 'delete':
        logger.debug("Client requested delete action")
        delete_actions(vim=vim, action=action, namespace=namespace)

    # create action
    if command == 'create' or namespace.command == 'create':
        logger.debug("Client requested create action")
        create_actions(vim=vim, action=action, namespace=namespace)

    # image action
    if command == 'image' or namespace.command == 'image':
        logger.debug("Client requested create action")
        image_action(vim=vim, action=action, namespace=namespace)


if __name__ == '__main__':
    defaults = {'vcdvdc': 'default',
                'vcduser': 'admin',
                'vcdpassword': 'admin',
                'vcdhost': 'https://localhost',
                'vcdorg': 'default',
                'debug': 'INFO'}

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--vcduser', help='vcloud director username', type=str)
    parser.add_argument('-p', '--vcdpassword', help='vcloud director password', type=str)
    parser.add_argument('-U', '--vcdamdin', help='vcloud director password', type=str)
    parser.add_argument('-P', '--vcdadminpassword', help='vcloud director password', type=str)
    parser.add_argument('-c', '--vcdhost', help='vcloud director host', type=str)
    parser.add_argument('-o', '--vcdorg', help='vcloud director org', type=str)
    parser.add_argument('-v', '--vcdvdc', help='vcloud director vdc', type=str)
    parser.add_argument('-d', '--debug', help='debug level', type=int)

    parser_subparsers = parser.add_subparsers(help='commands', dest='command')
    sub = parser_subparsers.add_parser('list', help='List objects (VMs, vApps, networks)')
    sub_subparsers = sub.add_subparsers(dest='action')

    list_vms = sub_subparsers.add_parser('vms', help='list - all vm deployed in vCloud director')
    list_vapps = sub_subparsers.add_parser('vapps', help='list - all vapps deployed in vCloud director')
    list_network = sub_subparsers.add_parser('networks', help='list - all networks deployed')
    list_network.add_argument('-o', '--osm', default=False, action='store_true', help='provide view in OSM format')

    #list vdc
    list_vdc = sub_subparsers.add_parser('vdc', help='list - list all vdc for organization accessible to you')
    list_vdc.add_argument('-o', '--osm', default=False, action='store_true', help='provide view in OSM format')

    list_org = sub_subparsers.add_parser('org', help='list - list of organizations accessible to you.')

    create_sub = parser_subparsers.add_parser('create')
    create_sub_subparsers = create_sub.add_subparsers(dest='action')
    create_vms = create_sub_subparsers.add_parser('vms')
    create_vapp = create_sub_subparsers.add_parser('vapp')
    create_vapp.add_argument('uuid')

    # add network
    create_network = create_sub_subparsers.add_parser('network')
    create_network.add_argument('network_name', action='store', help='create a network for a vdc')

    # add VDC
    create_vdc = create_sub_subparsers.add_parser('vdc')
    create_vdc.add_argument('vdc_name', action='store', help='create a new VDC for org')

    delete_sub = parser_subparsers.add_parser('delete')
    del_sub_subparsers = delete_sub.add_subparsers(dest='action')
    del_vms = del_sub_subparsers.add_parser('vms')
    del_vapp = del_sub_subparsers.add_parser('vapp')
    del_vapp.add_argument('uuid', help='view vapp based on UUID')

    # delete network
    del_network = del_sub_subparsers.add_parser('network')
    del_network.add_argument('network_name', action='store',
                             help='- delete network for vcloud director by provided name')
    del_network.add_argument('-u', '--uuid', default=False, action='store_true',
                             help='delete network for vcloud director by provided uuid')

    # delete vdc
    del_vdc = del_sub_subparsers.add_parser('vdc')

    view_sub = parser_subparsers.add_parser('view')
    view_sub_subparsers = view_sub.add_subparsers(dest='action')

    view_vms_parser = view_sub_subparsers.add_parser('vms')
    view_vms_parser.add_argument('uuid', default=False, action='store_true',
                                 help='- View VM for specific uuid in vcloud director')
    view_vms_parser.add_argument('name', default=False, action='store_true',
                                 help='- View VM for specific vapp name in vcloud director')

    # view vapp
    view_vapp_parser = view_sub_subparsers.add_parser('vapp')
    view_vapp_parser.add_argument('vapp_name', action='store',
                                  help='- view vapp for specific vapp name in vcloud director')
    view_vapp_parser.add_argument('-u', '--uuid', default=False, action='store_true', help='view vapp based on uuid')
    view_vapp_parser.add_argument('-o', '--osm', default=False, action='store_true',  help='provide view in OSM format')

    # view network
    view_network = view_sub_subparsers.add_parser('network')
    view_network.add_argument('network_name', action='store',
                              help='- view network for specific network name in vcloud director')
    view_network.add_argument('-u', '--uuid', default=False, action='store_true', help='view network based on uuid')

    # view VDC command and actions
    view_vdc = view_sub_subparsers.add_parser('vdc')
    view_vdc.add_argument('vdc_name', action='store',
                          help='- View VDC based and action based on provided vdc uuid')
    view_vdc.add_argument('-u', '--uuid', default=False, action='store_true', help='view vdc based on uuid')

    # view organization command and actions
    view_org = view_sub_subparsers.add_parser('org')
    view_org.add_argument('org_name', action='store',
                          help='- View VDC based and action based on provided vdc uuid')
    view_org.add_argument('-u', '--uuid', default=False, action='store_true', help='view org based on uuid')

    # upload image action
    image_sub = parser_subparsers.add_parser('image')
    image_subparsers = image_sub.add_subparsers(dest='action')
    upload_parser = image_subparsers.add_parser('upload')
    upload_parser.add_argument('image', default=False, action='store', help='- valid path to OVF image ')
    upload_parser.add_argument('catalog', default=False, action='store_true', help='- catalog name')

    # boot vm action
    boot_parser = image_subparsers.add_parser('boot')
    boot_parser.add_argument('image', default=False, action='store', help='- Image name')
    boot_parser.add_argument('vmname', default=False, action='store', help='- VM name')
    boot_parser.add_argument('-u', '--uuid', default=False, action='store_true', help='view org based on uuid')

    namespace = parser.parse_args()
    # put command_line args to mapping
    command_line_args = {k: v for k, v in vars(namespace).items() if v}

    d = defaults.copy()
    d.update(os.environ)
    d.update(command_line_args)

    logger = logging.getLogger('mano.vim.vmware')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(str.upper(d['debug']))
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(getattr(logging, str.upper(d['debug'])))
    logger.info(
        "Connecting {} username: {} org: {} vdc: {} ".format(d['vcdhost'], d['vcduser'], d['vcdorg'], d['vcdvdc']))

    logger.debug("command: \"{}\" actio: \"{}\"".format(d['command'], d['action']))

    # main entry point.
    vmwarecli(namespace=namespace)
