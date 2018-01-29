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

package sonata.kernel.WimAdaptor.commons.vnfd;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class AssuranceParameter {

  private ArrayList<Violation> violation;
  private int value;
  private Penalty penalty;
  private String formula;
  @JsonProperty("rel_id")
  private String relId;
  private String id;
  private String unit;



  public void setViolation(ArrayList<Violation> violation) {
    this.violation = violation;
  }


  public void setValue(int value) {
    this.value = value;
  }


  public void setPenalty(Penalty penalty) {
    this.penalty = penalty;
  }


  public void setFormula(String formula) {
    this.formula = formula;
  }


  public void setRelId(String relId) {
    this.relId = relId;
  }


  public void setId(String id) {
    this.id = id;
  }


  public void setUnit(String unit) {
    this.unit = unit;
  }


  public ArrayList<Violation> getViolation() {
    return violation;
  }


  public int getValue() {
    return value;
  }


  public Penalty getPenalty() {
    return penalty;
  }


  public String getFormula() {
    return formula;
  }


  public String getRelId() {
    return relId;
  }


  public String getId() {
    return id;
  }


  public String getUnit() {
    return unit;
  }
}
