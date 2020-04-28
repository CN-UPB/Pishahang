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

package sonata.kernel.vimadaptor.wrapper.ovsWrapper;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.NapObject;
import sonata.kernel.vimadaptor.commons.NetworkAttachmentPoints;
import sonata.kernel.vimadaptor.commons.NetworkConfigurePayload;
import sonata.kernel.vimadaptor.commons.VduRecord;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.VnfcInstance;
import sonata.kernel.vimadaptor.commons.nsd.ConnectionPointRecord;
import sonata.kernel.vimadaptor.commons.nsd.ForwardingGraph;
import sonata.kernel.vimadaptor.commons.nsd.NetworkForwardingPath;
import sonata.kernel.vimadaptor.commons.nsd.NetworkFunction;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.ConnectionPointReference;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfVirtualLink;
import sonata.kernel.vimadaptor.wrapper.NetworkWrapper;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.net.InetAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Properties;

public class OvsWrapper extends NetworkWrapper {

  private static final String ADAPTOR_SEGMENTS_CONF = "/adaptor/segments.conf";

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(OvsWrapper.class);

  /**
   * Basic constructor.
   * 
   * @param config the configuration object of this wrapper.
   */
  public OvsWrapper(WrapperConfiguration config) {
    super(config);
  }

  @Override
  public void configureNetworking(NetworkConfigurePayload data) throws Exception {
    if (data.getNsd().getForwardingGraphs().size() <= 0)
      throw new Exception("No Forwarding Graph specified in the descriptor");

    long start = System.currentTimeMillis();

    String serviceInstanceId = data.getServiceInstanceId();
    ServiceDescriptor nsd = data.getNsd();
    ArrayList<VnfRecord> vnfrs = data.getVnfrs();
    ArrayList<VnfDescriptor> vnfds = data.getVnfds();
    ForwardingGraph graph = nsd.getForwardingGraphs().get(0);

    NetworkForwardingPath path = graph.getNetworkForwardingPaths().get(0);

    ArrayList<ConnectionPointReference> pathCp = path.getConnectionPoints();

    Collections.sort(pathCp);
    int portIndex = 0;

    ArrayList<OrderedMacAddress> odlList = new ArrayList<OrderedMacAddress>();
    // Pre-populate structures for efficent search.

    HashMap<String, String> vnfIdToNameMap = new HashMap<String, String>();

    for (NetworkFunction nf : nsd.getNetworkFunctions()) {
      vnfIdToNameMap.put(nf.getVnfId(), nf.getVnfName());
    }

    HashMap<String, VnfDescriptor> nameToVnfdMap = new HashMap<String, VnfDescriptor>();
    for (VnfDescriptor vnfd : vnfds) {
      nameToVnfdMap.put(vnfd.getName(), vnfd);
    }

    HashMap<String, VnfRecord> vnfdToVnfrMap = new HashMap<String, VnfRecord>();
    for (VnfRecord vnfr : vnfrs) {
      vnfdToVnfrMap.put(vnfr.getDescriptorReference(), vnfr);
    }

    for (ConnectionPointReference cpr : pathCp) {
      String name = cpr.getConnectionPointRef();
      if (!name.contains(":")) {
        continue;
      } else {
        String[] split = name.split(":");
        if (split.length != 2) {
          throw new Exception(
              "Illegal Format: A connection point reference should be in the format vnfId:CpName. It was "
                  + name);
        }
        String vnfId = split[0];
        String cpRef = split[1];
        String vnfName = vnfIdToNameMap.get(vnfId);
        if (vnfName == null) {
          throw new Exception("Illegal Format: Unable to bind vnfName to the vnfId: " + vnfId);
        }
        VnfDescriptor vnfd = nameToVnfdMap.get(vnfName);
        if (vnfd == null) {
          throw new Exception("Illegal Format: Unable to bind VNFD to the vnfName: " + vnfName);
        }

        VnfRecord vnfr = vnfdToVnfrMap.get(vnfd.getUuid());
        if (vnfr == null) {
          throw new Exception("Illegal Format: Unable to bind VNFD to the VNFR: " + vnfName);
        }

        VnfVirtualLink inputLink = null;
        for (VnfVirtualLink link : vnfd.getVirtualLinks()) {
          if (link.getConnectionPointsReference().contains(cpRef)) {
            inputLink = link;
            break;
          }
        }
        if (inputLink == null) {
          for (VnfVirtualLink link : vnfd.getVirtualLinks()) {
            Logger.info(link.getConnectionPointsReference().toString());
          }
          throw new Exception(
              "Illegal Format: unable to find the vnfd.VL connected to the VNFD.CP=" + vnfId+":"+cpRef);
        }

        if (inputLink.getConnectionPointsReference().size() != 2) {
          throw new Exception(
              "Illegal Format: A vnf in/out vl should connect exactly two CPs. found: "
                  + inputLink.getConnectionPointsReference().size());
        }
        String vnfcCpReference = null;
        for (String cp : inputLink.getConnectionPointsReference()) {
          if (!cp.equals(cpRef)) {
            vnfcCpReference = cp;
            break;
          }
        }
        if (vnfcCpReference == null) {
          throw new Exception(
              "Illegal Format: Unable to find the VNFC Cp name connected to this in/out VNF VL");
        }

        Logger.debug("Searching for CpRecord of Cp: " + vnfcCpReference);
        ConnectionPointRecord matchingCpRec = null;
        String vcId = null;
        split = vnfcCpReference.split(":");
        String vduId = split[0];
        String vnfcCpName = split[1];
        if (split.length != 2) {
          throw new Exception(
              "Illegal Format: A VL connection point reference should be in the format vdu_id:cp_name. Found: "
                  + vnfcCpReference);
        }

        for (VduRecord vdu : vnfr.getVirtualDeploymentUnits()) {
          if (vdu.getId().equals(vduId)) {
            for (VnfcInstance vnfc : vdu.getVnfcInstance()) {
              for (ConnectionPointRecord cpRec : vnfc.getConnectionPoints()) {
                Logger.debug("Checking " + cpRec.getId());
                if (vnfcCpName.equals(cpRec.getId())) {
                  matchingCpRec = cpRec;
                  vcId = vnfc.getVcId();
                  break;
                }
              }
            }
          }
        }

        String qualifiedName = vnfName + "." + vnfcCpReference + "." + nsd.getInstanceUuid();
        // HeatPort connectedPort = null;
        // for (HeatPort port : composition.getPorts()) {
        // if (port.getPortName().equals(qualifiedName)) {
        // connectedPort = port;
        // break;
        // }
        // }
        if (matchingCpRec == null) {
          throw new Exception(
              "Illegal Format: cannot find the VNFR.VDU.VNFC.CPR matching: " + vnfcCpReference);
        } else {
          // Eureka!
          OrderedMacAddress mac = new OrderedMacAddress();
          mac.setMac(matchingCpRec.getInterface().getHardwareAddress());
          mac.setPosition(portIndex);
          mac.setVcId(vcId);
          mac.setReferenceCp(qualifiedName);
          portIndex++;
          odlList.add(mac);
        }
      }
    }

    boolean nullNapCondition = data.getNap() == null
        || (data.getNap() != null
            && (data.getNap().getEgresses() == null || data.getNap().getIngresses() == null))
        || (data.getNap() != null && data.getNap().getEgresses() != null
            && data.getNap().getIngresses() != null && (data.getNap().getIngresses().size() == 0
                || data.getNap().getEgresses().size() == 0));
    if (nullNapCondition) {
      Logger.warn("NAP not specified, using default ones from default config file");
      Properties segments = new Properties();
      segments.load(new FileReader(new File(ADAPTOR_SEGMENTS_CONF)));
      NetworkAttachmentPoints nap = new NetworkAttachmentPoints();
      ArrayList<NapObject> ingresses = new ArrayList<NapObject>();
      ArrayList<NapObject> egresses = new ArrayList<NapObject>();
      ingresses.add(new NapObject("Athens", segments.getProperty("in")));
      egresses.add(new NapObject("Athens", segments.getProperty("out")));
      nap.setEgresses(egresses);
      nap.setIngresses(ingresses);
      data.setNap(nap);
    }
    Collections.sort(odlList);
    int ruleNumber = 0;
    for (NapObject inNap : data.getNap().getIngresses()) {
      for (NapObject outNap : data.getNap().getEgresses()) {
        OvsPayload odlPayload = new OvsPayload("add", serviceInstanceId + "." + ruleNumber,
            inNap.getNap(), outNap.getNap(), odlList);
        ObjectMapper mapper = new ObjectMapper(new JsonFactory());
        mapper.setSerializationInclusion(Include.NON_NULL);
        // Logger.info(compositionString);
        String payload = mapper.writeValueAsString(odlPayload);
        Logger.debug(this.getConfig().getUuid() + " - " + this.getConfig().getVimEndpoint());
        Logger.debug(payload);

        InetAddress IPAddress = InetAddress.getByName(this.getConfig().getVimEndpoint());
        int sfcAgentPort = 55555;
        Socket clientSocket = new Socket(IPAddress, sfcAgentPort);
        clientSocket.setSoTimeout(10000);
        byte[] sendData = new byte[1024];
        sendData = payload.getBytes(Charset.forName("UTF-8"));
        PrintStream out = new PrintStream(clientSocket.getOutputStream());
        BufferedReader in =
            new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));

        out.write(sendData);
        out.flush();

        String response;
        try {
          response = in.readLine();
        } catch (SocketTimeoutException e) {
          clientSocket.close();
          Logger.error("Timeout exception from the OVS SFC agent");
          throw new Exception("Request to OVS VIM agent timed out.");
        }
        if (response == null) {
          in.close();
          out.close();
          clientSocket.close();
          throw new Exception("null response received from OVS VIM ");
        }
        in.close();
        out.close();
        clientSocket.close();

        Logger.info("SFC Agent response:\n" + response);
        if (!response.equals("SUCCESS")) {
          Logger.error("Unexpected response.");
          Logger.error("received string length: " + response.length());
          Logger.error("received string: " + response);
          throw new Exception(
              "Unexpected response from OVS SFC agent while trying to add a configuration.");
        }
        ruleNumber++;
      }
    }
    long stop = System.currentTimeMillis();

    Logger.info("[OvsWrapper]networkConfigure-time: " + (stop - start) + " ms");

    return;
  }

  @Override
  public void deconfigureNetworking(String instanceId) throws Exception {
    long start = System.currentTimeMillis();
    OvsPayload odlPayload = new OvsPayload("delete", instanceId, null, null, null);
    ObjectMapper mapper = new ObjectMapper(new JsonFactory());
    mapper.setSerializationInclusion(Include.NON_NULL);
    // Logger.info(compositionString);
    String payload = mapper.writeValueAsString(odlPayload);
    Logger.info(payload);

    int sfcAgentPort = 55555;

    InetAddress IPAddress = InetAddress.getByName(this.getConfig().getVimEndpoint());
    Socket clientSocket = new Socket(IPAddress, sfcAgentPort);
    clientSocket.setSoTimeout(10000);
    byte[] sendData = new byte[1024];
    sendData = payload.getBytes(Charset.forName("UTF-8"));
    PrintStream out = new PrintStream(clientSocket.getOutputStream());
    BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));

    out.write(sendData);
    out.flush();
    String response;
    try {
      response = in.readLine();
    } catch (SocketTimeoutException e) {
      clientSocket.close();
      Logger.error("Timeout exception from the OVS SFC agent");
      throw new Exception("Request to OVS VIM agent timed out.");
    }
    if (response == null) {
      in.close();
      out.close();
      clientSocket.close();
      throw new Exception("null response received from OVS VIM ");
    }

    in.close();
    out.close();
    clientSocket.close();

    Logger.info("SFC Agent response:\n" + response);
    if (!(response.equals("SUCCESS")||response.startsWith("No instance-ID"))) {
      Logger.error("Unexpected response.");
      Logger.error("received string length: " + response.length());
      Logger.error("received string: " + response);
      throw new Exception(
          "Unexpected response from OVS SFC agent while trying to add a configuration.");
    }

    long stop = System.currentTimeMillis();
    Logger.info("[OvsWrapper]networkDeconfigure-time: " + (stop - start) + " ms");

    return;
  }
}
