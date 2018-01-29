/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, THALES, NCSR Demokritos ALL RIGHTS RESERVED. <p>
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at <p>
 * http://www.apache.org/licenses/LICENSE-2.0 <p> Unless required by applicable law or agreed to in
 * writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 * language governing permissions and limitations under the License. <p> Neither the name of the
 * SONATA-NFV, UCL, NOKIA, THALES NCSR Demokritos nor the names of its contributors may be used to
 * endorse or promote products derived from this software without specific prior written permission.
 * <p> This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 * @author Bruno Vidalenc (Ph.D.), THALES
 */

package sonata.kernel.vimadaptor.wrapper.openstack;


import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.JavaStackCore;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.JavaStackUtils;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.compute.FlavorProperties;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.compute.FlavorsData;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.compute.LimitsData;

import java.io.IOException;
import java.util.ArrayList;

/**
 * This class wraps a Nova Client written in python when instantiated the onnection details of the
 * OpenStack instance should be provided.
 *
 */
public class OpenStackNovaClient {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(OpenStackNovaClient.class);

  // private String url; // url of the OpenStack Client

  // private String userName; // OpenStack Client user
  //
  // private String password; // OpenStack Client password
  //
  // private String tenantName; // OpenStack tenant name
  //
  // private String identityPort; // Custom Identity Port

  private JavaStackCore javaStack; // instance for calling OpenStack APIs

  private ObjectMapper mapper;

  /**
   * Construct a new Openstack Nova Client.
   *
   * @param url of the OpenStack endpoint
   * @param userName to log into the OpenStack service
   * @param password to log into the OpenStack service
   * @param domain to log into the OpenStack service
   * @param tenantName to log into the OpenStack service
   * @throws IOException if the authentication process fails
   */
  public OpenStackNovaClient(String url, String userName, String password, String domain, String tenantName,
      String identityPort) throws IOException {
    // this.url = url;
    // this.userName = userName;
    // this.password = password;
    // this.tenantName = tenantName;
    // this.identityPort = identityPort;

    Logger.debug(
        "URL:" + url + "|User:" + userName + "|Project:" + tenantName + "|Pass:" + password + "|Domain:" + domain + "|");

    javaStack = JavaStackCore.getJavaStackCore();

    javaStack.setEndpoint(url);
    javaStack.setUsername(userName);
    javaStack.setPassword(password);
    javaStack.setDomain(domain);
    javaStack.setProjectId(tenantName);
    javaStack.setAuthenticated(false);
    // javaStack.setTenantId(tenantName);

    // Authenticate
    // try {
    javaStack.authenticateClientV3(identityPort);
    // } catch (IOException e) {
    // e.printStackTrace();
    // }
  }

  /**
   * Get the flavors.
   *
   * @return the flavors
   */
  public ArrayList<Flavor> getFlavors() {

    Flavor output_flavor = null;
    String flavorName = null;
    int cpu, ram, disk;

    ArrayList<Flavor> output_flavors = new ArrayList<>();
    Logger.info("Getting flavors");
    try {
      mapper = new ObjectMapper();
      String listFlavors =
          JavaStackUtils.convertHttpResponseToString(javaStack.listComputeFlavors());
      System.out.println(listFlavors);
      FlavorsData inputFlavors = mapper.readValue(listFlavors, FlavorsData.class);
      System.out.println(inputFlavors.getFlavors());
      for (FlavorProperties input_flavor : inputFlavors.getFlavors()) {
        System.out.println(input_flavor.getId() + ": " + input_flavor.getName());

        flavorName = input_flavor.getName();
        cpu = Integer.parseInt(input_flavor.getVcpus());
        ram = Integer.parseInt(input_flavor.getRam());
        disk = Integer.parseInt(input_flavor.getDisk());

        output_flavor = new Flavor(flavorName, cpu, ram, disk);
        output_flavors.add(output_flavor);
      }

    } catch (Exception e) {
      Logger.error("Runtime error getting openstack flavors" + " error message: " + e.getMessage());
    }

    return output_flavors;

  }

  /**
   * Get the limits and utilisation.
   *
   * @return a ResourceUtilisation Object with the limits and utilization for this tenant
   */
  public ResourceUtilisation getResourceUtilizasion() {

    int totalCores, usedCores, totalMemory, usedMemory;

    ResourceUtilisation resources = new ResourceUtilisation();
    Logger.info("Getting limits");
    try {
      String listLimits = JavaStackUtils.convertHttpResponseToString(javaStack.listComputeLimits());

      mapper = new ObjectMapper();
      LimitsData data = mapper.readValue(listLimits, LimitsData.class);

      totalCores = Integer.parseInt(data.getLimits().getAbsolute().getMaxTotalCores());
      Logger.debug("Total Core: " + totalCores);

      usedCores = Integer.parseInt(data.getLimits().getAbsolute().getTotalCoresUsed());
      Logger.debug("Used Cores: " + usedCores);

      totalMemory = Integer.parseInt(data.getLimits().getAbsolute().getMaxTotalRAMSize());
      Logger.debug("Total Memory:" + totalMemory);

      usedMemory = Integer.parseInt(data.getLimits().getAbsolute().getTotalRAMUsed());
      Logger.debug("Used Memory:" + usedMemory);


      // Set the resources values
      resources.setTotCores(totalCores);
      resources.setUsedCores(usedCores);
      resources.setTotMemory(totalMemory);
      resources.setUsedMemory(usedMemory);

    } catch (Exception e) {
      Logger.error("Runtime error getting openstack limits" + " error message: " + e.getMessage(),
          e);
    }

    return resources;
  }


  // @Override
  // public String toString() {
  // return "OpenStackNovaClient{" + "url='" + url + '\'' + ", userName='" + userName + '\''
  // + ", password='" + password + '\'' + ", tenantName='" + tenantName + '\'' + '}';
  // }

}
