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

package sonata.kernel.vimadaptor.commons;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import sonata.kernel.vimadaptor.commons.vnfd.Unit;
import sonata.kernel.vimadaptor.commons.vnfd.UnitDeserializer;

public class SonataManifestMapper {

  private static SonataManifestMapper myInstance = null;

  public static ObjectMapper getSonataMapper() {
    if (myInstance == null) myInstance = new SonataManifestMapper();
    return myInstance.getMapper();
  }
  
  public static ObjectMapper getSonataJsonMapper() {
    if (myInstance == null) myInstance = new SonataManifestMapper();
    return myInstance.getJsonMapper();
  }

  private ObjectMapper mapperYaml;
  private ObjectMapper mapperJson;

  private SonataManifestMapper() {
    this.mapperYaml = new ObjectMapper(new YAMLFactory());
    SimpleModule module = new SimpleModule();
    module.addDeserializer(Unit.class, new UnitDeserializer());
    // module.addDeserializer(VmFormat.class, new VmFormatDeserializer());
    // module.addDeserializer(ConnectionPointType.class, new ConnectionPointTypeDeserializer());
    mapperYaml.registerModule(module);
    mapperYaml.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
    mapperYaml.enable(DeserializationFeature.READ_ENUMS_USING_TO_STRING);
    mapperYaml.disable(SerializationFeature.WRITE_EMPTY_JSON_ARRAYS);
    mapperYaml.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);
    mapperYaml.disable(SerializationFeature.WRITE_NULL_MAP_VALUES);
    mapperYaml.setSerializationInclusion(Include.NON_NULL);
    
    this.mapperJson = new ObjectMapper();
    module = new SimpleModule();
    module.addDeserializer(Unit.class, new UnitDeserializer());
    // module.addDeserializer(VmFormat.class, new VmFormatDeserializer());
    // module.addDeserializer(ConnectionPointType.class, new ConnectionPointTypeDeserializer());
    mapperJson.registerModule(module);
    mapperJson.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
    mapperJson.enable(DeserializationFeature.READ_ENUMS_USING_TO_STRING);
    mapperJson.disable(SerializationFeature.WRITE_EMPTY_JSON_ARRAYS);
    mapperJson.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);
    mapperJson.disable(SerializationFeature.WRITE_NULL_MAP_VALUES);
    mapperJson.setSerializationInclusion(Include.NON_NULL);
  }

  private ObjectMapper getMapper() {
    return this.mapperYaml;
  }
  private ObjectMapper getJsonMapper() {
    return this.mapperJson;
  }

}
