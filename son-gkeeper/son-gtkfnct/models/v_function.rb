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
require 'curb'
require 'uri'

class VFunction
  
  attr_accessor :url
  
  JSON_HEADERS = {'Accept'=>'application/json', 'Content-Type'=>'application/json'}
  
  def initialize(url, logger)
    log_message= "GtkFnct::VFunction.new"
    @url = url
    @logger = logger
    @logger.debug(log_message) {"url="+@url}
  end
  
  def find(params)
    log_message = "VFunction.find"
    @logger.debug(log_message) {"entered: params=#{params}"}
    complete_url = params.empty? ? @url : @url + '?' + URI.encode_www_form(params)
    @logger.debug(log_message) {"complete_url=#{complete_url}"}
    begin
      res=Curl.get(complete_url) do |req|
        req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
      end
      @logger.debug(log_message) {"header_str=#{res.header_str}"}
      data = JSON.parse(res.body)
      @logger.debug(log_message) {"response body=#{data}"}
      count = record_count_from_response_headers(res.header_str)
      { status: 200, count: count, data: data, message: "Ok"}
    rescue Curl::Err::ConnectionFailedError => e
      {status: 500, count: nil, data: nil, message: "Couldn't connect to server #{complete_url}"}
    rescue Curl::Err::CurlError => e
      {status: 500, count: nil, data: nil, message: "Generic error while connecting to server #{complete_url}"}
    rescue Curl::Err::AccessDeniedError => e
      {status: 500, count: nil, data: nil, message: "Access denied while connecting to server #{complete_url}"}
    rescue Curl::Err::TimeoutError => e
      {status: 500, count: nil, data: nil, message: "Time out while connecting to server #{complete_url}"}
    end
  end

  def find_by_uuid(uuid)
    log_message = "VFunction.find"
    @logger.debug(log_message) {"entered: uuid=#{uuid}"}
    begin
      res=Curl.get(@url + "/#{uuid}") do |req|
        req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
      end
      @logger.debug(log_message) {"header_str=#{res.header_str}"}
      @logger.debug(log_message) {"response body=#{res.body}"}
      { status: 200, count: 1, data: JSON.parse(res.body), message: "Ok"}
    rescue Curl::Err::ConnectionFailedError => e
      {status: 500, count: nil, data: nil, message: 'Couldn\'t connect to server '+@url+'/'+uuid}
    rescue Curl::Err::CurlError => e
      {status: 500, count: nil, data: nil, message: 'Generic error while connecting to server '+@url+'/'+uuid}
    rescue Curl::Err::AccessDeniedError => e
      {status: 500, count: nil, data: nil, message: 'Access denied while connecting to server '+@url+'/'+uuid}
    rescue Curl::Err::TimeoutError => e
      {status: 500, count: nil, data: nil, message: 'Time out while connecting to server '+@url+'/'+uuid}
    end
  end
  
  private 
  
  def record_count_from_response_headers(header_str)
    # From http://stackoverflow.com/questions/14345805/get-response-headers-from-curb
    http_response, *http_headers = header_str.split(/[\r\n]+/).map(&:strip)
    http_headers = Hash[http_headers.flat_map{ |s| s.scan(/^(\S+): (.+)/) }]
    http_headers['Record-Count'].to_i
  end
end