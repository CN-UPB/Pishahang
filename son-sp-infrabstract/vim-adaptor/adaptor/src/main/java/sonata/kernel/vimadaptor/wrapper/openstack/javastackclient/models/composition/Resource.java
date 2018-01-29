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
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Resource<T> {

  T attributes;

  ArrayList<Link> links;
  @JsonProperty("parent_resource")
  String parent_resource;
  String physical_resource_id;
  String resource_name;

  String resource_type;

  public T getAttributes() {
    return attributes;
  }

  public ArrayList<Link> getLinks() {
    return links;
  }

  public String getParent_resource() {
    return parent_resource;
  }

  public String getPhysical_resource_id() {
    return physical_resource_id;
  }

  public String getResource_name() {
    return resource_name;
  }

  public String getResource_type() {
    return resource_type;
  }

  public void setAttributes(T attributes) {
    this.attributes = attributes;
  }

  public void setLinks(ArrayList<Link> links) {
    this.links = links;
  }

  public void setParent_resource(String parent_resource) {
    this.parent_resource = parent_resource;
  }

  public void setPhysical_resource_id(String physical_resource_id) {
    this.physical_resource_id = physical_resource_id;
  }

  public void setResource_name(String resource_name) {
    this.resource_name = resource_name;
  }

  public void setResource_type(String resource_type) {
    this.resource_type = resource_type;
  }

}
