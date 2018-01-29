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

package sonata.kernel.WimAdaptor;

import java.util.ArrayList;
import java.util.Observable;

import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.ObjectMapper;

import sonata.kernel.WimAdaptor.commons.ConfigureWanPayload;
import sonata.kernel.WimAdaptor.commons.DeconfigureWanPayload;
import sonata.kernel.WimAdaptor.commons.SonataManifestMapper;
import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;
import sonata.kernel.WimAdaptor.wrapper.WimWrapper;
import sonata.kernel.WimAdaptor.wrapper.WrapperBay;
import sonata.kernel.WimAdaptor.wrapper.WrapperRecord;

public class DeconfigureWimCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(DeconfigureWimCallProcessor.class);

  public DeconfigureWimCallProcessor(ServicePlatformMessage message, String sid,
      WimAdaptorMux mux) {
    super(message, sid, mux);
    // TODO Auto-generated constructor stub
  }

  @Override
  public void update(Observable arg0, Object arg1) {
    // TODO Auto-generated method stub

  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    DeconfigureWanPayload request = null;
    boolean out = true;
    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();
    try {
      request = mapper.readValue(message.getBody(), DeconfigureWanPayload.class);
      Logger.info("payload parsed");
    } catch (Exception e) {
      Logger.error("Error parsing the wan configure payload: " + e.getMessage(), e);
      this.sendToMux(new ServicePlatformMessage(
          "{\"request_status\":\"fail\",\"message\":\"Payload parse error\"}", "application/json",
          message.getReplyTo(), message.getSid(), null));
      out = false;
      return out;
    }
    Logger.debug("Received request: ");
    Logger.debug(message.getBody());
    String instanceId = request.getServiceInstanceId();
    
    ArrayList<String> wimList = WrapperBay.getInstance().getWimList();
    
    for(String wimUuid: wimList){
      WimWrapper wim = (WimWrapper) WrapperBay.getInstance().getWimRecordFromWimUuid(wimUuid).getWimWrapper();
      wim.removeNetConfiguration(instanceId);
    }

    this.sendToMux(new ServicePlatformMessage(
      "{\"request_status\":\"COMPLETED\",\"message\":\"\"}", "application/json",
      message.getReplyTo(), message.getSid(), null));
    return true;
  }

}
