
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

import logging
import os
import subprocess
import tempfile
import yaml
import shlex

import gi
gi.require_version('RwCal', '1.0')
gi.require_version('RwcalYang', '1.0')

import rift.rwcal.openstack as openstack_drv


import rw_status
import rift.cal.rwcal_status as rwcal_status
import rwlogger


from gi.repository import (
    GObject,
    RwCal,
    RwTypes,
    RwcalYang)

PREPARE_VM_CMD = "prepare_vm.py --auth_url {auth_url} --username {username} --password {password} --tenant_name {tenant_name} --region {region} --user_domain {user_domain} --project_domain {project_domain} --mgmt_network {mgmt_network} --server_id {server_id} --port_metadata "

rwstatus_exception_map = {IndexError: RwTypes.RwStatus.NOTFOUND,
                          KeyError: RwTypes.RwStatus.NOTFOUND,
                          NotImplementedError: RwTypes.RwStatus.NOT_IMPLEMENTED, }

rwstatus = rw_status.rwstatus_from_exc_map(rwstatus_exception_map)
rwcalstatus = rwcal_status.rwcalstatus_from_exc_map(rwstatus_exception_map)


class OpenstackCALOperationFailure(Exception):
    pass

class UninitializedPluginError(Exception):
    pass


class OpenstackServerGroupError(Exception):
    pass


class ImageUploadError(Exception):
    pass

class PrepareVduOnBoot(Exception):
    pass

class RwcalAccountDriver(object):
    """
    Container class per cloud account
    """
    def __init__(self, logger, **kwargs):
        self.log = logger
        try:
            self._driver = openstack_drv.OpenstackDriver(logger = self.log, **kwargs)
        except Exception as e:
            self.log.error("RwcalOpenstackPlugin: OpenstackDriver init failed. Exception: %s" %(str(e)))
            raise

    @property
    def driver(self):
        return self._driver
    
