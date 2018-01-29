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

package sonata.kernel.WimAdaptor.messaging;

import java.util.concurrent.BlockingQueue;

public abstract class AbstractMsgBusConsumer implements MsgBusConsumer {

  private BlockingQueue<ServicePlatformMessage> dispatcherQueue;

  /**
   * Create a MsgBusConsumer.
   * 
   * @param dispatcherQueue the queue in which enqueue incoming messages
   */
  public AbstractMsgBusConsumer(BlockingQueue<ServicePlatformMessage> dispatcherQueue) {
    this.dispatcherQueue = dispatcherQueue;
  }

  private void enqueue(ServicePlatformMessage message) {
    dispatcherQueue.add(message);
  }

  /**
   * process the message coming from the MsgBus and enqueue it towards the dispatcher.
   * 
   * @param message a string with the body of the message
   * @param topic from which the message has been received
   * @param the session id of the message
   * @param the topic to which reply
   */
  void processMessage(String message, String contentType, String topic, String sid,
      String replyTo) {
    // TODO process the string (or not, leaving the pre-processing to the
    // dispatcher?)
    ServicePlatformMessage spMessage =
        new ServicePlatformMessage(message, contentType, topic, sid, replyTo);
    this.enqueue(spMessage);
  }

}
