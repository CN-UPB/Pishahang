
/*
 * 
 *   Copyright 2016 RIFT.IO Inc
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */


/**
 * @file rwvx.h
 * @author Justin Bronder (justin.bronder@riftio.com)
 * @date 09/29/2014
 * @brief Top level API include for rwcal submodule
 */

#ifndef __RWCAL_API_H__
#define __RWCAL_API_H__

#include <stdbool.h>

#include <libpeas/peas.h>

#include <rwcal.h>
#include <rwlib.h>
#include <rw-manifest.pb-c.h>
#include <rw_vx_plugin.h>

#include "rwlog.h"

__BEGIN_DECLS

struct rwcal_module_s {
  rw_vx_framework_t * framework;
  rw_vx_modinst_common_t *mip;

  PeasExtension * cloud;
  RwCalCloud * cloud_cls;
  RwCalCloudIface * cloud_iface;

  rwlog_ctx_t *rwlog_instance;
};
typedef struct rwcal_module_s * rwcal_module_ptr_t;

// Redefine yang autonames
typedef RWPB_E(RwManifest_RwcalCloudType) rwcal_cloud_type;

/*
 * Allocate a rwcal module.  Once allocated, the clients within
 * the module still need to be initialized.  For rwzk, see
 * rwcal_rwzk_{kazoo,zake}_init().  For rwcloud, see
 * rwcal_cloud_init().  It is a fatal error to attempt to use any
 * client before it has been initialized.  However, it is
 * perfectly fine to not initialize a client that will remain
 * unused.  Note that every function contains the client that it
 * will use as part of the name, just after the rwcal_ prefix.
 *
 * @return - rwcal module handle or NULL on failure.
 */
rwcal_module_ptr_t rwcal_module_alloc();

/*
 * Deallocate a rwcal module.
 *
 * @param - pointer to the rwcal module to be deallocated.
 */
void rwcal_module_free(rwcal_module_ptr_t * rwcal);


/*
 * Initialize the rwcal cloud controller.
 *
 * key/secret for various cloud types:
 *  EC2: ACCESS_ID/SECRET_KEY
 *
 * @param rwcal       - module handle.
 * @return        - RW_STATUS_SUCCESS,
 *                  RW_STATUS_NOTFOUND if the type is unknown,
 *                  RW_STATUS_FAILURE otherwise.
 */
rw_status_t rwcal_cloud_init(rwcal_module_ptr_t rwcal);

/*
 * Get a list of the names of the available images that can be
 * used to start a new VM.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param image_names - on success, contains a NULL-terminated
 *                      list of image names.
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_image_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **images);

/*
 * Delete Image.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param image_id    - id of image to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_image(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * image_id);

/*
 * Create a flavor.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param flavor      - rwpb_gi_Rwcal_FlavorInfoItem object describing the
 *                      flavor to be created
 * @param flavor_id   - on success, contains a NULL-terminated string containing the new flavor_id
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_flavor(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_FlavorinfoList *flavor,
    char *flavor_id);


/*
 * Delete flavor.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param flavor_id   - id of flavor to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_flavor(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * flavor_id);

/*
 * Get a specific flavor
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param flavor_id   - id of the flavor to return
 * @param flavir      - rwpb_gi_Rwcal_FlavorInfoItem object containing the
 *                      details of the requested flavor
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_flavor(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * flavor_id,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_FlavorinfoList **flavor);

/*
 * Get a list of the details for all flavors
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param flavors     - on success, contains a list of flavor info objects
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_flavor_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **flavors);

/*
 * Create a virtual machine.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vm          - the information that defines what kind of VM will be
 *                      created
 * @param vm_id       - on success, contains a NULL-terminated string
 *                      containing the new vm id
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_vm(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_VminfoList *vm,
    char **vm_id);

/*
 * Delete VM.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vm_id       - id of vm to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_vm(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * vm_id);

/*
 * Reboot VM.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vm_id       - id of vm to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_reboot_vm(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * vm_id);

/*
 * Start VM.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vm_id       - id of a vm to start
 * @return            - rw_status_t
 */
