/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA ALL RIGHTS RESERVED.
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
 * Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION] nor the names of its
 * contributors may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Sharon Mendel-Brin, Nokia
 */

package sonata.kernel.vimadaptor;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.FunctionScalePayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;

import java.util.Observable;

/**
 * Created by smendel on 2017.
 */
public class ScaleFunctionCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(ScaleFunctionCallProcessor.class);
  private FunctionScalePayload data;

  public ScaleFunctionCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
    super(message, sid, mux);
  }

  @Override
  public boolean process(ServicePlatformMessage message) {
    boolean out = true;
    Logger.info("Scale function call received by call processor.");
    // parse the payload to get Wrapper UUID and NSD/VNFD from the request body
    data = null;
    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();
    try {
      Logger.info("Parsing scaling payload...");
      data = mapper.readValue(message.getBody(), FunctionScalePayload.class);
      Logger.info("payload parsed");

      WrapperBay wrapperBay = WrapperBay.getInstance();
      String vimUuid = wrapperBay.getVimRepo()
          .getComputeVimUuidByFunctionInstanceId(data.getFunctionInstanceId());
      Logger.info("Wrapper retrieved, vimUuid = " + (vimUuid == null ? "null" : vimUuid));

      ComputeWrapper wr = wrapperBay.getComputeWrapper(vimUuid);

      if (wr == null) {
        Logger.warn("Error retrieving the wrapper");

        this.sendToMux(new ServicePlatformMessage(
            "{\"request_status\":\"ERROR\",\"message\":\"VIM not found\"}", "application/json",
            message.getReplyTo(), message.getSid(), null));
        out = false;
      } else {
        // use wrapper interface to send the NSD/VNFD, along with meta-data
        // to the wrapper, triggering the service scaling.
        Logger.info("Calling wrapper: " + wr);
        wr.addObserver(this);
        wr.scaleFunction(data, this.getSid());
      }
    } catch (Exception e) {
      Logger.error("Error scaling the vnf: " + e.getMessage(), e);
      this.sendToMux(
          new ServicePlatformMessage("{\"request_status\":\"ERROR\",\"message\":\"Scaling Error\"}",
              "application/json", message.getReplyTo(), message.getSid(), null));
      out = false;
    }
    return out;
  }

  @Override
  public void update(Observable observable, Object o) {

  }
}
