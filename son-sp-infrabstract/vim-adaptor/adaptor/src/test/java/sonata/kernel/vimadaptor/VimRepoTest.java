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

package sonata.kernel.vimadaptor;


import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import sonata.kernel.vimadaptor.wrapper.ComputeVimVendor;
import sonata.kernel.vimadaptor.wrapper.ComputeWrapper;
import sonata.kernel.vimadaptor.wrapper.NetworkVimVendor;
import sonata.kernel.vimadaptor.wrapper.NetworkWrapper;
import sonata.kernel.vimadaptor.wrapper.VimRepo;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.WrapperType;
import sonata.kernel.vimadaptor.wrapper.mock.ComputeMockWrapper;
import sonata.kernel.vimadaptor.wrapper.ovsWrapper.OvsWrapper;

import java.io.IOException;
import java.util.ArrayList;


/**
 * Unit test for simple App.
 */
public class VimRepoTest {

  private VimRepo repoInstance;

  
  @Before
  public void setUp(){
    System.setProperty("org.apache.commons.logging.Log", "org.apache.commons.logging.impl.SimpleLog");

    System.setProperty("org.apache.commons.logging.simplelog.showdatetime", "false");

    System.setProperty("org.apache.commons.logging.simplelog.log.httpclient.wire.header", "warn");

    System.setProperty("org.apache.commons.logging.simplelog.log.org.apache.commons.httpclient", "warn");
  }
  
  /**
   * Register, send 4 heartbeat, deregister.
   * 
   * @throws IOException
   */
  @Test
  public void testCreateVimRepo() {

    repoInstance = new VimRepo();
    ArrayList<String> vims = repoInstance.getComputeVims();
    Assert.assertNotNull("Unable to retrieve an empy list. SQL exception occurred", vims);
  }

  @Test
  public void testAddVim() {

    repoInstance = new VimRepo();
    WrapperConfiguration config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setDomain("default");
    config.setUuid("12345");
    config.setWrapperType(WrapperType.COMPUTE);
    String configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");

    ComputeWrapper record = new ComputeMockWrapper(config);
    boolean out = repoInstance.writeVimEntry(config.getUuid(), record);


    Assert.assertTrue("Unable to write a vim", out);

    out = repoInstance.removeVimEntry(config.getUuid());
    Assert.assertTrue("unable to remove vim", out);
  }

