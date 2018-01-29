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

package sonata.kernel.WimAdaptor.messaging;

public class ServicePlatformMessage {

  String body;
  String topic;
  String replyTo;
  String sid;
  String contentType;

  /**
   * Create the Service Platform Message.
   * 
   * @param message a JSON or YAML formatted String to wrap in the SP Message
   * @param topic the topic on which the message has been received
   * @param sid the session ID of this message
   * @param reply the topic on which a response is expected. null if no response is expected.
   */
  public ServicePlatformMessage(String message, String contentType, String topic, String sid,
      String reply) {
    body = message;
    this.topic = topic;
    this.sid = sid;
    this.replyTo = reply;
    this.contentType = contentType;
  }

  public String getReplyTo() {
    return replyTo;
  }

  public void setReplyTo(String reply) {
    this.replyTo = reply;
  }

  /**
   * @return a String representing the message wrapped in this object.
   */
  public String getBody() {
    return body;
  }

  /**
   * set the topic of this message.
   * 
   * @param topic a String representing the Topic to set
   */
  public void setTopic(String topic) {
    this.topic = topic;
  }

  /**
   * @return a String representing the topic of this message.
   */
  public String getTopic() {
    return topic;
  }

  /**
   * @return a String representing the session ID of this message.
   */
  public String getSid() {
    return this.sid;
  }

  @Override
  public String toString() {
    return "sid: " + sid + " - message: " + body + " - topic: " + topic;
  }


  public String getContentType() {
    return contentType;
  }

}
