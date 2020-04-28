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

package sonata.kernel.vimadaptor.commons.nsd;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class ForwardingGraph {

  @JsonProperty("constituent_services")
  private ArrayList<String> constituentServices;
  @JsonProperty("constituent_vnfs")
  private ArrayList<String> constituentVnfs;
  @JsonProperty("dependent_virtual_links")
  private ArrayList<String> dependentVirtualLinks;
  @JsonProperty("fg_description")
  private String fgDescription;

  // Forwarding Graph reference case.
  @JsonProperty("fg_group")
  private String fgGroup;
  // Forwarding Graph description case.
  @JsonProperty("fg_id")
  private String fgId;
  @JsonProperty("fg_name")
  private String fgName;
  @JsonProperty("fg_version")
  private String fgVersion;
  @JsonProperty("network_forwarding_paths")
  private ArrayList<NetworkForwardingPath> networkForwardingPaths;
  @JsonProperty("number_of_endpoints")
  private int numberOfEndpoints;
  @JsonProperty("number_of_virtual_links")
  private int numberOfVirtualLinks;


  public ArrayList<String> getConstituentServices() {
    return constituentServices;
  }

  public ArrayList<String> getConstituentVnfs() {
    return constituentVnfs;
  }

  public ArrayList<String> getDependentVirtualLinks() {
    return dependentVirtualLinks;
  }

  public String getFgDescription() {
    return fgDescription;
  }

  public String getFgGroup() {
    return fgGroup;
  }

  public String getFgId() {
    return fgId;
  }

  public String getFgName() {
    return fgName;
  }

  public String getFgVersion() {
    return fgVersion;
  }

  public ArrayList<NetworkForwardingPath> getNetworkForwardingPaths() {
    return networkForwardingPaths;
  }

  public int getNumberOfEndpoints() {
    return numberOfEndpoints;
  }

  public int getNumberOfVirtualLinks() {
    return numberOfVirtualLinks;
  }

  public void setConstituentServices(ArrayList<String> constituentServices) {
    this.constituentServices = constituentServices;
  }

  public void setConstituentVnfs(ArrayList<String> constituentVnfs) {
    this.constituentVnfs = constituentVnfs;
  }

  public void setDependentVirtualLinks(ArrayList<String> dependentVirtualLinks) {
    this.dependentVirtualLinks = dependentVirtualLinks;
  }

  public void setFgDescription(String fgDescription) {
    this.fgDescription = fgDescription;
  }

  public void setFgGroup(String fgGroup) {
    this.fgGroup = fgGroup;
  }

  public void setFgId(String fgId) {
    this.fgId = fgId;
  }

  public void setFgName(String fgName) {
    this.fgName = fgName;
  }

  public void setFgVersion(String fgVersion) {
    this.fgVersion = fgVersion;
  }

  public void setNetworkForwardingPaths(ArrayList<NetworkForwardingPath> networkForwardingPaths) {
    this.networkForwardingPaths = networkForwardingPaths;
  }

  public void setNumberOfEndpoints(int numberOfEndpoints) {
    this.numberOfEndpoints = numberOfEndpoints;
  }

  public void setNumberOfVirtualLinks(int numberOfVirtualLinks) {
    this.numberOfVirtualLinks = numberOfVirtualLinks;
  }

}
