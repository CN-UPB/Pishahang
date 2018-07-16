
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

import rift.rwcal.kubernetes as kubernetes_drv


import rw_status
import rift.cal.rwcal_status as rwcal_status
import rwlogger


from gi.repository import (
    GObject,
    RwCal,
    RwTypes,
    RwcalYang)

rwstatus_exception_map = {IndexError: RwTypes.RwStatus.NOTFOUND,
                          KeyError: RwTypes.RwStatus.NOTFOUND,
                          NotImplementedError: RwTypes.RwStatus.NOT_IMPLEMENTED, }

rwstatus = rw_status.rwstatus_from_exc_map(rwstatus_exception_map)
rwcalstatus = rwcal_status.rwcalstatus_from_exc_map(rwstatus_exception_map)


class OpenstackCALOperationFailure(Exception):
    pass

class UninitializedPluginError(Exception):
    pass

class RwcalAccountDriver(object):
    """
    Container class per cloud account
    """
    def __init__(self, logger, **kwargs):
        self.log = logger
        try:
            self._driver = kubernetes_drv.KubernetesDriver(logger = self.log, **kwargs)
        except Exception as e:
            self.log.error("RwcalKubernetesPlugin: KubernetesDriver init failed. Exception: %s" %(str(e)))
            raise

    @property
    def driver(self):
        return self._driver
    
