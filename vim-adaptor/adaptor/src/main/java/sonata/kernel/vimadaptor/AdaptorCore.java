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
 * @author Michael Bredel (Ph.D.), NEC
 */

package sonata.kernel.vimadaptor;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.messaging.AbstractMsgBusConsumer;
import sonata.kernel.vimadaptor.messaging.AbstractMsgBusProducer;
import sonata.kernel.vimadaptor.messaging.MsgBusConsumer;
import sonata.kernel.vimadaptor.messaging.MsgBusProducer;
import sonata.kernel.vimadaptor.messaging.RabbitMqConsumer;
import sonata.kernel.vimadaptor.messaging.RabbitMqProducer;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.VimRepo;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.Properties;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;



public class AdaptorCore {

  public static final String APP_ID = "sonata.kernel.InfrAdaptor";
  private static AdaptorCore core;
  private static final String description = "Service Platform Infrastructure Adaptor";
  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(AdaptorCore.class);
  private static final String version = "0.0.1";
  private static final int writeLockCoolDown = 100000;
  private static final String SONATA_CONFIG_FILEPATH = "/etc/son-mano/sonata.config";
  private static AdaptorCore myInstance = null;
  private Properties sonataProperties;

  
  public static AdaptorCore getInstance(){
   if (myInstance == null){
     myInstance = new AdaptorCore(0.1);
   } 
   return myInstance;
  }
  
  
  public Object getSystemParameter(String key){
    return sonataProperties.getProperty(key);
  }
  
  /**
   * Main method. param args the adaptor take no args.
   */
  public static void main(String[] args) throws IOException {
    // System.setProperty("log4j.logger.httpclient.wire.header", "WARN");
    // System.setProperty("log4j.logger.httpclient.wire.content", "WARN");
    System.setProperty("org.apache.commons.logging.Log",
        "org.apache.commons.logging.impl.SimpleLog");

    System.setProperty("org.apache.commons.logging.simplelog.showdatetime", "false");

    System.setProperty("org.apache.commons.logging.simplelog.log.httpclient.wire.header", "warn");

    System.setProperty("org.apache.commons.logging.simplelog.log.org.apache.commons.httpclient",
        "warn");
    
    Runtime.getRuntime().addShutdownHook(new Thread() {
      @Override
      public void run() {
        if(AdaptorCore.getInstance().getState().equals("RUNNNING"))
          AdaptorCore.getInstance().stop();
      }
    });
    AdaptorCore.getInstance().start();
    
  }

  private AdaptorDispatcher dispatcher;
  private HeartBeat heartbeat;
  private AdaptorMux mux;
  private MsgBusConsumer northConsumer;

  private MsgBusProducer northProducer;
  private double rate;
  private String registrationSid;
  private String status;


  private String uuid;

  private Object writeLock = new Object();

  /**
   * utility constructor for Tests. Allows attaching mock MsgBus to the adaptor plug-in Manager.
   * 
   * @param muxQueue A Java BlockingQueue for the AdaptorMux
   * @param dispatcherQueue A Java BlockingQueue for the AdaptorDispatcher
   * @param consumer The consumer queuing messages in the dispatcher queue
   * @param producer The producer de-queuing messages from the mux queue
   * @param rate of the heart-beat in beat/s
   */
  public AdaptorCore(BlockingQueue<ServicePlatformMessage> muxQueue,
      BlockingQueue<ServicePlatformMessage> dispatcherQueue, AbstractMsgBusConsumer consumer,
      AbstractMsgBusProducer producer, double rate) {
    mux = new AdaptorMux(muxQueue);
    dispatcher = new AdaptorDispatcher(dispatcherQueue, mux, this);
    northConsumer = consumer;
    northProducer = producer;
    VimRepo repo = new VimRepo();
    WrapperBay.getInstance().setRepo(repo);
    status = "READY";
    this.rate = rate;
    this.sonataProperties = parseConfigFile();
  }

  /**
   * Create an AdaptorCore ready to use. No services are started.
   * 
   * @param rate of the heart-beat in beat/s
   */
  private AdaptorCore(double rate) {
    
    this.sonataProperties = parseConfigFile();
    
    this.rate = rate;
    // instantiate the Adaptor:
    // - Mux and queue
    BlockingQueue<ServicePlatformMessage> muxQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    mux = new AdaptorMux(muxQueue);

    // - Dispatcher and queue
    BlockingQueue<ServicePlatformMessage> dispatcherQueue =
        new LinkedBlockingQueue<ServicePlatformMessage>();
    dispatcher = new AdaptorDispatcher(dispatcherQueue, mux, this);

    // - Wrapper bay connection with the Database.
    VimRepo repo = new VimRepo();
    WrapperBay.getInstance().setRepo(repo);

    // - Northbound interface

    northConsumer = new RabbitMqConsumer(dispatcherQueue);
    northProducer = new RabbitMqProducer(muxQueue);
    
    status = "RUNNING";

  }

