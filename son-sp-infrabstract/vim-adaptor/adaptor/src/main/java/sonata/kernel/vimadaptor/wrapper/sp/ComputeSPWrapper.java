/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, THALES, NCSR Demokritos ALL RIGHTS RESERVED.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 * 
 * Neither the name of the SONATA-NFV, UCL, NOKIA, NCSR Demokritos nor the names of its contributors
 * may be used to endorse or promote products derived from this software without specific prior
 * written permission.
 * 
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 */

package sonata.kernel.vimadaptor.wrapper.sp;

import sonata.kernel.vimadaptor.commons.*;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.VimRepo;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.WrapperStatusUpdate;
import sonata.kernel.vimadaptor.wrapper.sp.client.SonataGkClient;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkRequestStatus;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkServiceListEntry;

import java.io.IOException;

import javax.ws.rs.NotAuthorizedException;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import org.apache.http.client.ClientProtocolException;
import org.slf4j.LoggerFactory;


public class ComputeSPWrapper extends ComputeWrapper {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(ComputeSPWrapper.class);

  public ComputeSPWrapper(WrapperConfiguration config) {
    super(config);
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#deployFunction(sonata.kernel.vimadaptor.commons
   * .FunctionDeployPayload, java.lang.String)
   */
  @Override
  public void deployFunction(FunctionDeployPayload data, String sid) {
    Long start = System.currentTimeMillis();

    ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
    mapper.disable(SerializationFeature.WRITE_EMPTY_JSON_ARRAYS);
    mapper.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);
    mapper.disable(SerializationFeature.WRITE_NULL_MAP_VALUES);
    mapper.setSerializationInclusion(Include.NON_NULL);

    // - Fetch available NS from the lower level SP
    Logger.info("[SpWrapper] Creating SONATA Rest Client");
    SonataGkClient gkClient = new SonataGkClient(this.getConfig().getVimEndpoint(),
        this.getConfig().getAuthUserName(), this.getConfig().getAuthPass());

    Logger.info("[SpWrapper] Authenticating SONATA Rest Client");
    if (!gkClient.authenticate()) throw new NotAuthorizedException("Client cannot login to the SP");

