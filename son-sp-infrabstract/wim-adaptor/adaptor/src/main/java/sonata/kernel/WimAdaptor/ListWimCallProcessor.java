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

import java.util.ArrayList;
import java.util.Observable;

import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import sonata.kernel.WimAdaptor.commons.SonataManifestMapper;
import sonata.kernel.WimAdaptor.commons.WimRecord;
import sonata.kernel.WimAdaptor.messaging.ServicePlatformMessage;
import sonata.kernel.WimAdaptor.wrapper.WrapperBay;
import sonata.kernel.WimAdaptor.wrapper.WrapperRecord;

public class ListWimCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(ListWimCallProcessor.class);

  
  public ListWimCallProcessor(ServicePlatformMessage message, String sid, WimAdaptorMux mux) {
    super(message, sid, mux);
  }

  @Override
  public void update(Observable obs, Object arg) {
    // This call does not need to be updated by any observable (wrapper).
  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    Logger.info("Received a call on List WIM");
    // TODO
    // ArrayList<String> vimList = WrapperBay.getInstance().getComputeWrapperList();
    ArrayList<WimRecord> wimList = new ArrayList<WimRecord>();
    ArrayList<String> wimsUuid = WrapperBay.getInstance().getWimList();

    Logger.debug(wimsUuid.toString());

    for(String wim : wimsUuid){
      WrapperRecord wr = WrapperBay.getInstance().getWimRecordFromWimUuid(wim);
     
      if(wr==null){
        this.sendToMux(new ServicePlatformMessage("{\"request_status\":\"ERROR\"}", "application/json", message.getReplyTo(), message.getSid(), null));
        return false;
      }
      WimRecord out = new WimRecord();
      //Logger.debug(wr.toString());
      out.setUuid(wr.getConfig().getUuid());
      out.setName(wr.getConfig().getName());
      ArrayList<String> attachedVims = WrapperBay.getInstance().getAttachedVims(wim);
      out.setAttachedVims(attachedVims);
      wimList.add(out);
    }

    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();
    String body;
    try {
      body = mapper.writeValueAsString(wimList);


      ServicePlatformMessage response = new ServicePlatformMessage(body, "application/x-yaml",
          this.getMessage().getReplyTo(), this.getSid(), null);

      this.getMux().enqueue(response);
      return true;
    } catch (JsonProcessingException e) {
      ServicePlatformMessage response =
          new ServicePlatformMessage("{\"status\":\"ERROR\",\"message\":\"Internal Server Error\"}",
              "application/json", this.getMessage().getReplyTo(), this.getSid(), null);
      this.getMux().enqueue(response);
      return false;
    }
  }

}
