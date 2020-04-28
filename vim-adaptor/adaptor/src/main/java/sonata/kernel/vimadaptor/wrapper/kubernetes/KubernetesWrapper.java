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

package sonata.kernel.vimadaptor.wrapper.kubernetes;

import com.mitchellbosecke.pebble.error.PebbleException;
import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.*;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;

import io.fabric8.kubernetes.api.model.NodeList;
import sonata.kernel.vimadaptor.wrapper.terraform.TerraformTemplate;
import sonata.kernel.vimadaptor.wrapper.terraform.TerraformWrapper;

import java.io.IOException;


public class KubernetesWrapper extends TerraformWrapper {

    private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(KubernetesWrapper.class);

    /**
     * Kubernetes related vars
     */
    private KubernetesClient client;

    private ResponseHelper response;

    private NodeList nodes;

    /**
     * Constructor.
     *
     * @param config WrapperConfiguration
     */
    public KubernetesWrapper(WrapperConfiguration config) {
        super(config);

        this.client = new KubernetesClient(config);
        this.response = new ResponseHelper(config);
    }

    /**
     * Get the resource utilisation of the Kubernetes cluster.
     */
    @Override
    public ResourceUtilisation getResourceUtilisation() {
        long start = System.currentTimeMillis();
        Logger.info(this.buildLogMessage("Getting resource utilisation..."));

        ResourceUtilisation resourceUtilisation = new ResourceUtilisation();

        try {
            resourceUtilisation = this.client.getClusterResourceUtilisation(this.getNodes());

            Logger.info(this.buildLogMessage("Resource utilisation retrieved in " + (System.currentTimeMillis() - start) + "ms."));
        } catch (IOException e) {
            Logger.error(this.buildLogMessage("Failed to retrieve resource utilisation. Error message: " + e.getMessage()));
        }

        return resourceUtilisation;
    }

    @Override
    public TerraformTemplate buildTemplate(CloudServiceDeployPayload data) throws IOException, PebbleException {
        return new KubernetesTerraformTemplate()
                .forService(data.getServiceInstanceId())
                .withCsd(data.getCsd())
                .withWrapperConfiguration(this.getConfig())
                .build();
    }

    /**
     * Get the deploy response from the deploy payload.
     *
     * @param payload CloudServiceDeployPayload
     *
     * @return CloudServiceDeployResponse
     */
    @Override
    protected CloudServiceDeployResponse getCloudServiceDeployResponse(CloudServiceDeployPayload payload) {
        return this.response.buildDeployResponse(payload);
    }

    /**
     * Get all nodes of the Kubernetes cluster.
     *
     * @return NodeList
     */
    private NodeList getNodes() {
        if (this.nodes == null) {
            return this.nodes = this.client.fetchNodes();
        }

        return this.nodes;
    }

    /**
     * Get the wrapper's name.
     *
     * @return String
     */
    @Override
    protected String getWrapperName() {
        return "KubernetesWrapper";
    }

    public String toString() {
        return "KubernetesWrapper-"+this.getConfig().getUuid();
    }
}
