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

import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.LoggerFactory;

import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;
import sonata.kernel.WimAdaptor.wrapper.WrapperBay;

public class AttachVimCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(AttachVimCallProcessor.class);

  
  public AttachVimCallProcessor(ServicePlatformMessage message, String sid, WimAdaptorMux mux) {
    super(message, sid, mux);
  }

  @Override
  public void update(Observable arg0, Object arg1) {
    // Nothing to do here
  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    JSONTokener tokener = new JSONTokener(message.getBody());
    Logger.info("Request received to attach VIM to WIM");
    JSONObject jsonObject = (JSONObject) tokener.nextValue();
    // String wrapperType = jsonObject.getString("WIM");
    if (!(jsonObject.has("wim_uuid") && jsonObject.has("vim_uuid")
        && jsonObject.has("vim_address"))) {
      sendResponse("{\"request_status\":\"ERROR\",\"message\":\"Malformed request\"}");
      return false;
    }

    String wimUuid = jsonObject.getString("wim_uuid");
    String vimUuid = jsonObject.getString("vim_uuid");
    String vimAddress = jsonObject.getString("vim_address");

    String result = WrapperBay.getInstance().attachVim(wimUuid, vimUuid, vimAddress);
    this.sendResponse(result);
    return true;
  }

  private void sendResponse(String message) {
    ServicePlatformMessage spMessage = new ServicePlatformMessage(message, "application/json",
        this.getMessage().getTopic(), this.getMessage().getSid(), null);
    this.sendToMux(spMessage);
  }

}
