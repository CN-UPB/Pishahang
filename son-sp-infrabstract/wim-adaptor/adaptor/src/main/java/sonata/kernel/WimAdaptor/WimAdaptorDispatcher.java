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

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;


public class WimAdaptorDispatcher implements Runnable {

  private BlockingQueue<ServicePlatformMessage> myQueue;
  private Executor myThreadPool;
  private boolean stop = false;
  private WimAdaptorMux mux;
  private WimAdaptorCore core;

  /**
   * Create an WimAdaptorDispatcher attached to the queue. CallProcessor will be bind to the
   * provided mux.
   * 
   * @param queue the queue the dispatcher is attached to
   * 
   * @param mux the WimAdaptorMux the CallProcessors will be attached to
   */
  public WimAdaptorDispatcher(BlockingQueue<ServicePlatformMessage> queue, WimAdaptorMux mux,
      WimAdaptorCore core) {
    myQueue = queue;
    myThreadPool = Executors.newCachedThreadPool();
    this.mux = mux;
    this.core = core;
  }

  @Override
  public void run() {
    ServicePlatformMessage message;
    do {
      try {
        message = myQueue.take();

        if (isRegistrationResponse(message)) {
          this.core.handleRegistrationResponse(message);
        } else if (isDeregistrationResponse(message)) {
          this.core.handleDeregistrationResponse(message);
        } else if (!isWanMessage(message)){
          continue;
        }else {
          if (message.getTopic().endsWith("wan.add")) {
            myThreadPool.execute(new AddWimCallProcessor(message, message.getSid(), mux));
          } else if (message.getTopic().endsWith("wan.remove")) {
            myThreadPool.execute(new RemoveWimCallProcessor(message, message.getSid(), mux));
          } else if (message.getTopic().endsWith("wan.configure")) {
            myThreadPool.execute(new ConfigureWimCallProcessor(message, message.getSid(), mux));
          }else if (message.getTopic().endsWith("wan.deconfigure")) {
            myThreadPool.execute(new DeconfigureWimCallProcessor(message, message.getSid(), mux));
          } else if (message.getTopic().endsWith("wan.list")) {
            myThreadPool.execute(new ListWimCallProcessor(message, message.getSid(), mux));
          } else if (message.getTopic().endsWith("wan.attach")){
            myThreadPool.execute(new AttachVimCallProcessor(message, message.getSid(), mux));            
          }
        }
      } catch (InterruptedException e) {
        e.printStackTrace();
      }
    } while (!stop);
  }

  private boolean isWanMessage(ServicePlatformMessage message) {
    return message.getTopic().contains(".wan.");
  }

  // private void handleManagementMessage(ServicePlatformMessage message) {
  //
  // }


  private boolean isRegistrationResponse(ServicePlatformMessage message) {
    return message.getTopic().equals("platform.management.plugin.register")
        && message.getSid().equals(core.getRegistrationSid());
  }

  private boolean isDeregistrationResponse(ServicePlatformMessage message) {
    return message.getTopic().equals("platform.management.plugin.deregister")
        && message.getSid().equals(core.getRegistrationSid());
  }

  public void start() {
    Thread thread = new Thread(this);
    thread.start();
  }

  public void stop() {
    this.stop = true;
  }
}
