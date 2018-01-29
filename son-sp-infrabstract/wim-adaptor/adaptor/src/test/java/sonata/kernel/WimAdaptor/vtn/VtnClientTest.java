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


package sonata.kernel.WimAdaptor.vtn;


import java.io.IOException;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;

import sonata.kernel.WimAdaptor.wrapper.vtn.VtnClient;


/**
 * Unit test for simple App.
 */
public class VtnClientTest {

  private VtnClient client;

  /**
   * Create the Wim.
   * 
   * @throws IOException
   */
  @Before
  public void testCreateWimRepo() {

    client = new VtnClient("10.30.0.13", "admin", "admin");
  }

  @Ignore
  public void testAddDeleteVtn() {
    System.out.println("Adding and deleting a test VTN");
    boolean create = client.setupVtn("TestVtn01");
    boolean delete = client.deleteVtn("TestVtn01");
    Assert.assertTrue("Cannot create the test VTN", create);
    Assert.assertTrue("Cannot delete the test VTN", delete);
    System.out.println("DONE");
  }

  @Ignore
  public void testDeleteNonEsistingVtn() {
    System.out.println("Deleting a non existing VTN");
    boolean delete = client.deleteVtn("TestVtn01");
    Assert.assertFalse("Cannot delete the test VTN", delete);
  }

  @Ignore
  public void testAddDeleteFlowRule() {
    System.out.println("Adding a flow rule");
    boolean create = client.setupVtn("TestVtn01");
    boolean setup = client.setupFlow("TestVtn01", "Instance0000");
    boolean delete = client.deleteVtn("TestVtn01");
    Assert.assertTrue("Cannot create the test VTN to setup the flow", create);
    Assert.assertTrue("Cannot setup the Flow Rule", setup);
    Assert.assertTrue("Cannot delete the test VTN after the flow setup", delete);
  }
}
