namespace RwCal {

  public class RwcalStatus : GLib.Object {
    public RwTypes.RwStatus status;
    public string error_msg;
    public string traceback;
  }

  public interface Cloud: GLib.Object {
    /*
     * Init routine
     */
    public abstract RwTypes.RwStatus init(RwLog.Ctx log_ctx);

    /*
     * Cloud Account Credentails Validation related API
     */
    public abstract RwTypes.RwStatus validate_cloud_creds(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_Rwcal_ConnectionStatus status);

    /*
     * Image related APIs
     */
    public abstract RwTypes.RwStatus get_image_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources images);

    public abstract RwTypes.RwStatus create_image(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_ImageinfoList image,
      out string image_id);

    public abstract RwTypes.RwStatus delete_image(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string image_id);

    public abstract RwTypes.RwStatus get_image(
        Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
        string image_id,
        out Rwcal.YangData_RwProject_Project_VimResources_ImageinfoList image);

    /*
     * VM Releated APIs
     */
    public abstract RwTypes.RwStatus create_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_VminfoList vm,
      out string vm_id);

    public abstract RwTypes.RwStatus start_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vm_id);

    public abstract RwTypes.RwStatus stop_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vm_id);

    public abstract RwTypes.RwStatus delete_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vm_id);

    public abstract RwTypes.RwStatus reboot_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vm_id);

    public abstract RwTypes.RwStatus get_vm_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources vms);

    public abstract RwTypes.RwStatus get_vm(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vm_id,
      out Rwcal.YangData_RwProject_Project_VimResources_VminfoList vm);

    /*
     * Flavor related APIs
     */
    public abstract RwTypes.RwStatus create_flavor(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_FlavorinfoList flavor_info_item,
      out string flavor_id);

    public abstract RwTypes.RwStatus delete_flavor(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string flavor_id);

    public abstract RwTypes.RwStatus get_flavor_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources flavors);

    public abstract RwTypes.RwStatus get_flavor(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string flavor_id,
      out Rwcal.YangData_RwProject_Project_VimResources_FlavorinfoList flavor);


    /*
     * Tenant related APIs
     */
    public abstract RwTypes.RwStatus create_tenant(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string tenant_name,
      [CCode (array_length = false, array_null_terminated = true)]
      out string [] tenant_info);

    public abstract RwTypes.RwStatus delete_tenant(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string tenant_id);

    public abstract RwTypes.RwStatus get_tenant_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources tenants);

    /*
     * Role related APIs
     */
    public abstract RwTypes.RwStatus create_role(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string role_name,
      [CCode (array_length = false, array_null_terminated = true)]
      out string [] role_info);

    public abstract RwTypes.RwStatus delete_role(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string role_id);

    public abstract RwTypes.RwStatus get_role_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources roles);

    /*
     * Port related APIs
     */
    public abstract RwTypes.RwStatus create_port(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_PortinfoList port,
      out string port_id);

    public abstract RwTypes.RwStatus delete_port(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string port_id);

    public abstract RwTypes.RwStatus get_port(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string port_id,
      out Rwcal.YangData_RwProject_Project_VimResources_PortinfoList port);

    public abstract RwTypes.RwStatus get_port_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources ports);

    /*
     * Host related APIs
     */
    public abstract RwTypes.RwStatus add_host(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_HostinfoList host,
      out string host_id);

    public abstract RwTypes.RwStatus remove_host(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string host_id);

    public abstract RwTypes.RwStatus get_host(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string host_id,
      out Rwcal.YangData_RwProject_Project_VimResources_HostinfoList host);

    public abstract RwTypes.RwStatus get_host_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources hosts);

    /*
     * Network related APIs
     */
    public abstract RwTypes.RwStatus create_network(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VimResources_NetworkinfoList network,
      out string network_id);

    public abstract RwTypes.RwStatus delete_network(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string network_id);

    public abstract RwTypes.RwStatus get_network(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string network_id,
      out Rwcal.YangData_RwProject_Project_VimResources_NetworkinfoList network);

    public abstract RwTypes.RwStatus get_network_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources networks);

    public abstract RwTypes.RwStatus get_management_network(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VimResources_NetworkinfoList network);

    /*
     * Higher Order CAL APIs
     */
    public abstract void create_virtual_link(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VirtualLinkReqParams link_params,
      out RwcalStatus status,
      out string link_id);
    
    public abstract RwTypes.RwStatus delete_virtual_link(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string link_id);

    public abstract RwTypes.RwStatus get_virtual_link(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string link_id,
      out Rwcal.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList response);

    public abstract RwTypes.RwStatus get_virtual_link_by_name(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string link_name,
      out Rwcal.YangData_RwProject_Project_VnfResources_VirtualLinkInfoList response);

    public abstract RwTypes.RwStatus get_virtual_link_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out Rwcal.YangData_RwProject_Project_VnfResources resources);


    public abstract void create_vdu(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VduInitParams vdu_params,
      out RwcalStatus status,
      out string vdu_id);

    public abstract RwTypes.RwStatus modify_vdu(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      Rwcal.YangData_RwProject_Project_VduModifyParams vdu_params);
    
    public abstract RwTypes.RwStatus delete_vdu(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vdu_id);

    public abstract void get_vdu(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      string vdu_id,
      string mgmt_network,
      out RwcalStatus status,
      out Rwcal.YangData_RwProject_Project_VnfResources_VduInfoList response);
    
    public abstract void get_vdu_list(
      Rwcal.YangData_RwProject_Project_CloudAccounts_CloudAccountList account,
      out RwcalStatus status,
      out Rwcal.YangData_RwProject_Project_VnfResources resources);
  }
}


