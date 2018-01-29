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

import java.util.Observable;
import java.util.UUID;

import org.json.JSONObject;
import org.json.JSONTokener;

import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;
import sonata.kernel.WimAdaptor.wrapper.WimVendor;
import sonata.kernel.WimAdaptor.wrapper.WrapperBay;
import sonata.kernel.WimAdaptor.wrapper.WrapperConfiguration;

public class AddWimCallProcessor extends AbstractCallProcessor {

  /**
   * Generate a CallProcessor to process an API call to create a new VIM wrapper
   * 
   * @param message the API call message
   * @param sid the session ID of thi API call
   * @param mux the Adaptor Mux to which send responses.
   */
  public AddWimCallProcessor(ServicePlatformMessage message, String sid, WimAdaptorMux mux) {
    super(message, sid, mux);

  }

  @Override
  public boolean process(ServicePlatformMessage message) {

    // process json message to extract the new Wrapper configurations
    // and ask the bay to create and register it

    JSONTokener tokener = new JSONTokener(message.getBody());

    WrapperConfiguration config = new WrapperConfiguration();

    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    //String wrapperType = jsonObject.getString("WIM");
    String wimVendor = jsonObject.getString("wim_vendor");
    String vimEndpoint = jsonObject.getString("wim_address");
    String authUser = jsonObject.getString("username");
    String name = jsonObject.getString("name");
    String authPass = jsonObject.getString("pass");
    // JSONArray jsonServicedSegments = jsonObject.getJSONArray("serviced_segments");
    // ArrayList<String> servicedSegments = new ArrayList<String>();

    config.setUuid(UUID.randomUUID().toString());
    config.setWrapperType("WIM");
    config.setWimVendor(WimVendor.getByName(wimVendor));
    config.setWimEndpoint(vimEndpoint);
    config.setAuthUserName(authUser);
    config.setAuthPass(authPass);
    config.setName(name);
    String output = null;
    boolean out = true;

    output = WrapperBay.getInstance().registerWrapper(config);

    this.sendResponse(output);

    return out;
  }

  // private void sendError(String message) {
  //
  // String jsonError =
  // "{\"status\":\"error,\"sid\":\"" + this.getSid() + "\",\"message\":\"" + message + "\"}";
  // ServicePlatformMessage spMessage = new ServicePlatformMessage(jsonError, "application/json",
  // this.getMessage().getTopic(), this.getMessage().getSid(), null);
  // this.sendToMux(spMessage);
  // }

  private void sendResponse(String message) {
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/json",
        this.getMessage().getTopic(), this.getMessage().getSid(), null);
    this.sendToMux(spMessage);
  }

  @Override
  public void update(Observable observable, Object arg) {
    // This call does not need to be updated by any observable (wrapper).
  }
}
