namespace RwSdn {

  public interface Topology: GLib.Object {
    /*
     * Init routine
     */
    public abstract RwTypes.RwStatus init(RwLog.Ctx log_ctx);

    /*
     * Credential Validation related APIs
     */
    public abstract RwTypes.RwStatus validate_sdn_creds(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      out Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList_ConnectionStatus status);

    /*
     * Configuring  related APIs
     */
    /* TODO */

    /*
     * Network related APIs
     */
    public abstract RwTypes.RwStatus get_network_list(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      out RwTopology.YangData_IetfNetwork network_topology);
   
    /*
     * VNFFG Chain related APIs
     */
    public abstract RwTypes.RwStatus create_vnffg_chain(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      Rwsdnal.YangData_RwProject_Project_Vnffgs_VnffgChain vnffg_chain,
      out string vnffg_id);

    /*
     * VNFFG Chain Terminate related APIs
     */
    public abstract RwTypes.RwStatus terminate_vnffg_chain(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      string vnffg_id);


    /*
     * Network related APIs
     */
    public abstract RwTypes.RwStatus get_vnffg_rendered_paths(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      out Rwsdnal.YangData_RwProject_Project_VnffgRenderedPaths rendered_paths);

    /*
     * Classifier related APIs
     */
    public abstract RwTypes.RwStatus create_vnffg_classifier(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      Rwsdnal.YangData_RwProject_Project_VnffgClassifiers vnffg_classifier, 
      [CCode (array_length = false, array_null_terminated = true)]
      out string [] vnffg_classifier_id);

    /*
     * Classifier related APIs
     */
    public abstract RwTypes.RwStatus terminate_vnffg_classifier(
      Rwsdnal.YangData_RwProject_Project_SdnAccounts_SdnAccountList account,
      [CCode (array_length = false, array_null_terminated = true)]
      string [] vnffg_classifier_id);



    /*
     * Node Related APIs
     */
     /* TODO */

    /*
     * Termination-point Related APIs
     */
     /* TODO */

    /*
     * Link Related APIs
     */
     /* TODO */
    
  }
}


