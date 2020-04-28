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

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;

import java.util.UUID;

public class HeartBeat implements Runnable {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(HeartBeat.class);
  private AdaptorCore core;
  private AdaptorMux mux;
  private double rate; // measured in beat/s

  private boolean stop;

  /**
   * Create the Heart-beat runnable.
   * 
   * @param mux the mux to which send the outgoing messages.
   * @param rate the rate of the heart-beat
   * @param core the AdaptorCore which created this heart-beat
   */
  public HeartBeat(AdaptorMux mux, double rate, AdaptorCore core) {
    this.mux = mux;
    this.rate = rate;
    this.core = core;
  }

  @Override
  public void run() {
    String uuid = core.getUuid();
    while (!stop) {
      try {
        String body = "{\"uuid\":\"" + uuid + "\",\"state\":\"" + core.getState() + "\"}";
        ServicePlatformMessage message = new ServicePlatformMessage(body, "application/json",
            "platform.management.plugin." + uuid + ".heartbeat", UUID.randomUUID().toString(),
            null);
        mux.enqueue(message);
        Thread.sleep((int) ((1 / rate) * 1000));
      } catch (InterruptedException e) {
        Logger.error(e.getMessage(), e);
      }
    }

  }

  public void stop() {
    this.stop = true;

  }

}
