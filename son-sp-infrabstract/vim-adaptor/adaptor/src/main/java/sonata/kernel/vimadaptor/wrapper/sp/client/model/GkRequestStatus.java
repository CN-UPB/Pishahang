/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, THALES, NCSR Demokritos ALL RIGHTS RESERVED.
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
package sonata.kernel.vimadaptor.wrapper.sp.client.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import sonata.kernel.vimadaptor.commons.NapObject;

import java.util.ArrayList;

public class GkRequestStatus {


  @JsonProperty("id")
  private String id;
  @JsonProperty("created_at")
  private String createdAt;
  @JsonProperty("updated_at")
  private String updatedAt;
  @JsonProperty("service_uuid")
  private String serviceUuid;
  @JsonProperty("status")
  private String status;
  @JsonProperty("request_type")
  private String requestType;
  @JsonProperty("service_instance_uuid")
  private String serviceInstanceUuid;
  @JsonProperty("ingress")
  private ArrayList<NapObject> ingresses;
  @JsonProperty("egress")
  private ArrayList<NapObject> egresses;

  public String getId() {
    return id;
  }

  public String getCreatedAt() {
    return createdAt;
  }

  public String getUpdatedAt() {
    return updatedAt;
  }

  public String getServiceUuid() {
    return serviceUuid;
  }

  public String getStatus() {
    return status;
  }

  public String getRequestType() {
    return requestType;
  }

  public String getServiceInstanceUuid() {
    return serviceInstanceUuid;
  }

  public ArrayList<NapObject> getIngresses() {
    return ingresses;
  }

  public ArrayList<NapObject> getEgresses() {
    return egresses;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setCreatedAt(String createdAt) {
    this.createdAt = createdAt;
  }

  public void setUpdatedAt(String updatedAt) {
    this.updatedAt = updatedAt;
  }

  public void setServiceUuid(String serviceUuid) {
    this.serviceUuid = serviceUuid;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public void setRequestType(String requestType) {
    this.requestType = requestType;
  }

  public void setServiceInstanceUuid(String serviceInstanceUuid) {
    this.serviceInstanceUuid = serviceInstanceUuid;
  }

  public void setIngresses(ArrayList<NapObject> ingresses) {
    this.ingresses = ingresses;
  }

  public void setEgresses(ArrayList<NapObject> egresses) {
    this.egresses = egresses;
  }
}
