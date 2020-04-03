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


import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import sonata.kernel.vimadaptor.commons.IpNetPool;
import sonata.kernel.vimadaptor.commons.VimNetTable;

import java.util.ArrayList;
import java.util.UUID;

/**
 * Unit test for simple App.
 */
public class IpNetPoolTest {
  private IpNetPool pool;

  /**
   * Create the test case
   *
   * @param testName name of the test case
   */
  @Before
  public void setUp() {
    VimNetTable.getInstance().registerVim("1111-1111", null);
    pool = VimNetTable.getInstance().getNetPool("1111-1111");
    System.setProperty("org.apache.commons.logging.Log",
        "org.apache.commons.logging.impl.SimpleLog");

    System.setProperty("org.apache.commons.logging.simplelog.showdatetime", "false");

    System.setProperty("org.apache.commons.logging.simplelog.log.httpclient.wire.header", "warn");

    System.setProperty("org.apache.commons.logging.simplelog.log.org.apache.commons.httpclient",
        "warn");
  }



  /**
   * Allocate and de-allocate a subnet range.
   * 
   * 
   */
  @Test
  public void testReserveSubnetRange() throws Exception {


    int totSubnet = pool.getFreeSubnetsNumber();
    int neededSubnet = 100;
    String instanceUuid = UUID.randomUUID().toString();
    ArrayList<String> myPool = pool.reserveSubnets(instanceUuid, neededSubnet);
    int availableSubnet = pool.getFreeSubnetsNumber();
    Assert.assertNotNull("Null pool returned from allocation", myPool);

    Assert.assertTrue("Subnets have not been reserved",
        totSubnet == (availableSubnet + neededSubnet));

    pool.freeSubnets(instanceUuid);

    availableSubnet = pool.getFreeSubnetsNumber();

    Assert.assertTrue("Subnets have not been freed", totSubnet == availableSubnet);
  }

  /**
   * Try to allocate too many subnets.
   * 
   * 
   */
  @Test
  public void testReserveSubnetRangeTooMany() {

    pool = VimNetTable.getInstance().getNetPool("1111-1111");
    int totSubnet = pool.getFreeSubnetsNumber();
    String instanceUuid = UUID.randomUUID().toString();
    ArrayList<String> myPool = pool.reserveSubnets(instanceUuid, totSubnet + 1);

    Assert.assertNull(
        "More reserved subnets than available subnets, result should be null and it's not.",
        myPool);

  }

  /**
   * Try a double allocation. Get the same
   * 
   * 
   */
  @Test
  public void testReserveSubnetRangeTwice() {

    pool = VimNetTable.getInstance().getNetPool("1111-1111");
    int numOfSubnet = 100;
    String instanceUuid1 = UUID.randomUUID().toString();
    ArrayList<String> myPool = pool.reserveSubnets(instanceUuid1, numOfSubnet);

    Assert.assertNotNull("Reservation gave unexpected null result.", myPool);

    ArrayList<String> mySecondPool = pool.reserveSubnets(instanceUuid1, numOfSubnet);

    Assert.assertNotNull("Second reservation gave unexpected null result.", mySecondPool);

    Assert.assertTrue("The two reservation should be equals. They are not.",
        myPool.equals(mySecondPool));
  }

  /**
   * Get the gateway of a network.
   * 
   * 
   */
  @Test
  public void testGetGateway() {

    pool = VimNetTable.getInstance().getNetPool("1111-1111");
    String gateway = pool.getGateway("192.168.0.0/24");
    Assert.assertTrue("Unexpected gateway.", gateway.equals("192.168.0.1"));
    gateway = pool.getGateway("192.168.0.8/29");
    Assert.assertTrue("Unexpected gateway.", gateway.equals("192.168.0.9"));
    gateway = pool.getGateway("172.0.0.0/29");
    Assert.assertTrue("Unexpected gateway.", gateway.equals("172.0.0.1"));


  }

  @After
  public void deregisterTestVim() {
    VimNetTable.getInstance().deregisterVim("1111-1111");
  }
}
