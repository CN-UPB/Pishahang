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

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;

import java.util.HashMap;

@JsonPropertyOrder({"type", "properties"})
public class HeatResource implements Comparable<HeatResource> {

  private HashMap<String, Object> properties;
  @JsonIgnore
  private String resourceName;
  private String type;

  public HeatResource() {
    this.properties = new HashMap<String, Object>();
  }

  @Override
  public int compareTo(HeatResource object) {
    return this.type.compareTo(object.getType());
  }

  @Override
  public boolean equals(Object object) {
    if (object instanceof HeatResource) {
      return this.type.equals(((HeatResource) object).getType());
    } else {
      return false;
    }
  }

  public HashMap<String, Object> getProperties() {
    return properties;
  }

  public String getResourceName() {
    return resourceName;
  }

  public String getType() {
    return type;
  }

  @Override
  public int hashCode() {
    return this.getType().hashCode();
  }

  public void putProperty(String key, Object value) {
    this.properties.put(key, value);
  }

  public void setName(String name) {
    this.resourceName = name;
  }

  public void setProperties(HashMap<String, Object> properties) {
    this.properties = properties;
  }

  public void setType(String type) {
    this.type = type;
  }

}
