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

import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperStatusUpdate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Observable;

public class RemoveServiceCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(RemoveServiceCallProcessor.class);
  private boolean errorsHappened;
  private ArrayList<String> wrapperQueue;

  /**
   * Generate a CallProcessor to process an API call to create a new VIM wrapper
   * 
   * @param message the API call message
   * @param sid the session ID of thi API call
   * @param mux the Adaptor Mux to which send responses.
   */
  public RemoveServiceCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    super(message, sid, mux);
    this.errorsHappened = false;
  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    // process json message to get the service UUID
    // and remove it
    JSONTokener tokener = new JSONTokener(message.getBody());
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String instanceUuid = jsonObject.getString("instance_uuid");
    String[] vimUuidList =
        WrapperBay.getInstance().getVimRepo().getComputeVimUuidFromInstance(instanceUuid);
    if (vimUuidList == null || vimUuidList.length == 0) {
      this.sendResponse(
          "{\"request_status\":\"WARNING\",\"message\":\"can't find instance UUID or associated VIMs in Infrastructure repository\"}");
      return false;
    }
    this.wrapperQueue = new ArrayList<String>(Arrays.asList(vimUuidList));
    Logger.debug("List of VIMs hosting the service: ");
    Logger.debug(wrapperQueue.toString());
    for (String vimUuid : vimUuidList) {
      ComputeWrapper wr = WrapperBay.getInstance().getComputeWrapper(vimUuid);
      if (wr == null) {
        Logger.warn("Error retrieving the wrapper");

        this.sendToMux(new ServicePlatformMessage(
            "{\"request_status\":\"WARNING\",\"message\":\"can't build a wrapper for VIM UUID "
                + vimUuid + "\"}",
            "application/json", message.getReplyTo(), message.getSid(), null));
        // return false;
        continue;
      }
      wr.addObserver(this);
      wr.removeService(instanceUuid, this.getSid());
    }
    boolean out = true;
    return out;
  }

  @Override
  public void update(Observable observable, Object arg) {

    WrapperStatusUpdate update = (WrapperStatusUpdate) arg;
    if (update.getSid() == null) {
      Logger.warn("Wrapper Update message with no SID.");
      return;
    }
    if (!update.getSid().equals(this.getSid())) return;
    Logger.info("Received an update:\n" + update.getBody());

    String updateStatus = update.getStatus();

    if (updateStatus.equals("SUCCESS")) {
      
      JSONTokener tokener = new JSONTokener(update.getBody());
      JSONObject jsonObject = (JSONObject) tokener.nextValue();
      String wrapperId = jsonObject.getString("wrapper_uuid");
      String status = jsonObject.getString("status");
      if (wrapperQueue.remove(wrapperId)) {
        Logger.debug("wrapperSuccesfully dequeued.");
      } else {
        Logger.error("Error removing the service. " + status);
        this.errorsHappened = true;
      }
    }

    if (wrapperQueue.size() == 0) {
      if (!errorsHappened) {
        sendResponse("{\"request_status\":\"COMPLETED\",\"message\":\"\"}");
      } else {
        sendResponse("{\"request_status\":\"ERROR\",\"message\":\"\"}");
      }
      return;
    }
  }

  private void sendResponse(String message) {
    if (this.getMessage().getReplyTo() != null) {
      ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/json",
          this.getMessage().getReplyTo(), this.getMessage().getSid(), null);
      this.sendToMux(spMessage);
    }
  }
}
