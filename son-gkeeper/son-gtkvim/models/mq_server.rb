## SONATA - Gatekeeper
##
## Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## 
## Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote 
## products derived from this software without specific prior written 
## permission.
## 
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through 
## the Horizon 2020 and 5G-PPP programmes. The authors would like to 
## acknowledge the contributions of their colleagues of the SONATA 
## partner consortium (www.sonata-nfv.eu).
# encoding: utf-8
require 'bunny'
require 'pp'
require 'yaml'
require 'json'

class MQServer
  attr_accessor :url, :correlation_ids

  def initialize(queue_name,url,logger)
    @url = url
    @logger=logger
    @channel = Bunny.new(url,:automatically_recover => false).start.create_channel
    @topic = @channel.topic('son-kernel', :auto_delete => false)
    @queue   = @channel.queue(queue_name, :auto_delete => true).bind(@topic, :routing_key => queue_name)
    self.consume
  end

  def publish(msg, correlation_id)
    @logger.debug "MQServer.publish #{msg} with correlation #{correlation_id} to #{@queue.name}"
    @topic.publish(msg, :content_type =>'text/x-yaml', :routing_key => @queue.name, :correlation_id =>
        correlation_id, :reply_to => @queue.name,:app_id => 'son_gk')
  end

  def consume
    @queue.subscribe do |delivery_info, properties, payload|
      begin
        if properties[:app_id]=='sonata.kernel.InfrAdaptor'
          @logger.debug "MQServer.consume: delivery_info: #{delivery_info}"
          @logger.debug "MQServer.consume: properties: #{properties}"
          @logger.debug "MQServer.consume: payload: #{payload}"

          # This is because the payload is being returned as a string like
          # {error: null, status: INSTANTIATING, timestamp: 1465488253.8547997}
          parsed_payload = YAML.load(payload)

          #@logger.debug "MQServer.consume: status: #{status}"

          vimsRequest = VimsRequest.find_by(id: properties[:correlation_id])

          if vimsRequest
            vimsRequest['status']='complete'
            vimsRequest['query_response']=parsed_payload.to_json
            begin
              vimsRequest.save
              @logger.debug 'MQServer.consume: vimsquery saved'
            rescue Exception => e
              @logger.error e.message
              @logger.error e.backtrace.inspect
            end
          else
            @logger.error "MQServer.consume: #{properties[:correlation_id]} not found"
          end
        elsif properties[:app_id]=='sonata.kernel.WimAdapter'
          @logger.debug "MQServer.consume: delivery_info: #{delivery_info}"
          @logger.debug "MQServer.consume: properties: #{properties}"
          @logger.debug "MQServer.consume: payload: #{payload}"

          # This is because the payload is being returned as a string like
          # {error: null, status: INSTANTIATING, timestamp: 1465488253.8547997}
          parsed_payload = YAML.load(payload)

          #@logger.debug "MQServer.consume: status: #{status}"

          wimsRequest = WimsRequest.find_by(id: properties[:correlation_id])

          if wimsRequest
            wimsRequest['status']='complete'
            wimsRequest['query_response']=parsed_payload.to_json
            begin
              wimsRequest.save
              @logger.debug 'MQServer.consume: wimsquery saved'
            rescue Exception => e
              @logger.error e.message
              @logger.error e.backtrace.inspect
            end
          else
            @logger.error "MQServer.consume: #{properties[:correlation_id]} not found"
          end
        end
      rescue Exception => e
        @logger.error e.message
        @logger.error e.backtrace.inspect
      end
    end
  end
end