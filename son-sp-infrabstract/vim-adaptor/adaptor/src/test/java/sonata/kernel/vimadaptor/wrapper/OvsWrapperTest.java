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

package sonata.kernel.vimadaptor.wrapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;

import sonata.kernel.vimadaptor.AdaptorMux;
import sonata.kernel.vimadaptor.ConfigureNetworkCallProcessor;
import sonata.kernel.vimadaptor.commons.NetworkConfigurePayload;
import sonata.kernel.vimadaptor.commons.ServiceDeployPayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.mock.ComputeMockWrapper;
import sonata.kernel.vimadaptor.wrapper.ovsWrapper.OvsWrapper;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.concurrent.LinkedBlockingQueue;

public class OvsWrapperTest {

  private ServiceDeployPayload data;
  private ArrayList<VnfRecord> records;
  private ObjectMapper mapper;

  @Before
  public void setUp() throws Exception {

    ServiceDescriptor sd;
    StringBuilder bodyBuilder = new StringBuilder();
    BufferedReader in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/long-chain-demo.nsd")), Charset.forName("UTF-8")));
    String line;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    this.mapper = SonataManifestMapper.getSonataMapper();

    sd = mapper.readValue(bodyBuilder.toString(), ServiceDescriptor.class);

    VnfDescriptor vnfd1;
    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/1-vnf.vnfd")), Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vnfd1 = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    VnfDescriptor vnfd2;
    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/2-vnf.vnfd")), Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vnfd2 = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    VnfDescriptor vnfd3;
    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/3-vnf.vnfd")), Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vnfd3 = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    VnfDescriptor vnfd4;
    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/4-vnf.vnfd")), Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vnfd4 = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    VnfDescriptor vnfd5;
    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/5-vnf.vnfd")), Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vnfd5 = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    this.data = new ServiceDeployPayload();
    sd.setInstanceUuid(sd.getInstanceUuid() + "IASFCTEST");
    data.setServiceDescriptor(sd);
    data.addVnfDescriptor(vnfd1);
    data.addVnfDescriptor(vnfd2);
    data.addVnfDescriptor(vnfd3);
    data.addVnfDescriptor(vnfd4);
    data.addVnfDescriptor(vnfd5);

    records = new ArrayList<VnfRecord>();
    for (int i = 1; i <= 5; i++) {
      VnfRecord record;
      bodyBuilder = new StringBuilder();
      in = new BufferedReader(
          new InputStreamReader(new FileInputStream(new File("./YAML/" + i + "-vnf.vnfr")),
              Charset.forName("UTF-8")));
      line = null;
      while ((line = in.readLine()) != null)
        bodyBuilder.append(line + "\n\r");
      //System.out.println(bodyBuilder.toString());
      record = mapper.readValue(bodyBuilder.toString(), VnfRecord.class);
      records.add(record);
    }

  }


