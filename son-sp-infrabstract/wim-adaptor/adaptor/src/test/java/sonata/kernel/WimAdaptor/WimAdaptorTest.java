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

package sonata.kernel.WimAdaptor;


import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;

import com.fasterxml.jackson.databind.ObjectMapper;

import sonata.kernel.WimAdaptor.commons.DeployServiceResponse;
import sonata.kernel.WimAdaptor.commons.SonataManifestMapper;
import sonata.kernel.WimAdaptor.commons.Status;
import sonata.kernel.WimAdaptor.commons.WimRecord;
import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;
import sonata.kernel.WimAdaptor.messaging.TestConsumer;
import sonata.kernel.WimAdaptor.messaging.TestProducer;
import sonata.kernel.WimAdaptor.wrapper.vtn.VtnClient;


/**
 * Unit test for simple App.
 */
public class WimAdaptorTest implements MessageReceiver {
  private String output = null;
  private Object mon = new Object();
  private TestConsumer consumer;
  private String lastHeartbeat;
  private ObjectMapper mapper;
  private DeployServiceResponse response;

  @Before
  public void setUp() throws IOException {
    StringBuilder bodyBuilder = new StringBuilder();
    BufferedReader in = new BufferedReader(
        new InputStreamReader(new FileInputStream(new File("./YAML/DeployResponseExample.yml")),
            Charset.forName("UTF-8")));
    String line;
    while ((line = in.readLine()) != null) {
      bodyBuilder.append(line + "\n\r");
    }
    in.close();
    this.mapper = SonataManifestMapper.getSonataMapper();

    response = mapper.readValue(bodyBuilder.toString(), DeployServiceResponse.class);

  }

  /**
   * Register, send 4 heartbeat, deregister.
   * 
   * @throws IOException
   */
  @Test
  public void testHeartbeating() throws IOException {
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    consumer = new TestConsumer(dispatcherQueue);
    WimAdaptorCore core = new WimAdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 2);
    int counter = 0;

    core.start();
    Assert.assertNotNull(core.getUuid());

    try {
      while (counter < 4) {
        synchronized (mon) {
          mon.wait();
          if (lastHeartbeat.contains("RUNNING")) counter++;
        }
      }
    } catch (Exception e) {
      Assert.assertTrue(false);
    }

    System.out.println("Heartbeats received");
    Assert.assertTrue(true);

