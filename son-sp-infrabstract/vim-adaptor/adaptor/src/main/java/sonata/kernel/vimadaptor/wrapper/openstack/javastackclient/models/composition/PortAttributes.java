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
 * @author Adel Zaalouk (Ph.D.), NEC
 * 
 */

package sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.composition;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.ArrayList;
import java.util.HashMap;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PortAttributes {

  private ArrayList<HashMap<String, String>> fixed_ips;
  private String id;
  private String mac_address;
  private String name;

  public ArrayList<HashMap<String, String>> getFixed_ips() {
    return fixed_ips;
  }

  public String getId() {
    return id;
  }

  public String getMac_address() {
    return mac_address;
  }

  public String getName() {
    return name;
  }


  public void setFixed_ips(ArrayList<HashMap<String, String>> fixed_ips) {
    this.fixed_ips = fixed_ips;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setMac_address(String mac_address) {
    this.mac_address = mac_address;
  }

  public void setName(String name) {
    this.name = name;
  }
}