  @Test
  public void testListVims() {

    repoInstance = new VimRepo();
    WrapperConfiguration config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setDomain("default");
    config.setUuid("1");
    config.setWrapperType(WrapperType.COMPUTE);
    String configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");

    ComputeWrapper wrapper = new ComputeMockWrapper(config);
    boolean out = repoInstance.writeVimEntry(config.getUuid(), wrapper);
    Assert.assertTrue("Unable to write a vim", out);

    config.setUuid("2");
    wrapper = new ComputeMockWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), wrapper);
    Assert.assertTrue("Unable to write a vim", out);

    config.setUuid("3");
    wrapper = new ComputeMockWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), wrapper);
    Assert.assertTrue("Unable to write a vim", out);


    ArrayList<String> vims = repoInstance.getComputeVims();

    Assert.assertTrue("Db doesn't contain all the stored VIMs", vims.contains("1"));
    Assert.assertTrue("Db doesn't contain all the stored VIMs", vims.contains("2"));
    Assert.assertTrue("Db doesn't contain all the stored VIMs", vims.contains("3"));

    out = repoInstance.removeVimEntry("1");
    Assert.assertTrue("unable to remove vim", out);
    out = repoInstance.removeVimEntry("2");
    Assert.assertTrue("unable to remove vim", out);
    out = repoInstance.removeVimEntry("3");
    Assert.assertTrue("unable to remove vim", out);
  }

  @Test
  public void testAddInstance() {

    repoInstance = new VimRepo();

    boolean out = repoInstance.writeServiceInstanceEntry("1", "1-1", "stack1-1",
        "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while writing the instance", out);

    out = repoInstance.removeServiceInstanceEntry("1", "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while removing the instance", out);

  }

  @Test
  public void testGetInstanceVimUuid() {

    repoInstance = new VimRepo();

    boolean out = repoInstance.writeServiceInstanceEntry("1", "1-1", "stack1-1",
        "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while writing the instance", out);

    String vimUuid = repoInstance.getServiceInstanceVimUuid("1");

    Assert.assertTrue("Retrieved vim UUID different from the stored UUID", vimUuid.equals("1-1"));

    out = repoInstance.removeServiceInstanceEntry("1", "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while removing the instance", out);
  }

  @Test
  public void testGetInstanceVimName() {

    repoInstance = new VimRepo();

    boolean out = repoInstance.writeServiceInstanceEntry("1", "1-1", "stack1-1",
        "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while writing the instance", out);

    String vimName = repoInstance.getServiceInstanceVimName("1");

    Assert.assertTrue("Retrieved vim Name different from the stored Name",
        vimName.equals("stack1-1"));

    out = repoInstance.removeServiceInstanceEntry("1", "xxxx-xxxxxxxx-xxxxxxxx-xxxx");

    Assert.assertTrue("Errors while removing the instance", out);

  }

  @Test
  public void testFunctionInstance() {
    repoInstance = new VimRepo();
    boolean out = repoInstance.writeServiceInstanceEntry("1", "1-1", "stack1-1", "xxxx-xxxx");
    Assert.assertTrue("Errors while writing the service instance", out);
    out = repoInstance.writeServiceInstanceEntry("1", "a-1", "stacka-1", "yyyy-yyyy");
    Assert.assertTrue("Errors while writing the service instance", out);
    out = repoInstance.writeFunctionInstanceEntry("0001", "1", "xxxx-xxxx");
    Assert.assertTrue("Errors while writing the function instance", out);
    out = repoInstance.writeFunctionInstanceEntry("0002", "1", "xxxx-xxxx");
    Assert.assertTrue("Errors while writing the function instance", out);
    out = repoInstance.writeFunctionInstanceEntry("0003", "1", "yyyy-yyyy");
    Assert.assertTrue("Errors while writing the function instance", out);
    out = repoInstance.writeFunctionInstanceEntry("0004", "1", "yyyy-yyyy");
    Assert.assertTrue("Errors while writing the function instance", out);

    String vimUuid = repoInstance.getComputeVimUuidByFunctionInstanceId("0003");

    String stackId = repoInstance.getServiceInstanceVimUuidByFunction("0003");
    System.out.println("Function Instance 0003 is at VIM " + vimUuid + " with stack id " + stackId);
    Assert.assertTrue(vimUuid.equals("yyyy-yyyy"));
    Assert.assertTrue(stackId.equals("a-1"));

    out = repoInstance.writeFunctionInstanceEntry("0005", "1", "zzzz-zzzz");

    Assert.assertFalse(out);

    repoInstance.removeServiceInstanceEntry("1", "xxxx-xxxx");
    repoInstance.removeServiceInstanceEntry("1", "yyyy-yyyy");
    stackId = repoInstance.getServiceInstanceVimUuidByFunction("0001");
    Assert.assertNull(stackId);
    stackId = repoInstance.getServiceInstanceVimUuidByFunction("0002");
    Assert.assertNull(stackId);
    stackId = repoInstance.getServiceInstanceVimUuidByFunction("0003");
    Assert.assertNull(stackId);
    stackId = repoInstance.getServiceInstanceVimUuidByFunction("0004");
    Assert.assertNull(stackId);

  }

  @Test
  public void testNetworkingVim() {

    repoInstance = new VimRepo();
    String computeUuid = "12345777";
    String networkingUuid = "abcde";

    WrapperConfiguration config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(ComputeVimVendor.MOCK);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setDomain("default");
    config.setUuid(computeUuid);
    config.setWrapperType(WrapperType.COMPUTE);
    String configs =
        "{\"tenant\":\"the_tenant\",\"tenant_ext_net\":\"ext_net\",\"tenant_ext_router\":\"ext_router\"}";
    config.setConfiguration(configs);
    config.setCity("London");
    config.setCountry("England");
    ComputeWrapper computeWrapper = new ComputeMockWrapper(config);
    boolean out = repoInstance.writeVimEntry(config.getUuid(), computeWrapper);
    Assert.assertTrue("Unable to write the compute vim", out);

    config = new WrapperConfiguration();
    config.setVimEndpoint("x.x.x.x");
    config.setVimVendor(NetworkVimVendor.OVS);
    config.setAuthUserName("operator");
    config.setAuthPass("apass");
    config.setDomain("default");
    config.setUuid(networkingUuid);
    config.setWrapperType(WrapperType.NETWORK);
    config.setConfiguration("{\"compute_uuid\":\"" + computeUuid + "\"}");
    NetworkWrapper netWrapper = new OvsWrapper(config);
    out = repoInstance.writeVimEntry(config.getUuid(), netWrapper);
    Assert.assertTrue("Unable to write the networking vim", out);

    out = repoInstance.writeNetworkVimLink(computeUuid, networkingUuid);
    Assert.assertTrue("Unable to write compute/networking association", out);

    String netVimUuid = repoInstance.getNetworkVimFromComputeVimUuid(computeUuid);
    NetworkWrapper netRecord = repoInstance.getNetworkVim(netVimUuid);

    Assert.assertNotNull("Retrieved netVim is null", netRecord);
    Assert.assertNotNull("Retrieved netVim has null configuration", netRecord.getConfig());

    Assert.assertTrue("The retrieved vim is not a networking vim",
        netRecord.getConfig().getWrapperType().equals(WrapperType.NETWORK));
    Assert.assertTrue("Unexpected networking vim uuid",
        netRecord.getConfig().getUuid().equals(networkingUuid));

    out = repoInstance.writeNetworkVimLink("zxyz", networkingUuid);
    Assert.assertFalse("Error. I managed to link the net VIM to a-non existing compute VIM", out);

    out = repoInstance.writeNetworkVimLink(computeUuid, "hhhhh");
    Assert.assertFalse("Error. I managed to link the compute VIM to a-non existing net VIM", out);

    out = repoInstance.removeVimEntry(networkingUuid);
    Assert.assertTrue("unable to remove vim", out);
    out = repoInstance.removeVimEntry(computeUuid);
    Assert.assertTrue("unable to remove vim", out);
  }
}
