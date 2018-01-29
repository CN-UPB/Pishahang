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

package sonata.kernel.WimAdaptor.wrapper;

import java.util.ArrayList;

public class WrapperConfiguration {

  private String wimEndpoint;
  private WimVendor wimVendor;
  private String wrapperType;
  private String authUserName;
  private String authPass;
  private String authKey;
  private String name;
  private String uuid;
  private ArrayList<String> attachedVims;

  public String getWrapperType() {
    return wrapperType;
  }

  public void setWrapperType(String wrapperType) {
    this.wrapperType = wrapperType;
  }

  public String getWimEndpoint() {
    return wimEndpoint;
  }

  public void setWimEndpoint(String wimEndpoint) {
    this.wimEndpoint = wimEndpoint;
  }

  public WimVendor getWimVendor() {
    return wimVendor;
  }

  public void setWimVendor(WimVendor wimType) {
    this.wimVendor = wimType;
  }

  public String getAuthUserName() {
    return authUserName;
  }

  public void setAuthUserName(String authUserName) {
    this.authUserName = authUserName;
  }

  public String getAuthPass() {
    return authPass;
  }

  public void setAuthPass(String authPass) {
    this.authPass = authPass;
  }

  public String getAuthKey() {
    return authKey;
  }

  public void setAuthKey(String authKey) {
    this.authKey = authKey;
  }

  public String getUuid() {
    return this.uuid;
  }

  public void setUuid(String uuid) {
    this.uuid = uuid;
  }

  @Override
  public String toString() {
    String out = "";

    out += "sid: " + uuid + "\n\r";
    out += "WrapperType: " + wrapperType + "\n\r";
    out += "WimVendor: " + wimVendor + "\n\r";
    out += "WimEndpount: " + wimEndpoint + "\n\r";
    out += "User: " + authUserName + "\n\r";
    out += "pass: " + authPass + "\n\r";
    out += "name: " + name + "\n\r";
    out += "attached_vims: \n\r" + attachedVims;
    return out;
  }

  public ArrayList<String> getAttachedVims() {
    return attachedVims;
  }

  public void setAttachedVims(ArrayList<String> attachedVims) {
    this.attachedVims = attachedVims;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

}
