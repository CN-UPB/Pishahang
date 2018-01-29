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

class ComplexServiceManagerService < ManagerService

  JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  LOG_MESSAGE = 'GtkApi::' + self.name

  def self.config(url:, logger:)
    method = LOG_MESSAGE + "#config"
    raise ArgumentError.new('ComplexServiceManagerService can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {"entered with url=#{url}"}
  end

  def self.find_service_by_uuid(uuid:, params: {})
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with uuid= #{uuid}, params=#{params}"}
    find(url: @@url + '/complex-services/' + uuid, params: params, log_message: LOG_MESSAGE + "##{__method__}(#{uuid})")
  end

  def self.find_services(params)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{params}"}
    services=find(url: @@url + '/complex-services', params: params, log_message: LOG_MESSAGE + "##{__method__}(#{params})")
    vectorize_hash services
  end

  def self.find_requests(params)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{params}"}
    requests=find(url: @@url + '/requests', params: params, log_message: LOG_MESSAGE + "##{__method__}(#{params})")
    vectorize_hash requests
  end

  def self.find_requests_by_uuid(uuid)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{uuid}"}
    find(url: @@url + '/requests/' + uuid, log_message: LOG_MESSAGE + "##{__method__}")
  end

  def self.find_requests_by_service_instance_uuid(uuid)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{uuid}"}
    find(url: @@url + '/requests?service_instance_uuid=' + uuid, log_message: LOG_MESSAGE + "##{__method__}")
  end

  def self.create_service_request(params)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{params}"}
    @@logger.debug(message) {"@@url = "+@@url}

    begin
      resp = self.postCurb(url: @@url+'/requests', body: params) ## TODO: check if this tests ok!!
      @@logger.debug(message) {"resp=#{resp}"}
      resp
    rescue => e
      @@logger.error(message) {"Error during processing: #{$!}"}
      @@logger.error(message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.create_service_update_request(nsr_uuid:, nsd:)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with service instance=#{nsr_uuid}, nsd=#{nsd}"}
    begin
      @@logger.debug(message) {"@url = "+@@url}
      response = self.postCurb(url: @@url+'/complex-services/'+nsr_uuid, body: nsd)
      @@logger.debug(message) {"response="+response}
      response
    rescue => e
      @@logger.error(message) {"Error during processing: #{$!}"}
      @@logger.error(message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.create_service_termination_request(service_instance_uuid:)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with service instance=#{service_instance_uuid}"}

    record = RecordManagerService.find_record_by_uuid(kind: 'services', uuid: service_instance_uuid)
    @@logger.debug(message) {"record found=#{record}"}
    unless record[:status] == 200
      return {status: record[:status], count: 0, items: [], message: record[:message]}
    end
    descriptor = find_service_by_uuid(uuid: record[:items][:descriptor_reference])
    @@logger.debug(message) {"descriptor found=#{descriptor}"}
    unless descriptor[:status] == 200
      return {status: descriptor[:status], count: 0, items: [], message: descriptor[:message]}
    end
    begin
      response = self.putCurb(url: @@url+'/complex-services/'+service_instance_uuid+'/terminate', body: descriptor[:items][:nsd])
      @@logger.debug(message) {"response=#{response}"}
      response
    rescue => e
      @@logger.error(message) {"Error during processing: #{$!}"}
      @@logger.error(message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end

  # TODO
  def self.valid?(service_uuid)
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with service uuid=#{service_uuid}"}
    service = find_service_by_uuid(uuid: service_uuid)
    @@logger.debug(message) {"found service =#{service}"}
    service
  end
end
