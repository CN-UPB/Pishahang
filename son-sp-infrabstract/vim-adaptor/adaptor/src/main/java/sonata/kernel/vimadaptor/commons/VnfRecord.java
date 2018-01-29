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

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

@JsonIgnoreProperties(ignoreUnknown = true)
public class VnfRecord {

  @JsonProperty("descriptor_reference")
  private String descriptorReference;
  @JsonProperty("descriptor_version")
  private String descriptorVersion;
  @JsonProperty("id")
  private String id;

  // @JsonProperty("descriptor_reference_vendor")
  // private String descriptorReferenceVendor;
  // @JsonProperty("descriptor_reference_name")
  // private String descriptorReferenceName;
  // @JsonProperty("descriptor_reference_version")
  // private String descriptorReferenceVersion;

  private Status status;

  @JsonProperty("virtual_deployment_units")
  private ArrayList<VduRecord> virtualDeploymentUnits;


  public VnfRecord() {
    this.virtualDeploymentUnits = new ArrayList<VduRecord>();
  }

  public void addVdu(VduRecord unit) {
    this.virtualDeploymentUnits.add(unit);
  }

  @Override
  public boolean equals(Object obj) {
    if (obj instanceof VnfRecord) {
      VnfRecord temp = (VnfRecord) obj;
      return temp.getId().equals(this.getId());
    } else {
      return false;
    }
  }


  public String getDescriptorReference() {
    return descriptorReference;
  }


  public String getDescriptorVersion() {
    return descriptorVersion;
  }

  public String getId() {
    return id;
  }


  public Status getStatus() {
    return status;
  }


  public ArrayList<VduRecord> getVirtualDeploymentUnits() {
    return virtualDeploymentUnits;
  }


  public void setDescriptorReference(String descriptorReference) {
    this.descriptorReference = descriptorReference;
  }

  // public String getDescriptorReferenceVendor() {
  // return descriptorReferenceVendor;
  // }
  //
  // public String getDescriptorReferenceName() {
  // return descriptorReferenceName;
  // }
  //
  // public String getDescriptorReferenceVersion() {
  // return descriptorReferenceVersion;
  // }
  //
  // public void setDescriptorReferenceVendor(String descriptorReferenceVendor) {
  // this.descriptorReferenceVendor = descriptorReferenceVendor;
  // }
  //
  // public void setDescriptorReferenceName(String descriptorReferenceName) {
  // this.descriptorReferenceName = descriptorReferenceName;
  // }
  //
  // public void setDescriptorReferenceVersion(String descriptorReferenceVersion) {
  // this.descriptorReferenceVersion = descriptorReferenceVersion;
  // }

  public void setDescriptorVersion(String descriptorVersion) {
    this.descriptorVersion = descriptorVersion;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setStatus(Status status) {
    this.status = status;
  }

  public void setVirtualDeploymentUnits(ArrayList<VduRecord> virtualDeploymentUnits) {
    this.virtualDeploymentUnits = virtualDeploymentUnits;
  }


}
