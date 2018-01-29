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

import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.NetworkDeconfigurePayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.NetworkWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;

import java.io.IOException;
import java.util.Observable;

public class DeconfigureNetworkCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(DeployFunctionCallProcessor.class);

  /**
   * @param message
   * @param sid
   * @param mux
   */
  public DeconfigureNetworkCallProcessor(ServicePlatformMessage message, String sid,
      AdaptorMux mux) {
    super(message, sid, mux);
  }

  /*
   * (non-Javadoc)
   * 
   * @see sonata.kernel.vimadaptor.AbstractCallProcessor#process(sonata.kernel.vimadaptor.messaging.
   * ServicePlatformMessage)
   */
  @Override
  public boolean process(ServicePlatformMessage message) {

    NetworkDeconfigurePayload data = null;
    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();
    try {
      data = mapper.readValue(message.getBody(), NetworkDeconfigurePayload.class);
      Logger.info("payload parsed");
    } catch (IOException e) {
      Logger.error("Unable to parse the payload received");
      String responseJson =
          "{\"request_status\":\"ERROR\",\"message\":\"Unable to parse API payload\"}";
      this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
          message.getReplyTo(), message.getSid(), null));
      return false;
    }
    Logger.info(
        "Received networking.deconfigure call for service instance " + data.getServiceInstanceId());

    String[] computeUuids = WrapperBay.getInstance().getVimRepo()
        .getComputeVimUuidFromInstance(data.getServiceInstanceId());

    for (String computeVimUuid : computeUuids) {
      NetworkWrapper netVim =
          WrapperBay.getInstance().getNetworkVimFromComputeVimUuid(computeVimUuid);
      if (netVim == null) {
        continue;
        // TODO: Uncomment once Kubernetes wrapper is attached to a network wrapper
        /*Logger.error(
            "Unable to deconfigure networking. Cannot find NetVim associated with compute vim "
                + computeVimUuid);
        String responseJson =
            "{\"request_status\":\"ERROR\",\"message\":\"Internal Server Error. Can't deconfigure networking.\"}";
        this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
            message.getReplyTo(), message.getSid(), null));
        return false;*/
      }
      try {
        netVim.deconfigureNetworking(data.getServiceInstanceId());
      } catch (Exception e) {
        Logger.error("Unable to deconfigure networking on VIM: " + netVim.getConfig().getUuid(), e);
        String responseJson =
            "{\"request_status\":\"ERROR\",\"message\":\"" + e.getMessage() + "\"}";
        this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
            message.getReplyTo(), message.getSid(), null));
        return false;
      }
    }


    String responseJson = "{\"request_status\":\"COMPLETED\",\"message\":\"\"}";
    this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
        message.getReplyTo(), message.getSid(), null));
    return true;
  }

  /*
   * (non-Javadoc)
   * 
   * @see java.util.Observer#update(java.util.Observable, java.lang.Object)
   */
  @Override
  public void update(Observable arg0, Object arg1) {

  }

}
