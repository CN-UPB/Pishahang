
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
from gi import require_version
require_version('RwCal', '1.0')
import rift.rwcal.openmano_vimconnector as vimconn_openvim
import contextlib
import requests
import paramiko
import os
import uuid

from gi.repository import (
    GObject,
    RwCal,
    RwTypes,
    RwcalYang)

import rw_status
import rift.cal.rwcal_status as rwcal_status
import rwlogger

logger = logging.getLogger('rwcal.openmano_vimconnector')

class UnknownAccountError(Exception):
    pass

class OpenvimCALOperationFailure(Exception):
    pass

class MissingFileError(Exception):
    pass


class ImageLocationError(Exception):
    pass

class UninitializedPluginError(Exception):
    pass

rwstatus_exception_map = {IndexError: RwTypes.RwStatus.NOTFOUND,
                          KeyError: RwTypes.RwStatus.NOTFOUND,
                          UnknownAccountError: RwTypes.RwStatus.NOTFOUND,
                          MissingFileError: RwTypes.RwStatus.NOTFOUND,
                          } 

rwstatus = rw_status.rwstatus_from_exc_map(rwstatus_exception_map)
rwcalstatus = rwcal_status.rwcalstatus_from_exc_map(rwstatus_exception_map)


class RwcalOpenmanoVimConnector(GObject.Object, RwCal.Cloud):
    """Stub implementation the CAL VALA methods for Openmano. """

    instance_num = 1
    def __init__(self):
        GObject.Object.__init__(self)
        self._driver_class = vimconn_openvim.vimconnector
        self.log = logging.getLogger('rwcal.openmano_vimconnector.%s' % RwcalOpenmanoVimConnector.instance_num)
        self.log.setLevel(logging.DEBUG)
        self._rwlog_handler = None
        self._tenant_name = None
        RwcalOpenmanoVimConnector.instance_num += 1

    @contextlib.contextmanager
    def _use_driver(self, account):
        #if self._rwlog_handler is None:
        #    raise UninitializedPluginError("Must call init() in CAL plugin before use.")

        #with rwlogger.rwlog_root_handler(self._rwlog_handler):
            try:
                if self._tenant_name != account.openvim.tenant_name:
                    tmp_drv = self._driver_class(uuid = '',
                                  name  = '',
                                  #tenant_id  = account.openvim.tenant_id,
                                  tenant_id  = '',
                                  tenant_name = '',
                                  url   ='http://{}:{}/openvim'.format(account.openvim.host,account.openvim.port),
                                  url_admin = '')
                    tenant_dict = {'name':account.openvim.tenant_name}
                    tenant_list = tmp_drv.get_tenant_list(tenant_dict)
                    if len(tenant_list) == 0:
                        tmp_drv.new_tenant(account.openvim.tenant_name,"default tenant")
                        self._tenant_name = account.openvim.tenant_name 
                    else:
                        self._tenant_name = account.openvim.tenant_name
                  
                     
                drv = self._driver_class(uuid = '',
                                  name  = '',
                                  #tenant_id  = account.openvim.tenant_id,
                                  tenant_id  = '',
                                  tenant_name = account.openvim.tenant_name,
                                  url   ='http://{}:{}/openvim'.format(account.openvim.host,account.openvim.port),
                                  url_admin = '')

            except Exception as e:
                self.log.error("RwcalOpenmanoVimConnectorPlugin: VimConnector init failed. Exception: %s" %(str(e)))
                raise

            yield drv

    @rwstatus
    def do_init(self, rwlog_ctx):
        if not any(isinstance(h, rwlogger.RwLogger) for h in logger.handlers):
            logger.addHandler(
                rwlogger.RwLogger(
                    category="rw-cal-log",
                    subcategory="openmano_vimconnector",
                    log_hdl=rwlog_ctx,
                )
            )

    @rwstatus(ret_on_failure=[None])
    def do_validate_cloud_creds(self, account):
        """
        Validates the cloud account credentials for the specified account.
        If creds are not valid, returns an error code & reason string
        Arguments:
            account - a cloud account to validate

        Returns:
            Validation Code and Details String
        """
        status = RwcalYang.YangData_Rwcal_ConnectionStatus()
        url = 'http://{}:{}/openvim/'.format(account.openvim.host,account.openvim.port)
        try:
            r=requests.get(url,timeout=3)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.log.error("OpenvimConnectorPlugin: Openvim account credential validation failed. Exception: %s", str(e))
            status.status = "failure"
            status.details = "Invalid Credentials: %s" % str(e)
        except Exception as e:
            self.log.error("OpenvimConnectorPlugin: Openvim connection failed. Exception: %s", str(e))
            status.status = "failure"
            status.details = "Connection Failed (Invlaid URL): %s" % str(e)
        else:
            self.log.debug("Openvim Successfully connected")
            status.status = "success"
            status.details = "Connection was successful"

        return status

    @rwstatus(ret_on_failure=[None])
    def do_get_management_network(self, account):
        raise NotImplementedError()

    @rwstatus
    def do_create_tenant(self, account, name):
        with self._use_driver(account) as drv:
            return drv.new_tenant(name, "New CAL teannt");

    @rwstatus
    def do_delete_tenant(self, account, tenant_id):
        with self._use_driver(account) as drv:
            drv.delete_tenant(tenant_id);

    @staticmethod
    def _fill_tenant_info(tenant_info):
        """Create a GI object from tenant info dictionary

        Converts tenant information dictionary object returned by openmano vimconnector
        driver into Protobuf Gi Object

        Arguments:
            tenant_info - tenant information dictionary object

        Returns:
            The TenantInfoItem
        """
        tenant = RwcalYang.YangData_RwProject_Project_VimResources_TenantinfoList()
        tenant.tenant_name = tenant_info['name']
        tenant.tenant_id = tenant_info['id']
        return tenant

    @rwstatus(ret_on_failure=[[]])
    def do_get_tenant_list(self, account):
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        with self._use_driver(account) as drv:
            tenants = drv.get_tenant_list()
        for tenant in tenants:
            response.tenantinfo_list.append(RwcalOpenmanoVimConnector._fill_tenant_info(tenant))
        return response

    @rwstatus
    def do_create_role(self, account, name):
        raise NotImplementedError()

    @rwstatus
    def do_delete_role(self, account, role_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[[]])
    def do_get_role_list(self, account):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[None])
    def do_create_image(self, account, image):
        with self._use_driver(account) as drv:
            try:
                # If the use passed in a file descriptor, use that to
                # upload the image.
                if image.has_field("fileno"):
                    new_fileno = os.dup(image.fileno)
                    hdl = os.fdopen(new_fileno, 'rb')
                else:
                    hdl = open(image.location, "rb")
            except Exception as e:
                self.log.error("Could not open file for upload. Exception received: %s", str(e))
                raise

            tpt = paramiko.Transport((account.openvim.host, 22))
            try:
                tpt.connect(username=account.openvim.image_management.username,
                            password=account.openvim.image_management.password)
            except Exception as e:
                self.log.error('Could not connect to openvim host: %s. Exception: %s', account.openvim.host, e)
                return

            sftp = paramiko.SFTPClient.from_transport(tpt)
            destination = account.openvim.image_management.image_directory_path.rstrip('/')+'/'+image.name
            with hdl as fd:
                try:
                    sftp.putfo(fd, destination)
                except Exception as e:
                    self.log.warn('*** Caught exception: %s: %s', e.__class__, e)
                finally:
                    sftp.close()
                    tpt.close()

            image_dict = {}
            image_dict['name'] = image.name
            image_dict['location'] = destination
            image_id = drv.new_image(image_dict)
        return image_id

    @rwstatus
    def do_delete_image(self, account, image_id):
        with self._use_driver(account) as drv:
            drv.delete_image(image_id)

    @staticmethod
    def _fill_image_info(img_info):
        img = RwcalYang.YangData_RwProject_Project_VimResources_ImageinfoList()
        img.name = img_info['name']
        img.id = img_info['id']
        img.location = img_info['path']
        if img_info['status'] == 'ACTIVE':
            img.state = 'active'
        else:
            img.state = 'inactive'
        return img

    @rwstatus(ret_on_failure=[None])
    def do_get_image(self, account, image_id):
        with self._use_driver(account) as drv:
            image = drv.get_image(image_id)
        return RwcalOpenmanoVimConnector._fill_image_info(image)

    @rwstatus(ret_on_failure=[[]])
    def do_get_image_list(self, account):
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        with self._use_driver(account) as drv:
            images = drv.get_image_list()
        for img in images:
            image_info = drv.get_image(img['id'])
            response.imageinfo_list.append(RwcalOpenmanoVimConnector._fill_image_info(image_info))
        return response

    @rwstatus
    def do_create_vm(self, account, vm):
        raise NotImplementedError()

    @rwstatus
    def do_start_vm(self, account, vm_id):
        raise NotImplementedError()

    @rwstatus
    def do_stop_vm(self, account, vm_id):
        raise NotImplementedError()

    @rwstatus
    def do_delete_vm(self, account, vm_id):
        raise NotImplementedError()

    @rwstatus
    def do_reboot_vm(self, account, vm_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[[]])
    def do_get_vm_list(self, account):
        return RwcalYang.YangData_RwProject_Project_VimResources()

    def _fill_flavor_create_attributes(flavor):
        flavor_dict = dict()
        flavor_dict['name'] = flavor.name
        flavor_dict['ram'] = flavor.vm_flavor.memory_mb
        flavor_dict['disk'] = flavor.vm_flavor.storage_gb
        flavor_dict['vcpus'] = flavor.vm_flavor.vcpu_count 
        return flavor_dict

    @rwstatus
    def do_create_flavor(self, account, flavor):
        with self._use_driver(account) as drv:
            flavor_dict = RwcalOpenmanoVimConnector._fill_flavor_create_attributes(flavor) 
            flavor_id = drv.new_flavor(flavor_dict)
        return flavor_id

    @rwstatus
    def do_delete_flavor(self, account, flavor_id):
        with self._use_driver(account) as drv:
            drv.delete_flavor(flavor_id)

    @staticmethod
    def _fill_epa_attributes(flavor, flavor_info):
        if 'ram' in flavor_info and flavor_info['ram']:
            getattr(flavor, 'vm_flavor').memory_mb   = flavor_info.get('ram',0)
        if 'disk' in flavor_info and flavor_info['disk']:
            getattr(flavor, 'vm_flavor').storage_gb  = flavor_info.get('disk',0)
        if 'vcpus' in flavor_info and flavor_info['vcpus']:
            getattr(flavor, 'vm_flavor').vcpu_count  = flavor_info.get('vcpus',0)

        if not 'extended' in flavor_info or flavor_info['extended'] is None:
            return
        getattr(flavor,'guest_epa').numa_node_policy.node_cnt = len(flavor_info['extended']['numas'])
        for attr in flavor_info['extended']['numas']:
            numa_node = getattr(flavor,'guest_epa').numa_node_policy.node.add()
            numa_node.memory_mb = attr.get('memory',0)*1024
            #getattr(flavor, 'host_epa').cpu_core_thread_count =

    @staticmethod
    def _fill_flavor_info(flavor_info):
        flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()
        flavor.name                       = flavor_info['name']
        flavor.id                         = flavor_info['id']
        RwcalOpenmanoVimConnector._fill_epa_attributes(flavor, flavor_info)
        return flavor

    @rwstatus(ret_on_failure=[None])
    def do_get_flavor(self, account, flavor_id):
        with self._use_driver(account) as drv:
            flavor = drv.get_flavor(flavor_id)
        return RwcalOpenmanoVimConnector._fill_flavor_info(flavor)


    @rwstatus(ret_on_failure=[[]])
    def do_get_flavor_list(self, account):
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        with self._use_driver(account) as drv:
            flavors = drv.get_flavor_list()
        for flav in flavors:
            flav_info = drv.get_flavor(flav['id'])
            response.flavorinfo_list.append(RwcalOpenmanoVimConnector._fill_flavor_info(flav_info))
        return response

    @rwstatus
    def do_add_host(self, account, host):
        raise NotImplementedError()

    @rwstatus
    def do_remove_host(self, account, host_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[None])
    def do_get_host(self, account, host_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[[]])
    def do_get_host_list(self, account):
        raise NotImplementedError()

    @rwstatus
    def do_create_port(self, account, port):
        raise NotImplementedError()

    @rwstatus
    def do_delete_port(self, account, port_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[None])
    def do_get_port(self, account, port_id):
        raise NotImplementedError()

    @rwstatus(ret_on_failure=[[]])
    def do_get_port_list(self, account):
        return RwcalYang.YangData_RwProject_Project_VimResources()

    @rwstatus
    def do_create_network(self, account, network):
        with self._use_driver(account) as drv:
            network_id = drv.new_network(network.name,'bridge_man')
            return network_id

    @rwstatus
    def do_delete_network(self, account, network_id):
        with self._use_driver(account) as drv:
            drv.delete_network(network_id)

    def _fill_network_info(self, network_info):
        network                  = RwcalYang.YangData_RwProject_Project_VimResources_NetworkinfoList()
        network.network_name     = network_info['name']
        network.network_id       = network_info['id']
        if ('provider:physical' in network_info) and (network_info['provider:physical']):
            network.provider_network.physical_network = network_info['provider:physical'].upper()
        if ('provider:vlan' in network_info) and (network_info['provider:vlan']):
            network.provider_network.segmentation_id = network_info['provider:vlan']
            network.provider_network.overlay_type = 'vlan'
        return network

    @rwstatus(ret_on_failure=[None])
    def do_get_network(self, account, network_id):
        with self._use_driver(account) as drv:
            network = drv.get_network(id)
        return self._fill_network_info(network)

    @rwstatus(ret_on_failure=[[]])
    def do_get_network_list(self, account):
        response = RwcalYang.YangData_RwProject_Project_VimResources()
        with self._use_driver(account) as drv:
            networks = drv.get_network_list()
        for network in networks:
            response.networkinfo_list.append(self._fill_network_info(network))
        return response

    @rwcalstatus(ret_on_failure=[""])
    def do_create_virtual_link(self, account, link_params):
        with self._use_driver(account) as drv:
            net = dict()
            if link_params.provider_network.physical_network is not None:
                net['provider:physical'] = link_params.provider_network.physical_network
            #else:
            #    net['provider:physical'] = 'default'
            if link_params.provider_network.overlay_type == 'VLAN' and link_params.provider_network.segmentation_id:
                net['provider:vlan'] = link_params.provider_network.segmentation_id
            network_id = drv.new_network(link_params.name,'bridge_man',shared=False,**net)
            return network_id

    @rwstatus
    def do_delete_virtual_link(self, account, link_id):
        with self._use_driver(account) as drv:
            drv.delete_network(link_id)


    @staticmethod
    def _fill_connection_point_info(c_point, port_info):
        c_point.name = port_info['name']
        c_point.connection_point_id = port_info['id']
        if 'ip_address' in port_info:
                c_point.ip_address = port_info['ip_address']
        if port_info['status'] == 'ACTIVE':
            c_point.state = 'active'
        else:
            c_point.state = 'inactive'
        if 'network_id' in port_info:
            c_point.virtual_link_id = port_info['network_id']
        if ('device_id' in port_info) and (port_info['device_id']):
            c_point.vdu_id = port_info['device_id']

    def _fill_virtual_link_info(self, drv, network_info):
        link = RwcalYang.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList()
        link.name     = network_info['name']
        link.virtual_link_id       = network_info['id']
        if network_info['admin_state_up']:
            link.state = 'active'
        else:
            link.state = 'inactive'
        link.virtual_link_id = network_info['id']
        if ('provider:physical' in network_info) and (network_info['provider:physical']):
            link.provider_network.physical_network = network_info['provider:physical']
        if ('provider:vlan' in network_info) and (network_info['provider:vlan']):
            link.provider_network.segmentation_id = network_info['provider:vlan']
            link.provider_network.overlay_type = 'VLAN'

        if 'ports' in network_info:
            for port in network_info['ports']:
                if 'port_id' in port:
                    port_id = port['port_id']
                    port = drv.get_port(port_id)
                    c_point = link.connection_points.add()
                    RwcalOpenmanoVimConnector._fill_connection_point_info(c_point, port)
        return link

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link(self, account, link_id):
        with self._use_driver(account) as drv:
            network = drv.get_network(link_id)
        return self._fill_virtual_link_info(drv,network)

    @rwstatus(ret_on_failure=[None])
    def do_get_virtual_link_by_name(self, account, link_name):
        raise NotImplementedError()
        
    @rwstatus(ret_on_failure=[""])
    def do_get_virtual_link_list(self, account):
        response = RwcalYang.YangData_RwProject_Project_VnfResources()
        with self._use_driver(account) as drv:
            networks = drv.get_network_list()
        for network in networks:
            network_info = drv.get_network(network['id'])
            response.virtual_link_info_list.append(self._fill_virtual_link_info(drv,network_info))
        return response

    def _match_vm_flavor(self, required, available):
        self.log.info("Matching VM Flavor attributes required {}, available {}".format(required, available))
        if available.vcpu_count != required.vcpu_count:
            return False
        if available.memory_mb != required.memory_mb:
            return False
        if available.storage_gb != required.storage_gb:
            return False
        self.log.debug("VM Flavor match found")
        return True


    def _select_resource_flavor(self, account, vdu_init):
        """ 
            Select a existing flavor if it matches the request or create new flavor
        """
        flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()
        flavor.name = str(uuid.uuid4())
        epa_types = ['vm_flavor', 'guest_epa', 'host_epa', 'host_aggregate', 'hypervisor_epa', 'vswitch_epa']
        epa_dict = {k: v for k, v in vdu_init.as_dict().items() if k in epa_types}
        flavor.from_dict(epa_dict)
 
        rc, response = self.do_get_flavor_list(account)
        if rc != RwTypes.RwStatus.SUCCESS:
            self.log.error("Get-flavor-info-list operation failed for cloud account: %s",
                        account.name)
            raise OpenvimCALOperationFailure("Get-flavor-info-list operation failed for cloud account: %s" %(account.name))

        flavor_id = None
        flavor_list = response.flavorinfo_list
        self.log.debug("Received %d flavor information from RW.CAL", len(flavor_list))
        for flv in flavor_list:
            self.log.info("Attempting to match compute requirement for VDU: %s with flavor %s",
                       vdu_init.name, flv)
            if self._match_vm_flavor(flavor.vm_flavor,flv.vm_flavor):
                self.log.info("Flavor match found for compute requirements for VDU: %s with flavor name: %s, flavor-id: %s",
                           vdu_init.name, flv.name, flv.id)
                return flv.id

        if account.openvim.dynamic_flavor_support is False:
            self.log.error("Unable to create flavor for compute requirement for VDU: %s. VDU instantiation failed", vdu_init.name)
            raise OpenvimCALOperationFailure("No resource available with matching EPA attributes")
        else:
            rc,flavor_id = self.do_create_flavor(account,flavor)
            if rc != RwTypes.RwStatus.SUCCESS:
                self.log.error("Create-flavor operation failed for cloud account: %s",
                        account.name)
                raise OpenvimCALOperationFailure("Create-flavor operation failed for cloud account: %s" %(account.name))
            return flavor_id


    @rwcalstatus(ret_on_failure=[""])
    def do_create_vdu(self, account, vdu_init):
        with self._use_driver(account) as drv:
            net_list = list()

            if not vdu_init.has_field('flavor_id'):
                vdu_init.flavor_id = self._select_resource_flavor(account,vdu_init)

            if account.openvim.mgmt_network:
                mgmt_net_list = drv.get_network_list()
                mgmt_net_id = [net['id'] for net in mgmt_net_list if net['name'] == account.openvim.mgmt_network]
                if len(mgmt_net_id) > 0:
                    mgmt_net_dict = {}
                    mgmt_net_dict['name'] = account.openvim.mgmt_network
                    mgmt_net_dict['net_id'] = mgmt_net_id[0]
                    mgmt_net_dict['type'] = 'virtual'
                    net_list.append(mgmt_net_dict)
                
            for c_point in vdu_init.connection_points:
                net_dict = {}
                net_dict['name'] = c_point.name
                net_dict['net_id'] = c_point.virtual_link_id
                net_dict['type'] = 'virtual'
                net_list.append(net_dict)

            vm_id = drv.new_vminstance(vdu_init.name,vdu_init.name,None,vdu_init.image_id,vdu_init.flavor_id,net_list);
            return vm_id

    @rwstatus
    def do_modify_vdu(self, account, vdu_modify):
        pass

    @rwstatus
    def do_delete_vdu(self, account, vdu_id):
        if not vdu_id:
            self.log.error("empty vdu_id during the vdu deletion")
            return

        with self._use_driver(account) as drv:
            drv.delete_vminstance(vdu_id)

    @staticmethod
    def _fill_vdu_info(drv,account,vm_info):
        vdu = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList()
        vdu.name = vm_info['name']
        vdu.vdu_id = vm_info['id']
        mgmt_net_id = None
        if ('image' in vm_info) and ('id' in vm_info['image']):
            vdu.image_id = vm_info['image']['id']
        if ('flavor' in vm_info) and ('id' in vm_info['flavor']):
            vdu.flavor_id = vm_info['flavor']['id']
        vdu.cloud_type  = 'openvim'

        if account.openvim.mgmt_network:
            net_list = drv.get_network_list()
            mgmt_net_list = [net['id'] for net in net_list if net['name'] == account.openvim.mgmt_network]
            if len(mgmt_net_list) > 0:
                mgmt_net_id = mgmt_net_list[0]

        if 'networks' in vm_info:
            for network in vm_info['networks']:
                port_id = network['iface_id']
                port = drv.get_port(port_id)
                if 'network_id' in port and mgmt_net_id == port['network_id'] and 'ip_address' in port:
                    vdu.management_ip = port['ip_address']
                    vdu.public_ip = vdu.management_ip
                else:
                    c_point = vdu.connection_points.add()
                    RwcalOpenmanoVimConnector._fill_connection_point_info(c_point, port)


        if vm_info['status'] == 'ACTIVE' and vdu.management_ip != '':
            vdu.state = 'active'
        elif vm_info['status'] == 'ERROR':
            vdu.state = 'failed'
        else:
            vdu.state = 'inactive'

        if vdu.flavor_id:
           flavor = drv.get_flavor(vdu.flavor_id)
           RwcalOpenmanoVimConnector._fill_epa_attributes(vdu, flavor)
        return vdu

    @rwcalstatus(ret_on_failure=[None])
    def do_get_vdu(self, account, vdu_id, mgmt_network):
        # mgmt_network - Added due to need for mgmt network.
        # TO DO: Investigate the need here.
        with self._use_driver(account) as drv:
            vm_info = drv.get_vminstance(vdu_id)
        return  RwcalOpenmanoVimConnector._fill_vdu_info(drv,account,vm_info)

    @rwcalstatus(ret_on_failure=[None])
    def do_get_vdu_list(self, account):
        vnf_resource = RwcalYang.YangData_RwProject_Project_VnfResources()
        with self._use_driver(account) as drv:
            vms = drv.get_vminstance_list()
        for vm in vms:
            vm_info = drv.get_vminstance(vm['id'])
            vdu = RwcalOpenmanoVimConnector._fill_vdu_info(drv,account,vm_info)
            vnf_resource.vdu_info_list.append(vdu)
        return vnf_resource