class RwcalKubernetesPlugin(GObject.Object, RwCal.Cloud):
    """This class implements the CAL VALA methods for Kubernetes."""

    instance_num = 1

    def __init__(self):
        GObject.Object.__init__(self)
        self.log = logging.getLogger('rwcal.kubernetes.%s' % RwcalKubernetesPlugin.instance_num)
        self.log.setLevel(logging.DEBUG)
        self._rwlog_handler = None
        self._account_drivers = dict()
        RwcalKubernetesPlugin.instance_num += 1

    def _get_account_key(self, account):
        key = str()
        for f in account.openstack.fields:
            try:
                key+= str(getattr(account.kubernetes, f))
            except:
                pass
        key += account.name
        return key

    def _use_driver(self, account):
        if self._rwlog_handler is None:
            raise UninitializedPluginError("Must call init() in CAL plugin before use.")

        acct_key = self._get_account_key(account)
        
        if acct_key not in self._account_drivers:
            self.log.debug("Creating KubernetesDriver")
            kwargs = dict(host = account.kubernetes.host,
                          username = account.kubernetes.username,
                          password = account.kubernetes.password,
                          kubernetes_local_api_connector = account.kubernetes.kubernetes_local_api_connector)
            drv = RwcalAccountDriver(self.log, **kwargs)
            self._account_drivers[account.name] = drv
            return drv.driver
        else:
            return self._account_drivers[acct_key].driver

    @rwstatus
    def do_init(self, rwlog_ctx):
        self._rwlog_handler = rwlogger.RwLogger(category="rw-cal-log",
                                                subcategory="kubernetes",
                                                log_hdl=rwlog_ctx,)
        self.log.addHandler(self._rwlog_handler)
        self.log.propagate = False

        self.auth_url = account.kubernetes.auth_url

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
        status = RwcalYang.YangData_Rwcal_ConnectionStatus(
                status="success",
                details="Kubernetes Account validation not implemented yet"
                )

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
        raise NotImplementedError

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
        raise NotImplementedError

    @rwstatus
    def do_delete_image(self, account, image_id):
        """Delete a vm image.

        Arguments:
            account - a cloud account
            image_id - id of the image to delete
        """
        raise NotImplementedError


    @rwstatus(ret_on_failure=[[]])
    def do_get_image_list(self, account):
        """Return a list of the names of all available images.

        Arguments:
            account - a cloud account

        Returns:
            The the list of images in VimResources object
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_image(self, account, image_id):
        """Return a image information.

        Arguments:
            account - a cloud account
            image_id - an id of the image

        Returns:
            ImageInfoItem object containing image information.
        """
        raise NotImplementedError
    

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
        drv =  self._driver
        try:
            vm_id = drv.create_pod(**kwargs)
        except Exception as e:
            self.log.exception("Exception %s occured during create-vdu", str(e))
            raise

        return vm_id

    @rwstatus
    def do_start_vm(self, account, vm_id):
        """Start an existing virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        raise NotImplementedError

    @rwstatus
    def do_stop_vm(self, account, vm_id):
        """Stop a running virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        raise NotImplementedError

    @rwstatus
    def do_delete_vm(self, account, vm_id):
        """Delete a virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        # TODO: implement

    @rwstatus
    def do_reboot_vm(self, account, vm_id):
        """Reboot a virtual machine.

        Arguments:
            account - a cloud account
            vm_id - an id of the VM
        """
        raise NotImplementedError

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
        # TODO: delete above and implement for kubernetes


    @rwstatus(ret_on_failure=[None])
    def do_get_vm(self, account, id):
        """Return vm information.

        Arguments:
            account - a cloud account
            id - an id for the VM

        Returns:
            VM information
        """
        drv =  self._driver
        try:
            vm_id = drv.get_pod(**kwargs)
        except Exception as e:
            self.log.exception("Exception %s occured during get-vdu", str(e))
            raise

        return vm_id
        # TODO: delete above and implement for kubernetes


    @rwstatus(ret_on_failure=[""])
    def do_create_flavor(self, account, flavor):
        """Create new flavor.

        Arguments:
            account - a cloud account
            flavor - flavor of the VM

        Returns:
            flavor id
        """
        raise NotImplementedError

    @rwstatus
    def do_delete_flavor(self, account, flavor_id):
        """Delete flavor.

        Arguments:
            account - a cloud account
            flavor_id - id flavor of the VM
        """
        raise NotImplementedError


    @rwstatus(ret_on_failure=[[]])
    def do_get_flavor_list(self, account):
        """Return flavor information.

        Arguments:
            account - a cloud account

        Returns:
            List of flavors
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_flavor(self, account, id):
        """Return flavor information.

        Arguments:
            account - a cloud account
            id - an id for the flavor

        Returns:
            Flavor info item
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[[]])
    def do_get_network_list(self, account):
        """Return a list of networks

        Arguments:
            account - a cloud accountr

        Returns:
            List of networks
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_network(self, account, id):
        """Return a network

        Arguments:
            account - a cloud account
            id - an id for the network

        Returns:
            Network info item
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[""])
    def do_create_network(self, account, network):
        """Create a new network

        Arguments:
            account - a cloud account
            network - Network object

        Returns:
            Network id
        """
        raise NotImplementedError

    @rwstatus
    def do_delete_network(self, account, network_id):
        """Delete a network

        Arguments:
            account - a cloud account
            network_id - an id for the network
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_port(self, account, port_id):
        """Return a port

        Arguments:
            account - a cloud account
            port_id - an id for the port

        Returns:
            Port info item
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[[]])
    def do_get_port_list(self, account):
        """Return a list of ports

        Arguments:
            account - a cloud account

        Returns:
            Port info list
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[""])
    def do_create_port(self, account, port):
        """Create a new port

        Arguments:
            account - a cloud account
            port - port object

        Returns:
            Port id
        """
        raise NotImplementedError

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
        raise NotImplementedError

    @rwstatus
    def do_delete_virtual_link(self, account, link_id):
        """Delete a virtual link

        Arguments:
            account - a cloud account
            link_id - id for the virtual-link to be deleted

        Returns:
            None
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link(self, account, link_id):
        """Get information about virtual link.

        Arguments:
            account  - a cloud account
            link_id  - id for the virtual-link

        Returns:
            Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link_by_name(self, account, link_name):
        """Get information about virtual link.

        Arguments:
            account  - a cloud account
            link_name  - name for the virtual-link

        Returns:
            Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        raise NotImplementedError

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link_list(self, account):
        """Get information about all the virtual links

        Arguments:
            account  - a cloud account

        Returns:
            A list of objects of type RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList
        """
        raise NotImplementedError

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
        kwargs = {}
        image_id = vdu_init.image_id
        name = vdu_init.name
        try:
            pod_uid = drv.create_pod(name=name, description='', start=True, image_id=image_id, flavor_id=None, net_list=None)
        except Exception as e:
            self.log.exception("Exception %s occured during create-vdu", str(e))
            raise

        return pod_uid
    
    def prepare_vdu_on_boot(self, account, server_id, vdu_params):
        raise NotImplementedError
        
    @rwstatus
    def do_modify_vdu(self, account, vdu_modify):
        """Modify Properties of existing virtual deployment unit

        Arguments:
            account     -  a cloud account
            vdu_modify  -  Information about VDU Modification (RwcalYang.YangData_RwProject_Project_VduModifyParams)
        """
        raise NotImplementedError


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
        # TODO: delete above and implement for kubernetes
            

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
        # TODO: delete above and implement for kubernetes


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
        # TODO: same as do_get_vm_list()?


