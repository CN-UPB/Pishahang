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
 * @author Adel Zaalouk (Ph.D.), NEC
 * 
 */

package sonata.kernel.vimadaptor.wrapper.openstack.javastackclient;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import org.apache.http.HttpResponse;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Paths;

import javax.ws.rs.NotFoundException;

public class JavaStackUtils {

  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(JavaStackCore.class);

  public static String convertHttpResponseToString(HttpResponse response) throws IOException {

    int status = response.getStatusLine().getStatusCode();
    String statusCode = Integer.toString(status);
    String reasonPhrase = response.getStatusLine().getReasonPhrase();

    if (statusCode.startsWith("2") || statusCode.startsWith("3")) {
      Logger.debug("Response Received with Status: " + response.getStatusLine().getStatusCode());

      StringBuilder sb = new StringBuilder();
      if (response.getEntity() != null) {
        BufferedReader reader =
            new BufferedReader(new InputStreamReader(response.getEntity().getContent()));

        String line;
        while ((line = reader.readLine()) != null) {
          sb.append(line);
        }
        // Logger.debug("Response: " + sb.toString());
        return sb.toString();
      } else {
        return null;
      }
    } else if (status == 404) {
      throw new NotFoundException("Resource doesn't exists");
    } else if (status == 403) {
      throw new IOException(
          "Access forbidden, make sure you are using the correct credentials: " + reasonPhrase);
    } else if (status == 409) {
      throw new IOException("Stack is already created, conflict detected: " + reasonPhrase);
    } else {
      throw new IOException("Failed Request: " + reasonPhrase);
    }
  }

  public static String convertYamlToJson(String yamlToConvert) throws IOException {
    ObjectMapper yamlReader = new ObjectMapper(new YAMLFactory());
    Object obj = yamlReader.readValue(yamlToConvert, Object.class);

    ObjectMapper jsonWriter = new ObjectMapper();
    return jsonWriter.writeValueAsString(obj);
  }

  public static String readFile(String filePath) throws IOException {
    return new String(Files.readAllBytes(Paths.get(filePath)));
  }
}

