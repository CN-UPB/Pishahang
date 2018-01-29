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
 * @author Guy Paz, Nokia
 * 
 */

package sonata.kernel.vimadaptor.wrapper.openstack.heat;

import com.fasterxml.jackson.annotation.JsonProperty;

public class HeatServer {

  private InstanceFlavor flavor;
  @JsonProperty("server_id")
  private String serverId;

  @JsonProperty("server_name")
  private String serverName;

  public InstanceFlavor getFlavor() {
    return flavor;
  }

  public String getServerId() {
    return serverId;
  }

  public String getServerName() {
    return serverName;
  }

  public void setFlavor(InstanceFlavor flavor) {
    this.flavor = flavor;
  }

  public void setServerId(String serverId) {
    this.serverId = serverId;
  }

  public void setServerName(String serverName) {
    this.serverName = serverName;
  }

}