  @Ignore
  public void testOvsWrapperSinglePoP() throws JsonProcessingException {
    VimRepo repoInstance = new VimRepo();
    WrapperBay.getInstance().setRepo(repoInstance);
    String instanceId = data.getNsd().getInstanceUuid();
    String computeUuid1 = "1111-11111-1111";
    String netUuid1 = "aaaa-aaaaa-aaaa";
    // First PoP
    WrapperConfiguration config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(computeUuid1);
    config.setWrapperType(WrapperType.COMPUTE);
    String configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");
    ComputeWrapper computeWr =new ComputeMockWrapper(config);
    boolean out = repoInstance.writeVimEntry(config.getUuid(), computeWr);
    Assert.assertTrue("Unable to write the compute vim", out);

    config = new WrapperConfiguration();
    config.setVimEndpoint("10.100.32.200");
    config.setVimVendor(NetworkVimVendor.OVS);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(netUuid1);
    config.setWrapperType(WrapperType.NETWORK);
    config.setConfiguration("{\"compute_uuid\":\"" + computeUuid1 + "\"}");
    NetworkWrapper netWr = new OvsWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), netWr);
    repoInstance.writeNetworkVimLink(computeUuid1, netUuid1);

    // Populate VimRepo with Instance data, VNF1 And VNF2 are deployed on PoP1, VNF3 on PoP2, and
    // VNF4 and VNF5 on PoP3
    repoInstance.writeServiceInstanceEntry(instanceId, "1", "stack-1", computeUuid1);

    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(0).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(1).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(2).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(3).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(4).getInstanceUuid(), instanceId,
        computeUuid1);

    // Prepare environment and create the call processor.
    NetworkConfigurePayload netData = new NetworkConfigurePayload();
    netData.setServiceInstanceId(data.getNsd().getInstanceUuid());
    netData.setNsd(data.getNsd());
    netData.setVnfds(data.getVnfdList());
    netData.setVnfrs(records);
    String message = mapper.writeValueAsString(netData);
    LinkedBlockingQueue<ServicePlatformMessage> outQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    AdaptorMux mux = new AdaptorMux(outQueue);
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/xyaml",
        "chain.setup", "aVeryNiceSession", "chain.setup");
    Thread t = new Thread(new ConfigureNetworkCallProcessor(spMessage, spMessage.getSid(), mux));

    t.run();
    try {
      ServicePlatformMessage response = outQueue.take();

      JSONTokener tokener = new JSONTokener(response.getBody());
      JSONObject jsonObject = (JSONObject) tokener.nextValue();
      String status = jsonObject.getString("status");
      String responseMessage = jsonObject.getString("message");
      Assert.assertTrue("Request Not completed: " + responseMessage, status.equals("COMPLETED"));

    } catch (InterruptedException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }


  }

  @Ignore
  public void testOvsWrapperMultiPoP() throws Exception {

    // TODO FIXME Edit this test to reflect the new NetworkWrapper interface.
    VimRepo repoInstance = new VimRepo();
    WrapperBay.getInstance().setRepo(repoInstance);
    String instanceId = data.getNsd().getInstanceUuid();
    String computeUuid1 = "1111-11111-1111";
    String computeUuid2 = "2222-22222-2222";
    String computeUuid3 = "3333-33333-3333";
    String netUuid1 = "aaaa-aaaaa-aaaa";
    String netUuid2 = "bbbb-bbbbb-bbbb";
    String netUuid3 = "cccc-ccccc-cccc";
    // First PoP
    WrapperConfiguration config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(computeUuid1);
    config.setWrapperType(WrapperType.COMPUTE);
    String configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");
    ComputeWrapper computeWr = new ComputeMockWrapper(config);
    boolean out = repoInstance.writeVimEntry(config.getUuid(), computeWr);
    Assert.assertTrue("Unable to write the compute vim", out);

    config = new WrapperConfiguration();
    config.setVimEndpoint("10.100.32.200");
    config.setVimVendor(NetworkVimVendor.OVS);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(netUuid1);
    config.setWrapperType(WrapperType.NETWORK);
    config.setConfiguration("{\"compute_uuid\":\"" + computeUuid1 + "\"}");
    NetworkWrapper netWr = new OvsWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), netWr);
    repoInstance.writeNetworkVimLink(computeUuid1, netUuid1);

    // Second PoP
    config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(computeUuid2);
    config.setWrapperType(WrapperType.COMPUTE);
    configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");
    computeWr = new ComputeMockWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), computeWr);
    Assert.assertTrue("Unable to write the compute vim", out);

    config = new WrapperConfiguration();
    config.setVimEndpoint("10.100.32.200");
    config.setVimVendor(NetworkVimVendor.OVS);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(netUuid2);
    config.setWrapperType(WrapperType.NETWORK);
    config.setConfiguration("{\"compute_uuid\":\"" + computeUuid1 + "\"}");
    netWr = new OvsWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), netWr);
    repoInstance.writeNetworkVimLink(computeUuid2, netUuid2);

    // Third PoP
    config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(computeUuid3);
    config.setWrapperType(WrapperType.COMPUTE);
    configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");
    computeWr = new ComputeMockWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), computeWr);
    Assert.assertTrue("Unable to write the compute vim", out);

    config = new WrapperConfiguration();
    config.setVimEndpoint("10.100.32.200");
    config.setVimVendor(NetworkVimVendor.OVS);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setUuid(netUuid3);
    config.setWrapperType(WrapperType.NETWORK);
    config.setConfiguration("{\"compute_uuid\":\"" + computeUuid1 + "\"}");
    netWr = new OvsWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), netWr);
    repoInstance.writeNetworkVimLink(computeUuid3, netUuid3);


    // Populate VimRepo with Instance data, VNF1 And VNF2 are deployed on PoP1, VNF3 on PoP2, and
    // VNF4 and VNF5 on PoP3
    repoInstance.writeServiceInstanceEntry(instanceId, "1", "stack-1", computeUuid1);
    repoInstance.writeServiceInstanceEntry(instanceId, "1", "stack-1", computeUuid2);
    repoInstance.writeServiceInstanceEntry(instanceId, "1", "stack-1", computeUuid3);

    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(0).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(1).getInstanceUuid(), instanceId,
        computeUuid1);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(2).getInstanceUuid(), instanceId,
        computeUuid2);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(3).getInstanceUuid(), instanceId,
        computeUuid3);
    repoInstance.writeFunctionInstanceEntry(data.getVnfdList().get(4).getInstanceUuid(), instanceId,
        computeUuid3);

    // Prepare environment and create che call processor.
    NetworkConfigurePayload netData = new NetworkConfigurePayload();
    netData.setServiceInstanceId(data.getNsd().getInstanceUuid());
    netData.setNsd(data.getNsd());
    netData.setVnfds(data.getVnfdList());
    netData.setVnfrs(records);
    String message = mapper.writeValueAsString(netData);
    LinkedBlockingQueue<ServicePlatformMessage> outQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    AdaptorMux mux = new AdaptorMux(outQueue);
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/xyaml",
        "chain.setup", "abla", "chain.setup");
    Thread t = new Thread(new ConfigureNetworkCallProcessor(spMessage, "abla", mux));

    t.run();

    try {
      ServicePlatformMessage response = outQueue.take();

      JSONTokener tokener = new JSONTokener(response.getBody());
      JSONObject jsonObject = (JSONObject) tokener.nextValue();
      String status = jsonObject.getString("status");
      String responseMessage = jsonObject.getString("message");
      Assert.assertTrue("Request Not completed. Message: " + responseMessage,
          status.equals("COMPLETED"));

    } catch (InterruptedException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
  }

}
