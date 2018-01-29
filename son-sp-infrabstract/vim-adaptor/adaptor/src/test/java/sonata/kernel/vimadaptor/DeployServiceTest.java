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

package sonata.kernel.vimadaptor;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Charsets;
import com.jcraft.jsch.ChannelExec;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.KeyPair;
import com.jcraft.jsch.Session;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;

import sonata.kernel.vimadaptor.AdaptorCore;
import sonata.kernel.vimadaptor.commons.FunctionDeployPayload;
import sonata.kernel.vimadaptor.commons.FunctionDeployResponse;
import sonata.kernel.vimadaptor.commons.NapObject;
import sonata.kernel.vimadaptor.commons.NetworkAttachmentPoints;
import sonata.kernel.vimadaptor.commons.NetworkConfigurePayload;
import sonata.kernel.vimadaptor.commons.ResourceAvailabilityData;
import sonata.kernel.vimadaptor.commons.ServiceDeployPayload;
import sonata.kernel.vimadaptor.commons.ServicePreparePayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.commons.Status;
import sonata.kernel.vimadaptor.commons.VduRecord;
import sonata.kernel.vimadaptor.commons.VimPreDeploymentList;
import sonata.kernel.vimadaptor.commons.VimResources;
import sonata.kernel.vimadaptor.commons.VnfImage;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.VnfcInstance;
import sonata.kernel.vimadaptor.commons.nsd.ConnectionPointRecord;
import sonata.kernel.vimadaptor.commons.nsd.ConnectionPointType;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.Unit.MemoryUnit;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.messaging.TestConsumer;
import sonata.kernel.vimadaptor.messaging.TestProducer;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;



/**
 * Unit test for simple App.
 */

public class DeployServiceTest implements MessageReceiver {
  private String output = null;
  private Object mon = new Object();
  private TestConsumer consumer;
  private String lastHeartbeat;
  private VnfDescriptor vtcVnfd;
  private VnfDescriptor vfwVnfd;
  private ServiceDeployPayload nsdPayload;
  private ObjectMapper mapper;

  /**
   * Set up the test environment
   *
   */
  @Before
  public void setUp() throws Exception {

    System.setProperty("org.apache.commons.logging.Log",
        "org.apache.commons.logging.impl.SimpleLog");

    System.setProperty("org.apache.commons.logging.simplelog.showdatetime", "false");

    System.setProperty("org.apache.commons.logging.simplelog.log.httpclient.wire.header", "warn");

    System.setProperty("org.apache.commons.logging.simplelog.log.org.apache.commons.httpclient",
        "warn");

    ServiceDescriptor sd;
    StringBuilder bodyBuilder = new StringBuilder();
    BufferedReader in = new BufferedReader(new InputStreamReader(
        new FileInputStream(new File("./YAML/sonata-demo.nsd")), Charset.forName("UTF-8")));
    String line;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    this.mapper = SonataManifestMapper.getSonataMapper();

    sd = mapper.readValue(bodyBuilder.toString(), ServiceDescriptor.class);

    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(new FileInputStream(new File("./YAML/vbar.vnfd")),
        Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vtcVnfd = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);

    bodyBuilder = new StringBuilder();
    in = new BufferedReader(new InputStreamReader(new FileInputStream(new File("./YAML/vfoo.vnfd")),
        Charset.forName("UTF-8")));
    line = null;
    while ((line = in.readLine()) != null)
      bodyBuilder.append(line + "\n\r");
    vfwVnfd = mapper.readValue(bodyBuilder.toString(), VnfDescriptor.class);


    this.nsdPayload = new ServiceDeployPayload();

    nsdPayload.setServiceDescriptor(sd);
    nsdPayload.addVnfDescriptor(vtcVnfd);
    nsdPayload.addVnfDescriptor(vfwVnfd);

  }

  /**
   * Test the checkResource API with the mock wrapper.
   *
   * @throws IOException
   * @throws InterruptedException
   */
  @Test
  public void testCheckResources() throws IOException, InterruptedException {

    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    consumer = new TestConsumer(dispatcherQueue);
    AdaptorCore core = new AdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.1);

    core.start();
    int counter = 0;

    try {
      while (counter < 2) {
        synchronized (mon) {
          mon.wait();
          if (lastHeartbeat.contains("RUNNING")) counter++;
        }
      }
    } catch (Exception e) {
      Assert.assertTrue(false);
    }

    String message =
        "{\"vim_type\":\"mock\",\"vim_address\":\"http://localhost:9999\",\"username\":\"Eve\","
            + "\"name\":\"Mock1\"," + "\"pass\":\"Operator\",\"city\":\"London\",\"country\":\"\",\"domain\":\"default\","
            + "\"configuration\":{\"tenant\":\"operator\",\"tenant_ext_net\":\"ext-subnet\",\"tenant_ext_router\":\"ext-router\"}}";
    String topic = "infrastructure.management.compute.add";
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String status = jsonObject.getString("request_status");
    String wrUuid = jsonObject.getString("uuid");
    Assert.assertTrue(status.equals("COMPLETED"));
    System.out.println("Mock Wrapper added, with uuid: " + wrUuid);

