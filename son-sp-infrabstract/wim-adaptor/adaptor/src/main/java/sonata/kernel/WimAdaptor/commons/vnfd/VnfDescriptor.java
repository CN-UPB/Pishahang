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

package sonata.kernel.WimAdaptor.commons.vnfd;


import com.fasterxml.jackson.annotation.JsonProperty;

import sonata.kernel.WimAdaptor.commons.nsd.ConnectionPoint;

import java.util.ArrayList;

public class VnfDescriptor {



  @JsonProperty("descriptor_version")
  private String descriptorVersion;
  private String vendor;
  private String name;
  private String version;
  @JsonProperty("created_at")
  private String createdAt;
  @JsonProperty("updated_at")
  private String updatedAt;
  private String uuid;
  @JsonProperty("instance_uuid")
  private String instanceUuid;
  private String author;
  private String description;
  @JsonProperty("virtual_deployment_units")
  private ArrayList<VirtualDeploymentUnit> virtualDeploymentUnits;
  @JsonProperty("connection_points")
  private ArrayList<ConnectionPoint> connectionPoints;
  @JsonProperty("virtual_links")
  private ArrayList<VnfVirtualLink> virtualLinks;
  @JsonProperty("deployment_flavors")
  private ArrayList<DeploymentFlavor> deploymentFlavors;
  @JsonProperty("lifecycle_events")
  private ArrayList<VnfLifeCycleEvent> lifecycleEvents;
  @JsonProperty("monitoring_rules")
  private ArrayList<VduMonitoringRules> monitoringRules;
  @JsonProperty("function_specific_managers")
  private ArrayList<FunctionSpecificManager> functionSpecificManagers;

  @Override
  public boolean equals(Object obj) {
    if (obj instanceof VnfDescriptor) {
      VnfDescriptor temp = (VnfDescriptor) obj;
      return temp.getUuid().equals(this.getUuid());
    } else {
      return false;
    }
  }


  public void setDescriptorVersion(String descriptorVersion) {
    this.descriptorVersion = descriptorVersion;
  }

  public void setVendor(String vendor) {
    this.vendor = vendor;
  }

  public void setName(String name) {
    this.name = name;
  }

  public void setVersion(String version) {
    this.version = version;
  }

  public void setCreatedAt(String createdAt) {
    this.createdAt = createdAt;
  }

  public void setUpdatedAt(String updatedAt) {
    this.updatedAt = updatedAt;
  }

  public void setUuid(String uuid) {
    this.uuid = uuid;
  }

  public void setAuthor(String author) {
    this.author = author;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public void setVirtualDeploymentUnits(ArrayList<VirtualDeploymentUnit> virtualDeploymentUnits) {
    this.virtualDeploymentUnits = virtualDeploymentUnits;
  }

  public void setConnectionPoints(ArrayList<ConnectionPoint> connectionPoints) {
    this.connectionPoints = connectionPoints;
  }

  public void setVirtualLinks(ArrayList<VnfVirtualLink> virtualLinks) {
    this.virtualLinks = virtualLinks;
  }

  public void setDeploymentFlavors(ArrayList<DeploymentFlavor> deploymentFlavors) {
    this.deploymentFlavors = deploymentFlavors;
  }

  public void setLifecycleEvents(ArrayList<VnfLifeCycleEvent> lifecycleEvents) {
    this.lifecycleEvents = lifecycleEvents;
  }

  public void setMonitoringRules(ArrayList<VduMonitoringRules> monitoringRules) {
    this.monitoringRules = monitoringRules;
  }

  public String getDescriptorVersion() {
    return descriptorVersion;
  }

  public String getVendor() {
    return vendor;
  }

  public String getName() {
    return name;
  }

  public String getVersion() {
    return version;
  }

  public String getCreatedAt() {
    return createdAt;
  }

  public String getUpdatedAt() {
    return updatedAt;
  }

  public String getUuid() {
    return uuid;
  }

  public String getAuthor() {
    return author;
  }

  public String getDescription() {
    return description;
  }

  public ArrayList<VirtualDeploymentUnit> getVirtualDeploymentUnits() {
    return virtualDeploymentUnits;
  }

  public ArrayList<ConnectionPoint> getConnectionPoints() {
    return connectionPoints;
  }

  public ArrayList<VnfVirtualLink> getVirtualLinks() {
    return virtualLinks;
  }

  public ArrayList<DeploymentFlavor> getDeploymentFlavors() {
    return deploymentFlavors;
  }

  public ArrayList<VnfLifeCycleEvent> getLifecycleEvents() {
    return lifecycleEvents;
  }

  public ArrayList<VduMonitoringRules> getMonitoringRules() {
    return monitoringRules;
  }

  public String getInstanceUuid() {
    return instanceUuid;
  }

  public void setInstanceUuid(String instanceUuid) {
    this.instanceUuid = instanceUuid;
  }

  public ArrayList<FunctionSpecificManager> getFunctionSpecificManagers() {
    return functionSpecificManagers;
  }

  public void setFunctionSpecificManagers(
      ArrayList<FunctionSpecificManager> functionSpecificManagers) {
    this.functionSpecificManagers = functionSpecificManagers;
  }

}
