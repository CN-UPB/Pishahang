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

import sonata.kernel.vimadaptor.commons.CloudServiceDeployPayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperStatusUpdate;

import java.util.Observable;

public class DeployCloudServiceProcessor extends AbstractCallProcessor {

    private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(DeployCloudServiceProcessor.class);

    private CloudServiceDeployPayload data;

    /**
     * Basic constructor for the call processor.
     *
     * @param message
     * @param sid
     * @param mux
     */
    public DeployCloudServiceProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
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
        Logger.info("Deploy cloud service call received by call processor.");

        // parse the payload to get Wrapper UUID and COSD/CSD from the request body
        data = null;
        ObjectMapper mapper = SonataManifestMapper.getSonataMapper();

        try {
            data = mapper.readValue(message.getBody(), CloudServiceDeployPayload.class);
            Logger.info("Payload parsed");
            ComputeWrapper wr = WrapperBay.getInstance().getComputeWrapper(data.getVimUuid());
            Logger.info("Wrapper retrieved: " + wr.getConfig().getUuid());

            if (wr == null) {
                Logger.warn("Error retrieving the wrapper");

                this.sendToMux(new ServicePlatformMessage(
                        "{\"request_status\":\"ERROR\",\"message\":\"VIM not found\"}", "application/json",
                        message.getReplyTo(), message.getSid(), null));
                return false;
            } else {
                // use wrapper interface to send the NSD/VNFD, along with meta-data
                // to the wrapper, triggering the service instantiation.
                Logger.info("Calling wrapper: " + wr.getConfig().getName() + "- UUID: " +wr.getConfig().getUuid());
                wr.addObserver(this);
                wr.deployCloudService(data, this.getSid());
            }
        } catch (Exception e) {
            Logger.error("Error deploying the system: " + e.getMessage(), e);
            this.sendToMux(new ServicePlatformMessage(
                    "{\"request_status\":\"ERROR\",\"message\":\"Deployment Error\"}", "application/json",
                    message.getReplyTo(), message.getSid(), null));
            return false;
        }

        return true;
    }

    /*
     * (non-Javadoc)
     *
     * @see java.util.Observer#update(java.util.Observable, java.lang.Object)
     */
    @Override
    public void update(Observable o, Object arg) {
        Logger.info("[DeployCloudServiceProcessor] Deploy status update received.");

        WrapperStatusUpdate update = (WrapperStatusUpdate) arg;

        if (!update.getSid().equals(this.getSid())) {
            return;
        }

        switch (update.getStatus()) {
            case "SUCCESS":
                this.handleReceivedSuccessUpdate(update);
                break;
            case "ERROR":
                this.handleReceivedErrorUpdate(update);
                break;
            default:
                Logger.error("[DeployCloudServiceProcessor] Received invalid update status: " + update.getStatus());
                break;
        }
    }

    private void handleReceivedSuccessUpdate(WrapperStatusUpdate update) {
        Logger.info("[DeployCloudServiceProcessor] Deploy of service succeeded.");

        ServicePlatformMessage response = new ServicePlatformMessage(update.getBody(),
                "application/x-yaml", this.getMessage().getReplyTo(), this.getSid(), null);
        this.sendToMux(response);
    }

    private void handleReceivedErrorUpdate(WrapperStatusUpdate update) {
        Logger.error("[DeployCloudServiceProcessor] Deploy of service " + this.getSid() + " failed.");

        ServicePlatformMessage response = new ServicePlatformMessage(
                "{\"request_status\":\"ERROR\",\"message\":\"" + update.getBody() + "\"}",
                "application/x-yaml", this.getMessage().getReplyTo(), this.getSid(), null);
        this.sendToMux(response);
    }
}
