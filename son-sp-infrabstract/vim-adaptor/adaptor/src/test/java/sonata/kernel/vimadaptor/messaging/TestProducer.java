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

package sonata.kernel.vimadaptor.messaging;

import sonata.kernel.vimadaptor.MessageReceiver;
import sonata.kernel.vimadaptor.messaging.AbstractMsgBusProducer;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;

import java.io.IOException;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;

public class TestProducer extends AbstractMsgBusProducer {

  private MessageReceiver output;

  public TestProducer(BlockingQueue<ServicePlatformMessage> muxQueue, MessageReceiver output) {
    super(muxQueue);
    this.output = output;
  }

  @Override
  public void connectToBus() throws IOException {
    // do nothing
  }

  @Override
  public boolean sendMessage(ServicePlatformMessage message) {
    System.out
        .println("[TestProducer] Topic: " + message.getTopic() + " - Message:" + message.getBody());
    if (message.getTopic().contains("infrastructure.management.compute")) {
      output.receive(message);
    }
    if (message.getTopic().contains("infrastructure.management.network")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.service.deploy")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.service.prepare")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.function.deploy")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.service.chain.configure")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.service.chain.deconfigure")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.wan.configure")) {
      output.receive(message);
    }
    if (message.getTopic().equals("infrastructure.service.remove")) {
      output.receive(message);
    }
    if (message.getTopic().equals("platform.management.plugin.register")) {
      String registrationResponse = "{\"status\":\"OK\",\"uuid\":\"" + UUID.randomUUID().toString()
          + "\",\"error\":\"none\"}";
      ServicePlatformMessage response = new ServicePlatformMessage(registrationResponse,
          "application/json", "platform.management.plugin.register", message.getSid(), null);
      output.forwardToConsumer(response);
    }
    if (message.getTopic().equals("platform.management.plugin.deregister")) {
      String registrationResponse = "{\"status\":\"OK\"}";
      ServicePlatformMessage response = new ServicePlatformMessage(registrationResponse,
          "application/json", "platform.management.plugin.deregister", message.getSid(), null);
      output.forwardToConsumer(response);
    }
    if (message.getTopic().contains("heartbeat")) {
      output.receiveHeartbeat(message);
    }
    return true;
  }

}
