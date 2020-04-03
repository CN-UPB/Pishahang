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
 * @author Dario Valocchi (Ph.D.)
 * 
 */

package sonata.kernel.vimadaptor.wrapper.openstack;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.JavaStackCore;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.JavaStackUtils;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.Image.Image;
import sonata.kernel.vimadaptor.wrapper.openstack.javastackclient.models.Image.Images;

import java.io.IOException;
import java.util.ArrayList;


public class OpenStackGlanceClient {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(OpenStackGlanceClient.class);

  // private String url; // url of the OpenStack Client
  //
  // private String userName; // OpenStack Client user
  //
  // private String password; // OpenStack Client password
  //
  // private String domain; // OpenStack Client domain
  //
  // private String tenantName; // OpenStack tenant name

  private JavaStackCore javaStack; // instance for calling OpenStack APIs

  private ObjectMapper mapper;

  public OpenStackGlanceClient(String url, String userName, String password, String domain, String tenantName,
      String identityPort) throws IOException {
    // this.url = url;
    // this.userName = userName;
    // this.password = password;
    // this.tenantName = tenantName;

    this.mapper = SonataManifestMapper.getSonataMapper();

    Logger.debug(
        "URL: " + url + "|User:" + userName + "|Project:" + tenantName + "|Pass:" + password + "|Domain:" + domain + "|" );

    javaStack = JavaStackCore.getJavaStackCore();
    javaStack.setEndpoint(url);
    javaStack.setUsername(userName);
    javaStack.setPassword(password);
    javaStack.setDomain(domain);
    javaStack.setProjectName(tenantName);
    javaStack.setProjectId(tenantName);
    javaStack.setAuthenticated(false);
    // Authenticate
    javaStack.authenticateClientV3(identityPort);
  }


  /**
   * Create an image place-holder with the given name
   * 
   * @param imageName a String representing the name of the image (in the format
   *        vnf_vendor:vnf_name:vnf_version:vdu_id)
   * @return a String representing the UUID of the image place-holder created
   * @throws IOException
   */
  public String createImage(String imageName) throws IOException {
    Logger.debug("[Glance-client] Creating new image container");
    String response = null;

    response =
        JavaStackUtils.convertHttpResponseToString(javaStack.createImage("", "", "", imageName));

    Image imageContainerData = mapper.readValue(response, Image.class);
    Logger.debug("[Glance-client] Image container creade with UUID: " + imageContainerData.getId());

    return imageContainerData.getId();
  }


  /**
   * List glance Images.
   *
   * @return - A list of image objects containing name, id, and other useful parameters
   */
  public ArrayList<Image> listImages() {

    Logger.debug("Listing available Images");
    Images images = null;

    String listImages = null;
    try {
      listImages = JavaStackUtils.convertHttpResponseToString(javaStack.listImages());
      images = mapper.readValue(listImages, Images.class);
      Logger.debug("Retrieved image list"+images.getImages());
      Logger.debug("Number of retrieved images:"+images.getImages().size());
    } catch (IOException e) {
      e.printStackTrace();
    }
    return images.getImages();
  }

  /**
   * Create an image place-holder with the given name
   * 
   * @param imageId Glance UUID of the image
   * @param imageFileLocalPath the path to the local copy of the image file
   * 
   */
  public void uploadImage(String imageId, String imageFileLocalPath) {
    Logger.debug("[Glance-client] Pushing image binary...");
    try {

      JavaStackUtils.convertHttpResponseToString(
          javaStack.uploadBinaryImageData(null, imageId, imageFileLocalPath));

    } catch (IOException e) {
      e.printStackTrace();
    }

    return;
  }



}
