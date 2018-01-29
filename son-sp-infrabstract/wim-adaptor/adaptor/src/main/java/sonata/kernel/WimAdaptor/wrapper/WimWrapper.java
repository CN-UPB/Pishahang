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

package sonata.kernel.WimAdaptor.wrapper;

public abstract class WimWrapper extends AbstractWrapper implements Wrapper {

  protected WrapperConfiguration config;

  
  
  /**
   * general constructor for wrappers of type compute.
   */
  public WimWrapper(WrapperConfiguration config) {
    this.config=config;
    this.setType("wim");

  }


  /**
   * Configure the WAN for a service instance. V2 with multiple NFVi-PoP.
   * 
   * @param instanceId the ID of the service instance
   * 
   * @return true if the WAN has been configured correctly.
   */
  public abstract boolean configureNetwork(String instanceId, String inputSegment, String outputSegment, String[] segmentList);

  
  
  /**
   * Remove the WAN configuration for a given service instance.
   * 
   * @param instanceId the ID of the service instance to de-configure
   * @return true if the WAN has been de-configured correctly.
   */
  public abstract boolean removeNetConfiguration(String instanceId);

  public WrapperConfiguration getConfig() {
    return config;
  }

}
