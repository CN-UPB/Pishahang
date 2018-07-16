# -*- coding: utf-8 -*-

##
# Copyright 2017  Telefónica Digital España S.L.U.
# This file is part of ETSI OSM
#  All Rights Reserved.
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
# contact with: patent-office@telefonica.com
##

"""
vimconnector implements all the methods to interact with OpenNebula using the XML-RPC API.
"""
__author__ = "Jose Maria Carmona Perez,Juan Antonio Hernando Labajo, Emilio Abraham Garrido Garcia,Alberto Florez " \
             "Pages, Andres Pozo Muñoz, Santiago Perez Marin, Onlife Networks Telefonica I+D Product Innovation "
__date__ = "$13-dec-2017 11:09:29$"
import vimconn
import requests
import logging
import oca
import untangle
import math
import random


class vimconnector(vimconn.vimconnector):
    def __init__(self, uuid, name, tenant_id, tenant_name, url, url_admin=None, user=None, passwd=None,
                 log_level="DEBUG", config={}, persistent_info={}):
        vimconn.vimconnector.__init__(self, uuid, name, tenant_id, tenant_name, url, url_admin, user, passwd, log_level,
                                      config)
        self.tenant = None
        self.headers_req = {'content-type': 'application/json'}
        self.logger = logging.getLogger('openmano.vim.opennebula')
        self.persistent_info = persistent_info
        if tenant_id:
            self.tenant = tenant_id

    def __setitem__(self, index, value):
        """Set individuals parameters
        Throw TypeError, KeyError
        """
        if index == 'tenant_id':
            self.tenant = value
        elif index == 'tenant_name':
            self.tenant = None
        vimconn.vimconnector.__setitem__(self, index, value)

    def new_tenant(self, tenant_name, tenant_description):
        # '''Adds a new tenant to VIM with this name and description, returns the tenant identifier'''
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            group_list = oca.GroupPool(client)
            user_list = oca.UserPool(client)
            group_list.info()
            user_list.info()
            create_primarygroup = 1
            # create group-tenant
            for group in group_list:
                if str(group.name) == str(tenant_name):
                    create_primarygroup = 0
                    break
            if create_primarygroup == 1:
                oca.Group.allocate(client, tenant_name)
            group_list.info()
            # set to primary_group the tenant_group and oneadmin to secondary_group
            for group in group_list:
                if str(group.name) == str(tenant_name):
                    for user in user_list:
                        if str(user.name) == str(self.user):
                            if user.name == "oneadmin":
                                return str(0)
                            else:
                                self._add_secondarygroup(user.id, group.id)
                                user.chgrp(group.id)
                                return str(group.id)
        except Exception as e:
            self.logger.error("Create new tenant error: " + str(e))
            raise vimconn.vimconnException(e)

    def _add_secondarygroup(self, id_user, id_group):
        # change secondary_group to primary_group
        params = '<?xml version="1.0"?> \
                   <methodCall>\
                   <methodName>one.user.addgroup</methodName>\
                   <params>\
                   <param>\
                   <value><string>{}:{}</string></value>\
                   </param>\
                   <param>\
                   <value><int>{}</int></value>\
                   </param>\
                   <param>\
                   <value><int>{}</int></value>\
                   </param>\
                   </params>\
                   </methodCall>'.format(self.user, self.passwd, (str(id_user)), (str(id_group)))
        requests.post(self.url, params)

    def delete_tenant(self, tenant_id):
        """Delete a tenant from VIM. Returns the old tenant identifier"""
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            group_list = oca.GroupPool(client)
            user_list = oca.UserPool(client)
            group_list.info()
            user_list.info()
            for group in group_list:
                if str(group.id) == str(tenant_id):
                    for user in user_list:
                        if str(user.name) == str(self.user):
                            self._delete_secondarygroup(user.id, group.id)
                            group.delete(client)
                    return None
            raise vimconn.vimconnNotFoundException("Group {} not found".format(tenant_id))
        except Exception as e:
            self.logger.error("Delete tenant " + str(tenant_id) + " error: " + str(e))
            raise vimconn.vimconnException(e)

    # to be used in future commits
    def _delete_secondarygroup(self, id_user, id_group):
        params = '<?xml version="1.0"?> \
                   <methodCall>\
                   <methodName>one.user.delgroup</methodName>\
                   <params>\
                   <param>\
                   <value><string>{}:{}</string></value>\
                   </param>\
                   <param>\
                   <value><int>{}</int></value>\
                   </param>\
                   <param>\
                   <value><int>{}</int></value>\
                   </param>\
                   </params>\
                   </methodCall>'.format(self.user, self.passwd, (str(id_user)), (str(id_group)))
        requests.post(self.url, params)

    # to be used in future commits
    # def get_tenant_list(self, filter_dict={}):
    #     return ["tenant"]

    # to be used in future commits
    # def _check_tenant(self):
    #     try:
    #         client = oca.Client(self.user + ':' + self.passwd, self.url)
    #         group_list = oca.GroupPool(client)
    #         user_list = oca.UserPool(client)
    #         group_list.info()
    #         user_list.info()
    #         for group in group_list:
    #             if str(group.name) == str(self.tenant_name):
    #                 for user in user_list:
    #                     if str(user.name) == str(self.user):
    #                         self._add_secondarygroup(user.id, group.id)
    #                         user.chgrp(group.id)
    #     except vimconn.vimconnException as e:
    #         self.logger.error(e)

    # to be used in future commits, needs refactor to manage networks
    # def _create_bridge_host(self, vlan):
    #     file = open('manage_bridge_OSM', 'w')
    #     # password_path = self.config["password"]["path"]
    #     a = "#! /bin/bash\nsudo brctl addbr br_osm_{vlanused}\n" \
    #         "sudo ip link add link veth1 name veth1.{vlanused} type vlan id {vlanused}\n" \
    #         "sudo brctl addif br_osm_{vlanused} veth1.{vlanused}\n" \
    #         "sudo ip link set dev br_osm_{vlanused} up\n" \
    #         "sudo ip link set dev veth1.{vlanused} up\n".format(vlanused=vlan)
    #     # a = "#! /bin/bash\nsudo brctl addbr br_osm\nsudo ip link set dev br_osm up\n"
    #     file.write(a)
    #     file.close()
    #     for host in self.config["cluster"]["ip"]:
    #         file_scp = "/usr/bin/scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {} manage_bridge_OSM {}@{}:/home/{}".format(
    #             self.config["cluster"]["password_path"][host], self.config["cluster"]["login"][host],
    #             self.config["cluster"]["ip"][host], self.config["cluster"]["login"][host])
    #         os.system(file_scp)
    #         file_permissions = "/usr/bin/ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {} {}@{} sudo chmod 700 manage_bridge_OSM".format(
    #             self.config["cluster"]["password_path"][host], self.config["cluster"]["login"][host],
    #             self.config["cluster"]["ip"][host])
    #         os.system(file_permissions)
    #         exec_script = "/usr/bin/ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {} {}@{} sudo ./manage_bridge_OSM".format(
    #             self.config["cluster"]["password_path"][host], self.config["cluster"]["login"][host],
    #             self.config["cluster"]["ip"][host])
    #         os.system(exec_script)
    #     os.remove("manage_bridge_OSM")

    # to be used to manage networks with vlan
    # def delete_bridge_host(self, vlan):
    #      file = open('manage_bridge_OSM', 'w')
    #      a = "#! /bin/bash\nsudo ip link set dev veth1.3142 down\nsudo ip link set dev br_3142 down\nsudo brctl delbr br_3142\n"
    #      file.write(a)
    #      file.close()
    #      os.system("/usr/bin/scp -i onlife manage_bridge_OSM sysadmin@10.95.84.12:/home/sysadmin")
    #      os.system("/usr/bin/ssh -i onlife sysadmin@10.95.84.12 sudo chmod 700 manage_bridge_OSM")
    #      os.system("/usr/bin/ssh -i onlife sysadmin@10.95.84.12 sudo ./manage_bridge_OSM")
    #      os.remove("manage_bridge_OSM")

    def new_network(self, net_name, net_type, ip_profile=None, shared=False, vlan=None):  # , **vim_specific):
        """Returns the network identifier"""
        # oca library method cannot be used in this case (problem with cluster parameters)
        try:
            # vlan = str(random.randint(self.config["vlan"]["start-range"], self.config["vlan"]["finish-range"]))
            # self.create_bridge_host(vlan)
            bridge_config = self.config["bridge_service"]
            ip_version = "IP4"
            size = "256"
            if ip_profile is None:
                random_number_ipv4 = random.randint(1, 255)
                ip_start = "192.168." + str(random_number_ipv4) + ".1"  # random value
            else:
                index = ip_profile["subnet_address"].find("/")
                ip_start = ip_profile["subnet_address"][:index]
                if "dhcp_count" in ip_profile.keys() and ip_profile["dhcp_count"] is not None:
                    size = str(ip_profile["dhcp_count"])
                elif not ("dhcp_count" in ip_profile.keys()) and ip_profile["ip_version"] == "IPv4":
                    prefix = ip_profile["subnet_address"][index + 1:]
                    size = int(math.pow(2, 32 - prefix))
                if "dhcp_start_address" in ip_profile.keys() and ip_profile["dhcp_start_address"] is not None:
                    ip_start = str(ip_profile["dhcp_start_address"])
                if ip_profile["ip_version"] == "IPv6":
                    ip_version = "IP6"
            if ip_version == "IP6":
                config = "NAME = {}\
                        BRIDGE = {}\
                        VN_MAD = dummy\
                        AR = [TYPE = {}, GLOBAL_PREFIX = {}, SIZE = {}]".format(net_name, bridge_config, ip_version,
                                                                                ip_start, size)
            else:
                config = 'NAME = "{}"\
                        BRIDGE = {}\
                        VN_MAD = dummy\
                        AR = [TYPE = {}, IP = {}, SIZE = {}]'.format(net_name, bridge_config, ip_version, ip_start,
                                                                     size)

            params = '<?xml version="1.0"?> \
            <methodCall>\
            <methodName>one.vn.allocate</methodName>\
            <params>\
            <param>\
            <value><string>{}:{}</string></value>\
            </param>\
            <param>\
            <value><string>{}</string></value>\
            </param>\
            <param>\
            <value><int>{}</int></value>\
            </param>\
            </params>\
            </methodCall>'.format(self.user, self.passwd, config, self.config["cluster"]["id"])
            r = requests.post(self.url, params)
            obj = untangle.parse(str(r.content))
            return obj.methodResponse.params.param.value.array.data.value[1].i4.cdata.encode('utf-8')
        except Exception as e:
            self.logger.error("Create new network error: " + str(e))
            raise vimconn.vimconnException(e)

    def get_network_list(self, filter_dict={}):
        """Obtain tenant networks of VIM
        Filter_dict can be:
            name: network name
            id: network uuid
            public: boolean
            tenant_id: tenant
            admin_state_up: boolean
            status: 'ACTIVE'
        Returns the network list of dictionaries
        """
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            networkList = oca.VirtualNetworkPool(client)
            networkList.info()
            response = []
            if "name" in filter_dict.keys():
                network_name_filter = filter_dict["name"]
            else:
                network_name_filter = None
            if "id" in filter_dict.keys():
                network_id_filter = filter_dict["id"]
            else:
                network_id_filter = None
            for network in networkList:
                match = False
                if network.name == network_name_filter and str(network.id) == str(network_id_filter):
                    match = True
                if network_name_filter is None and str(network.id) == str(network_id_filter):
                    match = True
                if network_id_filter is None and network.name == network_name_filter:
                    match = True
                if match:
                    net_dict = {"name": network.name, "id": str(network.id)}
                    response.append(net_dict)
            return response
        except Exception as e:
            self.logger.error("Get network list error: " + str(e))
            raise vimconn.vimconnException(e)

    def get_network(self, net_id):
        """Obtain network details of network id"""
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            networkList = oca.VirtualNetworkPool(client)
            networkList.info()
            net = {}
            for network in networkList:
                if str(network.id) == str(net_id):
                    net['id'] = net_id
                    net['name'] = network.name
                    net['status'] = "ACTIVE"
                    break
            if net:
                return net
            else:
                raise vimconn.vimconnNotFoundException("Network {} not found".format(net_id))
        except Exception as e:
                self.logger.error("Get network " + str(net_id) + " error): " + str(e))
                raise vimconn.vimconnException(e)

    def delete_network(self, net_id):
        """Deletes a tenant network from VIM
            Returns the network identifier
        """
        try:
            # self.delete_bridge_host()
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            networkList = oca.VirtualNetworkPool(client)
            networkList.info()
            network_deleted = False
            for network in networkList:
                if str(network.id) == str(net_id):
                    oca.VirtualNetwork.delete(network)
                    network_deleted = True
            if network_deleted:
                return net_id
            else:
                raise vimconn.vimconnNotFoundException("Network {} not found".format(net_id))
        except Exception as e:
                self.logger.error("Delete network " + str(net_id) + "error: " + str(e))
                raise vimconn.vimconnException(e)

    def get_flavor(self, flavor_id):  # Esta correcto
        """Obtain flavor details from the  VIM"""
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            listaTemplate = oca.VmTemplatePool(client)
            listaTemplate.info()
            for template in listaTemplate:
                if str(template.id) == str(flavor_id):
                    return {'id': template.id, 'name': template.name}
            raise vimconn.vimconnNotFoundException("Flavor {} not found".format(flavor_id))
        except Exception as e:
            self.logger.error("get flavor " + str(flavor_id) + " error: " + str(e))
            raise vimconn.vimconnException(e)

    def new_flavor(self, flavor_data):
        """Adds a tenant flavor to VIM
            Returns the flavor identifier"""
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            template_name = flavor_data["name"][:-4]
            name = 'NAME = "{}" '.format(template_name)
            cpu = 'CPU = "{}" '.format(flavor_data["vcpus"])
            memory = 'MEMORY = "{}" '.format(flavor_data["ram"])
            context = 'CONTEXT = [NETWORK = "YES",SSH_PUBLIC_KEY = "$USER[SSH_PUBLIC_KEY]" ] '
            graphics = 'GRAPHICS = [ LISTEN = "0.0.0.0", TYPE = "VNC" ] '
            sched_requeriments = 'CLUSTER_ID={}'.format(self.config["cluster"]["id"])
            template = name + cpu + memory + context + graphics + sched_requeriments
            template_id = oca.VmTemplate.allocate(client, template)
            return template_id
        except Exception as e:
            self.logger.error("Create new flavor error: " + str(e))
            raise vimconn.vimconnException(e)

    def delete_flavor(self, flavor_id):
        """ Deletes a tenant flavor from VIM
            Returns the old flavor_id
        """
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            listaTemplate = oca.VmTemplatePool(client)
            listaTemplate.info()
            self.logger.info("Deleting VIM flavor DELETE {}".format(self.url))
            for template in listaTemplate:
                if str(template.id) == str(flavor_id):
                    template.delete()
                    return template.id
            raise vimconn.vimconnNotFoundException("Flavor {} not found".format(flavor_id))
        except Exception as e:
            self.logger.error("Delete flavor " + str(flavor_id) + " error: " + str(e))
            raise vimconn.vimconnException(e)

    def get_image_list(self, filter_dict={}):
        """Obtain tenant images from VIM
        Filter_dict can be:
            name: image name
            id: image uuid
            checksum: image checksum
            location: image path
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        """
        # IMPORTANT!!!!! Modify python oca library path pool.py line 102

        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            image_pool = oca.ImagePool(client)
            image_pool.info()
            images = []
            if "name" in filter_dict.keys():
                image_name_filter = filter_dict["name"]
            else:
                image_name_filter = None
            if "id" in filter_dict.keys():
                image_id_filter = filter_dict["id"]
            else:
                image_id_filter = None
            for image in image_pool:
                match = False
                if str(image_name_filter) == str(image.name) and str(image.id) == str(image_id_filter):
                    match = True
                if image_name_filter is None and str(image.id) == str(image_id_filter):
                    match = True
                if image_id_filter is None and str(image_name_filter) == str(image.name):
                    match = True
                if match:
                    images_dict = {"name": image.name, "id": str(image.id)}
                    images.append(images_dict)
            return images
        except Exception as e:
            self.logger.error("Get image list error: " + str(e))
            raise vimconn.vimconnException(e)

    def new_vminstance(self, name, description, start, image_id, flavor_id, net_list, cloud_config=None, disk_list=None,
                       availability_zone_index=None, availability_zone_list=None):
        """Adds a VM instance to VIM
        Params:
            start: indicates if VM must start or boot in pause mode. Ignored
            image_id,flavor_id: image and flavor uuid
            net_list: list of interfaces, each one is a dictionary with:
                name:
                net_id: network uuid to connect
                vpci: virtual vcpi to assign
                model: interface model, virtio, e2000, ...
                mac_address:
                use: 'data', 'bridge',  'mgmt'
                type: 'virtual', 'PF', 'VF', 'VFnotShared'
                vim_id: filled/added by this function
                #TODO ip, security groups
        Returns the instance identifier
        """
        self.logger.debug(
            "new_vminstance input: image='{}' flavor='{}' nics='{}'".format(image_id, flavor_id, str(net_list)))
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            listaTemplate = oca.VmTemplatePool(client)
            listaTemplate.info()
            for template in listaTemplate:
                if str(template.id) == str(flavor_id):
                    cpu = ' CPU = "{}"'.format(template.template.cpu)
                    memory = ' MEMORY = "{}"'.format(template.template.memory)
                    context = ' CONTEXT = [NETWORK = "YES",SSH_PUBLIC_KEY = "$USER[SSH_PUBLIC_KEY]" ]'
                    graphics = ' GRAPHICS = [ LISTEN = "0.0.0.0", TYPE = "VNC" ]'
                    disk = ' DISK = [ IMAGE_ID = {}]'.format(image_id)
                    sched_requeriments = ' SCHED_REQUIREMENTS = "CLUSTER_ID={}"'.format(self.config["cluster"]["id"])
                    template_updated = cpu + memory + context + graphics + disk + sched_requeriments
                    networkListVim = oca.VirtualNetworkPool(client)
                    networkListVim.info()
                    network = ""
                    for net in net_list:
                        network_found = False
                        for network_existingInVim in networkListVim:
                            if str(net["net_id"]) == str(network_existingInVim.id):
                                net["vim_id"] = network_existingInVim["id"]
                                network = 'NIC = [NETWORK = "{}",NETWORK_UNAME = "{}" ]'.format(
                                    network_existingInVim.name, network_existingInVim.uname)
                                network_found = True
                                break
                        if not network_found:
                            raise vimconn.vimconnNotFoundException("Network {} not found".format(net["net_id"]))
                        template_updated += network
                    oca.VmTemplate.update(template, template_updated)
                    self.logger.info(
                        "Instanciating in OpenNebula a new VM name:{} id:{}".format(template.name, template.id))
                    vminstance_id = template.instantiate(name=name)
                    return str(vminstance_id), None
            raise vimconn.vimconnNotFoundException("Flavor {} not found".format(flavor_id))
        except Exception as e:
            self.logger.error("Create new vm instance error: " + str(e))
            raise vimconn.vimconnException(e)

    def delete_vminstance(self, vm_id, created_items=None):
        """Removes a VM instance from VIM, returns the deleted vm_id"""
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            vm_pool = oca.VirtualMachinePool(client)
            vm_pool.info()
            vm_exist = False
            for i in vm_pool:
                if str(i.id) == str(vm_id):
                    vm_exist = True
                    break
            if not vm_exist:
                self.logger.info("The vm " + str(vm_id) + " does not exist or is already deleted")
                raise vimconn.vimconnNotFoundException("The vm {} does not exist or is already deleted".format(vm_id))
            params = '<?xml version="1.0"?> \
                        <methodCall>\
                        <methodName>one.vm.recover</methodName>\
                        <params>\
                        <param>\
                        <value><string>{}:{}</string></value>\
                        </param>\
                        <param>\
                        <value><int>{}</int></value>\
                        </param>\
                        <param>\
                        <value><int>{}</int></value>\
                        </param>\
                        </params>\
                        </methodCall>'.format(self.user, self.passwd, str(vm_id), str(3))
            r = requests.post(self.url, params)
            obj = untangle.parse(str(r.content))
            response_success = obj.methodResponse.params.param.value.array.data.value[0].boolean.cdata.encode('utf-8')
            response = obj.methodResponse.params.param.value.array.data.value[1].i4.cdata.encode('utf-8')
            # response can be the resource ID on success or the error string on failure.
            response_error_code = obj.methodResponse.params.param.value.array.data.value[2].i4.cdata.encode('utf-8')
            if response_success.lower() == "true":
                return response
            else:
                raise vimconn.vimconnException("vm {} cannot be deleted with error_code {}: {}".format(vm_id, response_error_code, response))
        except Exception as e:
            self.logger.error("Delete vm instance " + str(vm_id) + " error: " + str(e))
            raise vimconn.vimconnException(e)

    def refresh_vms_status(self, vm_list):
        """Refreshes the status of the virtual machines"""
        vm_dict = {}
        try:
            client = oca.Client(self.user + ':' + self.passwd, self.url)
            vm_pool = oca.VirtualMachinePool(client)
            vm_pool.info()
            for vm_id in vm_list:
                vm = {"interfaces": []}
                vm_exist = False
                vm_element = None
                for i in vm_pool:
                    if str(i.id) == str(vm_id):
                        vm_exist = True
                        vm_element = i
                        break
                if not vm_exist:
                    self.logger.info("The vm " + str(vm_id) + " does not exist.")
                    vm['status'] = "DELETED"
                    vm['error_msg'] = ("The vm " + str(vm_id) + " does not exist.")
                    continue
                vm_element.info()
                vm["vim_info"] = None
                VMstatus = vm_element.str_lcm_state
                if VMstatus == "RUNNING":
                    vm['status'] = "ACTIVE"
                elif "FAILURE" in VMstatus:
                    vm['status'] = "ERROR"
                    vm['error_msg'] = "VM failure"
                else:
                    vm['status'] = "BUILD"
                try:
                    for red in vm_element.template.nics:
                        interface = {'vim_info': None, "mac_address": str(red.mac), "vim_net_id": str(red.network_id),
                                     "vim_interface_id": str(red.network_id)}
                        # maybe it should be 2 different keys for ip_address if an interface has ipv4 and ipv6
                        if hasattr(red, 'ip'):
                            interface["ip_address"] = str(red.ip)
                        if hasattr(red, 'ip6_global'):
                            interface["ip_address"] = str(red.ip6_global)
                        vm["interfaces"].append(interface)
                except Exception as e:
                    self.logger.error("Error getting vm interface_information " + type(e).__name__ + ":" + str(e))
                    vm["status"] = "VIM_ERROR"
                    vm["error_msg"] = "Error getting vm interface_information " + type(e).__name__ + ":" + str(e)
                vm_dict[vm_id] = vm
            return vm_dict
        except Exception as e:
            self.logger.error(e)
            for k in vm_dict:
                vm_dict[k]["status"] = "VIM_ERROR"
                vm_dict[k]["error_msg"] = str(e)
            return vm_dict

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
        net_dict = {}
        try:
            for net_id in net_list:
                net = {}
                try:
                    net_vim = self.get_network(net_id)
                    net["status"] = net_vim["status"]
                    net["vim_info"] = None
                except vimconn.vimconnNotFoundException as e:
                    self.logger.error("Exception getting net status: {}".format(str(e)))
                    net['status'] = "DELETED"
                    net['error_msg'] = str(e)
                except vimconn.vimconnException as e:
                    self.logger.error(e)
                    net["status"] = "VIM_ERROR"
                    net["error_msg"] = str(e)
                net_dict[net_id] = net
            return net_dict
        except vimconn.vimconnException as e:
            self.logger.error(e)
            for k in net_dict:
                net_dict[k]["status"] = "VIM_ERROR"
                net_dict[k]["error_msg"] = str(e)
            return net_dict

    # to be used and fixed in future commits... not working properly
    # def action_vminstance(self, vm_id, action_dict):
    #     """Send and action over a VM instance from VIM
    #     Returns the status"""
    #     try:
    #         if "console" in action_dict:
    #             console_dict = {"protocol": "http",
    #                             "server": "10.95.84.42",
    #                             "port": "29876",
    #                             "suffix": "?token=4hsb9cu9utruakon4p3z"
    #                             }
    #         return console_dict
    #     except vimconn.vimconnException as e:
    #         self.logger.error(e)

