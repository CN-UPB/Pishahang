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

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;

public class OrderedMacAddress implements Comparable<OrderedMacAddress> {

  @JsonProperty("port")
  private String mac;
  @JsonProperty("order")
  private int position;
  @JsonIgnore
  private String referenceCp;

  @JsonProperty("vc_id")
  private String vcId;

  @Override
  public int compareTo(OrderedMacAddress o) {
    return (int) Math.signum(this.position - o.getPosition());
  }

  public String getMac() {
    return mac;
  }

  public int getPosition() {
    return position;
  }

  public String getReferenceCp() {
    return referenceCp;
  }


  public String getVcId() {
    return vcId;
  }

  public void setMac(String mac) {
    this.mac = mac;
  }

  public void setPosition(int position) {
    this.position = position;
  }

  public void setReferenceCp(String referenceCp) {
    this.referenceCp = referenceCp;
  }

  public void setVcId(String vcId) {
    this.vcId = vcId;
  }

  @Override
  public String toString() {
    return "{port:" + mac + ",order:" + position + ", cp: " + referenceCp + "}";
  }

}