rw_status_t rwcal_start_vm(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * vm_id);

/*
 * Stop VM.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vm_id       - id of a vm to stop
 * @return            - rw_status_t
 */
rw_status_t rwcal_stop_vm(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * vm_id);

/*
 * Get a list of the names of the available vms
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param vms         - on success, contains a NULL-terminated
 *                      list of vms.
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_vm_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources** vms);

/*
 * Create a tenant.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param tenant_name - name to assign to the tenant.
 * @param tenant_info - on success, contains a NULL-terminated list of tenant_info
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_tenant(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * tenant_name,
    char *** tenant_info);

/*
 * Delete tenant.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param tenant_id   - id of tenant to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_tenant(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * tenant_id);

/*
 * Get a list of the available tenants
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param tenants     - on success, contains a NULL-terminated
 *                      list of tenants.
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_tenant_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **tenants);

/*
 * Create a role.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param role_name   - name to assign to the role.
 * @param role_info   - on success, contains a NULL-terminated list of role_info
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_role(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * role_name,
    char *** role_info);

/*
 * Delete role.
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param role_id     - id of role to be deleted
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_role(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char * role_id);

/*
 * Get a list of the available roles
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param roles       - on success, contains a NULL-terminated
 *                      list of roles.
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_role_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **roles);

/*
 * Add a new host
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param host        - host info
 * @param host_id     - on success, contains a NULL-terminated string
 *                      containing the new host_id
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_add_host(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_HostinfoList *host,
    char **host_id);

/*
 * Remove a new host
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param host_id     - the id of the host to remove
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_remove_host(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *host_id);

/*
 * Get a specific host
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param host_id     - the id of the host to return
 * @param host        - the requested host info
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_host(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *host_id,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_HostinfoList **host);

/*
 * Get a list of hosts
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param hosts       - on success, contains a NULL-terminated list of hosts.
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_host_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **hosts);

/*
 * Create a new port
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param port        - port info
 * @param port_id     - on success, contains a NULL-terminated string
 *                      containing the new port id
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_port(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_PortinfoList *port,
    char **port_id);

/*
 * Delete a port
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param port_id     - the id of the port to remove
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_port(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *port_id);

/*
 * Get a specific port
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param port_id     - the id of the port to return
 * @param port        - the requested port info
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_port(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *port_id,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_PortinfoList **port);

/*
 * Get a list of ports
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param ports       - on success, contains a NULL-terminated list of ports.
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_port_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **ports);

/*
 * Create a new network
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param network     - network info
 * @param network_id  - on success, contains a NULL-terminated string
 *                      containing the new network id
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_create_network(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_NetworkinfoList *network,
    char **network_id);

/*
 * Delete a network
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param network_id  - the id of the network to remove
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_delete_network(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *network_id);

/*
 * Get a specific network
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param network_id  - the id of the network to return
 * @param network     - the requested network info
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_network(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    const char *network_id,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_NetworkinfoList **network);

/*
 * Get a the management network
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param network     - the management network info
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_management_network(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources_NetworkinfoList **network);

/*
 * Get a list of networks
 *
 * @param rwcal       - module handle.
 * @param account     - cloud account information.
 * @param networks    - on success, contains a NULL-terminated list of networks.
 *
 * @return            - rw_status_t
 */
rw_status_t rwcal_get_network_list(
    rwcal_module_ptr_t rwcal,
    rwpb_gi_Rwcal_YangData_RwProject_Project_CloudAccounts_CloudAccountList *account,
    rwpb_gi_Rwcal_YangData_RwProject_Project_VimResources **networks);

/*
 * Get a RwLog Context so that log messages can go to rwlog
 *
 * @param rwcal       - module handle.
 *
 * @return            - rwlog_ctx_t
 */
rwlog_ctx_t *rwcal_get_rwlog_ctx(rwcal_module_ptr_t rwcal);

__END_DECLS

#endif


