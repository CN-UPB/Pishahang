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

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.commons.VimResources;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;

import java.util.ArrayList;
import java.util.Observable;

public class ListComputeVimCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(ListComputeVimCallProcessor.class);

  public ListComputeVimCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    super(message, sid, mux);
  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    Logger.info("Retrieving VIM list from vim repository");
    ArrayList<String> vimList = WrapperBay.getInstance().getComputeWrapperList();
    Logger.info("Found " + vimList.size() + " VIMs");
    Logger.info("Retrieving VIM(s) resource utilisation");
    ArrayList<VimResources> resList = new ArrayList<VimResources>();
    for (String vimUuid : vimList) {
      ComputeWrapper wr = WrapperBay.getInstance().getComputeWrapper(vimUuid);
      if (wr == null) {
        Logger.warn("Error retrieving the wrapper");

        this.sendToMux(new ServicePlatformMessage(
            "{\"request_status\":\"fail\",\"message\":\"VIM not found\"}", "application/json",
            message.getReplyTo(), message.getSid(), null));
        return false;
      }
      ResourceUtilisation resource = wr.getResourceUtilisation();

      if (resource != null) {

        VimResources bodyElement = new VimResources();

        bodyElement.setVimUuid(vimUuid);
        bodyElement.setVimCity(wr.getConfig().getCity());
        bodyElement.setVimDomain(wr.getConfig().getDomain());
        bodyElement.setVimName(wr.getConfig().getName());
        bodyElement.setVimType(wr.getConfig().getVimVendor().toString());
        bodyElement.setVimEndpoint(wr.getConfig().getVimEndpoint());
        bodyElement.setCoreTotal(resource.getTotCores());
        bodyElement.setCoreUsed(resource.getUsedCores());
        bodyElement.setMemoryTotal(resource.getTotMemory());
        bodyElement.setMemoryUsed(resource.getUsedMemory());
        resList.add(bodyElement);
      } else {
        VimResources bodyElement = new VimResources();

        bodyElement.setVimUuid(vimUuid);
        bodyElement.setVimCity(wr.getConfig().getCity());
        bodyElement.setVimDomain(wr.getConfig().getDomain());
        bodyElement.setVimName(wr.getConfig().getName());
        bodyElement.setVimType(wr.getConfig().getVimVendor().toString());
        bodyElement.setVimEndpoint(wr.getConfig().getVimEndpoint());
        bodyElement.setCoreTotal(-1);
        bodyElement.setCoreUsed(-1);
        bodyElement.setMemoryTotal(-1);
        bodyElement.setMemoryUsed(-1);
        resList.add(bodyElement);
      }
    }

    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();

    String body;
    try {
      Logger.info("Sending back response...");
      body = mapper.writeValueAsString(resList);

      ServicePlatformMessage response = new ServicePlatformMessage(body, "application/x-yaml",
          this.getMessage().getReplyTo(), this.getSid(), null);

      this.getMux().enqueue(response);
      Logger.info("List VIM call completed.");
      return true;
    } catch (JsonProcessingException e) {
      ServicePlatformMessage response = new ServicePlatformMessage(
          "{\"request_status\":\"ERROR\",\"message\":\"Internal Server Error\"}",
          "application/json", this.getMessage().getReplyTo(), this.getSid(), null);
      this.getMux().enqueue(response);
      return false;
    }
  }

  @Override
  public void update(Observable obs, Object arg) {
    // This call does not need to be updated by any observable (wrapper).
  }

}
