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
import uuid
import gi
gi.require_version('RwcalYang', '1.0')
from gi.repository import RwcalYang


class ImageValidateError(Exception):
    pass

class VolumeValidateError(Exception):
    pass

class AffinityGroupError(Exception):
    pass


class ComputeUtils(object):
    """
    Utility class for compute operations
    """
    epa_types = ['vm_flavor',
                 'guest_epa',
                 'host_epa',
                 'host_aggregate',
                 'hypervisor_epa',
                 'vswitch_epa']
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

    def search_vdu_flavor(self, vdu_params):
        """
        Function to search a matching flavor for VDU instantiation
        from already existing flavors
        
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           flavor_id(string): Flavor id for VDU instantiation
           None if no flavor could be found
        """
        
        if vdu_params.vm_flavor.has_field('vm_flavor_name') and \
                        vdu_params.vm_flavor.vm_flavor_name is not None:
            nova_flavor_list = self.driver.nova_flavor_list()
            for flavor in nova_flavor_list:
                self.log.debug("Flavor {} ".format(flavor.get('name', '')))
                if flavor.get('name', '') == vdu_params.vm_flavor.vm_flavor_name:
                    return flavor['id']
            
        kwargs = { 'vcpus': vdu_params.vm_flavor.vcpu_count,
                   'ram'  : vdu_params.vm_flavor.memory_mb,
                   'disk' : vdu_params.vm_flavor.storage_gb,}
        
        flavors = self.driver.nova_flavor_find(**kwargs)
        flavor_list = list()
        for flv in flavors:
            flavor_list.append(self.driver.utils.flavor.parse_flavor_info(flv))
            
        flavor_id = self.driver.utils.flavor.match_resource_flavor(vdu_params, flavor_list)
        return flavor_id
        
    def select_vdu_flavor(self, vdu_params):
        """
        This function attempts to find a pre-existing flavor matching required 
        parameters for VDU instantiation. If no such flavor is found, a new one
        is created.
        
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           flavor_id(string): Flavor id for VDU instantiation
        """
        flavor_id = self.search_vdu_flavor(vdu_params)
        if flavor_id is not None:
            self.log.info("Found flavor with id: %s matching requirements for VDU: %s",
                          flavor_id, vdu_params.name)
            return flavor_id

        flavor = RwcalYang.YangData_RwProject_Project_VimResources_FlavorinfoList()
        flavor.name = str(uuid.uuid4())
        
        epa_dict = { k: v for k, v in vdu_params.as_dict().items()
                     if k in ComputeUtils.epa_types }
        
        flavor.from_dict(epa_dict)

        flavor_id = self.driver.nova_flavor_create(name      = flavor.name,
                                                   ram       = flavor.vm_flavor.memory_mb,
                                                   vcpus     = flavor.vm_flavor.vcpu_count,
                                                   disk      = flavor.vm_flavor.storage_gb,
                                                   epa_specs = self.driver.utils.flavor.get_extra_specs(flavor))
        return flavor_id

    def make_vdu_flavor_args(self, vdu_params):
        """
        Creates flavor related arguments for VDU operation
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           A dictionary {'flavor_id': <flavor-id>}
        """
        return {'flavor_id': self.select_vdu_flavor(vdu_params)}


    def make_vdu_image_args(self, vdu_params):
        """
        Creates image related arguments for VDU operation
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           A dictionary {'image_id': <image-id>}

        """
        kwargs = dict()
        if vdu_params.has_field('image_name'):
            kwargs['image_id'] = self.resolve_image_n_validate(vdu_params.image_name,
                                                               vdu_params.image_checksum)
        elif vdu_params.has_field('image_id'):
            kwargs['image_id'] = vdu_params.image_id
            
        return kwargs

    def resolve_image_n_validate(self, image_name, checksum = None):
        """
        Resolve the image_name to image-object by matching image_name and checksum
        
        Arguments:
          image_name (string): Name of image
          checksums  (string): Checksum associated with image

        Raises ImageValidateError in case of Errors
        """
        image_info = [ i for i in self.driver._glance_image_list if i['name'] == image_name]

        if not image_info:
            self.log.error("No image with name: %s found", image_name)
            raise ImageValidateError("No image with name %s found" %(image_name))
        
        for image in image_info:
            if 'status' not in image or image['status'] != 'active':
                self.log.error("Image %s not in active state. Current state: %s",
                               image_name, image['status'])
                raise ImageValidateError("Image with name %s found in incorrect (%s) state"
                                         %(image_name, image['status']))
            if not checksum or checksum == image['checksum']:
                break
        else:
            self.log.info("No image found with matching name: %s and checksum: %s",
                          image_name, checksum)
            raise ImageValidateError("No image found with matching name: %s and checksum: %s"
                                     %(image_name, checksum))
        return image['id']
        
    def resolve_volume_n_validate(self, volume_ref):
        """
        Resolve the volume reference
        
        Arguments:
          volume_ref (string): Name of volume reference

        Raises VolumeValidateError in case of Errors
        """
        
        for vol in self.driver._cinder_volume_list:
            voldict = vol.to_dict()
            if 'display_name' in voldict and voldict['display_name'] == volume_ref:
                if 'status' in voldict:
                    if voldict['status'] == 'available':
                        return voldict['id']
                    else:
                        self.log.error("Volume %s not in available state. Current state: %s",
                               volume_ref, voldict['status'])
                        raise VolumeValidateError("Volume with name %s found in incorrect (%s) state"
                                         %(volume_ref, voldict['status']))

        self.log.info("No volume found with matching name: %s ", volume_ref)
        raise VolumeValidateError("No volume found with matching name: %s " %(volume_ref))
        
    def make_vdu_volume_args(self, volume, vdu_params):
        """
        Arguments:
           volume:   Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams_Volumes()
           vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()
        
        Returns:
           A dictionary required to create volume for VDU

        Raises VolumeValidateError in case of Errors
        """
        kwargs = dict()

        if 'boot_priority' in volume:
            # Rift-only field
            kwargs['boot_index'] = volume.boot_priority
        if volume.has_field("image"):
            # Support image->volume
            kwargs['source_type'] = "image"
            kwargs['uuid'] = self.resolve_image_n_validate(volume.image, volume.image_checksum)
            kwargs['delete_on_termination'] = True
        elif "volume_ref" in volume:
            # Support volume-ref->volume (only ref)
            # Rift-only field
            kwargs['source_type'] = "volume"
            kwargs['uuid'] = self.resolve_volume_n_validate(volume.volume_ref)
            kwargs['delete_on_termination'] = False
        else:
            # Support blank->volume
            kwargs['source_type'] = "blank"
            kwargs['delete_on_termination'] = True
        kwargs['device_name'] = volume.name
        kwargs['destination_type'] = "volume"
        kwargs['volume_size'] = volume.size

        if volume.has_field('device_type'):
            if volume.device_type in ['cdrom', 'disk']:
                kwargs['device_type'] = volume.device_type
            else:
                self.log.error("Unsupported device_type <%s> found for volume: %s",
                               volume.device_type, volume.name)
                raise VolumeValidateError("Unsupported device_type <%s> found for volume: %s"
                                          %(volume.device_type, volume.name))

        if volume.has_field('device_bus'):
            if volume.device_bus in ['ide', 'virtio', 'scsi']:
                kwargs['disk_bus'] = volume.device_bus
            else:
                self.log.error("Unsupported device_type <%s> found for volume: %s",
                               volume.device_type, volume.name)
                raise VolumeValidateError("Unsupported device_type <%s> found for volume: %s"
                                          %(volume.device_type, volume.name))

        return kwargs
            
    def make_vdu_storage_args(self, vdu_params):
        """
        Creates volume related arguments for VDU operation
        
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           A dictionary required for volumes creation for VDU instantiation
        """
        kwargs = dict()
        if vdu_params.has_field('volumes'):
            kwargs['block_device_mapping_v2'] = list()
            bootvol_list = list()
            othervol_list = list()
            # Ignore top-level image
            kwargs['image_id']  = ""
            for volume in vdu_params.volumes:
                if 'boot_priority' in volume:
                    bootvol_list.append(self.make_vdu_volume_args(volume, vdu_params))
                else:
                    othervol_list.append(self.make_vdu_volume_args(volume, vdu_params))
            # Sort block_device_mapping_v2 list by boot index, Openstack does not seem to respecting order by boot index
            kwargs['block_device_mapping_v2'] = sorted(bootvol_list, key=lambda k: k['boot_index']) + othervol_list
        return kwargs

    def make_vdu_network_args(self, vdu_params):
        """
        Creates VDU network related arguments for VDU operation
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
           A dictionary {'port_list' : [ports], 'network_list': [networks]}

        """
        kwargs = dict()
        kwargs['port_list'], kwargs['network_list'] = self.driver.utils.network.setup_vdu_networking(vdu_params)
        
        return kwargs

    
    def make_vdu_boot_config_args(self, vdu_params):
        """
        Creates VDU boot config related arguments for VDU operation
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()

        Returns:
          A dictionary {
                         'userdata'    :  <cloud-init> , 
                         'config_drive':  True/False, 
                         'files'       :  [ file name ],
                         'metadata'    :  <metadata string>
        }
        """
        kwargs = dict()
        metadata = dict()

        if vdu_params.has_field('node_id'):
            metadata['rift_node_id'] = vdu_params.node_id
            kwargs['metadata'] = metadata

        if vdu_params.has_field('vdu_init') and vdu_params.vdu_init.has_field('userdata'):
            kwargs['userdata'] = vdu_params.vdu_init.userdata
        else:
            kwargs['userdata'] = ''

        if not vdu_params.has_field('supplemental_boot_data'):
            return kwargs
        
        if vdu_params.supplemental_boot_data.has_field('config_file'):
            files = dict()
            for cf in vdu_params.supplemental_boot_data.config_file:
                files[cf.dest] = cf.source
            kwargs['files'] = files

        if vdu_params.supplemental_boot_data.has_field('boot_data_drive'):
            kwargs['config_drive'] = vdu_params.supplemental_boot_data.boot_data_drive
        else:
            kwargs['config_drive'] = False

        try:
            # Rift model only
            if vdu_params.supplemental_boot_data.has_field('custom_meta_data'):
                for cm in vdu_params.supplemental_boot_data.custom_meta_data:
                    # Adding this condition as the list contains CLOUD_INIT Variables as 
                    # well. CloudInit Variables such as password are visible on the OpenStack UI
                    # if not removed from the custom_meta_data list.
                    if cm.destination == 'CLOUD_METADATA':
                        metadata[cm.name] = cm.value
                        kwargs['metadata'] = metadata
        except Exception as e:
            pass

        return kwargs

    def _select_affinity_group(self, group_name):
        """
        Selects the affinity group based on name and return its id
        Arguments:
          group_name (string): Name of the Affinity/Anti-Affinity group
        Returns:
          Id of the matching group

        Raises exception AffinityGroupError if no matching group is found
        """
        groups = [g['id'] for g in self.driver._nova_affinity_group if g['name'] == group_name]
        if not groups:
            self.log.error("No affinity/anti-affinity group with name: %s found", group_name)
            raise AffinityGroupError("No affinity/anti-affinity group with name: %s found" %(group_name))
        return groups[0]

        
    def make_vdu_server_placement_args(self, vdu_params):
        """
        Function to create kwargs required for nova server placement
        
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()
        
        Returns:
         A dictionary { 'availability_zone' : < Zone >, 'scheduler_hints': <group-id> } 

        """
        kwargs = dict()
        
        if vdu_params.has_field('availability_zone') \
           and vdu_params.availability_zone.has_field('name'):
            kwargs['availability_zone']  = vdu_params.availability_zone

        if vdu_params.has_field('server_group'):
            kwargs['scheduler_hints'] = {
                'group': self._select_affinity_group(vdu_params.server_group)
            }            
        return kwargs

    def make_vdu_server_security_args(self, vdu_params, account):
        """
        Function to create kwargs required for nova security group

        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()
          account: Protobuf GI object RwcalYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList()
        
        Returns:
          A dictionary {'security_groups' : < group > }
        """
        kwargs = dict()
        if account.openstack.security_groups:
            kwargs['security_groups'] = account.openstack.security_groups
        return kwargs
    
    
    def make_vdu_create_args(self, vdu_params, account):
        """
        Function to create kwargs required for nova_server_create API
        
        Arguments:
          vdu_params: Protobuf GI object RwcalYang.YangData_RwProject_Project_VduInitParams()
          account: Protobuf GI object RwcalYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList()

        Returns:
          A kwargs dictionary for VDU create operation
        """
        kwargs = dict()
        
        kwargs['name'] = vdu_params.name

        kwargs.update(self.make_vdu_flavor_args(vdu_params))
        kwargs.update(self.make_vdu_storage_args(vdu_params))
        kwargs.update(self.make_vdu_image_args(vdu_params))
        kwargs.update(self.make_vdu_network_args(vdu_params))
        kwargs.update(self.make_vdu_boot_config_args(vdu_params))
        kwargs.update(self.make_vdu_server_placement_args(vdu_params))
        kwargs.update(self.make_vdu_server_security_args(vdu_params, account))
        return kwargs
        
    
    def _parse_vdu_mgmt_address_info(self, vm_info):
        """
        Get management_ip and public_ip for VDU
        
        Arguments:
          vm_info : A dictionary object return by novaclient library listing VM attributes
        
        Returns:
          A tuple of mgmt_ip (string) and public_ip (string)
        """
        mgmt_ip = None
        public_ip = None
        if 'addresses' in vm_info:
            for network_name, network_info in vm_info['addresses'].items():
                if network_info and network_name == self.driver.mgmt_network:
                    for interface in network_info:
                        if 'OS-EXT-IPS:type' in interface:
                            if interface['OS-EXT-IPS:type'] == 'fixed':
                                mgmt_ip = interface['addr']
                            elif interface['OS-EXT-IPS:type'] == 'floating':
                                public_ip = interface['addr']

        return (mgmt_ip, public_ip)

    def get_vdu_epa_info(self, vm_info):
        """
        Get flavor information (including EPA) for VDU

        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes
        Returns:
          flavor_info: A dictionary object returned by novaclient library listing flavor attributes
        """
        if 'flavor' in vm_info and 'id' in vm_info['flavor']:
            try:
                flavor_info = self.driver.nova_flavor_get(vm_info['flavor']['id'])
                return flavor_info
            except Exception as e:
                self.log.exception("Exception %s occured during get-flavor", str(e))
        return dict()

    def _parse_vdu_cp_info(self, vdu_id):
        """
        Get connection point information for VDU identified by vdu_id
        Arguments:
        vdu_id (string) : VDU Id (vm_info['id']) 
        Returns:
        A List of object RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_ConnectionPoints()

        """
        cp_list = []
        # Fill the port information
        port_list = self.driver.neutron_port_list(**{'device_id': vdu_id})
        for port in port_list:
            cp_info = self.driver.utils.network._parse_cp(port)
            cp = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_ConnectionPoints()
            cp.from_dict(cp_info.as_dict())
            cp_list.append(cp)
        return cp_list

    def _parse_vdu_state_info(self, vm_info):
        """
        Get VDU state information

        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes

        Returns:
          state (string): State of the VDU
        """
        if 'status' in vm_info:
            if vm_info['status'] == 'ACTIVE':
                vdu_state = 'active'
            elif vm_info['status'] == 'ERROR':
                vdu_state = 'failed'
            else:
                vdu_state = 'inactive'
        else:
            vdu_state = 'unknown'
        return vdu_state

    def _parse_vdu_server_group_info(self, vm_info):
        """
        Get VDU server group information
        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes

        Returns:
          server_group_name (string): Name of the server group to which VM belongs, else empty string
        
        """
        server_group = [ v['name']
                         for v in self.driver.nova_server_group_list()
                         if vm_info['id'] in v['members'] ]
        if server_group:
            return server_group[0]
        else:
            return str()

    def _parse_vdu_boot_config_data(self, vm_info):
        """
        Parses VDU supplemental boot data
        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes

        Returns:
          List of RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_SupplementalBootData()
        """
        supplemental_boot_data = None
        node_id = None
        if 'config_drive' in vm_info:
            supplemental_boot_data = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_SupplementalBootData()
            supplemental_boot_data.boot_data_drive = vm_info['config_drive']
        # Look for any metadata
        if 'metadata' not in vm_info:
            return node_id, supplemental_boot_data
        if supplemental_boot_data is None:
            supplemental_boot_data = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_SupplementalBootData()
        for key, value in vm_info['metadata'].items():
            if key == 'rift_node_id':
                node_id = value
            else:
                try:
                    # rift only
                    cm = supplemental_boot_data.custom_meta_data.add()
                    cm.name = key
                    cm.value = str(value)
                except Exception as e:
                    pass
        return node_id, supplemental_boot_data 

    def _parse_vdu_volume_info(self, vm_info):
        """
        Get VDU server group information
        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes

        Returns:
          List of RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_Volumes()
        """
        volumes = list()
        
        try:
            volume_list = self.driver.nova_volume_list(vm_info['id'])
        except Exception as e:
            self.log.exception("Exception %s occured during nova-volume-list", str(e))
            return volumes

        for v in volume_list:
            volume = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList_Volumes()
            try:
                volume.name = (v['device']).split('/')[2]
                volume.volume_id = v['volumeId']
                details = self.driver.cinder_volume_get(volume.volume_id)
                if details is None:
                    continue
                try:
                    # Rift only
                    for k, v in details.metadata.items():
                        vd = volume.custom_meta_data.add()
                        vd.name = k
                        vd.value = v
                except Exception as e:
                    pass
            except Exception as e:
                self.log.exception("Exception %s occured during volume list parsing", str(e))
                continue
            else:
                volumes.append(volume)
        return volumes
    
    def _parse_vdu_console_url(self, vm_info):
        """
        Get VDU console URL
        Arguments:
          vm_info : A dictionary returned by novaclient library listing VM attributes

        Returns:
          console_url(string): Console URL for VM
        """
        console_url = None
        if self._parse_vdu_state_info(vm_info) == 'active':
            try:
                serv_console_url = self.driver.nova_server_console(vm_info['id'])
                if 'console' in serv_console_url:
                    console_url = serv_console_url['console']['url']
                else:
                    self.log.error("Error fetching console url. This could be an Openstack issue. Console : " + str(serv_console_url))


            except Exception as e:
                self.log.warning("Exception %s occured during volume list parsing", str(e))
        return console_url

    def parse_cloud_vdu_info(self, vm_info):
        """
        Parse vm_info dictionary (return by python-client) and put values in GI object for VDU

        Arguments:
           vm_info : A dictionary object return by novaclient library listing VM attributes
        
        Returns:
           Protobuf GI Object of type RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList()
        """
        vdu = RwcalYang.YangData_RwProject_Project_VnfResources_VduInfoList()
        vdu.name = vm_info['name']
        vdu.vdu_id = vm_info['id']
        vdu.cloud_type  = 'openstack'

        if 'image' in vm_info and 'id' in vm_info['image']:
            vdu.image_id = vm_info['image']['id']

        if 'availability_zone' in vm_info:
            vdu.availability_zone = vm_info['availability_zone']

        vdu.state = self._parse_vdu_state_info(vm_info)
        management_ip,public_ip = self._parse_vdu_mgmt_address_info(vm_info)

        if management_ip:
            vdu.management_ip = management_ip

        if public_ip:
            vdu.public_ip = public_ip

        if 'flavor' in vm_info and 'id' in vm_info['flavor']:
            vdu.flavor_id = vm_info['flavor']['id']
            flavor_info = self.get_vdu_epa_info(vm_info)
            if flavor_info is not None:
                vm_flavor = self.driver.utils.flavor.parse_vm_flavor_epa_info(flavor_info)
                guest_epa = self.driver.utils.flavor.parse_guest_epa_info(flavor_info)
                host_epa = self.driver.utils.flavor.parse_host_epa_info(flavor_info)
                host_aggregates = self.driver.utils.flavor.parse_host_aggregate_epa_info(flavor_info)

                vdu.vm_flavor.from_dict(vm_flavor.as_dict())
                vdu.guest_epa.from_dict(guest_epa.as_dict())
                vdu.host_epa.from_dict(host_epa.as_dict())
                for aggr in host_aggregates:
                    ha = vdu.host_aggregate.add()
                    ha.from_dict(aggr.as_dict())

        node_id, boot_data = self._parse_vdu_boot_config_data(vm_info)
        if node_id:
            vdu.node_id = node_id
        if boot_data:
            vdu.supplemental_boot_data = boot_data

        cp_list = self._parse_vdu_cp_info(vdu.vdu_id)
        for cp in cp_list:
            vdu.connection_points.append(cp)
        
        vdu.server_group.name = self._parse_vdu_server_group_info(vm_info)

        for v in self._parse_vdu_volume_info(vm_info):
            vdu.volumes.append(v)

        vdu.console_url = self._parse_vdu_console_url(vm_info)
        return vdu


    def perform_vdu_network_cleanup(self, vdu_id):
        """
        This function cleans up networking resources related to VDU
        Arguments:
           vdu_id(string): VDU id 
        Returns:
           None
        """
        ### Get list of floating_ips associated with this instance and delete them
        floating_ips = [ f for f in self.driver.nova_floating_ip_list() if f.instance_id == vdu_id ]
        for f in floating_ips:
            self.driver.nova_floating_ip_delete(f)

        ### Get list of port on VM and delete them.
        port_list = self.driver.neutron_port_list(**{'device_id': vdu_id})

        for port in port_list:
            self.driver.neutron_port_delete(port['id'])

