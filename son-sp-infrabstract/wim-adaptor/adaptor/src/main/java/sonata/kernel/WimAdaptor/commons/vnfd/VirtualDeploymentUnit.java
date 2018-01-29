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

public class VirtualDeploymentUnit {

  private String description;
  private String id;
  @JsonProperty("vm_image")
  private String vmImage;
  @JsonProperty("vm_image_format")
  private VmFormat vmImageFormat;
  @JsonProperty("vm_image_md5")
  private String vmImageMd5;
  @JsonProperty("resource_requirements")
  private ResourceRequirements resourceRequirements;
  @JsonProperty("connection_points")
  private ArrayList<ConnectionPoint> connectionPoints;
  @JsonProperty("monitoring_parameters")
  private ArrayList<VduMonitoringParameter> monitoringParameters;
  @JsonProperty("scale_in_out")
  private ScaleInOut scaleInOut;


  public void setDescription(String description) {
    this.description = description;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setVmImage(String vmImage) {
    this.vmImage = vmImage;
  }

  public void setVmImageFormat(VmFormat vmImageFormat) {
    this.vmImageFormat = vmImageFormat;
  }

  public void setVmImageMd5(String vmImageMd5) {
    this.vmImageMd5 = vmImageMd5;
  }

  public void setResourceRequirements(ResourceRequirements resourceRequirements) {
    this.resourceRequirements = resourceRequirements;
  }

  public void setConnectionPoints(ArrayList<ConnectionPoint> connectionPoints) {
    this.connectionPoints = connectionPoints;
  }

  public void setMonitoringParameters(ArrayList<VduMonitoringParameter> monitoringParameters) {
    this.monitoringParameters = monitoringParameters;
  }

  public void setScaleInOut(ScaleInOut scaleInOut) {
    this.scaleInOut = scaleInOut;
  }

  public String getDescription() {
    return description;
  }

  public String getId() {
    return id;
  }

  public String getVmImage() {
    return vmImage;
  }

  public VmFormat getVmImageFormat() {
    return vmImageFormat;
  }

  public String getVmImageMd5() {
    return vmImageMd5;
  }

  public ResourceRequirements getResourceRequirements() {
    return resourceRequirements;
  }

  public ArrayList<ConnectionPoint> getConnectionPoints() {
    return connectionPoints;
  }

  public ArrayList<VduMonitoringParameter> getMonitoringParameters() {
    return monitoringParameters;
  }

  public ScaleInOut getScaleInOut() {
    return scaleInOut;
  }


}
