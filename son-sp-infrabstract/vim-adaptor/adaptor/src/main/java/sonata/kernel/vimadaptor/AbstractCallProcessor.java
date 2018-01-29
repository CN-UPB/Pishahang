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



import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;

import java.util.Observer;
import java.util.UUID;

public abstract class AbstractCallProcessor implements Runnable, Observer {

  private ServicePlatformMessage message;

  private AdaptorMux mux;

  private String sid;

  /**
   * Abstract class for an API call processor. The processor runs on a thread an processes a
   * ServicePlatformMessage.
   * 
   * @param message The ServicePlatformMessage to process
   * @param sid the Session Identifier for this API call
   * @param mux the AdaptorMux where response messages are to be sent.
   */
  public AbstractCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    this.message = message;
    if (sid != null) {
      this.sid = sid;
    } else {
      this.sid = UUID.randomUUID().toString();
    }
    this.mux = mux;
  }

  /**
   * Getter for the Message handled by the processor.
   * 
   * @return the ServicePlatformMessage object representing the message.
   */
  public ServicePlatformMessage getMessage() {
    return message;
  }

  /**
   * Getter for multiplexer used by this processor to publish messages.
   * 
   * @return an AdaptorMux object.
   */
  public AdaptorMux getMux() {
    return mux;
  }

  /**
   * Getter for the session ID of the call handled by the processor.
   * 
   * @return a String object representing the session id.
   */
  public String getSid() {
    return sid;
  }

  /**
   * This method implements the actuall processing of the API call.
   * 
   * @param message The ServicePlatformMessage to process
   * 
   */
  public abstract boolean process(ServicePlatformMessage message);

  @Override
  public void run() {

    this.process(message);

  }

  protected void sendToMux(ServicePlatformMessage message) {
    mux.enqueue(message);
  }

}
