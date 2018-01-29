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

package sonata.kernel.vimadaptor.wrapper.ovsWrapper;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class OvsPayload {

  @JsonProperty("action")
  String action;

  @JsonProperty("in_segment")
  String inputSegment;
  @JsonProperty("instance_id")
  String instanceId;
  @JsonProperty("port_list")
  ArrayList<OrderedMacAddress> odlList;
  @JsonProperty("out_segment")
  String outputSegment;

  /**
   * @param string
   * @param string2
   * @param odlList2
   */
  public OvsPayload(String action, String instanceId, String inSeg, String outSeg,
      ArrayList<OrderedMacAddress> odlList2) {
    this.inputSegment = inSeg;
    this.outputSegment = outSeg;
    if (odlList2 != null) {
      @SuppressWarnings("unchecked")
      ArrayList<OrderedMacAddress> clone = (ArrayList<OrderedMacAddress>) odlList2.clone();
      this.odlList = clone;
    }
    this.instanceId = instanceId;
    this.action = action;
  }

}
