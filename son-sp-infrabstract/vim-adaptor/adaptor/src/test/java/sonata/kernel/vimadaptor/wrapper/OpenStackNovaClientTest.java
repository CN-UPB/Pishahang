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
 * @author Bruno Vidalenc, THALES
 * 
 */

package sonata.kernel.vimadaptor.wrapper;


import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;

import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.openstack.Flavor;
import sonata.kernel.vimadaptor.wrapper.openstack.OpenStackNovaClient;

import java.io.IOException;
import java.util.ArrayList;


public class OpenStackNovaClientTest {

  private OpenStackNovaClient novaClient;

  @Before
  public void initClient() throws IOException{

    // todo - this needs to be moved to configuration file
    this.novaClient =
        new OpenStackNovaClient("openstack.sonata-nfv.eu", "op_sonata", "op_s0n@t@", "default", "op_sonata",null);

  }


  /**
   * Test a flavor get.
   *
   * @throws IOException
   */
  @Ignore
  public void testFlavors() throws IOException {

    // System.out.println(novaClient);
    // list the flavors
    ArrayList<Flavor> vimFlavors = novaClient.getFlavors();
    System.out.println(vimFlavors);
    Assert.assertNotNull("Failed to retreive flavors", vimFlavors);

  }

  /**
   * Test a limits get.
   *
   * @throws IOException
   */
  @Ignore
  public void testLimits() throws IOException {
    System.out.println(novaClient);
    ResourceUtilisation resources = novaClient.getResourceUtilizasion();
    System.out.println(resources);
    Assert.assertNotNull("Failed to retrieve limits", resources);
  }

}
