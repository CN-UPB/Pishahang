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

class RecordManagerService < ManagerService
  
  JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  LOG_MESSAGE = 'GtkApi::' + self.name
  
  def self.config(url:, logger:)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new('RecordManagerService can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered with url='+url}
  end
  
  def self.find_records(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params=#{params}"}

    kind = params.delete('kind')
    @@logger.debug(method) {"url=#{@@url}/#{kind}"}
    records= find(url: "#{@@url}/#{kind}", params: params, log_message: LOG_MESSAGE + "##{__method__}(#{params})")
    vectorize_hash records
  end
  
  def self.find_record_by_uuid(kind: 'services', uuid:)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with uuid=#{uuid}"}
    find(url: @@url + '/' + kind + '/' + uuid, log_message: log_message) # + 'records/'
  end
  
  def self.find_records_by_function_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with uuid=#{uuid}"}
    find(url: @@url + '/functions?function_uuid=' + uuid, log_message: LOG_MESSAGE + "##{__method__}(#{uuid})") #+ '/records/' 
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
end