    GkServiceListEntry[] availableNsds;
    try {
      availableNsds = gkClient.getServices();
    } catch (IOException e1) {
      Logger.error("unable to contact the GK to check the list available services");
      Logger.error(e1.getMessage(), e1);
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Functiono deployment process failed. Can't get available services.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }

    String serviceUuid = null;
    VnfDescriptor vnfd = data.getVnfd();
    Logger.debug("VNF: " + vnfd.getVendor() + "::" + vnfd.getName() + "::" + vnfd.getVersion());
    for (GkServiceListEntry serviceEntry : availableNsds) {
      ServiceDescriptor nsd = serviceEntry.getNsd();
      Logger.debug("Checking NSD:");
      Logger.debug(nsd.getVendor() + "::" + nsd.getName() + "::" + nsd.getVersion());
      boolean matchingVendor = nsd.getVendor().equals(vnfd.getVendor());
      boolean matchingName = nsd.getName().equals(vnfd.getName());
      boolean matchingVersion = nsd.getVersion().equals(vnfd.getVersion());
      Logger.debug("Matches: " + matchingVendor + "::" + matchingName + "::" + matchingVersion);
      boolean matchingCondition = matchingVendor && matchingName && matchingVersion;
      if (matchingCondition) {
        serviceUuid = serviceEntry.getUuid();
        break;
      }
    }
    if (serviceUuid == null) {
      Logger.error("Error! Cannot find correct NSD matching the VNF identifier trio.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Error! Cannot find correct NSD matching the VNF identifier trio.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }
    // - sending a REST call to the underlying SP Gatekeeper for service deployment
    String requestUuid = null;
    Logger.debug("Sending NSD instantiation request to GK...");
    try {
      requestUuid = gkClient.instantiateService(serviceUuid);
    } catch (Exception e) {
      Logger.error(e.getMessage(), e);
      WrapperStatusUpdate update =
          new WrapperStatusUpdate(sid, "ERROR", "Exception during VNF Deployment");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }

    // - than poll the GK until the status is "READY" or "ERROR"

    int counter = 0;
    int wait = 1000;
    int maxCounter = 50;
    int maxWait = 15000;
    String status = null;
    while ((status == null || !status.equals("READY") || !status.equals("ERROR"))
        && counter < maxCounter) {
      try {
        status = gkClient.getRequestStatus(requestUuid);
      } catch (IOException e1) {
        Logger.error(e1.getMessage(), e1);
        Logger.error(
            "Error while retrieving the Service instantiation request status. Trying again in "
                + (wait / 1000) + " seconds");
      }
      Logger.info("Status of request " + requestUuid + ": " + status);
      if (status != null && (status.equals("READY") || status.equals("ERROR"))) {
        break;
      }
      try {
        Thread.sleep(wait);
      } catch (InterruptedException e) {
        Logger.error(e.getMessage(), e);
      }
      counter++;
      wait = Math.min(wait * 2, maxWait);

    }

    if (status == null) {
      Logger.error("Unable to contact the GK to check the service instantiation status");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Functiono deployment process failed. Can't get instantiation status.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }
    if (status.equals("ERROR")) {
      Logger.error("Service instantiation failed on the other SP side.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Function deployment process failed on the lower SP side.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }


    // Get NSR to retrieve VNFR_ID

    GkRequestStatus instantiationRequest;
    try {
      instantiationRequest = gkClient.getRequest(requestUuid);
    } catch (IOException e) {
      Logger.error(e.getMessage(), e);
      Logger.error("Service instantiation failed. Can't retrieve instantiation request status.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Function deployment process failed. Can't retrieve instantiation request status.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }

    ServiceRecord nsr;
    try {
      nsr = gkClient.getNsr(instantiationRequest.getServiceInstanceUuid());
    } catch (IOException e1) {
      Logger.error(e1.getMessage(), e1);
      Logger.error("Service instantiation failed. Can't retrieve NSR of instantiated service.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Function deployment process failed. Can't retrieve NSR of instantiated service.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }

    // Get VNFR
    // There will be just one VNFR referenced by this NSR
    String vnfrId = nsr.getNetworkFunctions().get(0).getVnfrId();
    VnfRecord remoteVnfr;
    try {
      remoteVnfr = gkClient.getVnfr(vnfrId);
    } catch (IOException e1) {
      Logger.error(e1.getMessage(), e1);
      Logger.error("Service instantiation failed. Can't retrieve VNFR of instantiated function.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR",
          "Function deployment process failed. Can't retrieve VNFR of instantiated function.");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }



    // Map VNFR field to stripped VNFR.
    FunctionDeployResponse response = new FunctionDeployResponse();
    response.setRequestStatus("COMPLETED");
    response.setInstanceVimUuid("");
    response.setInstanceName("");
    response.setVimUuid(this.getConfig().getUuid());
    response.setMessage("");


    VnfRecord vnfr = new VnfRecord();
    vnfr.setDescriptorVersion("vnfr-schema-01");
    vnfr.setId(vnfd.getInstanceUuid());
    vnfr.setDescriptorReference(vnfd.getUuid());
    vnfr.setStatus(Status.offline);

    vnfr.setVirtualDeploymentUnits(remoteVnfr.getVirtualDeploymentUnits());

    for (VduRecord vdur : vnfr.getVirtualDeploymentUnits()) {
      for (VnfcInstance vnfc : vdur.getVnfcInstance()) {
        vnfc.setVimId(data.getVimUuid());
      }
    }

    // Send the response back
    response.setVnfr(vnfr);
    String body = null;
    try {
      body = mapper.writeValueAsString(response);
    } catch (JsonProcessingException e) {
      Logger.error(e.getMessage(), e);
      WrapperStatusUpdate update =
          new WrapperStatusUpdate(sid, "ERROR", "Exception during VNF Deployment");
      this.markAsChanged();
      this.notifyObservers(update);
      return;
    }
    Logger.info("Response created");
    // Logger.info("body");

    WrapperBay.getInstance().getVimRepo().writeServiceInstanceEntry(data.getServiceInstanceId(),
        instantiationRequest.getServiceInstanceUuid(), "", this.getConfig().getUuid());

    WrapperBay.getInstance().getVimRepo().writeFunctionInstanceEntry(vnfd.getInstanceUuid(),
        data.getServiceInstanceId(), this.getConfig().getUuid());
    WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "SUCCESS", body);
    this.markAsChanged();
    this.notifyObservers(update);
    long stop = System.currentTimeMillis();

    Logger.info("[SonataSPWrapper]FunctionDeploy-time: " + (stop - start) + " ms");


  }

  @Override
  public void deployCloudService(CloudServiceDeployPayload data, String sid) {
    // TODO Implement this function
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#deployService(sonata.kernel.vimadaptor.commons.
   * ServiceDeployPayload, java.lang.String)
   */
  @Deprecated
  @Override
  public boolean deployService(ServiceDeployPayload data, String callSid) throws Exception {

    return false;
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#getResourceUtilisation()
   */
  @Override
  public ResourceUtilisation getResourceUtilisation() {
    ResourceUtilisation out = new ResourceUtilisation();
    VimResources[] resList = null;
    try {
      resList = this.listPoPs();
    } catch (NotAuthorizedException e) {
      Logger.error(e.getMessage(), e);
      WrapperStatusUpdate update = new WrapperStatusUpdate("", "ERROR",
          "Can't Authenticate with the underlying SONATA Platform");
      this.markAsChanged();
      this.notifyObservers(update);
      return null;
    } catch (IOException e) {
      Logger.error(e.getMessage(), e);
      WrapperStatusUpdate update = new WrapperStatusUpdate("", "ERROR",
          "IO Exception while getting resource utilisation from the underlying SONATA Platform");
      this.markAsChanged();
      this.notifyObservers(update);
      return null;
    }

    out.setTotCores(0);
    out.setTotMemory(0);
    out.setUsedCores(0);
    out.setUsedMemory(0);

    for (VimResources res : resList) {
      out.setTotCores(out.getTotCores() + res.getCoreTotal());
      out.setUsedCores(out.getUsedCores() + res.getCoreUsed());
      out.setTotMemory(out.getTotMemory() + res.getMemoryTotal());
      out.setUsedMemory(out.getUsedMemory() + res.getMemoryUsed());
    }

    return out;
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#isImageStored(sonata.kernel.vimadaptor.commons.
   * VnfImage, java.lang.String)
   */
  @Override
  public boolean isImageStored(VnfImage image, String callSid) {
    // This Wrapper ignores this call
    return true;
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#prepareService(java.lang.String)
   */
  @Override
  public boolean prepareService(String instanceId) throws Exception {

    return true;
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#removeService(java.lang.String,
   * java.lang.String)
   */
  @Override
  public boolean removeService(String instanceUuid, String callSid) {

    VimRepo repo = WrapperBay.getInstance().getVimRepo();
    Logger.info("[SpWrapper] Trying to remove NS instance: " + instanceUuid);
    String slaveServiceInstanceUuid = repo.getServiceInstanceVimUuid(instanceUuid);
    Logger.info("[SpWrapper] NS instance mapped to lower SONATA service instance: "
        + slaveServiceInstanceUuid);

    if (slaveServiceInstanceUuid == null) {
      Logger.info("[SpWrapper] Nothing to remove in underlying SONATA platform");
      WrapperBay.getInstance().getVimRepo().removeServiceInstanceEntry(instanceUuid,
          this.getConfig().getUuid());
      this.setChanged();
      String body =
          "{\"status\":\"COMPLETED\",\"wrapper_uuid\":\"" + this.getConfig().getUuid() + "\"}";
      WrapperStatusUpdate update = new WrapperStatusUpdate(callSid, "SUCCESS", body);
      this.notifyObservers(update);

      return true;
    }

    Logger.info("[SpWrapper] Creating SONATA Rest Client");
    SonataGkClient gkClient = new SonataGkClient(this.getConfig().getVimEndpoint(),
        this.getConfig().getAuthUserName(), this.getConfig().getAuthPass());

    Logger.info("[SpWrapper] Authenticating SONATA Rest Client");
    if (!gkClient.authenticate()) throw new NotAuthorizedException("Client cannot login to the SP");

    String requestUuid = null;
    try {
      requestUuid = gkClient.removeServiceInstance(slaveServiceInstanceUuid);
    } catch (Exception e) {
      Logger.error(e.getMessage(), e);
      WrapperStatusUpdate update =
          new WrapperStatusUpdate(callSid, "ERROR", "Exception during Service termination");
      this.markAsChanged();
      this.notifyObservers(update);
      return false;
    }

    // - than poll the GK until the status is "READY" or "ERROR"

    int counter = 0;
    int wait = 1000;
    int maxCounter = 50;
    int maxWait = 15000;
    String status = null;
    while ((status == null || !status.equals("READY") || !status.equals("ERROR"))
        && counter < maxCounter) {
      try {
        status = gkClient.getRequestStatus(requestUuid);
      } catch (IOException e1) {
        Logger.error(e1.getMessage(), e1);
        Logger
            .error("Error while retrieving the Service termination request status. Trying again in "
                + (wait / 1000) + " seconds");
      }
      Logger.info("Status of request " + requestUuid + ": " + status);
      if (status != null && (status.equals("READY") || status.equals("ERROR"))) {
        break;
      }
      try {
        Thread.sleep(wait);
      } catch (InterruptedException e) {
        Logger.error(e.getMessage(), e);
      }
      counter++;
      wait = Math.min(wait * 2, maxWait);

    }

    if (status == null) {
      Logger.error("Unable to contact the GK to check the service termination status");
      WrapperStatusUpdate update = new WrapperStatusUpdate(callSid, "ERROR",
          "Functiono deployment process failed. Can't get instantiation status.");
      this.markAsChanged();
      this.notifyObservers(update);
      return false;
    } else if (status.equals("ERROR")) {
      Logger.error("failed on the other SP side.");
      WrapperStatusUpdate update = new WrapperStatusUpdate(callSid, "ERROR",
          "Service termination process failed on the lower SP side.");
      this.markAsChanged();
      this.notifyObservers(update);
      return false;
    } else {
      // Notify Northbound that the delete in this PoP is done.
      WrapperBay.getInstance().getVimRepo().removeServiceInstanceEntry(instanceUuid,
          this.getConfig().getUuid());
      this.setChanged();
      String body =
          "{\"status\":\"COMPLETED\",\"wrapper_uuid\":\"" + this.getConfig().getUuid() + "\"}";
      WrapperStatusUpdate update = new WrapperStatusUpdate(callSid, "SUCCESS", body);
      this.notifyObservers(update);

      return true;
    }
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#scaleFunction(sonata.kernel.vimadaptor.commons.
   * FunctionScalePayload, java.lang.String)
   */
  @Override
  public void scaleFunction(FunctionScalePayload data, String sid) {
    // TODO Auto-generated method stub
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#uploadImage(sonata.kernel.vimadaptor.commons.
   * VnfImage)
   */
  @Override
  public void uploadImage(VnfImage image) {
    // This Wrapper ignores this call
  }

  private VimResources[] listPoPs()
      throws NotAuthorizedException, ClientProtocolException, IOException {

    Logger.info("[SpWrapper] Creating SONATA Rest Client");
    SonataGkClient client = new SonataGkClient(this.getConfig().getVimEndpoint(),
        this.getConfig().getAuthUserName(), this.getConfig().getAuthPass());

    Logger.info("[SpWrapper] Authenticating SONATA Rest Client");
    if (!client.authenticate()) throw new NotAuthorizedException("Client cannot login to the SP");

    Logger.info("[SpWrapper] Retrieving VIMs connected to slave SONATA SP");
    VimResources[] out = client.getVims();

    return out;
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#removeImage(sonata.kernel.vimadaptor.commons.
   * VnfImage)
   */
  @Override
  public void removeImage(VnfImage image) {
    // TODO Auto-generated method stub

  }
}
