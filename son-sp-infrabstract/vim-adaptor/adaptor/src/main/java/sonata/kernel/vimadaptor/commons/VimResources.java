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
 * @author Dario Valocchi (Ph.D.)
 * 
 */

package sonata.kernel.vimadaptor.commons;

import com.fasterxml.jackson.annotation.JsonProperty;

public class VimResources {

  @JsonProperty("core_total")
  private int coreTotal;
  @JsonProperty("core_used")
  private int coreUsed;
  @JsonProperty("memory_total")
  private int memoryTotal;
  @JsonProperty("memory_used")
  private int memoryUsed;
  @JsonProperty("vim_city")
  private String vimCity;
  @JsonProperty("vim_domain")
  private String vimDomain;
  @JsonProperty("vim_endpoint")
  private String vimEndpoint;
  @JsonProperty("vim_name")
  private String vimName;
  @JsonProperty("vim_uuid")
  private String vimUuid;
  @JsonProperty("vim_type")
  private String vimType;

  public int getCoreTotal() {
    return coreTotal;
  }

  public int getCoreUsed() {
    return coreUsed;
  }

  public int getMemoryTotal() {
    return memoryTotal;
  }

  public int getMemoryUsed() {
    return memoryUsed;
  }

  public String getVimCity() {
    return vimCity;
  }

  public String getVimDomain() {
    return vimDomain;
  }

  public String getVimEndpoint() {
    return vimEndpoint;
  }

  public String getVimName() {
    return vimName;
  }

  public String getVimUuid() {
    return vimUuid;
  }

  public String getVimType() {
    return this.vimType;
  }

  public void setCoreTotal(int coreTotal) {
    this.coreTotal = coreTotal;
  }

  public void setCoreUsed(int coreUsed) {
    this.coreUsed = coreUsed;
  }

  public void setMemoryTotal(int memoryTotal) {
    this.memoryTotal = memoryTotal;
  }

  public void setMemoryUsed(int memoryUsed) {
    this.memoryUsed = memoryUsed;
  }

  public void setVimCity(String vimCity) {
    this.vimCity = vimCity;
  }

  public void setVimDomain(String vimDomain) {
    this.vimDomain = vimDomain;
  }

  public void setVimEndpoint(String vimEndpoint) {
    this.vimEndpoint = vimEndpoint;
  }

  public void setVimName(String vimName) {
    this.vimName = vimName;
  }

  public void setVimUuid(String vimUuid) {
    this.vimUuid = vimUuid;
  }

  public void setVimType(String vimType) {
    this.vimType = vimType;
  }
}
