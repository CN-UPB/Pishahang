#!/usr/bin/python

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

from . import session as sess_drv
from . import keystone as ks_drv
from . import nova as nv_drv
from . import neutron as nt_drv
from . import glance as gl_drv
from . import ceilometer as ce_drv
from . import cinder as ci_drv
from . import utils as drv_utils

# Exceptions
import keystoneclient.exceptions as KeystoneExceptions
import neutronclient.common.exceptions as NeutronException


class ValidationError(Exception):
    pass


class DriverUtilities(object):
    """
    Class with utility method 
    """
    def __init__(self, driver):
        """
        Constructor of DriverUtilities class
        Arguments:
          driver: Object of OpenstackDriver
        """
        self.flavor_utils = drv_utils.FlavorUtils(driver)
        self.network_utils = drv_utils.NetworkUtils(driver)
        self.image_utils = drv_utils.ImageUtils(driver)
        self.compute_utils = drv_utils.ComputeUtils(driver)
        
    @property
    def flavor(self):
        return self.flavor_utils

    @property
    def compute(self):
        return self.compute_utils
    
    @property
    def network(self):
        return self.network_utils
    
    @property
    def image(self):
        return self.image_utils

    
class OpenstackDriver(object):
    """
    Driver for openstack nova, neutron, glance, keystone, swift, cinder services
    """
    def __init__(self, logger = None, **kwargs):
        """
        OpenstackDriver Driver constructor
        Arguments:
           logger: (instance of logging.Logger)
           kwargs:  A dictionary of 
            {
              username (string)                   : Username for project/tenant.
              password (string)                   : Password
              auth_url (string)                   : Keystone Authentication URL.
              project  (string)                   : Openstack project name
              mgmt_network(string, optional)      : Management network name. Each VM created with this cloud-account will
                                                    have a default interface into management network.
              cert_validate (boolean, optional)   : In case of SSL/TLS connection if certificate validation is required or not.
              user_domain                         : Domain name for user
              project_domain                      : Domain name for project
              region                              : Region name
            }
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.driver')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        args =  dict(auth_url            = kwargs['auth_url'],
                     username            = kwargs['username'],
                     password            = kwargs['password'],
                     project_name        = kwargs['project'],
                     project_domain_name = kwargs['project_domain'] if 'project_domain' in kwargs else None,
                     user_domain_name    = kwargs['user_domain'] if 'user_domain' in kwargs else None,)

        cert_validate = kwargs['cert_validate'] if 'cert_validate' in kwargs else False
        region = kwargs['region_name'] if 'region_name' in kwargs else False
        mgmt_network = kwargs['mgmt_network'] if 'mgmt_network' in kwargs else None
        
        discover = ks_drv.KeystoneVersionDiscover(kwargs['auth_url'],
                                                  cert_validate,
                                                  logger = self.log)
        (major, minor) = discover.get_version()

        self.sess_drv = sess_drv.SessionDriver(auth_method = 'password',
                                               version = str(major),
                                               cert_validate = cert_validate,
                                               logger = self.log,
                                               **args)

        self.ks_drv = ks_drv.KeystoneDriver(str(major),
                                            self.sess_drv,
                                            logger = self.log)
        
        self.nova_drv = nv_drv.NovaDriver(self.sess_drv,
                                          region_name = region,
                                          logger = self.log)
        
        self.neutron_drv = nt_drv.NeutronDriver(self.sess_drv,
                                                region_name = region,
                                                logger = self.log)
        
        self.glance_drv = gl_drv.GlanceDriver(self.sess_drv,
                                              region_name = region,
                                              logger = self.log)
       
        try: 
           self.cinder_drv = ci_drv.CinderDriver(self.sess_drv,
                                              region_name = region,
                                              logger = self.log)
        except Exception:
           self.cinder_drv = None
        
        self.ceilo_drv = ce_drv.CeilometerDriver(self.sess_drv,
                                                 region_name = region,
                                                 logger = self.log)
        
        self.utils = DriverUtilities(self)
        
        self._mgmt_network = mgmt_network
        
        self._cache = dict(neutron = dict(),
                           nova = dict(),
                           cinder = dict(),
                           glance = dict())
        self.build_resource_cache()

    @property
    def nova_cache(self):
        return self._cache['nova']

    @property
    def neutron_cache(self):
        return self._cache['neutron']
    
    @property
    def glance_cache(self):
        return self._cache['glance']

    @property
    def cinder_cache(self):
        return self._cache['cinder']
    
    def build_resource_cache(self):
        try:
            self.build_network_resource_cache()
        except KeyError:
            raise
        self.build_nova_resource_cache()
        self.build_cinder_resource_cache()
        self.build_glance_resource_cache()

    def _cache_populate(self, method, datatype, *args, **kwargs):
        try:
            rsp = method(*args, **kwargs)
        except Exception as e:
            self.log.exception("Exception %s occured during execution of %s",
                               str(e), method)
            return datatype
        else:
            return rsp
        
    def _build_nova_security_group_list(self):
        self.log.info("Building Nova security group cache")
        self.nova_cache['security_groups'] = self._cache_populate(self.nova_drv.security_group_list,
                                                                  list())
        return self.nova_cache['security_groups']
    
    def _build_nova_affinity_group_list(self):
        self.log.info("Building Nova affinity/anti-affinity group cache")
        self.nova_cache['affinity_groups'] = self._cache_populate(self.nova_server_group_list,
                                                                  list())              
        return self.nova_cache['affinity_groups']
    
    def _build_neutron_security_group_list(self):
        self.log.info("Discovering neutron security group")
        self.neutron_cache['security_groups'] = self._cache_populate(self.neutron_security_group_list,
                                                                     list())
        return self.neutron_cache['security_groups']

    def _build_neutron_subnet_prefix_list(self):
        self.log.info("Discovering subnet prefix pools")
        self.neutron_cache['subnet_pool'] = self._cache_populate(self.neutron_subnetpool_list,
                                                                 list())
        return self.neutron_cache['subnet_pool']

    def _get_neutron_mgmt_network(self):
        if self._mgmt_network:
            self.log.info("Discovering management network %s", self._mgmt_network)
            network_list = self._cache_populate(self.neutron_drv.network_get,
                                                None,
                                                **{'network_name': self._mgmt_network})
            if network_list:
                self.neutron_cache['mgmt_net'] = network_list['id']
            else:
                msg = "Could not find management network %s" % self._mgmt_network
                self.log.error(msg)
                raise KeyError(msg)

            
    def _build_glance_image_list(self):
        self.log.info("Discovering images")
        self.glance_cache['images'] = self._cache_populate(self.glance_image_list,
                                                           list())

        return self.glance_cache['images']
    
    def _build_cinder_volume_list(self):
        self.log.info("Discovering volumes")
        self.cinder_cache['volumes'] = self._cache_populate(self.cinder_volume_list,
                                                           list())
        return self.cinder_cache['volumes']
                                                                 
    def build_nova_resource_cache(self):
        self.log.info("Building nova resource cache")
        self._build_nova_security_group_list()
        self._build_nova_affinity_group_list()
        
            
    def build_network_resource_cache(self):
        self.log.info("Building network resource cache")
        try:
            self._get_neutron_mgmt_network()
        except KeyError:
            raise
        self._build_neutron_security_group_list()
        self._build_neutron_subnet_prefix_list()

    def build_cinder_resource_cache(self):
        self.log.info("Building cinder resource cache")
        if self.cinder_drv is not None:
            self._build_cinder_volume_list()

    def build_glance_resource_cache(self):
        self.log.info("Building glance resource cache")
        self._build_glance_image_list()

        
    @property
    def _nova_affinity_group(self):
        if 'affinity_groups' in self.nova_cache:
            return self.nova_cache['affinity_groups']
        else:
            return self._build_nova_affinity_group_list()

    @property
    def _nova_security_groups(self):
        if 'security_groups' in self.nova_cache:
            return self.nova_cache['security_groups']
        else:
            return self._build_nova_security_group_list()
        
    @property
    def mgmt_network(self):
        return self._mgmt_network
    
    @property
    def _mgmt_network_id(self):
        if 'mgmt_net' in self.neutron_cache:
            return self.neutron_cache['mgmt_net']
        else:
            return list()

    @property
    def _neutron_security_groups(self):
        if 'security_groups' in self.neutron_cache:
            return self.neutron_cache['security_groups']
        else:
            return self._build_neutron_security_group_list()

    @property
    def _neutron_subnet_prefix_pool(self):
        if 'subnet_pool' in self.neutron_cache:
            return self.neutron_cache['subnet_pool']
        else:
            return self._build_neutron_subnet_prefix_list()
        
    @property
    def _glance_image_list(self):
        if 'images' in self.glance_cache:
            return self.glance_cache['images']
        else:
            return self._build_glance_image_list()
    
    @property
    def _cinder_volume_list(self):
        if 'volumes' in self.cinder_cache:
            return self.cinder_cache['volumes']
        else:
            return self._build_cinder_volume_list()

    def validate_account_creds(self):
        try:
            self.sess_drv.invalidate_auth_token()
            self.sess_drv.auth_token
            self.build_resource_cache()
        except KeystoneExceptions.Unauthorized as e:
            self.log.error("Invalid credentials ")
            raise ValidationError("Invalid Credentials: "+ str(e))
        except KeystoneExceptions.AuthorizationFailure as e:
            self.log.error("Unable to authenticate or validate the existing credentials. Exception: %s", str(e))
            raise ValidationError("Invalid Credentials: "+ str(e))
        except NeutronException.NotFound as e:
            self.log.error("Given management network could not be found for Openstack account ")
            raise ValidationError("Neutron network not found "+ str(e))
        except Exception as e:
            self.log.error("Could not connect to Openstack. Exception: %s", str(e))
            raise ValidationError("Connection Error: "+ str(e))


    def glance_image_create(self, **kwargs):
        if 'disk_format' not in kwargs:
            kwargs['disk_format'] = 'qcow2'
        if 'container_format' not in kwargs:
            kwargs['container_format'] = 'bare'
        if 'min_disk' not in kwargs:
            kwargs['min_disk'] = 0
        if 'min_ram' not in kwargs:
            kwargs['min_ram'] = 0
        return self.glance_drv.image_create(**kwargs)

    def glance_image_upload(self, image_id, fd):
        self.glance_drv.image_upload(image_id, fd)

    def glance_image_add_location(self, image_id, location):
        self.glance_drv.image_add_location(image_id, location)

    def glance_image_update(self, image_id, remove_props = None, **kwargs):
        self.glance_drv.image_update(image_id, remove_props=remove_props, **kwargs)

    def glance_image_delete(self, image_id):
        self.glance_drv.image_delete(image_id)

    def glance_image_list(self):
        return self.glance_drv.image_list()

    def glance_image_get(self, image_id):
        return self.glance_drv.image_get(image_id)

    def nova_flavor_list(self):
        return self.nova_drv.flavor_list()

    def nova_flavor_find(self, **kwargs):
        return self.nova_drv.flavor_find(**kwargs)
    
    def nova_flavor_create(self, name, ram, vcpus, disk, epa_specs = dict()):
        return self.nova_drv.flavor_create(name,
                                           ram         = ram,
                                           vcpu        = vcpus,
                                           disk        = disk,
                                           extra_specs = epa_specs)

    def nova_flavor_delete(self, flavor_id):
        self.nova_drv.flavor_delete(flavor_id)

    def nova_flavor_get(self, flavor_id):
        return self.nova_drv.flavor_get(flavor_id)

    def nova_server_create(self, **kwargs):
        if 'security_groups' not in kwargs:
            security_groups = [s['name'] for s in self._nova_security_groups]
            #Remove the security group names that are duplicate - RIFT-17035
            valid_security_groups = list(filter(lambda s: security_groups.count(s) == 1, security_groups))
            kwargs['security_groups'] = valid_security_groups
        return self.nova_drv.server_create(**kwargs)

    def nova_server_add_port(self, server_id, port_id):
        self.nova_drv.server_add_port(server_id, port_id)

    def nova_server_delete_port(self, server_id, port_id):
        self.nova_drv.server_delete_port(server_id, port_id)

    def nova_server_start(self, server_id):
        self.nova_drv.server_start(server_id)

    def nova_server_stop(self, server_id):
        self.nova_drv.server_stop(server_id)

    def nova_server_delete(self, server_id):
        self.nova_drv.server_delete(server_id)

    def nova_server_reboot(self, server_id):
        self.nova_drv.server_reboot(server_id, reboot_type='HARD')

    def nova_server_rebuild(self, server_id, image_id):
        self.nova_drv.server_rebuild(server_id, image_id)

    def nova_floating_ip_list(self):
        return self.nova_drv.floating_ip_list()

    def nova_floating_ip_create(self, pool = None):
        return self.nova_drv.floating_ip_create(pool)

    def nova_floating_ip_delete(self, floating_ip):
        self.nova_drv.floating_ip_delete(floating_ip)

    def nova_floating_ip_assign(self, server_id, floating_ip, fixed_ip):
        self.nova_drv.floating_ip_assign(server_id, floating_ip, fixed_ip)

    def nova_floating_ip_release(self, server_id, floating_ip):
        self.nova_drv.floating_ip_release(server_id, floating_ip)

    def nova_server_list(self):
        return self.nova_drv.server_list()

    def nova_server_get(self, server_id):
        return self.nova_drv.server_get(server_id)

    def nova_server_console(self, server_id):
        return self.nova_drv.server_console(server_id)

    def nova_server_group_list(self):
        return self.nova_drv.group_list()

    def nova_volume_list(self, server_id):
        return self.nova_drv.volume_list(server_id)

    def neutron_extensions_list(self):
        return self.neutron_drv.extensions_list()

    def neutron_network_list(self):
        return self.neutron_drv.network_list()

    def neutron_network_get(self, network_id):
        return self.neutron_drv.network_get(network_id=network_id)

    def neutron_network_get_by_name(self, network_name):
        return self.neutron_drv.network_get(network_name=network_name)

    def neutron_network_create(self, **kwargs):
        return self.neutron_drv.network_create(**kwargs)

    def neutron_network_delete(self, network_id):
        self.neutron_drv.network_delete(network_id)

    def neutron_subnet_list(self):
        return self.neutron_drv.subnet_list(**{})

    def neutron_subnet_get(self, subnet_id):
        return self.neutron_drv.subnet_get(subnet_id)

    def neutron_subnet_create(self, **kwargs):
        return self.neutron_drv.subnet_create(**kwargs)

    def netruon_subnet_delete(self, subnet_id):
        self.neutron_drv.subnet_delete(subnet_id)

    def neutron_subnetpool_list(self):
        return self.neutron_drv.subnetpool_list()

    def netruon_subnetpool_by_name(self, pool_name):
        pool_list = self.neutron_drv.subnetpool_list(**{'name': pool_name})
        if pool_list:
            return pool_list[0]
        else:
            return None

    def neutron_port_list(self, **kwargs):
        return self.neutron_drv.port_list(**kwargs)

    def neutron_port_get(self, port_id):
        return self.neutron_drv.port_get(port_id)

    def neutron_port_create(self, **kwargs):
        port_id =  self.neutron_drv.port_create([kwargs])[0]
        if 'vm_id' in kwargs:
            self.nova_server_add_port(kwargs['vm_id'], port_id)
        return port_id

    def neutron_multi_port_create(self, ports):
        return self.neutron_drv.port_create(ports)
        
    def neutron_security_group_list(self):
        return self.neutron_drv.security_group_list(**{})

    def neutron_security_group_by_name(self, group_name):
        group_list = self.neutron_drv.security_group_list(**{'name': group_name})
        if group_list:
            return group_list[0]
        else:
            return None

    def neutron_port_delete(self, port_id):
        self.neutron_drv.port_delete(port_id)

    def ceilo_meter_endpoint(self):
        return self.ceilo_drv.endpoint

    def ceilo_meter_list(self):
        return self.ceilo_drv.meters

    def ceilo_nfvi_metrics(self, vim_id):
        """Returns a dict of NFVI metrics for a given VM

        Arguments:
            vim_id - the VIM ID of the VM to retrieve the metrics for

        Returns:
            A dict of NFVI metrics

        """
        return self.ceilo_drv.nfvi_metrics(vim_id)

    def ceilo_alarm_list(self):
        """Returns a list of ceilometer alarms"""
        return self.ceilo_drv.client.alarms.list()

    def ceilo_alarm_create(self,
                           name,
                           meter,
                           statistic,
                           operation,
                           threshold,
                           period,
                           evaluations,
                           severity='low',
                           repeat=True,
                           enabled=True,
                           actions=None,
                           **kwargs):
        """Create a new Alarm

        Arguments:
            name        - the name of the alarm
            meter       - the name of the meter to measure
            statistic   - the type of statistic used to trigger the alarm
                          ('avg', 'min', 'max', 'count', 'sum')
            operation   - the relational operator that, combined with the
                          threshold value, determines  when the alarm is
                          triggered ('lt', 'le', 'eq', 'ge', 'gt')
            threshold   - the value of the statistic that will trigger the
                          alarm
            period      - the duration (seconds) over which to evaluate the
                          specified statistic
            evaluations - the number of samples of the meter statistic to
                          collect when evaluating the threshold
            severity    - a measure of the urgency or importance of the alarm
                          ('low', 'moderate', 'critical')
            repeat      - a flag that indicates whether the alarm should be
                          triggered once (False) or repeatedly while the alarm
                          condition is true (True)
            enabled     - a flag that indicates whether the alarm is enabled
                          (True) or disabled (False)
            actions     - a dict specifying the URLs for webhooks. The dict can
                          have up to 3 keys: 'insufficient_data', 'alarm',
                          'ok'. Each key is associated with a list of URLs to
                          webhooks that will be invoked when one of the 3
                          actions is taken.
            kwargs      - an arbitrary dict of keyword arguments that are
                          passed to the ceilometer client

        """
        ok_actions = actions.get('ok') if actions is not None else None
        alarm_actions = actions.get('alarm') if actions is not None else None
        insufficient_data_actions = actions.get('insufficient_data') if actions is not None else None

        return self.ceilo_drv.client.alarms.create(name=name,
                                                   meter_name=meter,
                                                   statistic=statistic,
                                                   comparison_operator=operation,
                                                   threshold=threshold,
                                                   period=period,
                                                   evaluation_periods=evaluations,
                                                   severity=severity,
                                                   repeat_actions=repeat,
                                                   enabled=enabled,
                                                   ok_actions=ok_actions,
                                                   alarm_actions=alarm_actions,
                                                   insufficient_data_actions=insufficient_data_actions,
                                                   **kwargs)

    def ceilo_alarm_update(self, alarm_id, **kwargs):
        """Updates an existing alarm

        Arguments:
            alarm_id - the identifier of the alarm to update
            kwargs   - a dict of the alarm attributes to update

        """
        return self.ceilo_drv.client.alarms.update(alarm_id, **kwargs)

    def ceilo_alarm_delete(self, alarm_id):
        self.ceilo_drv.client.alarms.delete(alarm_id)

    def cinder_volume_list(self):
        return self.cinder_drv.volume_list()
  
    def cinder_volume_get(self, vol_id):
        return self.cinder_drv.volume_get(vol_id)
  
    def cinder_volume_set_metadata(self, volumeid, metadata):
        return self.cinder_drv.volume_set_metadata(volumeid, metadata)
  
    def cinder_volume_delete_metadata(self, volumeid, metadata):
        return self.cinder_drv.volume_delete_metadata(volumeid, metadata)
          
              
          
