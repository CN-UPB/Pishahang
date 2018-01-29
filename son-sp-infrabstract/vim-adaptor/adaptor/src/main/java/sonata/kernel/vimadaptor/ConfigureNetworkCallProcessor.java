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

import sonata.kernel.vimadaptor.commons.NetworkConfigurePayload;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.nsd.ForwardingGraph;
import sonata.kernel.vimadaptor.commons.nsd.NetworkForwardingPath;
import sonata.kernel.vimadaptor.commons.nsd.NetworkFunction;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.ConnectionPointReference;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.messaging.ServicePlatformMessage;
import sonata.kernel.vimadaptor.wrapper.NetworkWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Observable;

public class ConfigureNetworkCallProcessor extends AbstractCallProcessor {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(DeployFunctionCallProcessor.class);

  NetworkConfigurePayload data = null;

  /**
   * @param message
   * @param sid
   * @param mux
   */
  public ConfigureNetworkCallProcessor(ServicePlatformMessage message, String sid, AdaptorMux mux) {
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
    data = null;
    ObjectMapper mapper = SonataManifestMapper.getSonataMapper();

    try {
      data = mapper.readValue(message.getBody(), NetworkConfigurePayload.class);
      Logger.info("payload parsed");
    } catch (IOException e) {
      Logger.error("Unable to parse the payload received", e);
      String responseJson =
          "{\"request_status\":\"ERROR\",\"message\":\"Unable to parse API payload\"}";
      this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
          message.getReplyTo(), message.getSid(), null));
      return false;
    }

    String serviceInstaceId = data.getServiceInstanceId();
    Logger.info("Received networking.configure call for service instance " + serviceInstaceId);
    ServiceDescriptor nsd = data.getNsd();
    ArrayList<VnfRecord> vnfrs = data.getVnfrs();
    ArrayList<VnfDescriptor> vnfds = data.getVnfds();
    Logger.info("Processing Forwarding graphs...");
    if (nsd.getForwardingGraphs() != null) {
      for (ForwardingGraph graph : nsd.getForwardingGraphs()) {
        for (NetworkForwardingPath path : graph.getNetworkForwardingPaths()) {

          ArrayList<ConnectionPointReference> pathCp = path.getConnectionPoints();

          Collections.sort(pathCp);

          // Pre-populate structures for efficent search.

          HashMap<String, String> vnfId2NameMap = new HashMap<String, String>();

          for (NetworkFunction nf : nsd.getNetworkFunctions()) {
            vnfId2NameMap.put(nf.getVnfId(), nf.getVnfName());
          }

          HashMap<String, VnfDescriptor> vnfName2VnfdMap = new HashMap<String, VnfDescriptor>();
          for (VnfDescriptor vnfd : vnfds) {
            vnfName2VnfdMap.put(vnfd.getName(), vnfd);
          }

          HashMap<String, VnfRecord> vnfd2VnfrMap = new HashMap<String, VnfRecord>();
          for (VnfRecord vnfr : vnfrs) {
            vnfd2VnfrMap.put(vnfr.getDescriptorReference(), vnfr);
          }
          HashMap<String, ArrayList<ConnectionPointReference>> netVim2SubGraphMap =
              new HashMap<String, ArrayList<ConnectionPointReference>>();

          HashMap<String, VnfDescriptor> cpRef2VnfdMap = new HashMap<String, VnfDescriptor>();

          HashMap<String, VnfRecord> cpRef2VnfrMap = new HashMap<String, VnfRecord>();

          for (ConnectionPointReference cpr : pathCp) {
            String name = cpr.getConnectionPointRef();
            if (!name.contains(":")) {
              continue;
            } else {
              String[] split = name.split(":");
              if (split.length != 2) {
                Logger.error("Unable to parse the service graph");
                String responseJson =
                    "{\"request_status\":\"ERROR\",\"message\":\"Unable to parse NSD service graph. Error in the connection_point_reference fields: "
                        + name + "\"}";
                this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
                    message.getReplyTo(), message.getSid(), null));
                return false;
              }
              String vnfId = split[0];
              String vnfName = vnfId2NameMap.get(vnfId);
              VnfDescriptor vnfd = vnfName2VnfdMap.get(vnfName);
              cpRef2VnfdMap.put(name, vnfd);
              cpRef2VnfrMap.put(name, vnfd2VnfrMap.get(vnfd.getUuid()));
              // Logger.debug("Getting id for vnf: " + vnfName);
              String vnfInstanceUuid = vnfd.getInstanceUuid();
              String computeVimUuid = WrapperBay.getInstance().getVimRepo()
                  .getComputeVimUuidByFunctionInstanceId(vnfInstanceUuid);
              if (computeVimUuid == null) {
                Logger.error(
                    "Can't find Compute VIM UUID for Function Instance Id " + vnfInstanceUuid);
                String responseJson =
                    "{\"request_status\":\"ERROR\",\"message\":\"Can't find VIM where function instance"
                        + vnfInstanceUuid + " is deployed\"}";
                this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
                    message.getReplyTo(), message.getSid(), null));
                return false;
              }
              String netVimUuid = WrapperBay.getInstance()
                  .getNetworkVimFromComputeVimUuid(computeVimUuid).getConfig().getUuid();
              if (netVim2SubGraphMap.containsKey(netVimUuid)) {
                netVim2SubGraphMap.get(netVimUuid).add(cpr);
              } else {
                netVim2SubGraphMap.put(netVimUuid, new ArrayList<ConnectionPointReference>());
                netVim2SubGraphMap.get(netVimUuid).add(cpr);
              }
            }
          }


          // Logger.debug("subgraph data structure:");
          // Logger.debug(netVim2SubGraphMap.toString());

          for (String netVimUuid : netVim2SubGraphMap.keySet()) {
            ArrayList<VnfDescriptor> descriptorsSublist = new ArrayList<VnfDescriptor>();
            ArrayList<VnfRecord> recordsSublist = new ArrayList<VnfRecord>();


            ServiceDescriptor partialNsd = new ServiceDescriptor();
            partialNsd.setConnectionPoints(nsd.getConnectionPoints());
            partialNsd.setNetworkFunctions(nsd.getNetworkFunctions());
            partialNsd.setInstanceUuid(serviceInstaceId);
            ForwardingGraph partialGraph = new ForwardingGraph();
            NetworkForwardingPath partialPath = new NetworkForwardingPath();
            ArrayList<ConnectionPointReference> connectionPoints =
                netVim2SubGraphMap.get(netVimUuid);
            partialPath.setConnectionPoints(connectionPoints);
            ArrayList<NetworkForwardingPath> tempPaths = new ArrayList<NetworkForwardingPath>();
            tempPaths.add(partialPath);
            partialGraph.setNetworkForwardingPaths(tempPaths);
            ArrayList<ForwardingGraph> tempGraph = new ArrayList<ForwardingGraph>();
            tempGraph.add(partialGraph);
            partialNsd.setForwardingGraphs(tempGraph);

            for (ConnectionPointReference cpr : connectionPoints) {
              VnfDescriptor vnfd = cpRef2VnfdMap.get(cpr.getConnectionPointRef());
              VnfRecord vnfr = cpRef2VnfrMap.get(cpr.getConnectionPointRef());
              if (!descriptorsSublist.contains(vnfd)) descriptorsSublist.add(vnfd);
              if (!recordsSublist.contains(vnfr)) recordsSublist.add(vnfr);
            }

            NetworkConfigurePayload wrapperPayload = new NetworkConfigurePayload();
            wrapperPayload.setNsd(partialNsd);
            wrapperPayload.setVnfds(descriptorsSublist);
            wrapperPayload.setVnfrs(recordsSublist);
            wrapperPayload.setServiceInstanceId(serviceInstaceId);
            wrapperPayload.setNap(data.getNap());

            // try {
            // Logger.debug("Partial configuration for PoP "+netVimUuid+":");
            // Logger.debug(mapper.writeValueAsString(wrapperPayload));
            // } catch (JsonProcessingException e1) {
            // // TODO Auto-generated catch block
            // e1.printStackTrace();
            // }

            NetworkWrapper netWr = (NetworkWrapper) WrapperBay.getInstance().getWrapper(netVimUuid);
            try {
              netWr.configureNetworking(wrapperPayload);
            } catch (Exception e) {
              Logger.error("Unable to configure networking on VIM: " + netVimUuid, e);
              String responseJson =
                  "{\"request_status\":\"ERROR\",\"message\":\"" + e.getMessage() + "\"}";
              this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
                  message.getReplyTo(), message.getSid(), null));
              return false;
            }
          }
        }
      }
    }
    String responseJson = "{\"request_status\":\"COMPLETED\",\"message\":\"\"}";
    this.sendToMux(new ServicePlatformMessage(responseJson, "application/json",
        message.getReplyTo(), message.getSid(), null));
    return true;
  }

  /*
   * (non-Javadoc)
   * 
   * @see java.util.Observer#update(java.util.Observable, java.lang.Object)
   */
  @Override
  public void update(Observable arg0, Object arg1) {

  }

}
