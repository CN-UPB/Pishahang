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
from novaclient import client as nvclient


class NovaDrvAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(NovaDrvAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during Nova API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg


class NovaDriver(object):
    """
    NovaDriver Class for compute orchestration
    """
    ### List of supported API versions in prioritized order 
    supported_versions = ["2.1", "2.0"]
    
    def __init__(self,
                 sess_handle,
                 region_name    = 'RegionOne',
                 service_type   = 'compute',
                 logger = None):
        """
        Constructor for NovaDriver class
        Arguments:
        sess_handle (instance of class SessionDriver)
        region_name (string): Region Name
        service_type(string): Type of service in service catalog
        logger (instance of logging.Logger)
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.nova')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger
        
        self._sess_handle = sess_handle

        self._max_api_version = None
        self._min_api_version = None

        #### Attempt to use API versions in prioritized order defined in
        #### NovaDriver.supported_versions
        def select_version(version):
            try:
                self.log.info("Attempting to use Nova v%s APIs", version)
                nvdrv = nvclient.Client(version=version,
                                        region_name = region_name,
                                        service_type = service_type,
                                        session = self._sess_handle.session,
                                        logger = self.log)
                
                api_version = 'v' + nvdrv.versions.api_version.get_string()
                nova_version_list = nvdrv.versions.list()
                max_api_version, min_api_version = None, None
                
                for v in nova_version_list:
                    version_dict = v.to_dict()
                    if api_version == version_dict["id"]:
                        max_api_version = version_dict["version"] # Max version supported is stored in version field.
                        min_api_version = version_dict["min_version"]
                        break

            except Exception as e:
                self.log.info(str(e))
                raise
            else:
                self.log.info("Nova API v%s selected", version)
                return (version, nvdrv, max_api_version, min_api_version)

        errors = []
        for v in NovaDriver.supported_versions:
            try:
                (self._version, self._nv_drv, self._max_api_version, self._min_api_version) = select_version(v)
            except Exception as e:
                errors.append(e)
            else:
                break
        else:
            raise NovaDrvAPIVersionException(errors)

    @property
    def project_id(self):
        return self._sess_handle.project_id

    @property
    def nova_endpoint(self):
        return self._nv_drv.client.get_endpoint()

    @property
    def nova_quota(self):
        """
        Returns Nova Quota (a dictionary) for project
        """
        try:
            quota = self._nv_drv.quotas.get(self.project_id)
        except Exception as e:
            self.log.exception("Get Nova quota operation failed. Exception: %s", str(e))
            raise
        return quota.to_dict()
    
    def extensions_list(self):
        """
        Returns a list of available nova extensions.
        Arguments:
           None
        Returns:
           A list of dictionaries. Each dictionary contains attributes for a single NOVA extension
        """
        try:
            extensions = self._nv_drv.list_extensions.show_all()
        except Exception as e:
            self.log.exception("List extension operation failed. Exception: %s", str(e))
            raise
        return [ ext.to_dict() for ext in extensions ]
            
    
    def _get_nova_connection(self):
        """
        Returns instance of object novaclient.client.Client
        Use for DEBUG ONLY
        """
        return self._nv_drv

    def _flavor_extra_spec_get(self, flavor):
        """
        Get extra_specs associated with a flavor
        Arguments:
           flavor: Object of novaclient.v2.flavors.Flavor

        Returns:
           A dictionary of extra_specs (key-value pairs)
        """
        try:
            extra_specs = flavor.get_keys()
        except nvclient.exceptions.NotFound:
            return None
        except Exception as e:
            self.log.exception("Could not get the EPA attributes for flavor with flavor_id : %s. Exception: %s",
                               flavor.id, str(e))
            raise
        return extra_specs
    
    def _flavor_get(self, flavor_id):
        """
        Get flavor by flavor_id
        Arguments:
           flavor_id(string): UUID of flavor_id

        Returns:
        dictionary of flavor parameters
        """
        try:
            flavor = self._nv_drv.flavors.get(flavor_id)
        except nvclient.exceptions.NotFound:
            return None
        except Exception as e:
            self.log.exception("Did not find flavor with flavor_id : %s. Exception: %s",flavor_id, str(e))
            raise
        response = flavor.to_dict()
        try:
            response['extra_specs'] = self._flavor_extra_spec_get(flavor)
        except nvclient.exceptions.NotFound:
            pass
        except Exception as e:
            self.log.exception("Did not find extra_specs in flavor with flavor_id : %s. Exception: %s",flavor_id, str(e))
            raise
        return response
        
        try:
            extra_specs = flavor.get_keys()
        except Exception as e:
            self.log.exception("Could not get the EPA attributes for flavor with flavor_id : %s. Exception: %s",
                               flavor_id, str(e))
            raise

        response = flavor.to_dict()
        assert 'extra_specs' not in response, "Key extra_specs present as flavor attribute"
        response['extra_specs'] = extra_specs
        return response

    def flavor_get(self, flavor_id):
        """
        Get flavor by flavor_id
        Arguments:
           flavor_id(string): UUID of flavor_id

        Returns:
        dictionary of flavor parameters
        """
        return self._flavor_get(flavor_id)

    def flavor_find(self, **kwargs):
        """
        Returns list of all flavors (dictionary) matching the filters provided in kwargs 

        Arguments:
          A dictionary in following keys
             {
                "vcpus": Number of vcpus required
                "ram"  : Memory in MB
                "disk" : Secondary storage in GB
             }
        Returns:
           A list of dictionaries. Each dictionary contains attributes for a single flavor instance
        """
        try:
            flavor_list = self._nv_drv.flavors.findall(**kwargs)
        except Exception as e:
            self.log.exception("Find Flavor operation failed. Exception: %s",str(e))
            raise
        
        flavor_info = list()
        for f in flavor_list:
            flavor = f.to_dict()
            flavor['extra_specs'] = self._flavor_extra_spec_get(f)
            flavor_info.append(flavor)
            
        return flavor_info
    
    def flavor_list(self):
        """
        Returns list of all flavors (dictionary per flavor)

        Arguments:
           None
        Returns:
           A list of dictionaries. Each dictionary contains attributes for a single flavor instance
        """
        flavors = []
        flavor_info = []
        
        try:
            flavors = self._nv_drv.flavors.list()
        except Exception as e:
            self.log.exception("List Flavor operation failed. Exception: %s",str(e))
            raise
        if flavors:
            flavor_info = [ self.flavor_get(flv.id) for flv in flavors ]
        return flavor_info

    def flavor_create(self, name, ram, vcpu, disk, extra_specs):
        """
        Create a new flavor

        Arguments:
           name   (string):  Name of the new flavor
           ram    (int)   :  Memory in MB
           vcpus  (int)   :  Number of VCPUs
           disk   (int)   :  Secondary storage size in GB
           extra_specs (dictionary): EPA attributes dictionary

        Returns:
           flavor_id (string): UUID of flavor created
        """
        try:
            flavor = self._nv_drv.flavors.create(name         = name,
                                                 ram          = ram,
                                                 vcpus        = vcpu,
                                                 disk         = disk,
                                                 flavorid     = 'auto',
                                                 ephemeral    = 0,
                                                 swap         = 0,
                                                 rxtx_factor  = 1.0,
                                                 is_public    = True)
        except Exception as e:
            self.log.exception("Create Flavor operation failed. Exception: %s",str(e))
            raise

        if extra_specs:
            try:
                flavor.set_keys(extra_specs)
            except Exception as e:
                self.log.exception("Set Key operation failed for flavor: %s. Exception: %s",
                                   flavor.id, str(e))
                raise
        return flavor.id

    def flavor_delete(self, flavor_id):
        """
        Deletes a flavor identified by flavor_id

        Arguments:
           flavor_id (string):  UUID of flavor to be deleted

        Returns: None
        """
        assert flavor_id == self._flavor_get(flavor_id)['id']
        try:
            self._nv_drv.flavors.delete(flavor_id)
        except Exception as e:
            self.log.exception("Delete flavor operation failed for flavor: %s. Exception: %s",
                               flavor_id, str(e))
            raise


    def server_list(self):
        """
        Returns a list of available VMs for the project

        Arguments: None

        Returns:
           A list of dictionaries. Each dictionary contains attributes associated
           with individual VM
        """
        servers     = []
        server_info = []
        try:
            servers     = self._nv_drv.servers.list()
        except Exception as e:
            self.log.exception("List Server operation failed. Exception: %s", str(e))
            raise
        server_info = [ server.to_dict() for server in servers]
        return server_info

    def _nova_server_get(self, server_id):
        """
        Returns a dictionary of attributes associated with VM identified by service_id

        Arguments:
          server_id (string): UUID of the VM/server for which information is requested

        Returns:
          A dictionary object with attributes associated with VM identified by server_id
        """
        try:
            server = self._nv_drv.servers.get(server = server_id)
        except Exception as e:
            self.log.exception("Get Server operation failed for server_id: %s. Exception: %s",
                               server_id, str(e))
            raise
        else:
            return server.to_dict()

    def server_get(self, server_id):
        """
        Returns a dictionary of attributes associated with VM identified by service_id

        Arguments:
          server_id (string): UUID of the VM/server for which information is requested

        Returns:
          A dictionary object with attributes associated with VM identified by server_id
        """
        return self._nova_server_get(server_id)

    def server_create(self, **kwargs):
        """
        Creates a new VM/server instance

        Arguments:
          A dictionary of following key-value pairs
         {
           server_name(string)        : Name of the VM/Server
           flavor_id  (string)        : UUID of the flavor to be used for VM
           image_id   (string)        : UUID of the image to be used VM/Server instance,
                                             This could be None if volumes (with images) are being used
           network_list(List)         : A List of network_ids. A port will be created in these networks
           port_list (List)           : A List of port-ids. These ports will be added to VM.
           metadata   (dict)          : A dictionary of arbitrary key-value pairs associated with VM/server
           userdata   (string)        : A script which shall be executed during first boot of the VM
           availability_zone (string) : A name of the availability zone where instance should be launched
           scheduler_hints (string)   : Openstack scheduler_hints to be passed to nova scheduler
         }
        Returns:
          server_id (string): UUID of the VM/server created

        """
        nics = []
        if 'network_list' in kwargs:
            for network_id in kwargs['network_list']:
                nics.append({'net-id': network_id})

        if 'port_list' in kwargs:
            for port_id in kwargs['port_list']:
                port = { 'port-id': port_id['id'] }
                nics.append(port)

        try:
            server = self._nv_drv.servers.create(
                kwargs['name'],
                kwargs['image_id'],
                kwargs['flavor_id'],
                meta                 = kwargs['metadata'] if 'metadata' in kwargs else None,
                files                = kwargs['files'] if 'files' in kwargs else None,
                reservation_id       = None,
                min_count            = None,
                max_count            = None,
                userdata             = kwargs['userdata'] if 'userdata' in kwargs else None,
                security_groups      = kwargs['security_groups'] if 'security_groups' in kwargs else None,
                availability_zone    = kwargs['availability_zone'].name if 'availability_zone' in kwargs else None,
                block_device_mapping_v2 = kwargs['block_device_mapping_v2'] if 'block_device_mapping_v2' in kwargs else None,
                nics                 = nics,
                scheduler_hints      = kwargs['scheduler_hints'] if 'scheduler_hints' in kwargs else None,
                config_drive         = kwargs['config_drive'] if 'config_drive' in kwargs else None
            )
            
        except Exception as e:
            self.log.exception("Create Server operation failed. Exception: %s", str(e))
            raise
        return server.to_dict()['id']

    def server_delete(self, server_id):
        """
        Deletes a server identified by server_id

        Arguments:
           server_id (string): UUID of the server to be deleted

        Returns: None
        """
        try:
            self._nv_drv.servers.delete(server_id)
        except Exception as e:
            self.log.exception("Delete server operation failed for server_id: %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_start(self, server_id):
        """
        Starts a server identified by server_id

        Arguments:
           server_id (string): UUID of the server to be started

        Returns: None
        """
        try:
            self._nv_drv.servers.start(server_id)
        except Exception as e:
            self.log.exception("Start Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_stop(self, server_id):
        """
        Arguments:
           server_id (string): UUID of the server to be stopped

        Returns: None
        """
        try:
            self._nv_drv.servers.stop(server_id)
        except Exception as e:
            self.log.exception("Stop Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_pause(self, server_id):
        """
        Arguments:
           server_id (string): UUID of the server to be paused

        Returns: None
        """
        try:
            self._nv_drv.servers.pause(server_id)
        except Exception as e:
            self.log.exception("Pause Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_unpause(self, server_id):
        """
        Arguments:
           server_id (string): UUID of the server to be unpaused

        Returns: None
        """
        try:
            self._nv_drv.servers.unpause(server_id)
        except Exception as e:
            self.log.exception("Resume Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))
            raise


    def server_suspend(self, server_id):
        """
        Arguments:
           server_id (string): UUID of the server to be suspended

        Returns: None
        """
        try:
            self._nv_drv.servers.suspend(server_id)
        except Exception as e:
            self.log.exception("Suspend Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))


    def server_resume(self, server_id):
        """
        Arguments:
           server_id (string): UUID of the server to be resumed

        Returns: None
        """
        try:
            self._nv_drv.servers.resume(server_id)
        except Exception as e:
            self.log.exception("Resume Server operation failed for server_id : %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_reboot(self, server_id, reboot_type):
        """
        Arguments:
           server_id (string) : UUID of the server to be rebooted
           reboot_type(string):
                         'SOFT': Soft Reboot
                         'HARD': Hard Reboot
        Returns: None
        """
        try:
            self._nv_drv.servers.reboot(server_id, reboot_type)
        except Exception as e:
            self.log.exception("Reboot Server operation failed for server_id: %s. Exception: %s",
                               server_id, str(e))
            raise

    def server_console(self, server_id, console_type = 'novnc'):
        """
        Arguments:
           server_id (string) : UUID of the server to be rebooted
           console_type(string):
                               'novnc',
                               'xvpvnc'
        Returns:
          A dictionary object response for console information
        """
        try:
            console_info = self._nv_drv.servers.get_vnc_console(server_id, console_type)
        except Exception as e:
            # TODO: This error keeps repeating incase there is no console available
            # So reduced level from exception to warning
            self.log.warning("Server Get-Console operation failed for server_id: %s. Exception: %s",
                             server_id, str(e))
            raise e
        return console_info

    def server_rebuild(self, server_id, image_id):
        """
        Arguments:
           server_id (string) : UUID of the server to be rebooted
           image_id (string)  : UUID of the image to use
        Returns: None
        """

        try:
            self._nv_drv.servers.rebuild(server_id, image_id)
        except Exception as e:
            self.log.exception("Rebuild Server operation failed for server_id: %s. Exception: %s",
                               server_id, str(e))
            raise


    def server_add_port(self, server_id, port_id):
        """
        Arguments:
           server_id (string): UUID of the server
           port_id   (string): UUID of the port to be attached

        Returns: None
        """
        try:
            self._nv_drv.servers.interface_attach(server_id,
                                            port_id,
                                            net_id = None,
                                            fixed_ip = None)
        except Exception as e:
            self.log.exception("Server Port Add operation failed for server_id : %s, port_id : %s. Exception: %s",
                               server_id, port_id, str(e))
            raise

    def server_delete_port(self, server_id, port_id):
        """
        Arguments:
           server_id (string): UUID of the server
           port_id   (string): UUID of the port to be deleted
        Returns: None

        """
        try:
            self._nv_drv.servers.interface_detach(server_id, port_id)
        except Exception as e:
            self.log.exception("Server Port Delete operation failed for server_id : %s, port_id : %s. Exception: %s",
                               server_id, port_id, str(e))
            raise

    def floating_ip_list(self):
        """
        Arguments:
            None
        Returns:
            List of objects of floating IP nova class (novaclient.v2.floating_ips.FloatingIP)
        """
        try:
            ip_list = self._nv_drv.floating_ips.list()
        except Exception as e:
            self.log.exception("Floating IP List operation failed. Exception: %s", str(e))
            raise

        return ip_list

    def floating_ip_create(self, pool):
        """
        Arguments:
           pool (string): Name of the pool (optional)
        Returns:
           An object of floating IP nova class (novaclient.v2.floating_ips.FloatingIP)
        """
        try:
            floating_ip = self._nv_drv.floating_ips.create(pool)
        except Exception as e:
            self.log.exception("Floating IP Create operation failed. Exception: %s", str(e))
            raise

        return floating_ip

    def floating_ip_delete(self, floating_ip):
        """
        Arguments:
           floating_ip: An object of floating IP nova class (novaclient.v2.floating_ips.FloatingIP)
        Returns:
           None
        """
        try:
            floating_ip = self._nv_drv.floating_ips.delete(floating_ip)
        except Exception as e:
            self.log.exception("Floating IP Delete operation failed. Exception: %s", str(e))
            raise

    def floating_ip_assign(self, server_id, floating_ip, fixed_ip):
        """
        Arguments:
           server_id (string)  : UUID of the server
           floating_ip (string): IP address string for floating-ip
           fixed_ip (string)   : IP address string for the fixed-ip with which floating ip will be associated
        Returns:
           None
        """
        try:
            self._nv_drv.servers.add_floating_ip(server_id, floating_ip, fixed_ip)
        except Exception as e:
            self.log.exception("Assign Floating IP operation failed. Exception: %s", str(e))
            raise

    def floating_ip_release(self, server_id, floating_ip):
        """
        Arguments:
           server_id (string)  : UUID of the server
           floating_ip (string): IP address string for floating-ip
        Returns:
           None
        """
        try:
            self._nv_drv.servers.remove_floating_ip(server_id, floating_ip)
        except Exception as e:
            self.log.exception("Release Floating IP operation failed. Exception: %s", str(e))
            raise

    def volume_list(self, server_id):
        """
          List of volumes attached to the server
  
          Arguments:
              None
          Returns:
             List of dictionary objects where dictionary is representation of class (novaclient.v2.volumes.Volume)
        """
        try:
            volumes = self._nv_drv.volumes.get_server_volumes(server_id=server_id)
        except Exception as e:
            self.log.exception("Get volume information failed. Exception: %s", str(e))
            raise

        volume_info = [v.to_dict() for v in volumes]
        return volume_info


    def group_list(self):
        """
        List of Server Affinity and Anti-Affinity Groups

        Arguments:
            None
        Returns:
           List of dictionary objects where dictionary is representation of class (novaclient.v2.server_groups.ServerGroup)
        """
        try:
            group_list = self._nv_drv.server_groups.list()
        except Exception as e:
            self.log.exception("Server Group List operation failed. Exception: %s", str(e))
            raise

        group_info = [ group.to_dict() for group in group_list ]
        return group_info

        
    def security_group_list(self):
        """
        List of Security Group
        Arguments:
        None
        Returns:
        List of dictionary objects representating novaclient.v2.security_groups.SecurityGroup class
        """
        try:
            sec_groups = self._nv_drv.security_groups.list()
        except Exception as e:
            self.log.exception("Security Group List operation failed. Exception: %s", str(e))
            raise
        sec_info = [ sec_group.to_dict() for sec_group in sec_groups]
        return sec_info
    
