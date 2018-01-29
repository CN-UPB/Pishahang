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

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class VirtualLink {


  public enum ConnectivityType {
    E_LAN("E-LAN"), E_LINE("E-Line"), E_TREE("E-Tree");

    private final String name;

    @JsonCreator
    ConnectivityType(String name) {
      this.name = name;
    }

    @Override
    public String toString() {
      return this.name;
    }
  }


  private boolean access;
  @JsonProperty("connection_points_reference")
  private ArrayList<String> connectionPointsReference;
  @JsonProperty("connectivity_type")
  private ConnectivityType connectivityType;
  private boolean dhcp;

  // Virtual Link description case;

  @JsonProperty("external_access")
  private boolean externalAccess;
  private String id;
  @JsonProperty("leaf_requirement")
  private String leafRequirement;
  private String qos;
  @JsonProperty("root_requirement")
  private String rootRequirement;
  @JsonProperty("vl_description")
  private String vlDescription;
  // Virtual Link reference case
  @JsonProperty("vl_group")
  private String vlGroup;
  @JsonProperty("vl_name")
  private String vlName;
  @JsonProperty("vl_version")
  private String vlVersion;

  public ArrayList<String> getConnectionPointsReference() {
    return connectionPointsReference;
  }

  public ConnectivityType getConnectivityType() {
    return connectivityType;
  }

  public String getId() {
    return id;
  }

  public String getLeafRequirement() {
    return leafRequirement;
  }

  public String getQos() {
    return qos;
  }

  public String getRootRequirement() {
    return rootRequirement;
  }

  public String getVlDescription() {
    return vlDescription;
  }

  public String getVlGroup() {
    return vlGroup;
  }

  public String getVlName() {
    return vlName;
  }

  public String getVlVersion() {
    return vlVersion;
  }

  public boolean isAccess() {
    return access;
  }

  public boolean isDhcp() {
    return dhcp;
  }

  public boolean isExternalAccess() {
    return externalAccess;
  }

  public void setAccess(boolean access) {
    this.access = access;
  }

  public void setConnectionPointsReference(ArrayList<String> connectionPointsReference) {
    this.connectionPointsReference = connectionPointsReference;
  }

  public void setConnectivityType(ConnectivityType connectivityType) {
    this.connectivityType = connectivityType;
  }

  public void setDhcp(boolean dhcp) {
    this.dhcp = dhcp;
  }

  public void setExternalAccess(boolean externalAccess) {
    this.externalAccess = externalAccess;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setLeafRequirement(String leafRequirement) {
    this.leafRequirement = leafRequirement;
  }

  public void setQos(String qos) {
    this.qos = qos;
  }

  public void setRootRequirement(String rootRequirement) {
    this.rootRequirement = rootRequirement;
  }

  public void setVlDescription(String vlDescription) {
    this.vlDescription = vlDescription;
  }

  public void setVlGroup(String vlGroup) {
    this.vlGroup = vlGroup;
  }

  public void setVlName(String vlName) {
    this.vlName = vlName;
  }

  public void setVlVersion(String vlVersion) {
    this.vlVersion = vlVersion;
  }


}
