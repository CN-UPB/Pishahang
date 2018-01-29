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
require 'json'

class Repository
  
  attr_accessor :url
  
  JSON_HEADERS = {'Accept'=>'application/json', 'Content-Type'=>'application/json'}
  
  def initialize(url, logger)
    @url = url
    @logger = logger
  end
    
  def find_by_uuid(uuid)
    method = "Repository.find_by_uuid"
    @logger.debug(method) {"entered with uuid #{uuid}"}
    begin
      response = RestClient.get(@url+"/#{uuid}", JSON_HEADERS) 
      @logger.debug(method) {"response=#{response}"}  
      service_or_function = JSON.parse(response.body)
      case response.code.to_i
      when 200
        {status: response.code.to_i, count: 1, items: service_or_function, message: "OK"}
      when 400
      when 404
        {status: response.code.to_i, count: 0, items: [], message: "Not found"}
      else 
        {status: response.code.to_i, count: 0, items: [], message: "Unknown error"}
      end
#    rescue RestClient::ExceptionWithResponse => e
    rescue => e
      @logger.error(method) {"response=#{e.response}"}
      @logger.error(method) {e.backtrace.each {|l| puts l}} #format_error(e.backtrace)
      {status: 500, count: 0, items: [], message: "#{e.backtrace.join("\n\t")}"}
    end
  end
  
  def find(params)
    headers = JSON_HEADERS
    headers[:params] = params unless params.empty?
    method = "Repository.find(#{params})"
    @logger.debug(method) {"headers #{headers}"}
    @logger.debug(method) {"calling #{@url}"}
    
    begin
      response = RestClient.get(@url, headers)
      @logger.debug(method) {"response=#{response}"}  
      services_or_functions = JSON.parse(response.body)
      case response.code.to_i
      when 200
        {status: 200, count: services_or_functions.count, items: services_or_functions, message:"OK"}
      when 400
      when 404
        {status: 200, count: 0, items: [], message:"OK"}
      else
        {status: 500, count: 0, items: [], message:"Internal Error"}
      end
    rescue => e
      @logger.error(method) {"response=#{response}"}  
      @logger.error(method) {e.backtrace.each {|l| puts l}} #format_error(e.backtrace)
      {status: 500, count: 0, items: [], message: "#{e.backtrace.join("\n\t")}"}
    end
  end
  
  private
  
  def format_error(backtrace)
    first_line = backtrace[0].split(":")
    "In "+first_line[0].split("/").last+", "+first_line.last+": "+first_line[1]
  end  
end
