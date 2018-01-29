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
require './models/manager_service.rb'

class KpiManagerService < ManagerService
  
  LOG_MESSAGE = 'GtkApi::' + self.name
  
  def self.config(url:, logger:)
    method = LOG_MESSAGE + "##{__method__}(url=#{url})"
    raise ArgumentError.new('KpiManagerService can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered'}
  end

  def self.update_metric(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with #{params}"}
    
    begin
      @@logger.debug(method) {"url = "+@@url}      
      response = putCurb(url: @@url+'/kpis', body: params)      
      @@logger.error(method) {"response=#{response}"}
      case response[:status]
      when 201
        { status: response[:status], data: {}, message: 'Metric updated'}        
      else
        { status: response[:status], data: {}, message: 'Metric was not updated'}
      end      
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      { status: 500, data: {}, message: e.backtrace.join("\n\t")}
    end      
  end

  def self.find(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params=#{params}"}
    @@logger.debug(method) {"url = "+@@url}

    # POST .../api/v1/prometheus/metrics/data with body {"name":"user_registrations","start": "2017-05-03T11:41:22Z", "end": "2017-05-03T11:51:11Z", "step": "10s", "labels":[]}    
    # curl -H "Content-Type: application/json" -d '{"name":"user_registrations","start":"2017-05-05T14:13:02.699Z","end":"2017-05-05T14:33:02.699Z","step":"10m","labels":[{}]}' http://sp.int3.sonata-nfv.eu:8000/api/v1/prometheus/metrics/data
    begin
      response = getCurb(url: @@url+'/kpis', params: params)      
      @@logger.debug(method) {"response: #{response}"}
      case response[:status]
      when 200
        { status: response[:status], data: response[:items] }
      else
        { status: response[:status], data: {}, message: 'Metric were not retrieved'}
      end   
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      { status: 500, message: e.backtrace.join("\n\t")}
    end      
  end

  def self.get_metric(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {"entered"}
    
    begin
      @@logger.debug(method) {"url = "+@@url}
      response = getCurb(url: @@url+'/kpis', params: params, headers:JSON_HEADERS)      
      case response[:status]
      when 200
        { status: response[:status], data: JSON.parse(response[:items].to_json, :symbolize_names => true) }
      else
        { status: response[:status], data: {}, message: 'Metric does not retrieved'}
      end   
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      { status: 500, message: e.backtrace.join("\n\t")}
    end      
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
end