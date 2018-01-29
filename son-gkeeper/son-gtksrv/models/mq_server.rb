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
  attr_accessor :url
  
  CLASS = self.name
  
  def initialize(queue_name, url)
    @url = url
    @logger=GtkSrv.logger
    channel = Bunny.new(url,:automatically_recover => false).start.create_channel
    @topic = channel.topic("son-kernel", :auto_delete => false)
    @queue = channel.queue(queue_name, :auto_delete => true).bind(@topic, :routing_key => queue_name)
    method = queue_name.split('.')[-1]
    self.send(:"consume_#{method}")
    #self.consume
  end

  def publish(msg, correlation_id)
    logmsg= CLASS+'.'+__method__.to_s
    @logger.debug(logmsg) {"msg=#{msg} correlation_id=#{correlation_id}"}
    response = @topic.publish(msg, :content_type =>'text/yaml', :routing_key => @queue.name, :correlation_id => correlation_id, :reply_to => @queue.name, :app_id => 'son-gkeeper')
    @logger.debug(logmsg) {"published msg '"+msg+"', with correlation_id="+correlation_id}
    response
  end
  
  def consume_create
    logmsg= CLASS+'.'+__method__.to_s
    @logger.debug(logmsg) {"entered"}
    @queue.subscribe do |delivery_info, properties, payload|
      begin
        @logger.debug(logmsg) { "delivery_info: #{delivery_info}"}
        @logger.debug(logmsg) { "properties: #{properties}"}
        @logger.debug(logmsg) { "payload: #{payload}"}

        # We know our own messages, so just skip them
        unless properties[:app_id] == 'son-gkeeper'
          # We're interested in app_id == 'son-plugin.slm'
          parsed_payload = YAML.load(payload)
          @logger.debug(logmsg) { "parsed_payload: #{parsed_payload}"}
          status = parsed_payload['status']
          unless status
            @logger.error(logmsg) {'status not present'}
            return
          end
          @logger.debug(logmsg) { "status: #{status}"}
          request = Request.find_by(id: properties[:correlation_id])
          unless request
            @logger.error(logmsg) { "request "+properties[:correlation_id]+" not found"}
            return
          end
          @logger.debug(logmsg) { "request['status'] #{request['status']} turned into "+status}
          request['status']=status
          
          # if this is a final answer, there'll be an NSR
          service_instance = parsed_payload['nsr']
          service_instance ||= parsed_payload['cosr']
          if service_instance && service_instance.key?('id')
            service_instance_uuid = service_instance['id']
            @logger.debug(logmsg) { "request['service_instance_uuid'] turned into "+service_instance_uuid}
            request['service_instance_uuid'] = service_instance_uuid
          end
          begin
            request.save
            @logger.debug(logmsg) { "request saved"}
            register_kpi(request)
          rescue Exception => e
            @logger.error e.message
      	    @logger.error e.backtrace.inspect
          end
        end
        @logger.debug(logmsg) {" leaving..."}
      rescue Exception => e
        @logger.error e.message
  	    @logger.error e.backtrace.inspect
        @logger.debug(logmsg) {" leaving..."}
      end
    end
  end
  
  def consume_update
    logmsg= CLASS+'.'+__method__.to_s
    @logger.debug(logmsg) {"entered"}
    @queue.subscribe do |delivery_info, properties, payload|
      begin
        @logger.debug(logmsg) { "delivery_info: #{delivery_info}"}
        @logger.debug(logmsg) { "properties: #{properties}"}
        @logger.debug(logmsg) { "payload: #{payload}"}

        # We know our own messages, so just skip them
        unless properties[:app_id] == 'son-gkeeper'
          # We're interested in app_id == 'son-plugin.slm'
          parsed_payload = YAML.load(payload)
          @logger.debug(logmsg) { "parsed_payload: #{parsed_payload}"}
          status = parsed_payload['status']
          unless status
            @logger.debug(logmsg) {'status not present'}
            return
          end
          @logger.debug(logmsg) { "status: #{status}"}
          request = Request.find_by(id: properties[:correlation_id])
          unless request
            @logger.error(logmsg) { "request "+properties[:correlation_id]+" not found"}
            return
          end
          @logger.debug(logmsg) { "request[status] #{request['status']} turned into "+status}
          request['status']=status  
          begin
            request.save
            @logger.debug(logmsg) { "request saved"}
          rescue Exception => e
            @logger.error(logmsg) {e.message}
      	    @logger.error(logmsg) {e.backtrace.inspect}
          end
        end
        @logger.debug(logmsg) {" leaving..."}
      rescue Exception => e
        @logger.error e.message
  	    @logger.error e.backtrace.inspect
        @logger.debug(logmsg) {" leaving..."}
      end
    end
  end
  
  def consume_terminate
    logmsg= CLASS+'.'+__method__.to_s
    @logger.debug(logmsg) {"entered"}
    @queue.subscribe do |delivery_info, properties, payload|
      begin
        @logger.debug(logmsg) { "delivery_info: #{delivery_info}"}
        @logger.debug(logmsg) { "properties: #{properties}"}
        @logger.debug(logmsg) { "payload: #{payload}"}

        # We know our own messages, so just skip them
        unless properties[:app_id] == 'son-gkeeper'
          # We're interested in app_id == 'son-plugin.slm'
          parsed_payload = YAML.load(payload)
          @logger.debug(logmsg) { "parsed_payload: #{parsed_payload}"}
          status = parsed_payload['status']
          unless status
            @logger.debug(logmsg) {'status not present'}
            return
          end
          @logger.debug(logmsg) { "status: #{status}"}
          request = Request.find_by(id: properties[:correlation_id])
          unless request
            @logger.error(logmsg) { "request "+properties[:correlation_id]+" not found"}
            return
          end
          @logger.debug(logmsg) { "request[status] #{request['status']} turned into "+status}
          request['status']=status  
          begin
            request.save
            @logger.debug(logmsg) { "request saved"}
          rescue Exception => e
            @logger.error(logmsg) {e.message}
      	    @logger.error(logmsg) {e.backtrace.inspect}
          end
        end
        @logger.debug(logmsg) {" leaving..."}
      rescue Exception => e
        @logger.error e.message
  	    @logger.error e.backtrace.inspect
        @logger.debug(logmsg) {" leaving..."}
      end
    end
  end
  
  private
  
  def register_kpi(request)    
    log_message='MQServer.'+__method__.to_s
    @logger.debug(log_message) { "entered with request=#{request}"}
    now = Time.now.utc

    body = { uuid: request['uuid'], elapsed_time: now-Time.parse(request['began_at']).to_s, time_stamp: now}
    begin
      _response = RestClient.put(request['callback'], body.to_json, content_type: :json, accept: :json) 
      @logger.debug(log_message) { "response=#{_response}"}
      parsed_response = JSON.parse _response #.body
      @logger.debug(log_message) { "parsed_response=#{parsed_response}"}
      parsed_response
    rescue => e
      @logger.error(log_message) {"Error during processing: #{$!}"}
      @logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
    end    
  end
end