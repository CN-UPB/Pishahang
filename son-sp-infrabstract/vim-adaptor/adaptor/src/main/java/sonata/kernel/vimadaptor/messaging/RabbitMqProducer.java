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

package sonata.kernel.vimadaptor.messaging;

import com.rabbitmq.client.AMQP.BasicProperties;
import com.rabbitmq.client.Channel;

import org.slf4j.LoggerFactory;

import sonata.kernel.vimadaptor.AdaptorCore;

import java.util.concurrent.BlockingQueue;

public class RabbitMqProducer extends AbstractMsgBusProducer {


  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(RabbitMqProducer.class);


  public RabbitMqProducer(BlockingQueue<ServicePlatformMessage> muxQueue) {
    super(muxQueue);
  }

  @Override
  public void connectToBus() {
    // Do nothing
  }

  @Override
  public boolean sendMessage(ServicePlatformMessage message) {
    boolean out = true;

    // TODO maps the specific Adaptor message to the proper SP topic

    try {
      Channel channel = RabbitMqHelperSingleton.getInstance().getChannel();
      String exchangeName = RabbitMqHelperSingleton.getInstance().getExchangeName();
      BasicProperties properties = new BasicProperties().builder().appId(AdaptorCore.APP_ID)
          .contentType(message.getContentType()).replyTo(message.getReplyTo()).deliveryMode(2)
          .correlationId(message.getSid()).build();
      channel.basicPublish(exchangeName, message.getTopic(), properties,
          message.getBody().getBytes("UTF-8"));
      //Logger.info("Sending message: " + message + "\n\r - Properties:" + properties);
    } catch (Exception e) {
      Logger.error(e.getMessage(), e);
      out = false;
    }
    return out;
  }



}