  /**
   * return the session ID of the registration message used to register this plugin to the
   * plugin-manager.
   * 
   * @return the session ID
   */
  public String getRegistrationSid() {
    return registrationSid;
  }

  /**
   * @return The status of this plug-in.
   */
  public String getState() {
    return this.status;
  }



  /**
   * @return this plug-in UUID.
   */
  public String getUuid() {
    return this.uuid;
  }

  /**
   * Handle the DeregistrationResponse message from the MANO Plugin Manager.
   * 
   * @param message the response message
   */
  public void handleDeregistrationResponse(ServicePlatformMessage message) {
    Logger.info("Received the deregistration response from the pluginmanager");
    JSONTokener tokener = new JSONTokener(message.getBody());
    JSONObject object = (JSONObject) tokener.nextValue();
    String status = object.getString("status");
    if (status.equals("OK")) {
      synchronized (writeLock) {
        writeLock.notifyAll();
      }
    } else {
      Logger.error("Failed to deregister to the plugin manager");
      this.status = "FAILED";
    }

  }

  /**
   * Handle the RegistrationResponse message from the MANO Plugin Manager.
   * 
   * @param message the response message
   */
  public void handleRegistrationResponse(ServicePlatformMessage message) {
    Logger.info("Received the registration response from the pluginmanager");
    JSONTokener tokener = new JSONTokener(message.getBody());
    JSONObject object = (JSONObject) tokener.nextValue();
    String status = object.getString("status");
    String pid = object.getString("uuid");
    if (status.equals("OK")) {
      synchronized (writeLock) {
        uuid = pid;
        writeLock.notifyAll();
      }
    } else {
      String error = object.getString("error");
      Logger.error("Failed to register to the plugin manager");
      Logger.error("Message: " + error);
    }

  }


  /**
   * Start the adaptor engines. Starts reading messages from the MsgBus
   * 
   * @throws IOException when something goes wrong in the MsgBus plug-in
   */
  public void start() throws IOException {
    // Start the message plug-in
    northProducer.connectToBus();
    northConsumer.connectToBus();
    northProducer.startProducing();
    northConsumer.startConsuming();

    dispatcher.start();

    register();
    status = "RUNNING";
    // - Start pumping blood
    this.heartbeat = new HeartBeat(mux, rate, this);
    new Thread(this.heartbeat).start();
  }

  /**
   * Stop the engines: Message production and consumption, heart-beat.
   */
  public void stop() {
    this.deregister();
    this.heartbeat.stop();
    northProducer.stopProducing();
    northConsumer.stopConsuming();
    dispatcher.stop();
  }

  private void deregister() {
    String body = "{\"uuid\":\"" + this.uuid + "\"}";
    String topic = "platform.management.plugin.deregister";
    ServicePlatformMessage message = new ServicePlatformMessage(body, "application/json", topic,
        java.util.UUID.randomUUID().toString(), topic);
    synchronized (writeLock) {
      try {
        this.registrationSid = message.getSid();
        mux.enqueue(message);
        writeLock.wait(writeLockCoolDown);
      } catch (InterruptedException e) {
        Logger.error(e.getMessage(), e);
      }
    }
    this.status = "STOPPED";
  }

  private void register() {
    String body = "{\"name\":\"" + AdaptorCore.APP_ID + "\",\"version\":\"" + AdaptorCore.version
        + "\",\"description\":\"" + AdaptorCore.description + "\"}";
    String topic = "platform.management.plugin.register";
    ServicePlatformMessage message = new ServicePlatformMessage(body, "application/json", topic,
        java.util.UUID.randomUUID().toString(), topic);
    synchronized (writeLock) {
      try {
        this.registrationSid = message.getSid();
        mux.enqueue(message);
        writeLock.wait(writeLockCoolDown);
      } catch (InterruptedException e) {
        Logger.error(e.getMessage(), e);
      }
    }
  }
  
  private static Properties parseConfigFile() {
    Logger.debug("Parsing sonata.config conf file");
    Properties prop = new Properties();
    try {
      InputStreamReader in =
          new InputStreamReader(new FileInputStream(SONATA_CONFIG_FILEPATH), Charset.forName("UTF-8"));

      JSONTokener tokener = new JSONTokener(in);

      JSONObject jsonObject = (JSONObject) tokener.nextValue();

      String brokerUrl = jsonObject.getString("sonata_sp_address");
      prop.put("sonata_sp_address", brokerUrl);
    } catch (FileNotFoundException e) {
      Logger.error("Unable to load Broker Config file", e);
      System.exit(1);
    }
    Logger.debug("sonata.config conf file parsed");
    return prop;
  }
  
}
