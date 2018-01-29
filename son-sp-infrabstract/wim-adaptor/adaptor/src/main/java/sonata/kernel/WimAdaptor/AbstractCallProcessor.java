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


import java.util.Observer;

import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;

public abstract class AbstractCallProcessor implements Runnable, Observer {

  public ServicePlatformMessage getMessage() {
    return message;
  }

  public String getSid() {
    return sid;
  }

  public WimAdaptorMux getMux() {
    return mux;
  }

  private ServicePlatformMessage message;
  private String sid;
  private WimAdaptorMux mux;

  /**
   * Abtract class for an API call processor. The processo runs on a thread an processes a
   * ServicePlatformMessage.
   * 
   * @param message The ServicePlatformMessage to process
   * @param sid the Session Identifier for this API call
   * @param mux the WimAdaptorMux where response messages are to be sent.
   */
  public AbstractCallProcessor(ServicePlatformMessage message, String sid, WimAdaptorMux mux) {
    this.message = message;
    this.sid = sid;
    this.mux = mux;
  }

  protected void sendToMux(ServicePlatformMessage message) {
    mux.enqueue(message);
  }

  @Override
  public void run() {

    this.process(message);

  }

  public abstract boolean process(ServicePlatformMessage message);

}
