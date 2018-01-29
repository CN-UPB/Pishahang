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
 * @author Sharon Mendel Brin(Ph.D.), Nokia
 * 
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 */

package sonata.kernel.vimadaptor.wrapper;

import org.apache.commons.io.IOUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Ignore;

import sonata.kernel.vimadaptor.wrapper.openstack.OpenStackHeatClient;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.UUID;


public class OpenStackHeatClientTest {

  private OpenStackHeatClient heatClient;



  @Before
  public void initClient() throws IOException {

    // todo - this needs to be moved to configuration file
    this.heatClient = new OpenStackHeatClient("openstack.sonata-nfv.eu", "op_sonata", "op_s0n@t@",
        "op_sonata", "default",  null);
  }


  /**
   * Test a full flow of: 1-create stack 2-get stack status 3-delete stack
   *
   * @throws IOException
   */
  @Ignore
  public void testStackCreateAndStatusAndDelete() throws IOException {

    final String stackName = "testStack" + UUID.randomUUID().toString().replaceAll("-", "");

    // Heat template to be created - convert from file to string
    String template = convertTemplateFileToString("./YAML/single-vm-heat-example");

    // creat the stack, the output of a successful create process is the uuid of the new stack
    String stackUUID = heatClient.createStack(stackName, template);
    Assert.assertNotNull("Failed to create stack", stackUUID);

    // check the status of the new stack
    if (stackUUID != null) {
      // status after create
      String status = heatClient.getStackStatus(stackName, stackUUID);
      Assert.assertNotNull("Failed to get stack status", status);
      if (status != null) {
        System.out.println("status of stack " + stackName + " is " + status);
        Assert.assertTrue(status.contains("CREATE"));
      }

      // delete the stack, the output of a successful delete process is the String DELETED
      String isDeleted = heatClient.deleteStack(stackName, stackUUID);
      Assert.assertNotNull("Failed to delete stack", isDeleted);
      if (isDeleted != null) {
        System.out.println("status of deleted stack " + stackName + " is " + isDeleted);
        Assert.assertEquals("DELETED", isDeleted);
      }

    }

  }


  /**
   * Checks that when a status of a non existing stack is requested the returned status is null
   *
   * @throws Exception
   */
  @Ignore
  public void testStatusOfNonValidUUID() throws Exception {

    // generate random stack name and random stack uuid
    final String stackName = "testStack" + UUID.randomUUID().toString().replaceAll("-", "");
    final String stackUUID = UUID.randomUUID().toString().replaceAll("-", "");

    // try to get the status of this random uuid and verify it is null
    String isDeleted = heatClient.deleteStack(stackName, stackUUID);
    Assert.assertNull("Non valid delete operation - recieved DELETED of a non existing stack",
        isDeleted);

  }

  @Ignore
  public void testDeleteNonValidUUID() throws Exception {

    final String stackName = "testStack" + UUID.randomUUID().toString().replaceAll("-", "");
    final String stackUUID = UUID.randomUUID().toString().replaceAll("-", "");

    // try to delete the random uuid and verify it is null
    String deleted = heatClient.getStackStatus(stackName, stackUUID);
    Assert.assertNull("Non valid status - recieved status of a non existing stack", deleted);

  }

  private String convertTemplateFileToString(String templatePath) {

    String template = null;

    FileInputStream inputStream = null;
    try {
      inputStream = new FileInputStream(new File(templatePath));
    } catch (FileNotFoundException e) {
      System.out.println("Failed to get template from file" + e.getMessage());
    }


    if (inputStream != null) {
      try {
        template = IOUtils.toString(inputStream);
      } catch (IOException e) {
        System.out.println("Failed to get template from file" + e.getMessage());
      }


    }
    return template;

  }


}
