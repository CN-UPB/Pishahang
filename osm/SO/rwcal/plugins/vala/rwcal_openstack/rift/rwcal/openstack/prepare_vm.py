#!/usr/bin/env python3

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

import rift.rwcal.openstack as openstack_drv
import logging
import argparse
import sys, os, time
import rwlogger
import yaml
import random
import fcntl


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
rwlog_handler = rwlogger.RwLogger(category="rw-cal-log",
                                  subcategory="openstack",)
logger.addHandler(rwlog_handler)
#logger.setLevel(logging.DEBUG)

class FileLock:
    FILE_LOCK = '/tmp/_openstack_prepare_vm.lock'
    def __init__(self):
        # This will create it if it does not exist already
        self.filename = FileLock.FILE_LOCK
        self.handle = None
        
    # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock
    def acquire(self):
        logger.info("<PID: %d> Attempting to acquire log." %os.getpid())
        self.handle = open(self.filename, 'w')
        fcntl.flock(self.handle, fcntl.LOCK_EX)
        logger.info("<PID: %d> Lock successfully acquired." %os.getpid())
        
    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()
        logger.info("<PID: %d> Released lock." %os.getpid())
        
    def __del__(self):
        if self.handle and self.handle.closed == False:
            self.handle.close()
                                                                                        
    
def allocate_floating_ip(drv, argument):
    #### Allocate a floating_ip
    try:
        available_ip = [ ip for ip in drv.nova_floating_ip_list() if ip.instance_id == None ]

        if argument.pool_name:
            ### Filter further based on IP address
            available_ip = [ ip for ip in available_ip if ip.pool == argument.pool_name ]
            
        if not available_ip:
            logger.info("<PID: %d> No free floating_ips available. Allocating fresh from pool: %s" %(os.getpid(), argument.pool_name))
            pool_name = argument.pool_name if argument.pool_name is not None else None
            floating_ip = drv.nova_floating_ip_create(pool_name)
        else:
            floating_ip = random.choice(available_ip)
            logger.info("<PID: %d> Selected floating_ip: %s from available free pool" %(os.getpid(), floating_ip))

        return floating_ip
    
    except Exception as e:
        logger.error("Floating IP Allocation Failed - %s", e)
        return None    


def handle_floating_ip_assignment(drv, server, argument, management_ip):
    lock = FileLock()
    ### Try 3 time (<<<magic number>>>)
    RETRY = 3
    for attempt in range(RETRY):
        try:
            lock.acquire()
            floating_ip = allocate_floating_ip(drv, argument)
            logger.info("Assigning the floating_ip: %s to VM: %s" %(floating_ip, server['name']))
            drv.nova_floating_ip_assign(argument.server_id,
                                        floating_ip,
                                        management_ip)
            logger.info("Assigned floating_ip: %s to management_ip: %s" %(floating_ip, management_ip))
        except Exception as e:
            logger.error("Could not assign floating_ip: %s to VM: %s. Exception: %s" %(floating_ip, server['name'], str(e)))
            lock.release()
            if attempt == (RETRY -1):
                logger.error("Max attempts %d reached for floating_ip allocation. Giving up" %attempt)
                raise
            else:
                logger.error("Retrying floating ip allocation. Current retry count: %d" %attempt)
        else:
            lock.release()
            return
    
        
def assign_floating_ip_address(drv, argument):
    if not argument.floating_ip:
        return

    server = drv.nova_server_get(argument.server_id)

    for i in range(120):
        server = drv.nova_server_get(argument.server_id)
        for network_name,network_info in server['addresses'].items():
            if network_info and  network_name == argument.mgmt_network:
                for n_info in network_info:
                    if 'OS-EXT-IPS:type' in n_info and n_info['OS-EXT-IPS:type'] == 'fixed':
                        management_ip = n_info['addr']
                        try:
                            handle_floating_ip_assignment(drv, server, argument, management_ip)
                            return
                        except Exception as e:
                            logger.error("Exception in assign_floating_ip_address : %s", e)
                            raise
        else:
            logger.info("Waiting for management_ip to be assigned to server: %s" %(server['name']))
            time.sleep(1)
    else:
        logger.info("No management_ip IP available to associate floating_ip for server: %s" %(server['name']))
    return


