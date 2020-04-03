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

package sonata.kernel.vimadaptor.wrapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.wrapper.mock.ComputeMockWrapper;
import sonata.kernel.vimadaptor.wrapper.mock.NetworkMockWrapper;
import sonata.kernel.vimadaptor.wrapper.openstack.OpenStackHeatWrapper;
import sonata.kernel.vimadaptor.wrapper.ovsWrapper.OvsWrapper;
import sonata.kernel.vimadaptor.wrapper.sp.ComputeSPWrapper;
import sonata.kernel.vimadaptor.wrapper.sp.NetworkSPWrapper;
import sonata.kernel.vimadaptor.wrapper.kubernetes.KubernetesWrapper;

public class WrapperFactory {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(WrapperFactory.class);

  /**
   * Uses the parser configuration to create the relevant Wrapper.
   * 
   * @param config the WrapperConfiguration object describing the wrapper to create.
   * @return the brand new wrapper
   */
  public static Wrapper createWrapper(WrapperConfiguration config) {
    Wrapper output = null;
    Logger.debug("Factory - Creating wrapper...");
    if (config.getWrapperType().equals(WrapperType.COMPUTE)) {
      Logger.debug("Factory - Creating Compute Wrapper.");
      output = createComputeWrapper(config);
    }
    if (config.getWrapperType().equals(WrapperType.NETWORK)) {
      Logger.debug("Factory - Creating Network Wrapper.");
      output = createNetworkWrapper(config);
    }
    if (config.getWrapperType().equals(WrapperType.STORAGE)) {
      Logger.debug("Factory - Creating Storage Wrapper.");
      output = createStorageWrapper(config);
    }
    if (output != null) {
      Logger.debug("Factory - Wrapper created.");
    } else {
      Logger.debug("Factory - Unable to create wrapper.");

    }
    return output;
  }

  private static ComputeWrapper createComputeWrapper(WrapperConfiguration config) {
    ComputeWrapper output = null;

    if (config.getVimVendor().equals(ComputeVimVendor.MOCK)) {
      output = new ComputeMockWrapper(config);
    } else if (config.getVimVendor().equals(ComputeVimVendor.HEAT)) {
      output = new OpenStackHeatWrapper(config);
    } else if (config.getVimVendor().equals(ComputeVimVendor.SPVIM)) {
      output = new ComputeSPWrapper(config);
    } else if (config.getVimVendor().equals(ComputeVimVendor.KUBERNETES)) {
      output = new KubernetesWrapper(config);
    }
    // TODO Extends with all wrappers or refactor with a more OO type
    // generation

    return output;
  }

  private static NetworkWrapper createNetworkWrapper(WrapperConfiguration config) {
    NetworkWrapper output = null;
    if (config.getVimVendor().equals(NetworkVimVendor.OVS)) {
      output = new OvsWrapper(config);
    } else if (config.getVimVendor().equals(NetworkVimVendor.NETWORKMOCK)) {
      output = new NetworkMockWrapper(config);
    } else if (config.getVimVendor().equals(NetworkVimVendor.SPVIM)) {
      output = new NetworkSPWrapper(config);
    }
    return output;
  }

  private static StorageWrapper createStorageWrapper(WrapperConfiguration config) {
    return null;
  }
}
