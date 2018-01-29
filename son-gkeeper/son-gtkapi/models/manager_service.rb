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
require 'uri'

class ManagerService
  
  JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  CLASS_NAME = self.name
  LOG_MESSAGE = 'GtkApi::' + CLASS_NAME
  BASE_KPI_PARAMS = { "job": "sonata", "instance": "gtkapi"}
  
  def initialize(url, logger)
    method = 'GtkApi::' + CLASS_NAME + ".new(url=#{url}, logger=#{logger})"
    @url = url
    @logger = logger
    @logger.debug(method) {'entered'}
  end
  
  def self.getCurb(url:, params: {}, headers: {})
    log_message=LOG_MESSAGE+"##{__method__}"
    GtkApi.logger.debug(log_message) {"entered with url=#{url}, params=#{params}, headers=#{headers}"}
    complete_url = params.empty? ? url : url + '?' + URI.encode_www_form(params)
    GtkApi.logger.debug(log_message) {"complete_url=#{complete_url}"} 
    begin
      res=Curl.get(complete_url) do |req|
        if headers.empty?
          req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
        else
          headers.each do |h|
            GtkApi.logger.debug(log_message) {"header[#{h[0]}]: #{h[1]}"}
            req.headers[h[0]] = h[1]
          end
        end
      end
      GtkApi.logger.debug(log_message) {"header_str=#{res.header_str}"}
      GtkApi.logger.debug(log_message) {"response body=#{res.body}"}
      count = record_count_from_response_headers(res.header_str)
      status = res.response_code
      case status
      when 200..299
        begin
          parsed_response = res.body.empty? ? {} : JSON.parse(res.body, symbolize_names: true)
          GtkApi.logger.debug(log_message) {"parsed_response=#{parsed_response}"}
          if count == 0 && !parsed_response.to_s.empty?
            count = parsed_response.is_a?(Hash) ? 1 : parsed_response.count
          end
          {status: status, count: count, items: parsed_response, message: "OK"}
        rescue => e
          GtkApi.logger.error(log_message) {"Error during processing: #{$!}"}
          GtkApi.logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
          {status: nil, count: nil, items: nil, message: "Error processing #{$!}: \n\t#{e.backtrace.join("\n\t")}"}
        end
      when 400
      when 404
        GtkApi.logger.debug(log_message) {"Records not found for url=#{url}, params=#{params}, headers=#{headers}"}
        {status: status, count: 0, items: [], message: "Not Found"}
      else
        GtkApi.logger.debug(log_message) {"Unexpected status code received: #{status}"}
        {status: status, count: nil, items: nil, message: "Status #{status} unprocessable"}
      end
    rescue Curl::Err::ConnectionFailedError => e
      {status: 500, count: nil, items: nil, message: "Couldn't connect to server #{complete_url}"}
    rescue Curl::Err::CurlError => e
      {status: 500, count: nil, items: nil, message: "Generic error while connecting to server #{complete_url}"}
    rescue Curl::Err::AccessDeniedError => e
      {status: 500, count: nil, items: nil, message: "Access denied while connecting to server #{complete_url}"}
    rescue Curl::Err::TimeoutError => e
      {status: 500, count: nil, items: nil, message: "Time out while connecting to server #{complete_url}"}
    rescue Curl::Err::HostResolutionError => e
      {status: 500, count: nil, items: nil, message: "Couldn't resolve host name #{complete_url}"}
    end
  end
  
  def self.find(url:, params: {}, headers: JSON_HEADERS, log_message:'')
    GtkApi.logger.debug(log_message) {'entered'}
    response = getCurb(url: url, params: params, headers: headers)
    GtkApi.logger.debug(log_message) {"response=#{response}"}
    response
  end
  
  def self.postCurb(url:, body:, headers: {})
    log_message=LOG_MESSAGE+"##{__method__}"
    GtkApi.logger.debug(log_message) {"entered with url=#{url}, body=#{body}"}
    res=Curl.post(url, body.to_json) do |req|
      if headers.empty?
        req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
      else
        headers.each do |h|
          GtkApi.logger.debug(log_message) {"header[#{h[0]}]: #{h[1]}"}
          req.headers[h[0]] = h[1]
        end
      end
    end
    GtkApi.logger.debug(log_message) {"response body=#{res.body}"}
    status = res.response_code
    case status
    when 200..202
      begin
        parsed_response = JSON.parse(res.body, symbolize_names: true)
        GtkApi.logger.debug(log_message) {"status #{status}, parsed_response=#{parsed_response}"}
        {status: status, count: 1, items: parsed_response, message: "OK"}
      rescue => e
        GtkApi.logger.error(log_message) {"Error during processing: #{$!}"} 
        GtkApi.logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
        {status: nil, count: nil, items: nil, message: "Error processing #{$!}: \n\t#{e.backtrace.join("\n\t")}"}
      end
    when 400..499
      GtkApi.logger.error(log_message) {"Status #{status}"} 
      {status: status, count: nil, items: nil, message: "Status #{status}: could not process"}
    else
      GtkApi.logger.error(log_message) {"Status #{status}"} 
      {status: status, count: nil, items: nil, message: "Status #{status} unknown"}
    end
  end  

  def self.putCurb(url:, body:, headers: {})
    log_message=LOG_MESSAGE+"##{__method__}"
    GtkApi.logger.debug(log_message) {"entered with url=#{url}, body=#{body.to_json}"}   
    begin 
      res=Curl.put(url, body.to_json) do |req|
        if headers.empty?
          req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
        else
          headers.each do |h|
            GtkApi.logger.debug(log_message) {"header[#{h[0]}]: #{h[1]}"}
            req.headers[h[0]] = h[1]
          end
        end
      end

      status = res.response_code
      GtkApi.logger.debug(log_message) {"response body=#{res.body}"}
      case status
      when 200..202
        begin
          body = res.body
          if body.empty?
            GtkApi.logger.debug(log_message) {"status #{status}, parsed_response=[]"}
            {status: status, count: 1, items: [], message: "OK"}
          else
            parsed_response = JSON.parse(body, symbolize_names: true)
            GtkApi.logger.debug(log_message) {"status #{status}, parsed_response=#{parsed_response}"}
            {status: status, count: 1, items: parsed_response, message: "OK"}
          end
        rescue => e
          GtkApi.logger.error(log_message) {"Error during processing: #{$!}"} 
          GtkApi.logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
          {status: nil, count: nil, items: nil, message: "Error processing #{$!}: \n\t#{e.backtrace.join("\n\t")}"}
        end
      when 400..499
        GtkApi.logger.error(log_message) {"Status #{status}"} 
        {status: status, count: nil, items: nil, message: "Status #{status}: could not process"}
      else
        GtkApi.logger.error(log_message) {"Status #{status}"} 
        {status: status, count: nil, items: nil, message: "Status #{status} unknown"}
      end
    rescue Curl::Err::ConnectionFailedError => e
      {status: 500, count: nil, items: nil, message: "Couldn't connect to server #{url}"}
    rescue Curl::Err::CurlError => e
      {status: 500, count: nil, items: nil, message: "Generic error while connecting to server #{url}"}
    rescue Curl::Err::AccessDeniedError => e
      {status: 500, count: nil, items: nil, message: "Access denied while connecting to server #{url}"}
    rescue Curl::Err::TimeoutError => e
      {status: 500, count: nil, items: nil, message: "Time out while connecting to server #{url}"}
    rescue Curl::Err::HostResolutionError => e
      {status: 500, count: nil, items: nil, message: "Couldn't resolve host name #{url}"}
    end
  end
  
  private
  
  def self.format_error(backtrace)
    first_line = backtrace[0].split(":")
    "In "+first_line[0].split("/").last+", "+first_line.last+": "+first_line[1]
  end
    
  def self.header_from_response_headers(header_str)
    # From http://stackoverflow.com/questions/14345805/get-response-headers-from-curb
    http_response, *http_headers = header_str.split(/[\r\n]+/).map(&:strip)
    http_headers = Hash[http_headers.flat_map{ |s| s.scan(/^(\S+): (.+)/) }]

    #http_response # => "HTTP/1.1 200 OK"
    #http_headers => { "Date" => "2013-01-10 09:07:42 -0700", "Content-Type" => "text/html", "Server" => "WEBrick/1.3.1 (Ruby/1.9.3/2012-11-10)",
    #        "Content-Length" => "62164", "Connection" => "Keep-Alive"}
  end

  def self.record_count_from_response_headers(header_str)
    # From http://stackoverflow.com/questions/14345805/get-response-headers-from-curb
    http_response, *http_headers = header_str.split(/[\r\n]+/).map(&:strip)
    http_headers = Hash[http_headers.flat_map{ |s| s.scan(/^(\S+): (.+)/) }]

    #http_response # => "HTTP/1.1 200 OK"
    #http_headers => { "Date" => "2013-01-10 09:07:42 -0700", "Content-Type" => "text/html", "Server" => "WEBrick/1.3.1 (Ruby/1.9.3/2012-11-10)",
    #        "Content-Length" => "62164", "Connection" => "Keep-Alive"}
    http_headers['Record-Count'].to_i
  end
  
  def self.get_log(url:, log_message:'')
    GtkApi.logger.debug(log_message) {'entered'}

    res=Curl.get( url) do |req|
      req.headers['Content-Type'] = 'text/plain; charset=utf8'
      req.headers['Location'] = '/'
    end    
    status = res.response_code
    
    GtkApi.logger.debug(log_message) {"status=#{status}"}
    case status
      when 200
        res.body
      else
        GtkApi.logger.error(log_message) {"Error retrieving logs"}
        nil
      end
  end

  def self.vectorize_hash(hash)
    {
      status: hash[:status], 
      count: hash[:count], 
      items: hash[:items].is_a?(Hash) ? [hash[:items]] : hash[:items], 
      message: hash[:message]
    }
  end
  
  def self.counter_kpi(params)
    # params should have
    #  "name": "example_counter"
    #  "docstring": "metric counter test"
    #  "base_labels": {"result": "ok", "time-taken": (Time.now.utc-began_at).to_s} --> examples
    
    # Adds time and metric type
    params[:base_labels][:time_stamp] = Time.now.utc
    #params[:base_labels][:metric_type] = "counter"
    
    KpiManagerService.update_metric(BASE_KPI_PARAMS.merge({metric_type: "counter"}).merge(params))
  end
  
  # curl -H "Content-Type: application/json" -X PUT -d '{"job":"job-name","instance":"instance-name","name":"gauge_name", "metric_type": "gauge", "operation": "inc" (optional; default "inc"), "docstring":"metric gauge description", "metric_value (optional; default 1)", "base_labels": {"label1":"value1","label2":"value2"}}' http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis
  def self.gauge_kpi(params)
    # params should have
    #  "name": "example_counter"
    #  "docstring": "metric counter test"
    #  "base_labels": {"result": "ok", "time-taken": (Time.now.utc-began_at).to_s} --> examples
    KpiManagerService.update_metric(BASE_KPI_PARAMS.merge(params).merge({metric_type: "gauge"}))
  end
end