def create_port_metadata(drv, argument):
    if argument.port_metadata == False:
        return

    ### Get Management Network ID
    network_list = drv.neutron_network_list()
    mgmt_network_id = [net['id'] for net in network_list if net['name'] == argument.mgmt_network][0]
    port_list = [ port for port in drv.neutron_port_list(**{'device_id': argument.server_id})
                  if port['network_id'] != mgmt_network_id ]
    meta_data = {}

    meta_data['rift-meta-ports'] = str(len(port_list))
    port_id = 0
    for port in port_list:
        info = []
        info.append('"port_name":"'+port['name']+'"')
        if 'mac_address' in port:
            info.append('"hw_addr":"'+port['mac_address']+'"')
        if 'network_id' in port:
            #info.append('"network_id":"'+port['network_id']+'"')
            net_name = [net['name'] for net in network_list if net['id'] == port['network_id']]
            if net_name:
                info.append('"network_name":"'+net_name[0]+'"')
        if 'fixed_ips' in port:
            ip_address = port['fixed_ips'][0]['ip_address']
            info.append('"ip":"'+ip_address+'"')
            
        meta_data['rift-meta-port-'+str(port_id)] = '{' + ','.join(info) + '}'
        port_id += 1
        
    nvconn = drv.nova_drv._get_nova_connection()
    nvconn.servers.set_meta(argument.server_id, meta_data)

def get_volume_id(server_vol_list, name):
    if server_vol_list is None:
        return

    for os_volume in server_vol_list:
        try:
            " Device name is of format /dev/vda"
            vol_name = (os_volume['device']).split('/')[2]
        except:                   
            continue
        if name == vol_name:
           return os_volume['volumeId']
    
def create_volume_metadata(drv, argument):
    if argument.vol_metadata is None:
        return

    yaml_vol_str = argument.vol_metadata.read()
    yaml_vol_cfg = yaml.load(yaml_vol_str)

    srv_volume_list = drv.nova_volume_list(argument.server_id)
    for volume in yaml_vol_cfg:
        if 'custom_meta_data' not in volume:
            continue
        vmd = dict()
        for vol_md_item in volume['custom_meta_data']:
            if 'value' not in vol_md_item:
               continue
            vmd[vol_md_item['name']] = vol_md_item['value']

        # Get volume id
        vol_id = get_volume_id(srv_volume_list, volume['name'])
        if vol_id is None:
            logger.error("Server %s Could not find volume %s" %(argument.server_id, volume['name']))
            sys.exit(3)
        drv.cinder_volume_set_metadata(vol_id, vmd)

        
def prepare_vm_after_boot(drv,argument):
    ### Important to call create_port_metadata before assign_floating_ip_address
    ### since assign_floating_ip_address can wait thus delaying port_metadata creation

    ### Wait for a max of 5 minute for server to come up -- Needs fine tuning
    wait_time = 500
    sleep_time = 2
    for i in range(int(wait_time/sleep_time)):
        server = drv.nova_server_get(argument.server_id)
        if server['status'] == 'ACTIVE':
            logger.info("Server %s to reached active state" %(server['name']))
            break
        elif server['status'] == 'BUILD':
            logger.info("Waiting for server: %s to build. Current state: %s" %(server['name'], server['status']))
            time.sleep(sleep_time)
        else:
            logger.info("Server %s reached state: %s" %(server['name'], server['status']))
            sys.exit(3)
    else:
        logger.error("Server %s did not reach active state in %d seconds. Current state: %s" %(server['name'], wait_time, server['status']))
        sys.exit(4)
    #create_port_metadata(drv, argument)
    create_volume_metadata(drv, argument)
    try:
        assign_floating_ip_address(drv, argument)
    except Exception as e:
        logger.error("Exception in prepare_vm_after_boot : %s", e)
        raise
    