    ResourceAvailabilityData data = new ResourceAvailabilityData();

    data.setCpu(4);
    data.setMemory(10);
    data.setMemoryUnit(MemoryUnit.GB);
    data.setStorage(50);
    data.setStorageUnit(MemoryUnit.GB);
    topic = "infrastructure.management.compute.resourceAvailability";


    message = mapper.writeValueAsString(data);

    ServicePlatformMessage checkResourcesMessage = new ServicePlatformMessage(message,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    output = null;
    consumer.injectMessage(checkResourcesMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    Assert.assertTrue(output.contains("OK"));
    message = "{\"uuid\":\"" + wrUuid + "\"}";
    topic = "infrastructure.management.compute.remove";
    ServicePlatformMessage removeVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeVimMessage);
    output = null;
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }


    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));
    core.stop();

  }

  /**
   * test the service deployment API call with the mockWrapper.
   *
   * @throws IOException
   * @throws InterruptedException
   */
  @Test
  public void testDeployServiceMock() throws IOException, InterruptedException {


    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    consumer = new TestConsumer(dispatcherQueue);
    AdaptorCore core = new AdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.1);

    core.start();
    int counter = 0;

    try {
      while (counter < 2) {
        synchronized (mon) {
          mon.wait();
          if (lastHeartbeat.contains("RUNNING")) counter++;
        }
      }
    } catch (Exception e) {
      Assert.assertTrue(false);
    }


    String message =
        "{\"vim_type\":\"mock\",\"vim_address\":\"http://localhost:9999\",\"username\":\"Eve\","
            + "\"name\":\"Mock1\"," + "\"pass\":\"Operator\",\"city\":\"London\",\"country\":\"\",\"domain\":\"default\","
            + "\"configuration\":{\"tenant\":\"operator\",\"tenant_ext_net\":\"ext-subnet\",\"tenant_ext_router\":\"ext-router\"}}";
    String topic = "infrastructure.management.compute.add";
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String status = jsonObject.getString("request_status");
    String wrUuid = jsonObject.getString("uuid");
    Assert.assertTrue(status.equals("COMPLETED"));
    System.out.println("Mock Wrapper added, with uuid: " + wrUuid);

    output = null;
    nsdPayload.setVimUuid(wrUuid);

    String body = mapper.writeValueAsString(nsdPayload);

    topic = "infrastructure.service.deploy";
    ServicePlatformMessage deployServiceMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(deployServiceMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }
    Assert.assertNotNull(output);
    int retry = 0;
    int maxRetry = 60;
    while (output.contains("heartbeat") || output.contains("Vim Added") && retry < maxRetry)
      synchronized (mon) {
        mon.wait(1000);
        retry++;
      }

    Assert.assertTrue("No Deploy service response received", retry < maxRetry);

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("ERROR"));



    output = null;
    message = "{\"uuid\":\"" + wrUuid + "\"}";
    topic = "infrastructure.management.compute.remove";
    ServicePlatformMessage removeVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));
    core.stop();

  }


  /**
   * This test is de-activated, if you want to use it with your NFVi-PoP, please edit the addVimBody
   * String Member to match your OpenStack configuration and substitute the @ignore annotation with
   * the @test annotation
   *
   * @throws Exception
   */
  @Ignore
  public void testDeployServiceV2() throws Exception {
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    consumer = new TestConsumer(dispatcherQueue);
    AdaptorCore core = new AdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.1);

    core.start();
    int counter = 0;

    try {
      while (counter < 2) {
        synchronized (mon) {
          mon.wait();
          if (lastHeartbeat.contains("RUNNING")) counter++;
        }
      }
    } catch (Exception e) {
      Assert.assertTrue(false);
    }


    // Test PoP
    // PoP Athens.200 Newton
    // String addVimBody = "{\"vim_type\":\"Heat\", " +"\"name\":\"Athens1\"," +
    // "\"configuration\":{"
    // + "\"tenant_ext_router\":\"9303604f-bbf1-457a-824a-0229d103398e\", "
    // + "\"tenant_ext_net\":\"7666cbd8-6795-4fc3-a08c-af410b63ee43\"," + "\"tenant\":\"admin\""
    // + "}," + "\"city\":\"Athens\",\"country\":\"Greece\","
    // + "\"vim_address\":\"10.101.20.2\",\"username\":\"dario\","
    // + "\"pass\":\"d@rio\"}";
    // System.out.println("[TwoPoPTest] Adding test PoP .20.2");


    // Add first PoP
    // PoP Athens.200 Mitaka
    String addVimBody = "{\"vim_type\":\"Heat\", " + "\"name\":\"Athens1\"," + "\"configuration\":{"
        + "\"tenant_private_cidr\":\"10.128.0.0/9\","
        + "\"tenant_ext_router\":\"26f732b2-74bd-4f8c-a60e-dae4fb6a7c14\", "
        + "\"tenant_ext_net\":\"53d43a3e-8c86-48e6-b1cb-f1f2c48833de\"," + "\"tenant\":\"admin\""
        + "}," + "\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"vim_address\":\"10.100.32.200\",\"username\":\"sonata.dario\","
        + "\"pass\":\"s0n@t@.d@ri0\"}";
    System.out.println("[OnePoPTest] Adding PoP .200");

    // Add first PoP
    // PoP Athens.201 Newton
    // String addVimBody = "{\"vim_type\":\"Heat\", " + "\"configuration\":{"
    // + "\"tenant_ext_router\":\"3bc4fc5c-9c3e-4f29-8244-267fbc2c7ccb\", "
    // + "\"tenant_ext_net\":\"081e13ad-e231-4291-a390-4a66fa09b846\"," + "\"tenant\":\"admin\""
    // + "}," + "\"city\":\"Athens\",\"country\":\"Greece\","
    // + "\"vim_address\":\"10.30.0.201\",\"username\":\"admin\","
    // + "\"pass\":\"char1234\"}";

    String topic = "infrastructure.management.compute.add";
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(addVimBody,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }



    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String status = jsonObject.getString("request_status");
    String computeWrUuid = jsonObject.getString("uuid");
    Assert.assertTrue(status.equals("COMPLETED"));
    System.out.println("OpenStack Wrapper added, with uuid: " + computeWrUuid);


    output = null;
    String addNetVimBody = "{\"vim_type\":\"ovs\", " + "\"name\":\"Athens1-net\","
        + "\"vim_address\":\"10.100.32.200\",\"username\":\"operator\",\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"pass\":\"apass\",\"configuration\":{\"compute_uuid\":\"" + computeWrUuid + "\"}}";
    topic = "infrastructure.management.network.add";
    ServicePlatformMessage addNetVimMessage = new ServicePlatformMessage(addNetVimBody,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addNetVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    String netWrUuid = jsonObject.getString("uuid");
    Assert.assertTrue("Failed to add the ovs wrapper. Status " + status,
        status.equals("COMPLETED"));
    System.out.println("OVS Wrapper added, with uuid: " + netWrUuid);


    output = null;

    // Generate a ssh keypair for ssh connection test to VMs
    JSch jsch = new JSch();
    KeyPair keypair = KeyPair.genKeyPair(jsch, KeyPair.RSA);

    System.out.println("RSA Keypair toString:\n" + keypair.toString());
    System.out.println("RSA Keypair fingerprint:\n" + keypair.getFingerPrint());

    ByteArrayOutputStream baos = new ByteArrayOutputStream();
    keypair.writePublicKey(baos, "");
    String pubKeyString = baos.toString(Charsets.UTF_8.displayName()).replace("\n", "");

    baos = new ByteArrayOutputStream();
    keypair.writePrivateKey(baos);
    String privKeyString = baos.toString(Charsets.UTF_8.displayName());

    // Use PEM format for serialising keys
    // KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
    // generator.initialize(1024);
    //
    // java.security.KeyPair keyPair = generator.generateKeyPair();
    // RSAPrivateKey priv = (RSAPrivateKey) keyPair.getPrivate();
    // RSAPublicKey pub = (RSAPublicKey) keyPair.getPublic();
    //
    // PemObject pemPubKey = new PemObject("RSA PUBLIC KEY", pub.getEncoded());
    // PemObject pemPrivKey = new PemObject("RSA PRIVATE KEY", priv.getEncoded());
    //
    //
    // StringWriter strwr = new StringWriter();
    // PemWriter wr = new PemWriter(strwr);
    // wr.writeObject(pemPubKey);
    // wr.flush();
    // strwr.flush();
    // pubKeyString = strwr.getBuffer().toString();
    //
    // strwr = new StringWriter();
    // wr = new PemWriter(strwr);
    // wr.writeObject(pemPrivKey);
    // wr.flush();
    // strwr.flush();
    // privKeyString = strwr.getBuffer().toString();

    System.out.println(pubKeyString);
    System.out.println(privKeyString);


    // Service prepare call
    ServicePreparePayload payload = new ServicePreparePayload();

    payload.setInstanceId(nsdPayload.getNsd().getInstanceUuid());
    ArrayList<VimPreDeploymentList> vims = new ArrayList<VimPreDeploymentList>();
    VimPreDeploymentList vimDepList = new VimPreDeploymentList();
    vimDepList.setUuid(computeWrUuid);
    ArrayList<VnfImage> vnfImages = new ArrayList<VnfImage>();
    VnfImage vtcImgade = new VnfImage("eu.sonata-nfv_vbar-vnf_0.1_vdu01",
        // "http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img");
        // "https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img");
        "https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2");
    vnfImages.add(vtcImgade);
    VnfImage vfwImgade = new VnfImage("eu.sonata-nfv_vfoo-vnf_0.1_1",
        // "http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img",
        // "f8ab98ff5e73ebab884d80c9dc9c7290");
        "https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img",
        "c3e0b581d613a4806e6e5fd823d93f01");
    vnfImages.add(vfwImgade);
    vimDepList.setImages(vnfImages);
    vims.add(vimDepList);

    payload.setVimList(vims);

    String body = mapper.writeValueAsString(payload);

    topic = "infrastructure.service.prepare";
    ServicePlatformMessage servicePrepareMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(servicePrepareMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    String message = jsonObject.getString("message");
    Assert.assertTrue("Failed to prepare the environment for the service deployment: " + status
        + " - message: " + message, status.equals("COMPLETED"));
    System.out.println("Service " + payload.getInstanceId() + " ready for deployment");

    // Send a VNF instantiation request for each VNFD linked by the NSD
    ArrayList<VnfRecord> records = new ArrayList<VnfRecord>();
    for (VnfDescriptor vnfd : nsdPayload.getVnfdList()) {

      output = null;

      FunctionDeployPayload vnfPayload = new FunctionDeployPayload();
      vnfPayload.setVnfd(vnfd);
      vnfPayload.setVimUuid(computeWrUuid);
      vnfPayload.setPublicKey(null);
      vnfPayload.setPublicKey(pubKeyString);
      vnfPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());
      body = mapper.writeValueAsString(vnfPayload);

      topic = "infrastructure.function.deploy";
      ServicePlatformMessage functionDeployMessage = new ServicePlatformMessage(body,
          "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

      consumer.injectMessage(functionDeployMessage);

      Thread.sleep(2000);
      while (output == null)
        synchronized (mon) {
          mon.wait(1000);
        }
      Assert.assertNotNull(output);
      int retry = 0;
      int maxRetry = 60;
      while (output.contains("heartbeat") || output.contains("Vim Added") && retry < maxRetry) {
        synchronized (mon) {
          mon.wait(1000);
          retry++;
        }
      }

      System.out.println("FunctionDeployResponse: ");
      System.out.println(output);
      Assert.assertTrue("No response received after function deployment", retry < maxRetry);
      FunctionDeployResponse response = mapper.readValue(output, FunctionDeployResponse.class);
      Assert.assertTrue(response.getRequestStatus().equals("COMPLETED"));
      Assert.assertTrue(response.getVnfr().getStatus() == Status.offline);
      records.add(response.getVnfr());

      // Test SSH connection
      for (VduRecord vdu : response.getVnfr().getVirtualDeploymentUnits()) {
        for (VnfcInstance vnfc : vdu.getVnfcInstance()) {
          String host = "";
          for (ConnectionPointRecord cpr : vnfc.getConnectionPoints()) {
            if (cpr.getType() == ConnectionPointType.MANAGEMENT) {
              host = cpr.getInterface().getAddress();
            }
          }
          Assert.assertNotNull("Can't find management address of VNFC: "
              + response.getVnfr().getId() + "." + vdu.getId() + "." + vnfc.getId(), host);
          System.out.println("Trying to ssh connect into the public IP of the VNF");

          String user = "sonatamano";
          int port = 22;
          keypair.writePrivateKey("/tmp/privkey");
          jsch.addIdentity("/tmp/privkey");

          System.out.println("Connecting to host: " + host);
          Session session = jsch.getSession(user, host, port);
          System.out.println("session created.");

          java.util.Properties config = new java.util.Properties();
          config.put("StrictHostKeyChecking", "no");
          session.setConfig(config);

          session.connect();
          System.out.println("session connected.....");

          String commandToRun = "cat /etc/sonata_sp_address.conf 2>&1 \n";
          ChannelExec channelExec = (ChannelExec) session.openChannel("exec");

          InputStream in = channelExec.getInputStream();

          channelExec.setCommand(commandToRun);
          channelExec.connect();

          BufferedReader reader = new BufferedReader(new InputStreamReader(in));
          String line;
          int index = 0;
          String fileContent = "";
          while ((line = reader.readLine()) != null) {
            fileContent+=line;
            System.out.println(++index + " : " + line);
          }

          int exitStatus = channelExec.getExitStatus();
          channelExec.disconnect();
          session.disconnect();
          if (exitStatus < 0) {
            System.out.println("Done, but exit status not set!");
          } else if (exitStatus > 0) {
            System.out.println("Done, but with error!");
          } else {
            System.out.println("Done!");
          }

          System.out.println("FileContent: " + fileContent);

          Assert.assertTrue(fileContent.startsWith("SP_ADDRESS="));

          session.disconnect();
          System.out.println("session disconnected");
        }
      }

    }

    // Finally configure Networking in each NFVi-PoP (VIMs)

    output = null;

    NetworkAttachmentPoints nap = new NetworkAttachmentPoints();
    NapObject in1 = new NapObject();
    NapObject in2 = new NapObject();
    NapObject out1 = new NapObject();
    NapObject out2 = new NapObject();
    in1.setLocation("Athens");
    in2.setLocation("Athens");
    in1.setNap("10.100.32.40/32");
    in2.setNap("10.100.0.40/32");

    out1.setLocation("Athens");
    out2.setLocation("Athens");
    out1.setNap("10.100.32.40/32");
    out2.setNap("10.100.0.40/32");
    NapObject[] ingresses = {in1, in2};
    NapObject[] egresses = {out1, out2};
    nap.setEgresses(new ArrayList<NapObject>(Arrays.asList(egresses)));
    nap.setIngresses(new ArrayList<NapObject>(Arrays.asList(ingresses)));


    NetworkConfigurePayload netPayload = new NetworkConfigurePayload();
    netPayload.setNsd(nsdPayload.getNsd());
    netPayload.setVnfds(nsdPayload.getVnfdList());
    netPayload.setVnfrs(records);
    netPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());
    netPayload.setNap(nap);


    body = mapper.writeValueAsString(netPayload);

    topic = "infrastructure.service.chain.configure";
    ServicePlatformMessage networkConfigureMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(networkConfigureMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Failed to configure inter-PoP SFC. status:" + status,
        status.equals("COMPLETED"));
    System.out.println(
        "Service " + payload.getInstanceId() + " deployed and configured in selected VIM(s)");

    // Clean everything:
    // 1. De-configure SFC
    output = null;
    message = "{\"service_instance_id\":\"" + nsdPayload.getNsd().getInstanceUuid() + "\"}";
    topic = "infrastructure.service.chain.deconfigure";
    ServicePlatformMessage deconfigureNetworkMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(deconfigureNetworkMessage);
    try {
      while (output == null) {
        synchronized (mon) {
          mon.wait(2000);
          System.out.println(output);
        }
      }
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Adapter returned an unexpected status: " + status,
        status.equals("COMPLETED"));

    // Configure it again with default NAP

    output = null;


    netPayload = new NetworkConfigurePayload();
    netPayload.setNsd(nsdPayload.getNsd());
    netPayload.setVnfds(nsdPayload.getVnfdList());
    netPayload.setVnfrs(records);
    netPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());
    netPayload.setNap(null);


    body = mapper.writeValueAsString(netPayload);

    topic = "infrastructure.service.chain.configure";
    networkConfigureMessage = new ServicePlatformMessage(body, "application/x-yaml", topic,
        UUID.randomUUID().toString(), topic);

    consumer.injectMessage(networkConfigureMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Failed to configure inter-PoP SFC. status:" + status,
        status.equals("COMPLETED"));
    System.out.println(
        "Service " + payload.getInstanceId() + " deployed and configured in selected VIM(s)");

    // Clean everything again:
    // 1. De-configure SFC
    output = null;
    message = "{\"service_instance_id\":\"" + nsdPayload.getNsd().getInstanceUuid() + "\"}";
    topic = "infrastructure.service.chain.deconfigure";
    deconfigureNetworkMessage = new ServicePlatformMessage(message, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(deconfigureNetworkMessage);
    try {
      while (output == null) {
        synchronized (mon) {
          mon.wait(2000);
          System.out.println(output);
        }
      }
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Adapter returned an unexpected status: " + status,
        status.equals("COMPLETED"));


    // 2. Remove Service
    // Service removal
    output = null;
    String instanceUuid = nsdPayload.getNsd().getInstanceUuid();
    message = "{\"instance_uuid\":\"" + instanceUuid + "\"}";
    topic = "infrastructure.service.remove";
    ServicePlatformMessage removeInstanceMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeInstanceMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(2000);
        System.out.println(output);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Adapter returned an unexpected status: " + status,
        status.equals("COMPLETED"));

    // 3. De-register VIMs.

    output = null;
    message = "{\"uuid\":\"" + computeWrUuid + "\"}";
    topic = "infrastructure.management.compute.remove";
    ServicePlatformMessage removeVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"uuid\":\"" + netWrUuid + "\"}";
    topic = "infrastructure.management.network.remove";
    ServicePlatformMessage removeNetVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeNetVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    core.stop();


  }


  /**
   * This test is de-activated, if you want to use it with your NFVi-PoPs (at least two), please
   * edit the addVimBody String member to match your OpenStack configuration and substitute
   * the @ignore annotation with the @test annotation
   *
   * @throws Exception
   */
  @Ignore
  public void testDeployServiceV2MultiPoP() throws Exception {
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    consumer = new TestConsumer(dispatcherQueue);
    AdaptorCore core = new AdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.1);

    core.start();
    int counter = 0;

    try {
      while (counter < 2) {
        synchronized (mon) {
          mon.wait();
          if (lastHeartbeat.contains("RUNNING")) counter++;
        }
      }
    } catch (Exception e) {
      Assert.assertTrue(false);
    }

    System.out.println("[TwoPoPTest] Adding PoP .200");
    // Add first PoP
    // PoP Athens.200 Mitaka
    String addVimBody = "{\"vim_type\":\"Heat\", " + "\"configuration\":{"
        + "\"tenant_ext_router\":\"26f732b2-74bd-4f8c-a60e-dae4fb6a7c14\", "
        + "\"tenant_ext_net\":\"53d43a3e-8c86-48e6-b1cb-f1f2c48833de\"," + "\"tenant\":\"admin\""
        + "}," + "\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"vim_address\":\"10.100.32.200\", \"username\":\"sonata.dario\","
        + "\"name\":\"Athens1\"," + "\"pass\":\"s0n@t@.d@ri0\"}";



    String topic = "infrastructure.management.compute.add";
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(addVimBody,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }



    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String status = jsonObject.getString("request_status");
    String computeWrUuid1 = jsonObject.getString("uuid");
    Assert.assertTrue(status.equals("COMPLETED"));
    System.out.println("OpenStack Wrapper added, with uuid: " + computeWrUuid1);


    output = null;
    String addNetVimBody = "{\"vim_type\":\"ovs\", " + "\"name\":\"Athens1-net\","
        + "\"vim_address\":\"10.100.32.200\",\"username\":\"operator\",\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"pass\":\"apass\",\"configuration\":{\"compute_uuid\":\"" + computeWrUuid1 + "\"}}";
    topic = "infrastructure.management.network.add";
    ServicePlatformMessage addNetVimMessage = new ServicePlatformMessage(addNetVimBody,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addNetVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    String netWrUuid1 = jsonObject.getString("uuid");
    Assert.assertTrue("Failed to add the ovs wrapper. Status " + status,
        status.equals("COMPLETED"));
    System.out.println("OVS Wrapper added, with uuid: " + netWrUuid1);


    output = null;

    // Add second PoP
    System.out.println("[TwoPoPTest] Adding PoP .10");
    // PoP Athens.10 Mitaka
    addVimBody = "{\"vim_type\":\"Heat\", " + "\"configuration\":{"
        + "\"tenant_ext_router\":\"4e362dfd-ba10-4957-9b8b-51e31b5ec4e9\", "
        + "\"tenant_ext_net\":\"12bf4db8-0131-4322-bd22-0b1ad8333748\","
        + "\"tenant\":\"sonata.dario\"" + "}," + "\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"vim_address\":\"10.100.32.10\",\"username\":\"sonata.dario\","
        + "\"name\":\"Athens2\"," + "\"pass\":\"s0n@t@.d@ri0\"}";

    topic = "infrastructure.management.compute.add";
    addVimMessage = new ServicePlatformMessage(addVimBody, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }



    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    String computeWrUuid2 = jsonObject.getString("uuid");
    Assert.assertTrue(status.equals("COMPLETED"));
    System.out.println("OpenStack Wrapper added, with uuid: " + computeWrUuid2);


    output = null;
    addNetVimBody = "{\"vim_type\":\"ovs\", " + "\"name\":\"Athens2-net\","
        + "\"vim_address\":\"10.100.32.10\",\"username\":\"operator\",\"city\":\"Athens\",\"country\":\"Greece\",\"domain\":\"default\","
        + "\"pass\":\"apass\",\"configuration\":{\"compute_uuid\":\"" + computeWrUuid2 + "\"}}";
    topic = "infrastructure.management.network.add";
    addNetVimMessage = new ServicePlatformMessage(addNetVimBody, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addNetVimMessage);
    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    String netWrUuid2 = jsonObject.getString("uuid");
    Assert.assertTrue("Failed to add the ovs wrapper. Status " + status,
        status.equals("COMPLETED"));
    System.out.println("OVS Wrapper added, with uuid: " + netWrUuid2);


    output = null;

    // List available PoP
    System.out.println("[TwoPoPTest] Listing available NFVIi-PoP.");

    topic = "infrastructure.management.compute.list";
    ServicePlatformMessage listVimMessage =
        new ServicePlatformMessage(null, null, topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(listVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    VimResources[] vimList = mapper.readValue(output, VimResources[].class);
    System.out.println("[TwoPoPTest] Listing available PoP");
    for (VimResources resource : vimList) {
      System.out.println(mapper.writeValueAsString(resource));
    }

    output = null;
    // Prepare the system for a service deployment
    System.out.println("[TwoPoPTest] Building service.prepare call.");

    ServicePreparePayload payload = new ServicePreparePayload();

    payload.setInstanceId(nsdPayload.getNsd().getInstanceUuid());
    ArrayList<VimPreDeploymentList> vims = new ArrayList<VimPreDeploymentList>();
    VimPreDeploymentList vimDepList = new VimPreDeploymentList();
    vimDepList.setUuid(computeWrUuid1);
    ArrayList<VnfImage> vnfImages = new ArrayList<VnfImage>();
    VnfImage vtcImgade =
        // new VnfImage("eu.sonata-nfv_vtc-vnf_0.1_vdu01", "file:///test_images/sonata-vtc.img");
        new VnfImage("eu.sonata-nfv_vtc-vnf_0.1_vdu01",
            "http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img");

    vnfImages.add(vtcImgade);
    vimDepList.setImages(vnfImages);
    vims.add(vimDepList);



    vimDepList = new VimPreDeploymentList();
    vimDepList.setUuid(computeWrUuid2);
    vnfImages = new ArrayList<VnfImage>();
    VnfImage vfwImgade =
        // new VnfImage("eu.sonata-nfv_fw-vnf_0.1_1", "file:///test_images/sonata-vfw.img");
        new VnfImage("eu.sonata-nfv_fw-vnf_0.1_1",
            "http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img");
    vnfImages.add(vfwImgade);
    vimDepList.setImages(vnfImages);
    vims.add(vimDepList);

    payload.setVimList(vims);

    String body = mapper.writeValueAsString(payload);
    System.out.println("[TwoPoPTest] Request body:");
    System.out.println(body);

    topic = "infrastructure.service.prepare";
    ServicePlatformMessage servicePrepareMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(servicePrepareMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    String message = jsonObject.getString("message");
    Assert.assertTrue("Failed to prepare the environment for the service deployment: " + status
        + " - message: " + message, status.equals("COMPLETED"));
    System.out.println("Service " + payload.getInstanceId() + " ready for deployment");


    // Deploy the two VNFs, one in each PoP
    ArrayList<VnfRecord> records = new ArrayList<VnfRecord>();

    // vTC VNF in PoP#1
    output = null;

    FunctionDeployPayload vnfPayload = new FunctionDeployPayload();
    vnfPayload.setVnfd(vtcVnfd);
    vnfPayload.setVimUuid(computeWrUuid1);
    vnfPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());
    body = mapper.writeValueAsString(vnfPayload);

    topic = "infrastructure.function.deploy";
    ServicePlatformMessage functionDeployMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(functionDeployMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }
    Assert.assertNotNull(output);
    int retry = 0;
    int maxRetry = 60;
    while (output.contains("heartbeat") || output.contains("Vim Added") && retry < maxRetry) {
      synchronized (mon) {
        mon.wait(1000);
        retry++;
      }
    }

    System.out.println("FunctionDeployResponse: ");
    System.out.println(output);
    Assert.assertTrue("No response received after function deployment", retry < maxRetry);
    FunctionDeployResponse response = mapper.readValue(output, FunctionDeployResponse.class);
    Assert.assertTrue(response.getRequestStatus().equals("COMPLETED"));
    Assert.assertTrue(response.getVnfr().getStatus() == Status.offline);
    records.add(response.getVnfr());

    // vFw VNF in PoP#2
    output = null;
    response = null;

    vnfPayload = new FunctionDeployPayload();
    vnfPayload.setVnfd(vfwVnfd);
    vnfPayload.setVimUuid(computeWrUuid2);
    vnfPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());
    body = mapper.writeValueAsString(vnfPayload);

    topic = "infrastructure.function.deploy";
    functionDeployMessage = new ServicePlatformMessage(body, "application/x-yaml", topic,
        UUID.randomUUID().toString(), topic);

    consumer.injectMessage(functionDeployMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }
    Assert.assertNotNull(output);
    retry = 0;
    maxRetry = 60;
    while (output.contains("heartbeat") || output.contains("Vim Added") && retry < maxRetry) {
      synchronized (mon) {
        mon.wait(1000);
        retry++;
      }
    }

    System.out.println("FunctionDeployResponse: ");
    System.out.println(output);
    Assert.assertTrue("No response received after function deployment", retry < maxRetry);
    response = mapper.readValue(output, FunctionDeployResponse.class);
    Assert.assertTrue(response.getRequestStatus().equals("COMPLETED"));
    Assert.assertTrue(response.getVnfr().getStatus() == Status.offline);
    records.add(response.getVnfr());

    // Finally configure Networking in each NFVi-PoP (VIMs)

    output = null;

    NetworkConfigurePayload netPayload = new NetworkConfigurePayload();
    netPayload.setNsd(nsdPayload.getNsd());
    netPayload.setVnfds(nsdPayload.getVnfdList());
    netPayload.setVnfrs(records);
    netPayload.setServiceInstanceId(nsdPayload.getNsd().getInstanceUuid());


    body = mapper.writeValueAsString(netPayload);

    topic = "infrastructure.service.chain.configure";
    ServicePlatformMessage networkConfigureMessage = new ServicePlatformMessage(body,
        "application/x-yaml", topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(networkConfigureMessage);

    Thread.sleep(2000);
    while (output == null)
      synchronized (mon) {
        mon.wait(1000);
      }

    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = null;
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Failed to configure inter-PoP SFC. status:" + status,
        status.equals("COMPLETED"));
    System.out.println(
        "Service " + payload.getInstanceId() + " deployed and configured in selected VIM(s)");

    output = null;

    // TODO WIM PART

    // De-configure SFC

    message = "{\"service_instance_id\":\"" + nsdPayload.getNsd().getInstanceUuid() + "\"}";
    topic = "infrastructure.service.chain.deconfigure";
    ServicePlatformMessage deconfigureNetworkMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(deconfigureNetworkMessage);
    try {
      while (output == null) {
        synchronized (mon) {
          mon.wait(2000);
          System.out.println(output);
        }
      }
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Adapter returned an unexpected status: " + status,
        status.equals("COMPLETED"));

    output = null;

    // Remove service
    message = "{\"instance_uuid\":\"" + nsdPayload.getNsd().getInstanceUuid() + "\"}";
    topic = "infrastructure.service.remove";
    ServicePlatformMessage removeInstanceMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeInstanceMessage);
    try {
      while (output == null) {
        synchronized (mon) {
          mon.wait(2000);
          System.out.println(output);
        }
      }
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue("Adapter returned an unexpected status: " + status,
        status.equals("COMPLETED"));

    // Remove registered VIMs

    output = null;
    message = "{\"uuid\":\"" + computeWrUuid1 + "\"}";
    topic = "infrastructure.management.compute.remove";
    ServicePlatformMessage removeVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"uuid\":\"" + netWrUuid1 + "\"}";
    topic = "infrastructure.management.network.remove";
    ServicePlatformMessage removeNetVimMessage = new ServicePlatformMessage(message,
        "application/json", topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeNetVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"uuid\":\"" + computeWrUuid2 + "\"}";
    topic = "infrastructure.management.compute.remove";
    removeVimMessage = new ServicePlatformMessage(message, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"uuid\":\"" + netWrUuid2 + "\"}";
    topic = "infrastructure.management.network.remove";
    removeNetVimMessage = new ServicePlatformMessage(message, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(removeNetVimMessage);

    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    System.out.println(output);
    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    core.stop();


  }



  @Ignore
  public void testPrepareServicePayload() throws JsonProcessingException {

    ServicePreparePayload payload = new ServicePreparePayload();

    payload.setInstanceId(nsdPayload.getNsd().getInstanceUuid());
    ArrayList<VimPreDeploymentList> vims = new ArrayList<VimPreDeploymentList>();
    VimPreDeploymentList vimDepList = new VimPreDeploymentList();
    vimDepList.setUuid("aaaa-aaaaaaaaaaaaa-aaaaaaaaaaaaa-aaaaaaaa");
    ArrayList<VnfImage> vnfImages = new ArrayList<VnfImage>();
    VnfImage Image1 = new VnfImage("eu.sonata-nfv:1-vnf:0.1:1", "file:///test_images/sonata-1");
    VnfImage Image2 = new VnfImage("eu.sonata-nfv:2-vnf:0.1:1", "file:///test_images/sonata-2");
    VnfImage Image3 = new VnfImage("eu.sonata-nfv:3-vnf:0.1:1", "file:///test_images/sonata-3");
    VnfImage Image4 = new VnfImage("eu.sonata-nfv:4-vnf:0.1:1", "file:///test_images/sonata-4");
    vnfImages.add(Image1);
    vnfImages.add(Image2);
    vnfImages.add(Image3);
    vnfImages.add(Image4);
    vimDepList.setImages(vnfImages);
    vims.add(vimDepList);


    vimDepList = new VimPreDeploymentList();
    vimDepList.setUuid("bbbb-bbbbbbbbbbbb-bbbbbbbbbbbb-bbbbbbbbb");
    vnfImages = new ArrayList<VnfImage>();
    VnfImage Image5 = new VnfImage("eu.sonata-nfv:5-vnf:0.1:1", "file:///test_images/sonata-5");
    VnfImage Image6 = new VnfImage("eu.sonata-nfv:6-vnf:0.1:1", "file:///test_images/sonata-6");
    VnfImage Image7 = new VnfImage("eu.sonata-nfv:7-vnf:0.1:1", "file:///test_images/sonata-7");
    vnfImages.add(Image5);
    vnfImages.add(Image6);
    vnfImages.add(Image7);
    vimDepList.setImages(vnfImages);
    vims.add(vimDepList);

    payload.setVimList(vims);

    // System.out.println(mapper.writeValueAsString(payload));
  }


  public void receiveHeartbeat(ServicePlatformMessage message) {
    synchronized (mon) {
      this.lastHeartbeat = message.getBody();
      mon.notifyAll();
    }
  }

  public void receive(ServicePlatformMessage message) {
    synchronized (mon) {
      this.output = message.getBody();
      mon.notifyAll();
    }
  }

  public void forwardToConsumer(ServicePlatformMessage message) {
    consumer.injectMessage(message);
  }
}
