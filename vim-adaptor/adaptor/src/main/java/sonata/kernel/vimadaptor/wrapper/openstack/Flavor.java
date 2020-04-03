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
 * Neither the name of the SONATA-NFV, UCL, NOKIA, THALES, NCSR Demokritos nor the names of its
 * contributors may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 * 
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Bruno Vidalenc (Ph.D.), Thales
 * 
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 */

package sonata.kernel.vimadaptor.wrapper.openstack;

public class Flavor implements Comparable<Flavor> {


  private String flavorName;

  private String id;

  private int ram;

  private int storage;

  private int vcpu;

  /**
   * Basic flavor constructor.
   * 
   * @param flavorName the name of this flavor
   * @param vcpu the number of virtual cpu
   * @param ram the amount of memory
   * @param storage the amount of storage
   */
  public Flavor(String flavorName, int vcpu, int ram, int storage) {
    super();
    this.flavorName = flavorName;
    this.vcpu = vcpu;
    this.ram = ram;
    this.storage = storage;
  }

  /*
   * (non-Javadoc)
   * 
   * @see java.lang.Comparable#compareTo(java.lang.Object)
   */
  @Override
  public int compareTo(Flavor other) {
    if ((this.vcpu - other.vcpu) != 0)
      return (int) Math.signum(this.vcpu - other.vcpu);
    else if ((this.ram - other.ram) != 0)
      return (int) Math.signum(this.ram - other.ram);
    else if ((this.storage - other.storage) != 0)
      return (int) Math.signum(this.storage - other.storage);
    else
      return 0;
  }

  public String getFlavorName() {
    return flavorName;
  }

  public String getId() {
    return id;
  }

  public int getRam() {
    return ram;
  }

  public int getStorage() {
    return storage;
  }

  public int getVcpu() {
    return vcpu;
  }

  public void setFlavorName(String flavorName) {
    this.flavorName = flavorName;
  }

  public void setRam(int ram) {
    this.ram = ram;
  }

  public void setStorage(int storage) {
    this.storage = storage;
  }


  public void setVcpu(int vcpu) {
    this.vcpu = vcpu;
  }
}
