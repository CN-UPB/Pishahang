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
require 'pp'

class CService
  
  attr_accessor :url
  
  JSON_HEADERS = {'Accept'=>'application/json', 'Content-Type'=>'application/json'}
  
  def initialize(url, logger)
    log_message= "GtkCsrv::CService.new"
    @url = url
    @logger = logger
    @logger.debug(log_message) {"url="+@url}
  end
  
  def find(params)
    headers = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
    headers[:params] = params unless params.empty?
    log_message= "GtkCsrv::CService.find"
    @logger.debug(log_message) {"entered with params=#{params} and headers=#{headers}"}

    begin
      response = RestClient.get(@url, headers)
      @logger.debug(log_message) {"response=#{response}"}
      services = JSON.parse(response.body)
      @logger.debug(log_message) {"cloud_services= #{services}"}
      services
    rescue => e
      @logger.error(log_message) {e.backtrace}
      nil
    end
  end

  def find_by_uuid(uuid)
    headers = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
    headers[:params] = uuid
    log_message= "GtkCsrv::CService.find_by_uuid"
    @logger.debug(log_message) {"entered with uuid=#{uuid}"}
    begin
      response = RestClient.get(@url + "/#{uuid}", headers) 
      @logger.debug(log_message) {"response=#{response}"}
      service = JSON.parse(response)
      @logger.debug(log_message) {"cloud_services=#{service}"}
      service
    rescue => e
      @logger.error(log_message) {e.backtrace}
      nil
    end
  end
end