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

package sonata.kernel.vimadaptor.commons;

import com.fasterxml.jackson.annotation.JsonProperty;

import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;

import java.util.ArrayList;

public class ServiceDeployPayload {

  private ServiceDescriptor nsd;
  @JsonProperty("vim_uuid")
  private String vimUuid;
  private ArrayList<VnfDescriptor> vnfds;

  public ServiceDeployPayload() {
    this.vnfds = new ArrayList<VnfDescriptor>();
  }

  public void addVnfDescriptor(VnfDescriptor descriptor) {
    this.vnfds.add(descriptor);
  }

  public ServiceDescriptor getNsd() {
    return nsd;
  }

  public String getVimUuid() {
    return vimUuid;
  }

  public ArrayList<VnfDescriptor> getVnfdList() {
    return vnfds;
  }

  public void setNsd(ServiceDescriptor nsd) {
    this.nsd = nsd;
  }

  public void setServiceDescriptor(ServiceDescriptor descriptor) {
    this.nsd = descriptor;
  }

  public void setVimUuid(String vimUuid) {
    this.vimUuid = vimUuid;
  }

  public void setVnfds(ArrayList<VnfDescriptor> vnfds) {
    this.vnfds = vnfds;
  }

}
