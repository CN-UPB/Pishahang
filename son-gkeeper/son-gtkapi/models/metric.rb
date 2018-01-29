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

class MetricNameNotFoundError < StandardError; end
class MetricNameCanNotBeNilOrEmptyError < StandardError; end
class MetricNotCollectedError < StandardError; end
class AsynchMonitoringDataRequestNotCreatedError < StandardError; end
class SynchMonitoringDataRequestNotCreatedError < StandardError; end

class Metric < ManagerService
    
  #JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  LOG_MESSAGE = 'GtkApi::' + self.name
  
  # GET http://sp.int3.sonata-nfv.eu:8000/api/v1/prometheus/metrics/list
  # POST http://sp.int3.sonata-nfv.eu:8000/api/v1/ws/new -d {"metric":"vm_cpu_perc","filters":["id='123456asdas255sdas'","type='vnf'"]}
  
  attr_accessor :name, :instances
  
  def self.config(url:, logger:)
    log_message = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new('Metric model can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(log_message) {'entered with url='+url}
  end
  
  def initialize(params)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with params=#{params}"}
    @name = params[:name]
    # instance IDs could be used to validate if required metric name was available for that instance
    @instances = params[:instances]
  end
  
  # Get list of the available metrics.
  # curl -s http://<mon_manager_url>/api/v1/prometheus/metrics/list
  def self.find(params)
    # TODO: re-implement this like find_by_name: results are more complex than these
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with params=#{params}"}
    response = getCurb(url: @@url+'/prometheus/metrics/list', params: params)
    @@logger.debug(log_message) {"response=#{response}"}
    case response[:status]
    when 200
      metrics = response[:items][:metrics]
      result = []
      metrics.each do |metric_name|
        result << Metric.new({name: metric_name, instances: nil})
      end
      result
    else
      []
    end
  end
  
  # Get details about a specific metric
  # curl -s http://<mon_manager_url>/api/v1/prometheus/metrics/name/vm_mem_perc/
  def self.find_by_name(name)
    log_message = LOG_MESSAGE + "##{__method__}"
    raise MetricNameCanNotBeNilOrEmptyError.new('Metric name can not be nil or empty') if (name.nil? || name.empty?)
    @@logger.debug(log_message) {'entered with name='+name}
    response = getCurb(url: @@url+'/prometheus/metrics/name/'+name+'/')
    @@logger.debug(log_message) {"response=#{response}"}
    
    raise MetricNameNotFoundError.new('Metric with name '+name+' was not found') unless response[:status] == 200
    raise MetricNameNotFoundError.new('Metric with name '+name+' was not found') if response[:items][:metrics].empty?
    
    metrics = response[:items][:metrics][:result]
    @@logger.debug(log_message) {"found #{metrics.size} with name #{name}"}
    ids = []
    metrics.each do |metric|
      ids << metric[:metric][:id]
    end
    Metric.new({name: name, instances: ids})
  end

  def self.get_kpis(params)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with params=#{params}"}
    message = "Metric #{params[:name]}, from #{params[:start]} to #{params[:stop]} (step #{params[:step]}) could not be collected"
        
    begin
      resp = postCurb(url: @@url+'/prometheus/metrics/data', body: params)
      @@logger.debug(log_message) {"resp=#{resp}"}
      case resp[:status]
      when 200..202
        @@logger.debug(log_message) {"request=#{resp[:items]}"}
        unless resp[:items][:metrics].empty?
          resp[:items][:metrics][:result]
        else
          @@logger.error(log_message) {message} 
          raise MetricNotCollectedError.new message
        end
      else
        @@logger.error(log_message) {"Status #{resp[:status]}"} 
        raise MetricNotCollectedError.new message
      end
    rescue  => e
      @@logger.error(log_message) {"Error during processing: #{$!}"}
      @@logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise MetricNotCollectedError.new message
    end 
  end
  
  # Get mon data via asynch request
  # tw_end=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  # tw_start=$(date -u -d -10minutes '+%Y-%m-%dT%H:%M:%SZ')
  # curl -s 
  # -H "Accept: application/json" 
  # -H "Content-Type:application/json" 
  # -X POST --data '{"name":"vm_mem_perc","start": "'$tw_start'", "end": "'$tw_end'", "step": "10s", "labels": [{"labeltag":"exported_job", "labelid":"vnf"}]}' 
  # "http://<mon_manager_url>/api/v1/prometheus/metrics/data"
  # {"name":"vm_mem_perc","start": "'$tw_start'", "end": "'$tw_end'", "step": "10s", "labels": [{"labeltag":"exported_job", "labelid":"vnf"}]}
  # labels:[{"labeltag":"id", "labelid":"123456asdas255sdas"}]}'
  def asynch_monitoring_data(params)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with params=#{params}"}
    vnfc_uuid = params.delete(:vnfc_id)
    body = params.merge({name: @name})
    body = body.merge!({labels: [{labeltag:'id', labelid: vnfc_uuid}, {labeltag: 'exported_job', labelid: 'vnf'}]})
    
    begin
      resp = Metric.postCurb(url: @@url+'/prometheus/metrics/data', body: body)
      @@logger.debug(log_message) {"resp=#{resp}"}
      case resp[:status]
      when 200..202
        @@logger.debug(log_message) {"request=#{resp[:items]}"}
        resp[:items]
      else
        @@logger.error(log_message) {"Status #{resp[:status]}"} 
        raise AsynchMonitoringDataRequestNotCreatedError.new "Asynch monitoring data with params #{params} was not created "
      end
    rescue  => e
      @@logger.error(log_message) {"Error during processing: #{$!}"}
      @@logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise AsynchMonitoringDataRequestNotCreatedError.new "Asynch monitoring data with params #{params} was not created "
    end 
  end

  # Get monitoring data via synch request (websocket)
  # curl -s 
  # -H "Accept: application/json" 
  # -H "Content-Type:application/json" 
  # -X POST --data '{"metric":"vm_cpu_perc","filters":["id='123456asdas255sdas'","type='vnf'"]}' 
  # "http://<mon_manager_url>/api/v1/ws/new"
  def synch_monitoring_data(vnfc_uuid)
    log_message = LOG_MESSAGE + ".#{__method__}"
    @@logger.debug(log_message) {"entered with vnfc_uuid=#{vnfc_uuid}"}
    body = {}
    body[:metric]=@name
    body[:filters]=["id='#{vnfc_uuid}'", "type='vnf'"]
    begin
      resp = Metric.postCurb(url: @@url+'/ws/new', body: body)
      @@logger.debug(log_message) {"resp=#{resp}"}
      case resp[:status]
      when 200..202
        @@logger.debug(log_message) {"request=#{resp[:items]}"}
        resp[:items]
      else
        @@logger.error(log_message) {"Status #{resp[:status]} Synch monitoring data with params #{vnfc_uuid} was not created"} 
        raise SynchMonitoringDataRequestNotCreatedError.new "Synch monitoring data with params #{vnfc_uuid} was not created"
      end
    rescue  => e
      @@logger.error(log_message) {"Error during processing: #{$!}"}
      @@logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise SynchMonitoringDataRequestNotCreatedError.new "Synch monitoring data with params #{vnfc_uuid} was not created"
    end
  end
  
  def self.validate_and_create(names)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with names=#{names}"}
    metrics = []
    names.each do |name|
      begin
        metrics << Metric.find_by_name(name)
      rescue MetricNameNotFoundError
        @@logger.debug(log_message) {'Metric '+name+' could not be found'}
        next
      end
    end
    @@logger.debug(log_message) {"exiting with metrics=#{metrics}"}
    metrics
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
end
  