def main():
    """
    Main routine
    """
    parser = argparse.ArgumentParser(description='Script to create openstack resources')
    parser.add_argument('--auth_url',
                        action = "store",
                        dest = "auth_url",
                        type = str,
                        help='Keystone Auth URL')

    parser.add_argument('--username',
                        action = "store",
                        dest = "username",
                        type = str,
                        help = "Username for openstack installation")

    parser.add_argument('--password',
                        action = "store",
                        dest = "password",
                        type = str,
                        help = "Password for openstack installation")

    parser.add_argument('--tenant_name',
                        action = "store",
                        dest = "tenant_name",
                        type = str,
                        help = "Tenant name openstack installation")

    parser.add_argument('--user_domain',
                        action = "store",
                        dest = "user_domain",
                        default = None,
                        type = str,
                        help = "User domain name for openstack installation")

    parser.add_argument('--project_domain',
                        action = "store",
                        dest = "project_domain",
                        default = None,
                        type = str,
                        help = "Project domain name for openstack installation")

    parser.add_argument('--region',
                        action = "store",
                        dest = "region",
                        default = "RegionOne",
                        type = str,
                        help = "Region name for openstack installation")
    
    parser.add_argument('--mgmt_network',
                        action = "store",
                        dest = "mgmt_network",
                        type = str,
                        help = "mgmt_network")
    
    parser.add_argument('--server_id',
                        action = "store",
                        dest = "server_id",
                        type = str,
                        help = "Server ID on which boot operations needs to be performed")
    
    parser.add_argument('--floating_ip',
                        action = "store_true",
                        dest = "floating_ip",
                        default = False,
                        help = "Floating IP assignment required")

    parser.add_argument('--pool_name',
                        action = "store",
                        dest = "pool_name",
                        type = str,
                        help = "Floating IP pool name")


    parser.add_argument('--port_metadata',
                        action = "store_true",
                        dest = "port_metadata",
                        default = False,
                        help = "Create Port Metadata")

    parser.add_argument("--vol_metadata", type=argparse.FileType('r'))

    argument = parser.parse_args()

    if not argument.auth_url:
        logger.error("ERROR: AuthURL is not configured")
        sys.exit(1)
    else:
        logger.info("Using AuthURL: %s" %(argument.auth_url))

    if not argument.username:
        logger.error("ERROR: Username is not configured")
        sys.exit(1)
    else:
        logger.info("Using Username: %s" %(argument.username))

    if not argument.password:
        logger.error("ERROR: Password is not configured")
        sys.exit(1)
    else:
        logger.info("Using Password: %s" %(argument.password))

    if not argument.tenant_name:
        logger.error("ERROR: Tenant Name is not configured")
        sys.exit(1)
    else:
        logger.info("Using Tenant Name: %s" %(argument.tenant_name))

    if not argument.mgmt_network:
        logger.error("ERROR: Management Network Name is not configured")
        sys.exit(1)
    else:
        logger.info("Using Management Network: %s" %(argument.mgmt_network))
        
    if not argument.server_id:
        logger.error("ERROR: Server ID is not configured")
        sys.exit(1)
    else:
        logger.info("Using Server ID : %s" %(argument.server_id))
        
    try:
        pid = os.fork()
        if pid > 0:
            # exit for parent
            sys.exit(0)
    except OSError as e:
        logger.error("fork failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(2)

    kwargs = dict(username = argument.username,
                  password = argument.password,
                  auth_url = argument.auth_url,
                  project =  argument.tenant_name,
                  mgmt_network = argument.mgmt_network,
                  cert_validate = False,
                  user_domain = argument.user_domain,
                  project_domain = argument.project_domain,
                  region = argument.region)

    drv = openstack_drv.OpenstackDriver(logger = logger, **kwargs)
    try:
        prepare_vm_after_boot(drv, argument)
    except Exception as e:
        logger.error("Exception in main of prepare_vm : %s", e)
        raise
    
if __name__ == "__main__":
    try:
        main()
        # Do not print anything in this script. This is a subprocess spawned by rwmain
        # and the following print determines the success or failure of this script.
        print("True",end="")
    except Exception as e:
        logger.error("Exception in prepare_vm : %s", e)
        # Do not print anything in this script. This is a subprocess spawned by rwmain
        # and the following print determines the success or failure of this script.
        print("False+" + str(e),end="")
        sys.exit(2)
        

