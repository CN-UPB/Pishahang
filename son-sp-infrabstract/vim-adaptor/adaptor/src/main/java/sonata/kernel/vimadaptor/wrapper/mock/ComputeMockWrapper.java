/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, NCSR Demokritos ALL RIGHTS RESERVED.
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

package sonata.kernel.vimadaptor.wrapper.mock;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.*;
import sonata.kernel.vimadaptor.commons.vnfd.VirtualDeploymentUnit;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.WrapperStatusUpdate;

import java.io.IOException;
import java.util.Random;


public class ComputeMockWrapper extends ComputeWrapper {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(ComputeMockWrapper.class);
  /*
   * Utility fields to implement the mock response creation. A real wrapper should instantiate a
   * suitable object with these fields, able to handle the API call asynchronously, generate a
   * response and update the observer
   */
  @SuppressWarnings("unused")
  private ServiceDeployPayload data;
  private Random r;

  private String sid;

  public ComputeMockWrapper(WrapperConfiguration config) {
    super(config);
    this.r = new Random(System.currentTimeMillis());
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
    double avgTime = 51987.21;
    double stdTime = 14907.12;
    Logger.debug("[MockWrapper] deploying function...");
    waitGaussianTime(avgTime, stdTime);
    Logger.debug("[MockWrapper] function deployed. Generating response...");
    VnfDescriptor vnf = data.getVnfd();
    VnfRecord vnfr = new VnfRecord();
    vnfr.setDescriptorVersion("vnfr-schema-01");
    vnfr.setStatus(Status.normal_operation);
    vnfr.setDescriptorReference(vnf.getUuid());
    // vnfr.setDescriptorReferenceName(vnf.getName());
    // vnfr.setDescriptorReferenceVendor(vnf.getVendor());
    // vnfr.setDescriptorReferenceVersion(vnf.getVersion());

    vnfr.setId(vnf.getInstanceUuid());
    for (VirtualDeploymentUnit vdu : vnf.getVirtualDeploymentUnits()) {
      VduRecord vdur = new VduRecord();
      vdur.setId(vdu.getId());
      vdur.setNumberOfInstances(1);
      vdur.setVduReference(vnf.getName() + ":" + vdu.getId());
      vdur.setVmImage(vdu.getVmImage());
      vnfr.addVdu(vdur);
    }
    FunctionDeployResponse response = new FunctionDeployResponse();
    response.setRequestStatus("COMPLETED");
    response.setInstanceVimUuid("Stack-" + vnf.getInstanceUuid());
    response.setInstanceName("Stack-" + vnf.getInstanceUuid());
    response.setVimUuid(this.getConfig().getUuid());
    response.setMessage("");
    response.setVnfr(vnfr);
    Logger.info("Response created. Serializing...");

    ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
    mapper.disable(SerializationFeature.WRITE_EMPTY_JSON_ARRAYS);
    mapper.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);
    mapper.disable(SerializationFeature.WRITE_NULL_MAP_VALUES);
    mapper.setSerializationInclusion(Include.NON_NULL);
    String body;
    try {
      body = mapper.writeValueAsString(response);
      this.setChanged();
      Logger.info("Serialized. notifying call processor");
      WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "SUCCESS", body);
      this.notifyObservers(update);
    } catch (JsonProcessingException e) {
      Logger.error(e.getMessage(), e);
    }
    Logger.debug("[MockWrapper] Response generated. Writing record in the Infr. Repos...");
    WrapperBay.getInstance().getVimRepo().writeFunctionInstanceEntry(vnf.getInstanceUuid(),
        data.getServiceInstanceId(), this.getConfig().getUuid());
    Logger.debug("[MockWrapper] All done!");

  }

  @Override
  public void deployCloudService(CloudServiceDeployPayload data, String sid) {
    Logger.error("[MockWrapper] Received deploy cloud service call. Ignoring.");
  }

  @Deprecated
  @Override
  public boolean deployService(ServiceDeployPayload data, String callSid) {
    this.data = data;
    this.sid = callSid;
    // This is a mock compute wrapper.

    /*
     * Just use the SD to forge the response message for the SLM with a success. In general Wrappers
     * would need a complex set of actions to deploy the service, so this function should just check
     * if the request is acceptable, and if so start a new thread to deal with the perform the
     * needed actions.
     */
    return false;
  }

  @Override
  public ResourceUtilisation getResourceUtilisation() {

    double avgTime = 1769.39;
    double stdTime = 1096.48;
    waitGaussianTime(avgTime, stdTime);

    ResourceUtilisation resources = new ResourceUtilisation();
    resources.setTotCores(10);
    resources.setUsedCores(0);
    resources.setTotMemory(10000);
    resources.setUsedMemory(0);

    return resources;
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#isImageStored(java.lang.String)
   */
  @Override
  public boolean isImageStored(VnfImage image, String callSid) {
    double avgTime = 1357.34;
    double stdTime = 683.96;
    waitGaussianTime(avgTime, stdTime);
    return r.nextBoolean();
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#prepareService(java.lang.String)
   */
  @Override
  public boolean prepareService(String instanceId) {
    double avgTime = 10576.52;
    double stdTime = 1683.12;
    Logger.info("[MockWrapper] Preparing service for instance " + instanceId);
    waitGaussianTime(avgTime, stdTime);
    WrapperBay.getInstance().getVimRepo().writeServiceInstanceEntry(instanceId, instanceId,
        instanceId, this.getConfig().getUuid());
    return true;
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.wrapper.ComputeWrapper#removeImage(java.lang.String)
   */
  @Override
  public void removeImage(VnfImage image) {
    this.setChanged();
    String body = "{\"status\":\"SUCCESS\"}";
    WrapperStatusUpdate update = new WrapperStatusUpdate(this.sid, "SUCCESS", body);
    this.notifyObservers(update);
  }

  @Override
  public boolean removeService(String instanceUuid, String callSid) {
    boolean out = true;

    double avgTime = 1309;
    double stdTime = 343;
    waitGaussianTime(avgTime, stdTime);

    this.setChanged();
    String body = "{\"status\":\"SUCCESS\"}";
    WrapperStatusUpdate update = new WrapperStatusUpdate(this.sid, "SUCCESS", body);
    this.notifyObservers(update);

    return out;
  }

  @Override
  public void scaleFunction(FunctionScalePayload data, String sid) {
    // TODO - smendel - add implementation and comments on function
  }

  @Override
  public String toString() {
    return "MockWrapper-" + this.getConfig().getUuid();
  }

  /*
   * (non-Javadoc)
   * 
   * @see
   * sonata.kernel.vimadaptor.wrapper.ComputeWrapper#uploadImage(sonata.kernel.vimadaptor.commons.
   * VnfImage)
   */
  @Override
  public void uploadImage(VnfImage image) throws IOException {

    double avgTime = 7538.75;
    double stdTime = 1342.06;
    waitGaussianTime(avgTime, stdTime);

    return;
  }

  private void waitGaussianTime(double avgTime, double stdTime) {
    double waitTime = Math.abs((r.nextGaussian() - 0.5) * stdTime + avgTime);
    // Logger.debug("Simulating processing delay.Waiting "+waitTime/1000.0+"s");
    try {
      Thread.sleep((long) Math.floor(waitTime));
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
  }

}