class RwcalOpenstackPlugin(GObject.Object, RwCal.Cloud):
    """This class implements the CAL VALA methods for openstack."""

    instance_num = 1

    def __init__(self):
        GObject.Object.__init__(self)
        self.log = logging.getLogger('rwcal.openstack.%s' % RwcalOpenstackPlugin.instance_num)
        self.log.setLevel(logging.DEBUG)
        self._rwlog_handler = None
        self._account_drivers = dict()
        RwcalOpenstackPlugin.instance_num += 1

    def _get_account_key(self, account):
        key = str()
        for f in account.openstack.fields:
            try:
                key+= str(getattr(account.openstack, f))
            except:
                pass
        key += account.name
        return key
    
    def _use_driver(self, account):
        if self._rwlog_handler is None:
            raise UninitializedPluginError("Must call init() in CAL plugin before use.")

        acct_key = self._get_account_key(account)
        
        if acct_key not in self._account_drivers:
            self.log.debug("Creating OpenstackDriver")
            kwargs = dict(username = account.openstack.key,
                          password = account.openstack.secret,
                          auth_url = account.openstack.auth_url,
                          project = account.openstack.tenant,
                          mgmt_network = account.openstack.mgmt_network,
                          cert_validate = account.openstack.cert_validate,
                          user_domain = account.openstack.user_domain,
                          project_domain = account.openstack.project_domain,
                          region = account.openstack.region)
            drv = RwcalAccountDriver(self.log, **kwargs)
            self._account_drivers[account.name] = drv
            return drv.driver
        else:
            return self._account_drivers[acct_key].driver
        

    @rwstatus
    def do_init(self, rwlog_ctx):
        self._rwlog_handler = rwlogger.RwLogger(category="rw-cal-log",
                                                subcategory="openstack",
                                                log_hdl=rwlog_ctx,)
        self.log.addHandler(self._rwlog_handler)
        self.log.propagate = False

    @rwstatus(ret_on_failure=[None])
    def do_validate_cloud_creds(self, account):
        """
        Validates the cloud account credentials for the specified account.
        Performs an access to the resources using Keystone API. If creds
        are not valid, returns an error code & reason string
        Arguments:
            account - a cloud account to validate

        Returns:
            Validation Code and Details String
        """
        status = RwcalYang.YangData_Rwcal_ConnectionStatus()
        try:
            drv = self._use_driver(account) 
            drv.validate_account_creds()
        except Exception as e:
            msg = "RwcalOpenstackPlugin: Exception: %s" %(str(e))
            self.log.error(msg)
            status.status = "failure"
            status.details = msg

        else:
            status.status = "success"
            status.details = "Connection was successful"

        return status

    @rwstatus(ret_on_failure=[""])
    def do_get_management_network(self, account):
        """
        Returns the management network associated with the specified account.
        Arguments:
            account - a cloud account

        Returns:
            The management network
        """
        return account.openstack.mgmt_network

    @rwstatus(ret_on_failure=[""])
    def do_create_tenant(self, account, name):
        """Create a new tenant.

        Arguments:
            account - a cloud account
            name - name of the tenant

        Returns:
            The tenant id
        """
        raise NotImplementedError

    @rwstatus
    def do_delete_tenant(self, account, tenant_id):
        """delete a tenant.

        Arguments:
            account - a cloud account
            tenant_id - id of the tenant
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[[]])
    def do_get_tenant_list(self, account):
        """List tenants.

        Arguments:
            account - a cloud account

        Returns:
            List of tenants
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[""])
    def do_create_role(self, account, name):
        """Create a new user.

        Arguments:
            account - a cloud account
            name - name of the user

        Returns:
            The user id
        """
        raise NotImplementedError

    @rwstatus
    def do_delete_role(self, account, role_id):
        """Delete a user.

        Arguments:
            account - a cloud account
            role_id - id of the user
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[[]])
    def do_get_role_list(self, account):
        """List roles.

        Arguments:
            account - a cloud account

        Returns:
            List of roles
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[""])
    def do_create_image(self, account, image):
        """Create an image

        Arguments:
            account - a cloud account
            image - a description of the image to create

        Returns:
            The image id
        """
        drv = self._use_driver(account)
        fd = drv.utils.image.create_image_handle(image)
        kwargs = drv.utils.image.make_image_args(image)

        try:
            # Create Image
            image_id = drv.glance_image_create(**kwargs)
            drv.glance_image_upload(image_id, fd)
        except Exception as e:
            self.log.exception("Exception %s occured during image create", str(e))
            raise
        finally:
            fd.close()
            
        # Update image properties, if they are provided
        try:
            if image.has_field("properties") and image.properties is not None:
                for key in image.properties:
                    drv.glance_image_update(image_id, **{key.name: key.property_value})
        except Exception as e:
            self.log.exception("Exception %s occured during image update", str(e))
            raise
        
        if image.checksum:
            try:
                stored_image = drv.glance_image_get(image_id)
                if stored_image.checksum != image.checksum:
                    drv.glance_image_delete(image_id=image_id)
                    raise ImageUploadError("image checksum did not match (actual: %s, expected: %s). Deleting." %
                                           (stored_image.checksum, image.checksum))
            except Exception as e:
                self.log.exception("Exception %s occured during image checksum verification", str(e))
                raise

        return image_id

    @rwstatus
    def do_delete_image(self, account, image_id):
        """Delete a vm image.

        Arguments:
            account - a cloud account
            image_id - id of the image to delete
        """
        drv = self._use_driver(account)
        try:
            drv.glance_image_delete(image_id=image_id)
        except Exception as e:
            self.log.exception("Exception %s occured during image deletion", str(e))
            raise


    @rwstatus(ret_on_failure=[[]])
    def do_get_image_list(self, account):
        """Return a list of the names of all available images.

        Arguments:
            account - a cloud account

        Returns:
            The the list of images in VimResources object
        """
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        drv = self._use_driver(account)
        try:
            images = drv.glance_image_list()
            for img in images:
                response.imageinfo_list.append(drv.utils.image.parse_cloud_image_info(img))
        except Exception as e:
            self.log.exception("Exception %s occured during get-image-list", str(e))
            raise
        return response

    @rwstatus(ret_on_failure=[None])
    def do_get_image(self, account, image_id):
        """Return a image information.

        Arguments:
            account - a cloud account
            image_id - an id of the image

        Returns:
            ImageInfoItem object containing image information.
        """
        drv = self._use_driver(account)
        try:
            image_info = drv.glance_image_get(image_id)
            image =  drv.utils.image.parse_cloud_image_info(image_info)
        except Exception as e:
            self.log.exception("Exception %s occured during get-image", str(e))
            raise
        return image
    

    # This is being deprecated. Please do not use for new SW development
    @rwstatus(ret_on_failure=[""])
    def do_create_vm(self, account, vminfo):
        """Create a new virtual machine.

        Arguments:
            account - a cloud account
            vminfo - information that defines the type of VM to create

        Returns:
            The image id
        """
        from warnings import warn
        warn("This function is deprecated")
        kwargs = {}
        kwargs['name']      = vminfo.vm_name
        kwargs['flavor_id'] = vminfo.flavor_id
        if vminfo.has_field('image_id'):
            kwargs['image_id']  = vminfo.image_id

        ### If floating_ip is required and we don't have one, better fail before any further allocation
        floating_ip = False
        if vminfo.has_field('allocate_public_address') and vminfo.allocate_public_address:
            floating_ip = True

        if vminfo.has_field('cloud_init') and vminfo.cloud_init.has_field('userdata'):
            kwargs['userdata']  = vminfo.cloud_init.userdata
        else:
            kwargs['userdata'] = ''

        if account.openstack.security_groups:
            kwargs['security_groups'] = account.openstack.security_groups

        port_list = []
        for port in vminfo.port_list:
            port_list.append(port.port_id)

        if port_list:
            kwargs['port_list'] = port_list

        network_list = []
        for network in vminfo.network_list:
            network_list.append(network.network_id)

        if network_list:
            kwargs['network_list'] = network_list

        metadata = {}
        for field in vminfo.user_tags.fields:
            if vminfo.user_tags.has_field(field):
                metadata[field] = getattr(vminfo.user_tags, field)
        kwargs['metadata']  = metadata

        if vminfo.has_field('availability_zone'):
            kwargs['availability_zone']  = vminfo.availability_zone
        else:
            kwargs['availability_zone'] = None

        if vminfo.has_field('server_group'):
            kwargs['scheduler_hints'] = {'group': vminfo.server_group}
        else:
            kwargs['scheduler_hints'] = None

        drv = self._use_driver(account)
        vm_id = drv.nova_server_create(**kwargs)
        if floating_ip:
            self.prepare_vdu_on_boot(account, vm_id, floating_ip)

        return vm_id

    @rwstatus
    def do_start_vm(self, account, vm_id):
        """Start an existing virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        drv = self._use_driver(account)
        drv.nova_server_start(vm_id)

    @rwstatus
    def do_stop_vm(self, account, vm_id):
        """Stop a running virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        drv = self._use_driver(account)
        drv.nova_server_stop(vm_id)

    @rwstatus
    def do_delete_vm(self, account, vm_id):
        """Delete a virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        drv = self._use_driver(account)
        drv.nova_server_delete(vm_id)

    @rwstatus
    def do_reboot_vm(self, account, vm_id):
        """Reboot a virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        drv = self._use_driver(account)
        drv.nova_server_reboot(vm_id)

    @staticmethod
    def _fill_vm_info(vm_info, mgmt_network):
        """Create a GI object from vm info dictionary

        Converts VM information dictionary object returned by openstack
        driver into Protobuf Gi Object

        Arguments:
            vm_info - VM information from openstack
            mgmt_network - Management network

        Returns:
            Protobuf Gi object for VM
        """
        vm = RwcalYang.YangData_RwProject_Project_VimResources_VminfoList()
        vm.vm_id     = vm_info['id']
        vm.vm_name   = vm_info['name']
        vm.image_id  = vm_info['image']['id']
        vm.flavor_id = vm_info['flavor']['id']
        vm.state     = vm_info['status']
        for network_name, network_info in vm_info['addresses'].items():
            if network_info:
                if network_name == mgmt_network:
                    vm.public_ip = next((item['addr']
                                         for item in network_info
                                            if item['OS-EXT-IPS:type'] == 'floating'),
                                        network_info[0]['addr'])
                    vm.management_ip = network_info[0]['addr']
                else:
                    for interface in network_info:
                        addr = vm.private_ip_list.add()
                        addr.ip_address = interface['addr']

        for network_name, network_info in vm_info['addresses'].items():
            if network_info and network_name == mgmt_network and not vm.public_ip:
                for interface in network_info:
                    if 'OS-EXT-IPS:type' in interface and interface['OS-EXT-IPS:type'] == 'floating':
                        vm.public_ip = interface['addr']

        # Look for any metadata
        for key, value in vm_info['metadata'].items():
            if key in vm.user_tags.fields:
                setattr(vm.user_tags, key, value)
        if 'OS-EXT-SRV-ATTR:host' in vm_info:
            if vm_info['OS-EXT-SRV-ATTR:host'] is not None:
                vm.host_name = vm_info['OS-EXT-SRV-ATTR:host']
        if 'OS-EXT-AZ:availability_zone' in vm_info:
            if vm_info['OS-EXT-AZ:availability_zone'] is not None:
                vm.availability_zone = vm_info['OS-EXT-AZ:availability_zone']
        return vm

    @rwstatus(ret_on_failure=[[]])
    def do_get_vm_list(self, account):
        """Return a list of the VMs as vala boxed objects

        Arguments:
            account - a cloud account

        Returns:
            List containing VM information
        """
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        drv = self._use_driver(account)
        vms = drv.nova_server_list()
        for vm in vms:
            response.vminfo_list.append(RwcalOpenstackPlugin._fill_vm_info(vm, account.openstack.mgmt_network))
        return response

    @rwstatus(ret_on_failure=[None])
    def do_get_vm(self, account, id):
        """Return vm information.

        Arguments:
            account - a cloud account
            id - an id for the VM

        Returns:
            VM information
        """
        drv = self._use_driver(account)
        vm = drv.nova_server_get(id)
        return RwcalOpenstackPlugin._fill_vm_info(vm, account.openstack.mgmt_network)


    @rwstatus(ret_on_failure=[""])
    def do_create_flavor(self, account, flavor):
        """Create new flavor.

        Arguments:
            account - a cloud account
            flavor - flavor of the VM

        Returns:
            flavor id
        """
        drv = self._use_driver(account)
        try:
            flavor_id = drv.nova_flavor_create(name      = flavor.name,
                                               ram       = flavor.vm_flavor.memory_mb,
                                               vcpus     = flavor.vm_flavor.vcpu_count,
                                               disk      = flavor.vm_flavor.storage_gb,
                                               epa_specs = drv.utils.flavor.get_extra_specs(flavor))
        except Exception as e:
            self.log.error("Encountered exceptions during Flavor creation. Exception: %s", str(e))
            raise
            
        return flavor_id  

    @rwstatus
    def do_delete_flavor(self, account, flavor_id):
        """Delete flavor.

        Arguments:
            account - a cloud account
            flavor_id - id flavor of the VM
        """
        drv = self._use_driver(account)
        try:
            drv.nova_flavor_delete(flavor_id)
        except Exception as e:
            self.log.error("Encountered exceptions during Flavor deletion. Exception: %s", str(e))
            raise


    @rwstatus(ret_on_failure=[[]])
    def do_get_flavor_list(self, account):
        """Return flavor information.

        Arguments:
            account - a cloud account

        Returns:
            List of flavors
        """
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        drv = self._use_driver(account)
        try:
            flavors = drv.nova_flavor_list()
            for flv in flavors:
                response.flavorinfo_list.append(drv.utils.flavor.parse_flavor_info(flv))
        except Exception as e:
            self.log.error("Encountered exceptions during get-flavor-list. Exception: %s", str(e))
            raise

        return response

    @rwstatus(ret_on_failure=[None])
    def do_get_flavor(self, account, id):
        """Return flavor information.

        Arguments:
            account - a cloud account
            id - an id for the flavor

        Returns:
            Flavor info item
        """
        drv = self._use_driver(account)
        try:
            flavor = drv.nova_flavor_get(id)
            response = drv.utils.flavor.parse_flavor_info(flavor)
        except Exception as e:
            self.log.error("Encountered exceptions during get-flavor. Exception: %s", str(e))
            raise
        
        return response


    def _fill_network_info(self, network_info, account):
        """Create a GI object from network info dictionary

        Converts Network information dictionary object returned by openstack
        driver into Protobuf Gi Object

        Arguments:
            network_info - Network information from openstack
            account - a cloud account

        Returns:
            Network info item
        """
        network                  = RwcalYang.YangData_RwProject_Project_VimResources_NetworkinfoList()
        network.network_name     = network_info['name']
        network.network_id       = network_info['id']
        if ('provider:network_type' in network_info) and (network_info['provider:network_type'] is not None):
            network.provider_network.overlay_type = network_info['provider:network_type'].upper()
        if ('provider:segmentation_id' in network_info) and (network_info['provider:segmentation_id']):
            network.provider_network.segmentation_id = network_info['provider:segmentation_id']
        if ('provider:physical_network' in network_info) and (network_info['provider:physical_network']):
            network.provider_network.physical_network = network_info['provider:physical_network'].upper()

        if 'subnets' in network_info and network_info['subnets']:
            subnet_id = network_info['subnets'][0]
            drv = self._use_driver(account)
            subnet = drv.neutron_subnet_get(subnet_id)
            network.subnet = subnet['cidr']
        return network

    @rwstatus(ret_on_failure=[[]])
    def do_get_network_list(self, account):
        """Return a list of networks

        Arguments:
            account - a cloud accountr

        Returns:
            List of networks
        """
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        drv = self._use_driver(account)
        networks = drv.neutron_network_list()
        for network in networks:
            response.networkinfo_list.append(self._fill_network_info(network, account))
        return response

    @rwstatus(ret_on_failure=[None])
    def do_get_network(self, account, id):
        """Return a network

        Arguments:
            account - a cloud account
            id - an id for the network

        Returns:
            Network info item
        """
        drv = self._use_driver(account)
        network = drv.neutron_network_get(id)
        return self._fill_network_info(network, account)

    @rwstatus(ret_on_failure=[""])
    def do_create_network(self, account, network):
        """Create a new network

        Arguments:
            account - a cloud account
            network - Network object

        Returns:
            Network id
        """
        from warnings import warn
        warn("This function is deprecated")

        kwargs = {}
        kwargs['name']            = network.network_name
        kwargs['admin_state_up']  = True
        kwargs['external_router'] = False
        kwargs['shared']          = False

        if network.has_field('provider_network'):
            if network.provider_network.has_field('physical_network'):
                kwargs['physical_network'] = network.provider_network.physical_network
            if network.provider_network.has_field('overlay_type'):
                kwargs['network_type'] = network.provider_network.overlay_type.lower()
            if network.provider_network.has_field('segmentation_id'):
                kwargs['segmentation_id'] = network.provider_network.segmentation_id

        try:
            drv = self._use_driver(account)
            network_id = drv.neutron_network_create(**kwargs)
            drv.neutron_subnet_create(network_id = network_id,
                                    cidr = network.subnet)
        except Exception as e:
            self.log.exception("Exception %s occured during create-network", str(e))
            raise

        return network_id

    @rwstatus
    def do_delete_network(self, account, network_id):
        """Delete a network

        Arguments:
            account - a cloud account
            network_id - an id for the network
        """
        drv = self._use_driver(account)
        drv.neutron_network_delete(network_id)

    @staticmethod
    def _fill_port_info(port_info):
        """Create a GI object from port info dictionary

        Converts Port information dictionary object returned by openstack
        driver into Protobuf Gi Object

        Arguments:
            port_info - Port information from openstack

        Returns:
            Port info item
        """
        port = RwcalYang.YangData_RwProject_Project_VimResources_PortinfoList()

        port.port_name  = port_info['name']
        port.port_id    = port_info['id']
        port.network_id = port_info['network_id']
        port.port_state = port_info['status']
        if 'device_id' in port_info:
            port.vm_id = port_info['device_id']
        if 'fixed_ips' in port_info:
            port.ip_address = port_info['fixed_ips'][0]['ip_address']
        return port

    @rwstatus(ret_on_failure=[None])
    def do_get_port(self, account, port_id):
        """Return a port

        Arguments:
            account - a cloud account
            port_id - an id for the port

        Returns:
            Port info item
        """
        drv = self._use_driver(account)
        port = drv.neutron_port_get(port_id)
        return RwcalOpenstackPlugin._fill_port_info(port)

    @rwstatus(ret_on_failure=[[]])
    def do_get_port_list(self, account):
        """Return a list of ports

        Arguments:
            account - a cloud account

        Returns:
            Port info list
        """
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        drv = self._use_driver(account)
        ports = drv.neutron_port_list(*{})
        for port in ports:
            response.portinfo_list.append(RwcalOpenstackPlugin._fill_port_info(port))
        return response

    @rwstatus(ret_on_failure=[""])
    def do_create_port(self, account, port):
        """Create a new port

        Arguments:
            account - a cloud account
            port - port object

        Returns:
            Port id
        """
        from warnings import warn
        warn("This function is deprecated")

        kwargs = {}
        kwargs['name'] = port.port_name
        kwargs['network_id'] = port.network_id
        kwargs['admin_state_up'] = True
        if port.has_field('vm_id'):
            kwargs['vm_id'] = port.vm_id
        if port.has_field('port_type'):
            kwargs['port_type'] = port.port_type
        else:
            kwargs['port_type'] = "normal"

        drv = self._use_driver(account)
        return drv.neutron_port_create(**kwargs)

    @rwstatus
    def do_delete_port(self, account, port_id):
        """Delete a port

        Arguments:
            account - a cloud account
            port_id - an id for port
        """
        drv = self._use_driver(account)
        drv.neutron_port_delete(port_id)

    @rwstatus(ret_on_failure=[""])
    def do_add_host(self, account, host):
        """Add a new host

        Arguments:
            account - a cloud account
            host - a host object

        Returns:
            An id for the host
        """
        raise NotImplementedError

    @rwstatus
    def do_remove_host(self, account, host_id):
        """Remove a host

        Arguments:
            account - a cloud account
            host_id - an id for the host
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_host(self, account, host_id):
        """Return a host

        Arguments:
            account - a cloud account
            host_id - an id for host

        Returns:
            Host info item
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[[]])
    def do_get_host_list(self, account):
        """Return a list of hosts

        Arguments:
            account - a cloud account

        Returns:
            List of hosts
        """
        raise NotImplementedError


    @rwcalstatus(ret_on_failure=[""])
    def do_create_virtual_link(self, account, link_params):
        """Create a new virtual link

        Arguments:
            account     - a cloud account
            link_params - information that defines the type of VDU to create

        Returns:
            A kwargs dictionary for glance operation
        """
        drv = self._use_driver(account)
        network_id = None
        try:
            kwargs = drv.utils.network.make_virtual_link_args(link_params)
            network_id = drv.neutron_network_create(**kwargs)
            drv.utils.network.prepare_virtual_link(link_params, network_id)
        except Exception as e:
            self.log.exception("Encountered exceptions during network creation. Exception: %s", str(e))
            # This is to delete the network if neutron_subnet_create fails after creation of network
            # Note:- Any subnet created will be implicitly deleted.
            if network_id is not None:
                try:
                    drv.neutron_network_delete(network_id)
                except Exception as delete_exception:
                    self.log.debug("Exception while deleting the network after failure of neutron_subnet_create or make_subnet_args: %s", str(delete_exception))
                    # Raising exception so that the Exception is propagated to Resmgr.
                    # This fixes the UI Stuck at Vl-Init-Phase.
                    raise Exception(str(e) + " --> " + str(delete_exception))
            raise e
        return network_id


    @rwstatus
    def do_delete_virtual_link(self, account, link_id):
        """Delete a virtual link

        Arguments:
            account - a cloud account
            link_id - id for the virtual-link to be deleted

        Returns:
            None
        """
        drv = self._use_driver(account)
        try:
            port_list = drv.neutron_port_list(**{'network_id': link_id})
            for port in port_list:
                if ((port['device_owner'] == 'compute:None') or (port['device_owner'] == '')):
                    self.do_delete_port(account, port['id'], no_rwstatus=True)
            self.do_delete_network(account, link_id, no_rwstatus=True)
        except Exception as e:
            self.log.exception("Exception %s occured during virtual-link deletion", str(e))
            raise

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link(self, account, link_id):
        """Get information about virtual link.

        Arguments:
            account  - a cloud account
            link_id  - id for the virtual-link

        Returns:
            Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        drv = self._use_driver(account)
        try:
            network = drv.neutron_network_get(link_id)
            if network:
                port_list = drv.neutron_port_list(**{'network_id': network['id']})
                if 'subnets' in network and network['subnets']:
                    subnet = drv.neutron_subnet_get(network['subnets'][0])
                else:
                    subnet = None
                virtual_link = drv.utils.network.parse_cloud_virtual_link_info(network, port_list, subnet)
        except Exception as e:
            self.log.exception("Exception %s occured during virtual-link-get", str(e))
            raise
        return virtual_link

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link_by_name(self, account, link_name):
        """Get information about virtual link.

        Arguments:
            account  - a cloud account
            link_name  - name for the virtual-link

        Returns:
            Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        drv = self._use_driver(account)
        try:
            network = drv.neutron_network_get_by_name(link_name)
            if network:
                port_list = drv.neutron_port_list(**{'network_id': network['id']})
                if 'subnets' in network and network['subnets']:
                    subnet = drv.neutron_subnet_get(network['subnets'][0])
                else:
                    subnet = None
                virtual_link = drv.utils.network.parse_cloud_virtual_link_info(network, port_list, subnet)
            else:
                return None
        except Exception as e:
            self.log.exception("Exception %s occured during virtual-link-get-by-name", str(e))
            raise
        return virtual_link

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link_list(self, account):
        """Get information about all the virtual links

        Arguments:
            account  - a cloud account

        Returns:
            A list of objects of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        vnf_resources = RwcalYang.YangData_RwProject_Project_VnfResources()
        drv =  self._use_driver(account)
        try:
            networks = drv.neutron_network_list()
            for network in networks:
                port_list = drv.neutron_port_list(**{'network_id': network['id']})
                if 'subnets' in network and network['subnets']:
                    subnet = drv.neutron_subnet_get(network['subnets'][0])
                else:
                    subnet = None
                virtual_link = drv.utils.network.parse_cloud_virtual_link_info(network, port_list, subnet)
                vnf_resources.virtual_link_info_list.append(virtual_link)
        except Exception as e:
            self.log.exception("Exception %s occured during virtual-link-list-get", str(e))
            raise
        return vnf_resources



    @rwcalstatus(ret_on_failure=[""])
    def do_create_vdu(self, account, vdu_init):
        """Create a new virtual deployment unit

        Arguments:
            account     - a cloud account
            vdu_init  - information about VDU to create (RwcalYang.YangData_RwProject_Project_VduInitParams)

        Returns:
            The vdu_id
        """
        drv =  self._use_driver(account)
        vdu_prepared = True
        try:
            kwargs = drv.utils.compute.make_vdu_create_args(vdu_init, account)
            vm_id = drv.nova_server_create(**kwargs)
            vdu_prepared_on_boot = self.prepare_vdu_on_boot(account, vm_id, vdu_init)
            vdu_prepared = vdu_prepared_on_boot["status"]
        except Exception as e:
            self.log.exception("Exception %s occured during create-vdu", str(e))
            raise

        if vdu_prepared is False:
            drv.utils.compute.perform_vdu_network_cleanup(vm_id)
            drv.nova_server_delete(vm_id)
            self.log.exception("Cleaning Up VDU as Prepare Vdu Failed : %s", vdu_prepared_on_boot["exception"])
            raise PrepareVduOnBoot(vdu_prepared_on_boot["exception"])
        return vm_id
    

    def prepare_vdu_on_boot(self, account, server_id, vdu_params):
        if vdu_params.mgmt_network is not None:
            mgmt_network_param = vdu_params.mgmt_network
        else:
            mgmt_network_param = account.openstack.mgmt_network

        # Adding shell quote to all parameters in case they contain special characters.
        cmd = PREPARE_VM_CMD.format(auth_url       = shlex.quote(account.openstack.auth_url),
                                    username       = shlex.quote(account.openstack.key),
                                    password       = shlex.quote(account.openstack.secret),
                                    tenant_name    = shlex.quote(account.openstack.tenant),
                                    region         = shlex.quote(account.openstack.region),
                                    user_domain    = shlex.quote(account.openstack.user_domain),
                                    project_domain = shlex.quote(account.openstack.project_domain),
                                    mgmt_network   = shlex.quote(mgmt_network_param),
                                    server_id      = shlex.quote(server_id))
        vol_list = list()

        vdu_prepared = {"status": True, "exception": None}
        
        if vdu_params.has_field('allocate_public_address') and vdu_params.allocate_public_address:
            if account.openstack.has_field('floating_ip_pool'):
                cmd += " --floating_ip"
                cmd += (" --pool_name " + account.openstack.floating_ip_pool)
        
        if vdu_params.has_field('volumes'):
            for volume in vdu_params.volumes:
                if volume.has_field('custom_meta_data'):
                    vol_list.append(volume.as_dict())

        if vol_list:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                yaml.dump(vol_list, tmp_file)
                cmd += (" --vol_metadata {}").format(tmp_file.name)
        
        
        exec_path = 'python3 ' + os.path.dirname(openstack_drv.__file__)
        exec_cmd = exec_path + '/' + cmd
        self.log.info("Running command: %s" %(exec_cmd))
        
        # The return code for the subprocess is always 0. Hence using check_output
        # for validating the success/failure of the script
        # The check_output returns False or True on the basis of exception
        # handling in prepare_vm.py
        prepare_vm_status = subprocess.check_output(exec_cmd, shell=True)
        
        # prepare_vm_status is a string in the format of True/False+ error message
        # if any. This is to propagate the detailed exception to the callers.
        vdu_status_elems = prepare_vm_status.decode("utf-8").split("+")
        if(vdu_status_elems[0] == 'False'):
            self.log.exception("Exception occured while preparing vdu after boot")
            vdu_prepared = {"status": False, "exception": vdu_status_elems[1]}

        return vdu_prepared                      
        
    @rwstatus
    def do_modify_vdu(self, account, vdu_modify):
        """Modify Properties of existing virtual deployment unit

        Arguments:
            account     -  a cloud account
            vdu_modify  -  Information about VDU Modification (RwcalYang.YangData_RwProject_Project_VduModifyParams)
        """
        drv = self._use_driver(account)
        ### First create required number of ports aka connection points
        port_list = []
        network_list = []
        for c_point in vdu_modify.connection_points_add:
            if c_point.virtual_link_id in network_list:
                assert False, "Only one port per network supported. Refer: http://specs.openstack.org/openstack/nova-specs/specs/juno/implemented/nfv-multiple-if-1-net.html"
            else:
                network_list.append(c_point.virtual_link_id)
            port_id = self._create_connection_point(account, c_point)
            port_list.append(port_id)

        drv = self._use_driver(account)
        ### Now add the ports to VM
        for port_id in port_list:
            drv.nova_server_add_port(vdu_modify.vdu_id, port_id)

        ### Delete the requested connection_points
        for c_point in vdu_modify.connection_points_remove:
            self.do_delete_port(account, c_point.connection_point_id, no_rwstatus=True)

        if vdu_modify.has_field('image_id'):
            drv.nova_server_rebuild(vdu_modify.vdu_id, vdu_modify.image_id)


    @rwstatus
    def do_delete_vdu(self, account, vdu_id):
        """Delete a virtual deployment unit

        Arguments:
            account - a cloud account
            vdu_id  - id for the vdu to be deleted

        Returns:
            None
        """
        drv = self._use_driver(account)
        try:
            drv.utils.compute.perform_vdu_network_cleanup(vdu_id)
            drv.nova_server_delete(vdu_id)
        except Exception as e:
            self.log.exception("Exception %s occured during delete-vdu", str(e))
            raise
            

    @rwcalstatus(ret_on_failure=[None])
    def do_get_vdu(self, account, vdu_id, mgmt_network):
        """Get information about a virtual deployment unit.

        Arguments:
            account - a cloud account
            vdu_id  - id for the vdu
            mgmt_network - mgmt_network if provided in NSD VL

        Returns:
            Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList
        """
        if mgmt_network not in [None, ""]:
            account.openstack.mgmt_network = mgmt_network

        drv = self._use_driver(account)
        try:
            vm_info = drv.nova_server_get(vdu_id)
            vdu_info = drv.utils.compute.parse_cloud_vdu_info(vm_info)
        except Exception as e:
            self.log.debug("Exception occured during get-vdu: %s", str(e))
            raise 
        
        return vdu_info


    @rwcalstatus(ret_on_failure=[None])
    def do_get_vdu_list(self, account):
        """Get information about all the virtual deployment units

        Arguments:
            account     - a cloud account

        Returns:
            A list of objects of type RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList
        """
        vnf_resources = RwcalYang.YangData_RwProject_Project_VnfResources()
        drv = self._use_driver(account)
        try:
            vms = drv.nova_server_list()
            for vm in vms:
                vdu = drv.utils.compute.parse_cloud_vdu_info(vm)
                vnf_resources.vdu_info_list.append(vdu)
        except Exception as e:
            self.log.debug("Exception occured during get-vdu-list: %s", str(e))
            raise 
        return vnf_resources