    core.stop();
    Assert.assertTrue(core.getState().equals("STOPPED"));

  }

  /**
   * Create a VTNwrapper
   * 
   * @throws IOException
   */
  @Test
  public void testListWIM() throws InterruptedException, IOException {
    String message =
        "{\"wim_vendor\":\"VTN\",\"name\":\"Wan-area-1\",\"wim_address\":\"10.30.0.13\",\"username\":\"admin\",\"pass\":\"admin\"}";
    String topic = "infrastructure.management.wan.add";
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    ServicePlatformMessage addWimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer = new TestConsumer(dispatcherQueue);
    WimAdaptorCore core = new WimAdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.05);

    core.start();

    consumer.injectMessage(addWimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String uuid1 = jsonObject.getString("uuid");
    String status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    // Add a second WIM
    output = null;
    message =
        "{\"wim_vendor\":\"VTN\",\"name\":\"Wan-area-2\",\"wim_address\":\"10.20.0.12\",\"username\":\"admin\",\"pass\":\"admin\"}";
    topic = "infrastructure.management.wan.add";
    addWimMessage = new ServicePlatformMessage(message, "application/json", topic,
        UUID.randomUUID().toString(), topic);
    consumer.injectMessage(addWimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    tokener = new JSONTokener(output);
    jsonObject = (JSONObject) tokener.nextValue();
    String uuid2 = jsonObject.getString("uuid");
    status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    // attach 2 VIMs per WIM
    String vims[] = {"11111", "22222", "33333", "44444"};
    for (int i = 0; i < 2; i++) {
      message = "{\"wim_uuid\":\"" + uuid1 + "\",\"vim_uuid\":\""+vims[i]+"\",\"vim_address\":\""+vims[i]+"\"}";
      topic = "infrastructure.management.wan.attach";
      addWimMessage = new ServicePlatformMessage(message, "application/json", topic,
          UUID.randomUUID().toString(), topic);
      consumer.injectMessage(addWimMessage);
      Thread.sleep(2000);
      while (output == null) {
        synchronized (mon) {
          mon.wait(1000);
        }
      }

      tokener = new JSONTokener(output);
      jsonObject = (JSONObject) tokener.nextValue();
      status = jsonObject.getString("request_status");
      Assert.assertTrue("Status not completed: "+status,status.equals("COMPLETED"));
    }

    for (int i = 2; i < 4; i++) {
      message = "{\"wim_uuid\":\"" + uuid2 + "\",\"vim_uuid\":\""+vims[i]+"\",\"vim_address\":\""+vims[i]+"\"}";
      topic = "infrastructure.management.wan.attach";
      addWimMessage = new ServicePlatformMessage(message, "application/json", topic,
          UUID.randomUUID().toString(), topic);
      consumer.injectMessage(addWimMessage);
      Thread.sleep(2000);
      while (output == null) {
        synchronized (mon) {
          mon.wait(1000);
        }
      }

      tokener = new JSONTokener(output);
      jsonObject = (JSONObject) tokener.nextValue();
      status = jsonObject.getString("request_status");
      Assert.assertTrue(status.equals("COMPLETED"));
    }
    // List wim;
    output = null;
    message = null;
    topic = "infrastructure.management.wan.list";
    ServicePlatformMessage listWimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);

    consumer.injectMessage(listWimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }
    
    System.out.println("Lis results:\n" +output);
    WimRecord[] list = mapper.readValue(output, WimRecord[].class);

    for (WimRecord wim : list){
      System.out.println(wim);
      ArrayList<String> attachedVims = wim.getAttachedVims();
      if(wim.getUuid().equals(uuid1)){
        Assert.assertTrue(vims[0]+" not present", attachedVims.contains(vims[0]));
        Assert.assertTrue(vims[1]+" not present", attachedVims.contains(vims[1]));
      }
      if(wim.getUuid().equals(uuid2)){
        Assert.assertTrue(vims[2]+" not present", attachedVims.contains(vims[2]));
        Assert.assertTrue(vims[3]+" not present", attachedVims.contains(vims[3]));
      }
    }
    
    
    
  }
  /**
   * Create a VTNwrapper
   * 
   * @throws IOException
   */
  @Test
  public void testCreateMockWrapper() throws InterruptedException, IOException {
    String message =
        "{\"wim_vendor\":\"Mock\",\"name\":\"area-1\",\"wim_address\":\"10.30.0.13\",\"username\":\"admin\",\"pass\":\"admin\"}";
    String topic = "infrastructure.management.wan.add";
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer = new TestConsumer(dispatcherQueue);
    WimAdaptorCore core = new WimAdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.05);

    core.start();

    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String uuid = jsonObject.getString("uuid");
    String status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"wr_type\":\"WIM\",\"uuid\":\"" + uuid + "\"}";
    topic = "infrastructure.management.wan.remove";
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
    Assert.assertTrue(core.getState().equals("STOPPED"));
  }
  
  /**
   * Create a VTNwrapper
   * 
   * @throws IOException
   */
  @Test
  public void testCreateVTNWrapper() throws InterruptedException, IOException {
    String message =
        "{\"wim_vendor\":\"VTN\",\"name\":\"VTN-area-1\",\"wim_address\":\"10.30.0.13\",\"username\":\"admin\",\"pass\":\"admin\"}";
    String topic = "infrastructure.management.wan.add";
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    ServicePlatformMessage addVimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer = new TestConsumer(dispatcherQueue);
    WimAdaptorCore core = new WimAdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.05);

    core.start();

    consumer.injectMessage(addVimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String uuid = jsonObject.getString("uuid");
    String status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    message = "{\"wr_type\":\"WIM\",\"uuid\":\"" + uuid + "\"}";
    topic = "infrastructure.management.wan.remove";
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
    Assert.assertTrue(core.getState().equals("STOPPED"));
  }

  @Ignore
  public void configureService() throws IOException, InterruptedException {

    String message =
        "{\"wim_vendor\":\"VTN\",\"name\":\"VTN-area-1\",\"wim_address\":\"10.30.0.13\",\"username\":\"admin\",\"pass\":\"admin\"}";
    String topic = "infrastructure.management.wan.add";
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();

    TestProducer producer = new TestProducer(muxQueue, this);
    ServicePlatformMessage addWimMessage = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer = new TestConsumer(dispatcherQueue);
    WimAdaptorCore core = new WimAdaptorCore(muxQueue, dispatcherQueue, consumer, producer, 0.05);

    core.start();

    consumer.injectMessage(addWimMessage);
    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
    }

    JSONTokener tokener = new JSONTokener(output);
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String uuid = jsonObject.getString("uuid");
    String status = jsonObject.getString("request_status");
    Assert.assertTrue(status.equals("COMPLETED"));

    output = null;
    topic = "infrastructure.service.wan.configure";
    message = mapper.writeValueAsString(response);
    ServicePlatformMessage configService = new ServicePlatformMessage(message, "application/json",
        topic, UUID.randomUUID().toString(), topic);
    consumer.injectMessage(configService);

    Thread.sleep(2000);
    while (output == null) {
      synchronized (mon) {
        mon.wait(1000);
      }
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

    DeployServiceResponse response = mapper.readValue(output, DeployServiceResponse.class);
    Assert.assertTrue(response.getRequestStatus().equals("COMPLETED"));
    Assert.assertTrue(response.getNsr().getStatus() == Status.normal_operation);
    Assert.assertNull(response.getVimUuid());

    output = null;
    message = "{\"wr_type\":\"WIM\",\"uuid\":\"" + uuid + "\"}";
    topic = "infrastructure.management.wan.remove";
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
    status = jsonObject.getString("status");
    Assert.assertTrue(status.equals("COMPLETED"));

    core.stop();
    Assert.assertTrue(core.getState().equals("STOPPED"));

    // Clean the VTN

    VtnClient c = new VtnClient("10.30.0.13", "admin", "admin");
    boolean delete = c.deleteVtn(response.getNsr().getId());
    Assert.assertTrue("unable to delete the service configuration in VTN", delete);
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
