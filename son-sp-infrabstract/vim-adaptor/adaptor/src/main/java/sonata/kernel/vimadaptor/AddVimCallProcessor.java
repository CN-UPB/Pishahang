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
import sonata.kernel.vimadaptor.wrapper.ComputeVimVendor;
import sonata.kernel.vimadaptor.wrapper.NetworkVimVendor;
import sonata.kernel.vimadaptor.wrapper.VimVendor;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.WrapperType;

import java.util.Observable;
import java.util.UUID;

public class AddVimCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(AddVimCallProcessor.class);


  /**
   * Generate a CallProcessor to process an API call to create a new VIM wrapper
   * 
   * @param message the API call message
   * @param sid the session ID of thi API call
   * @param mux the Adaptor Mux to which send responses.
   */
  public AddVimCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    super(message, sid, mux);

  }

  @Override
  public boolean process(ServicePlatformMessage message) {

    // process json message to extract the new Wrapper configurations
    // and ask the bay to create and register it

    JSONTokener tokener = new JSONTokener(message.getBody());

    WrapperConfiguration config = new WrapperConfiguration();

    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    String[] topicSplit = message.getTopic().split("\\.");
    String wrTypeString = topicSplit[topicSplit.length - 2];
    WrapperType wrapperType = WrapperType.getByName(wrTypeString);
    String stringVimVendor = jsonObject.getString("vim_type");
    String vimEndpoint = jsonObject.getString("vim_address");
    String authUser = jsonObject.optString("username", "");
    String authPass = jsonObject.getString("pass");
    String city = jsonObject.getString("city");
    String domain = jsonObject.optString("domain", "");
    String name = jsonObject.getString("name");
    String country = jsonObject.getString("country");
    String configuration = jsonObject.getJSONObject("configuration").toString();

    String computeVimRef = null;
    VimVendor vimVendor = null;

    if (wrapperType.equals(WrapperType.COMPUTE)) {
      vimVendor = ComputeVimVendor.getByName(stringVimVendor);
    } else if (wrapperType.equals(WrapperType.NETWORK)) {
      // Logger.debug("Reading network-specific VIM parameters");
      tokener = new JSONTokener(configuration);
      jsonObject = (JSONObject) tokener.nextValue();
      computeVimRef = jsonObject.getString("compute_uuid");
      vimVendor = NetworkVimVendor.getByName(stringVimVendor);
    }
    config.setUuid(UUID.randomUUID().toString());
    config.setWrapperType(wrapperType);
    config.setVimVendor(vimVendor);
    config.setVimEndpoint(vimEndpoint);
    config.setAuthUserName(authUser);
    config.setAuthPass(authPass);
    config.setCity(city);
    config.setDomain(domain);
    config.setCountry(country);
    config.setConfiguration(configuration);
    config.setName(name);
    
    Logger.debug("Parsed Wrapper Configuration: ");
    System.out.println(config.toString());

    String output = null;
    boolean out = true;
    if (wrapperType.equals(WrapperType.COMPUTE)) {
      Logger.debug("Registering a COMPUTE wrapper.");
      output = WrapperBay.getInstance().registerComputeWrapper(config);
    } else if (wrapperType.equals(WrapperType.STORAGE)) {
      // TODO
      output = "";
    } else if (wrapperType.equals(WrapperType.NETWORK)) {
      Logger.debug("Registering a network VIM");
      output = WrapperBay.getInstance().registerNetworkWrapper(config, computeVimRef);
    }

    // Logger.debug("sending response.");
    this.sendResponse(output);

    return out;
  }

  // private void sendError(String message) {
  //
  // String jsonError =
  // "{\"status\":\"ERROR\",\"message\":\"" + message + "\"}";
  // ServicePlatformMessage spMessage = new ServicePlatformMessage(jsonError, "application/json",
  // this.getMessage().getTopic(), this.getMessage().getSid(), null);
  // this.sendToMux(spMessage);
  // }

  @Override
  public void update(Observable observable, Object arg) {
    // This call does not need to be updated by any observable (wrapper).
  }

  private void sendResponse(String message) {
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/json",
        this.getMessage().getTopic(), this.getMessage().getSid(), null);
    this.sendToMux(spMessage);
  }
}
