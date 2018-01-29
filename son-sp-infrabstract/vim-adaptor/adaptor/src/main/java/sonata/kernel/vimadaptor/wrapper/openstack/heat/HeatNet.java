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

package sonata.kernel.vimadaptor.wrapper.openstack.heat;

import com.fasterxml.jackson.annotation.JsonProperty;

public class HeatNet {


  private String cidr;

  @JsonProperty("net_id")
  private String netId;

  @JsonProperty("net_name")
  private String netName;

  @JsonProperty("segmentation_id")
  private int segmentationId;

  @JsonProperty("subnet_id")
  private String subnetId;

  @JsonProperty("subnet_name")
  private String subnetName;

  public String getCidr() {
    return cidr;
  }

  public String getNetId() {
    return netId;
  }

  public String getNetName() {
    return netName;
  }

  public int getSegmentationId() {
    return segmentationId;
  }

  public String getSubnetId() {
    return subnetId;
  }

  public String getSubnetName() {
    return subnetName;
  }

  public void setCidr(String cidr) {
    this.cidr = cidr;
  }

  public void setNetId(String netId) {
    this.netId = netId;
  }

  public void setNetName(String netName) {
    this.netName = netName;
  }

  public void setSegmentationId(int segmentationId) {
    this.segmentationId = segmentationId;
  }

  public void setSubnetId(String subnetId) {
    this.subnetId = subnetId;
  }

  public void setSubnetName(String subnetName) {
    this.subnetName = subnetName;
  }

}
