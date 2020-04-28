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

package sonata.kernel.vimadaptor.commons.vnfd;

import com.fasterxml.jackson.annotation.JsonProperty;

import sonata.kernel.vimadaptor.commons.vnfd.Unit.TimeUnit;

import java.util.ArrayList;

public class VduMonitoringRules {


  private String condition;
  private String description;
  private double duration;
  @JsonProperty("duration_unit")
  private TimeUnit durationUnit;
  private String name;
  private ArrayList<Notification> notification;

  public String getCondition() {
    return condition;
  }

  public String getDescription() {
    return description;
  }

  public double getDuration() {
    return duration;
  }

  public TimeUnit getDurationUnit() {
    return durationUnit;
  }

  public String getName() {
    return name;
  }

  public ArrayList<Notification> getNotification() {
    return notification;
  }

  public void setCondition(String condition) {
    this.condition = condition;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public void setDuration(double duration) {
    this.duration = duration;
  }

  public void setDurationUnit(TimeUnit durationUnit) {
    this.durationUnit = durationUnit;
  }

  public void setName(String name) {
    this.name = name;
  }

  public void setNotification(ArrayList<Notification> notification) {
    this.notification = notification;
  }



}
