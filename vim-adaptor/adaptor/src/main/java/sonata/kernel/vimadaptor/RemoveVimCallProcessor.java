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

import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperType;

import java.util.Observable;

public class RemoveVimCallProcessor extends AbstractCallProcessor {

  /**
   * Generate a CallProcessor to process an API call to create a new VIM wrapper
   * 
   * @param message the API call message
   * @param sid the session ID of thi API call
   * @param mux the Adaptor Mux to which send responses.
   */
  public RemoveVimCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    super(message, sid, mux);

  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    // process json message to get the wrapper type and UUID
    // and de-register it
    JSONTokener tokener = new JSONTokener(message.getBody());
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String[] topicSplit = message.getTopic().split("\\.");
    String wrTypeString = topicSplit[topicSplit.length - 2];
    String uuid = jsonObject.getString("uuid");
    if (uuid == null)
      this.sendResponse("{\"request_status\":\"ERROR\",\"message\":\"Malformed request\"}");
    WrapperType type = WrapperType.getByName(wrTypeString);
    String output = null;
    if (type.equals(WrapperType.COMPUTE)) {
      output = WrapperBay.getInstance().removeComputeWrapper(uuid);
    }
    if (type.equals(WrapperType.STORAGE)) {
      // TODO
      output = "";
    }
    if (type.equals(WrapperType.NETWORK)) {
      // TODO
      output = WrapperBay.getInstance().removeNetworkWrapper(uuid);
    }
    this.sendResponse(output);
    boolean out = true;
    return out;
  }

  @Override
  public void update(Observable observable, Object arg) {
    // This call does not need to be updated by any observable (wrapper).
  }

  private void sendResponse(String message) {
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/json",
        this.getMessage().getTopic(), this.getMessage().getSid(), this.getMessage().getReplyTo());
    this.sendToMux(spMessage);
  }
}
