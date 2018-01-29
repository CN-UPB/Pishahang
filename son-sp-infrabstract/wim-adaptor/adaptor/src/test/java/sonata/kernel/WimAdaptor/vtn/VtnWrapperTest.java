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


import java.util.UUID;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;


import sonata.kernel.WimAdaptor.wrapper.WimVendor;
import sonata.kernel.WimAdaptor.wrapper.WrapperConfiguration;
import sonata.kernel.WimAdaptor.wrapper.vtn.VTNCreateRequest;
import sonata.kernel.WimAdaptor.wrapper.vtn.VtnWrapper;

public class VtnWrapperTest {

  private VtnWrapper wrapper;

  private String instanceId;
  private String inputSegment;
  private String outputSegment;
  private String[] segmentList;

  @Before
  public void setUp() {
    WrapperConfiguration config = new WrapperConfiguration();
    config.setUuid(UUID.randomUUID().toString());
    config.setWrapperType("WIM");
    config.setWimVendor(WimVendor.getByName("VTN"));
    config.setWimEndpoint("10.30.0.13");
    config.setAuthUserName("stavros");
    config.setAuthPass("st@vr0s");
    config.setName("localTestWim");
    wrapper = new VtnWrapper(config);
    // System.out.println("Wrapper info:");
    // System.out.println(wrapper.getConfig());
    UUID uuid = UUID.randomUUID();
    instanceId = uuid.toString();
    inputSegment = "10.100.0.1/24";
    outputSegment = "10.100.0.40/32";
    segmentList = new String[2];
    segmentList[0] = "10.100.0.2/24";
    segmentList[1] = "10.100.0.5/24";
  }

  @Ignore
  public void testVtnWrapperConfigure() {

    System.out.println();
    System.out.println("Configure VTN rules test for instanceId "+instanceId);
    boolean out = wrapper.configureNetwork(instanceId, inputSegment, outputSegment, segmentList);
    Assert.assertTrue("Configuration call returned failed and returned \"false\" value",out);
    System.out.println("Delete VTN rules test for instanceId "+instanceId);
    out = wrapper.removeNetConfiguration(instanceId);
    Assert.assertTrue("Configuration call returned failed and returned \"false\" value", out);
  }


  @Ignore
  public void testVtnWrapperConfigureTwice() {

    System.out.println();
    System.out.println("Configure two VTN rules test for instanceId "+ instanceId);
    boolean out = wrapper.configureNetwork(instanceId, inputSegment, outputSegment, segmentList);
    Assert.assertTrue("First configuration call returned failed and returned \"false\" value",out);
    out = wrapper.configureNetwork(instanceId, inputSegment, outputSegment, segmentList);
    Assert.assertTrue("Second configuration call returned failed and returned \"false\" value",out);
    System.out.println("Delete VTN rules test for instanceId "+instanceId);
    out = wrapper.removeNetConfiguration(instanceId);
    Assert.assertTrue("Configuration call returned failed and returned \"false\" value", out);
  }
  
  @Ignore
  public void testVtnWrapperList() {
    System.out.println();
    System.out.println("List VTN rules test");
    VTNCreateRequest[] out = wrapper.listVTNRuleset();
    Assert.assertNotNull(out);
    System.out.println("Returned list of rules");
    System.out.println(out);
  }
}
