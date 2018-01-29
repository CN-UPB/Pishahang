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

package sonata.kernel.WimAdaptor.wrapper.vtn;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Properties;
import java.util.UUID;

import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.HttpClientBuilder;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import sonata.kernel.WimAdaptor.commons.SonataManifestMapper;
import sonata.kernel.WimAdaptor.wrapper.WimWrapper;
import sonata.kernel.WimAdaptor.wrapper.WrapperConfiguration;

public class VtnWrapper extends WimWrapper {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(VtnWrapper.class);

  public enum Constants {
    VTN_SERVER_PORT("5000"), VTN_URI("/flowchart/"), ADAPTOR_SEGMENTS_CONF("/adaptor/segments.conf");


    private final String constantValue;

    Constants(String constantValue) {
      this.constantValue = constantValue;
    }

    @Override
    public String toString() {
      return this.constantValue;
    }
  }

  public VtnWrapper(WrapperConfiguration config) {
    super(config);
  }

  @Override
  public String getType() {
    return null;
  }


  @Deprecated
  public boolean configureNetwork(String instanceId) {
    boolean out = true;
    VtnClient client = new VtnClient(this.config.getWimEndpoint(), this.config.getAuthUserName(),
        this.config.getAuthPass());
    /**
     * Logger.info("Setting up the VTN for the service"); out = out && client.setupVtn(instanceId);
     * if (out){ Logger.info("VTN created"); } else { Logger.error("Unable to create VTN"); }
     * Comment it out, as for the moment, new vtn will not be created
     */
    Logger.info("Setting up the flow rules in the VTN");
    out = out && client.setupFlow("vtn7", "green");
    if (out) {
      Logger.info("Flow rules created");
    } else {
      Logger.error("Unable to create flow rules. GOING ON NONETHELESS");
    }
    return out;
  }

  @Override
  public boolean removeNetConfiguration(String instanceId) {
    boolean success = true;
    UUID uuid = UUID.fromString(instanceId);
    Logger.debug("[VTN-Wrapper] UUID : "+uuid.toString());    
      long xor = uuid.getLeastSignificantBits() ^ uuid.getMostSignificantBits();
    String hexString = Long.toHexString(xor);
    Logger.debug("[VTN-Wrapper] UUID digest: "+hexString);
    int numberOfRules = 0;
    VTNCreateRequest[] existingRules = this.listVTNRuleset();
    for (VTNCreateRequest rule : existingRules) {
      if (rule.getInstanceId().startsWith(hexString)) numberOfRules++;
    }
    
    Logger.debug("[VTN-Wrapper] Found "+numberOfRules+" rules for this UUID");
    if(numberOfRules==0){
      Logger.debug("[VTN-Wrapper] No rule in this WIM for this service instance UUID");  
      return true;
    }
    for (int i = 0; i < numberOfRules; i++) {
      // Send HTTP POST to the VTN server

      HttpClient httpClient = HttpClientBuilder.create().build();
      HttpDelete delete;
      HttpResponse response = null;
      StringBuilder buildUrl = new StringBuilder();
      buildUrl.append("http://");
      buildUrl.append(this.config.getWimEndpoint());
      buildUrl.append(":");
      buildUrl.append(Constants.VTN_SERVER_PORT.toString());
      buildUrl.append(Constants.VTN_URI.toString());
      buildUrl.append(hexString + i);

      delete = new HttpDelete(buildUrl.toString());

      Logger.debug("[VTN-Wrapper] Sending rule deletion request");
      Logger.debug("[VTN-Wrapper] " + delete.toString());

      try {
        response = httpClient.execute(delete);
      } catch (ClientProtocolException e) {
        // TODO Auto-generated catch block
        e.printStackTrace();
      } catch (IOException e) {
        // TODO Auto-generated catch block
        e.printStackTrace();
      }

      Logger.debug("[VTN-Wrapper] VTN server response:");
      Logger.debug(response.toString());

      int statusCode = response.getStatusLine().getStatusCode();
      if (statusCode != 200) {
        Logger.error("Error while deconfiguring VTN WIM - instance id: " + instanceId
            + " - rule number: " + i + " response: " + statusCode + " - "
            + response.getStatusLine().getReasonPhrase());
        success = false;
      } else {
        Logger.info("[VTN-Wrapper] Rule " + i + " remove completed.");
      }
    }
    return success;
  }

  @Override
  public boolean configureNetwork(String instanceId, String inputSegment, String outputSegment,
      String[] segmentList) {
    // Send HTTP POST to the VTN server
    HttpClient httpClient = HttpClientBuilder.create().build();

    if(inputSegment==null||outputSegment==null){
      Logger.warn("NAP not specified, using default ones from default config file");
      Properties segments = new Properties();
      try {
        segments.load(new FileReader(new File(Constants.ADAPTOR_SEGMENTS_CONF.toString())));
      inputSegment = segments.getProperty("in");
      outputSegment = segments.getProperty("out");
      } catch (IOException e) {
        e.printStackTrace();
      }
    }
    
    HttpPost post;
    HttpResponse response = null;
    StringBuilder buildUrl = new StringBuilder();
    buildUrl.append("http://");
    buildUrl.append(this.config.getWimEndpoint());
    buildUrl.append(":");
    buildUrl.append(Constants.VTN_SERVER_PORT.toString());
    buildUrl.append(Constants.VTN_URI.toString());

    post = new HttpPost(buildUrl.toString());

    // Forge the JSON body
    UUID uuid = UUID.fromString(instanceId);
    Logger.debug("[VTN-Wrapper] UUID : "+uuid.toString());    
    long xor = uuid.getLeastSignificantBits() ^ uuid.getMostSignificantBits();
    String hexString = Long.toHexString(xor);
    Logger.debug("[VTN-Wrapper] UUID digest: "+hexString);

    int ruleIndex = 0;
    VTNCreateRequest[] existingRules = this.listVTNRuleset();
    for (VTNCreateRequest rule : existingRules) {
      if (rule.getInstanceId().startsWith(hexString)) ruleIndex++;
    }
    String ruleId = hexString + ruleIndex;

    VTNCreateRequest body = new VTNCreateRequest();

    body.setInstanceId(ruleId);
    body.setInSeg(inputSegment);
    body.setOutSeg(outputSegment);
    OrderedSegment[] pops = new OrderedSegment[segmentList.length];
    for (int i = 0; i < pops.length; i++) {
      pops[i] = new OrderedSegment(segmentList[i], i);
    }
    body.setPorts(pops);

    ObjectMapper mapper = SonataManifestMapper.getSonataMapperJson();
    String bodyString;

    try {
      bodyString = mapper.writeValueAsString(body);
    } catch (JsonProcessingException e) {
      Logger.error("[VTN-Wrapper]Unable to generate VTN payload.");
      return false;
    }

    Logger.debug("[VTN-Wrapper] Sending rule creation request");
    Logger.debug("[VTN-Wrapper] " + post.toString());
    Logger.debug("[VTN-Wrapper] " + bodyString);

    post.setEntity(new StringEntity(bodyString, ContentType.APPLICATION_JSON));
    try {
      response = httpClient.execute(post);
    } catch (ClientProtocolException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    } catch (IOException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }

    Logger.debug("[VTN-Wrapper] VTN server response:");
    Logger.debug(response.toString());

    int statusCode = response.getStatusLine().getStatusCode();

    if (statusCode != 200) {
      Logger.error("Error while configuring VTN WIM: " + statusCode + " - "
          + response.getStatusLine().getReasonPhrase());
      return false;
    } else {
      Logger.info("[VTN-Wrapper] VTN-WIM configuration completed.");
      return true;
    }
  }

  public VTNCreateRequest[] listVTNRuleset() {
    // Send HTTP POST to the VTN server

    HttpClient httpClient = HttpClientBuilder.create().build();
    HttpGet post;
    HttpResponse response = null;
    StringBuilder buildUrl = new StringBuilder();
    buildUrl.append("http://");
    buildUrl.append(this.config.getWimEndpoint());
    buildUrl.append(":");
    buildUrl.append(Constants.VTN_SERVER_PORT.toString());
    buildUrl.append(Constants.VTN_URI.toString());

    post = new HttpGet(buildUrl.toString());

    Logger.debug("[VTN-Wrapper] Sending rule list request");
    Logger.debug("[VTN-Wrapper] " + post.toString());

    try {
      response = httpClient.execute(post);
    } catch (ClientProtocolException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    } catch (IOException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }

    Logger.debug("[VTN-Wrapper] VTN server response:");
    Logger.debug(response.toString());
    int statusCode = response.getStatusLine().getStatusCode();

    if (statusCode != 200) {
      Logger.error("Error while deconfiguring VTN WIM: " + statusCode + " - "
          + response.getStatusLine().getReasonPhrase());
      return null;
    } else {
      Logger.info("[VTN-Wrapper] VTN-WIM configuration completed.");

      StringBuilder sb = new StringBuilder();
      if (response.getEntity() != null) {
        BufferedReader reader;
        try {
          reader = new BufferedReader(new InputStreamReader(response.getEntity().getContent()));


          String line;
          while ((line = reader.readLine()) != null) {
            sb.append(line);
          }
          Logger.debug("[VTN-Wrapper] Response body: " + sb.toString());
          ObjectMapper mapper = SonataManifestMapper.getSonataMapper();
          VTNFlows flows = mapper.readValue(sb.toString(), VTNFlows.class);
          VTNCreateRequest[] output = new VTNCreateRequest[flows.getFlows().length];
          for (int i = 0; i < output.length; i++) {
            output[i] = flows.getFlows()[i].getData();
          }
          return output;
        } catch (UnsupportedOperationException | IOException e) {
          e.printStackTrace();
          return null;
        }
      } else {
        return null;
      }
    }
  }

}
