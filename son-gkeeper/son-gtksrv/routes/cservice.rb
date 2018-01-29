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
require 'pp'
require 'addressable/uri'

class GtkSrv < Sinatra::Base

  get '/complex-services/?' do
    log_message="GtkSrv::GET /complex-services/?"
    logger.debug(log_message) {"entered with params #{params}"}

    # Remove list of wanted fields from the query parameter list
    field_list = params.delete('fields')

    logger.debug(log_message) { 'query_string='+query_string}
    logger.debug(log_message) { "params=#{params}"}

    begin
      services = CoService.new(settings.complex_services_catalogue, logger).find(params)
      logger.debug(log_message) { "services fetched: #{services}"}
      if field_list
        fields = field_list.split(',')
        logger.debug(log_message) { "fields=#{fields}"}
        records = services[:items].to_json(:only => fields)
      else
        records = services[:items].to_json
      end
      logger.debug(log_message) { "leaving with #{services[:count]}: #{records}"}
      headers 'Record-Count' => services[:count].to_s
      halt 200, records
    rescue CoServicesNotFoundError
      json_error 404, "No service with params #{query_string} was found", log_message
    end
  end

  get '/complex-services/:uuid' do
    log_message="GtkSrv: GET /complex-services/:uuid"
    logger.debug(log_message) {"entered with #{params[:uuid]}" }

    begin
      service = CoService.new(settings.complex_services_catalogue, logger).find_by_uuid(params[:uuid])
      logger.debug(log_message) {"service found #{service}"}
      halt 200, service.to_json
    rescue CoServiceNotFoundError
      json_error 404, "No service with uuid #{params[:uuid]} was found", log_message
    end
  end

  # PUTs an update on an existing service instance, given the service instance UUID
  put '/complex-services/:uuid/?' do
    method = MODULE + " PUT /complex-services/:uuid"
    logger.debug(method) {"entered with #{params[:uuid]}"}

    # is it a valid service instance uuid?
    begin
      valid = Request.validate_request(service_instance_uuid: params[:uuid])
      logger.debug(method) {"valid=#{valid.inspect}"}

      json_error 400, "Service instance '#{params[:uuid]} not 'READY'", method unless valid

      body = request.body.read
      logger.debug(method) {"with body=#{body}"}
      cosd = JSON.parse(body, quirks_mode: true)
      logger.debug(method) {"with nsd=#{cosd}"}

      cosd.delete('status') if cosd['status']
      update_response = Request.process_request(cosd: cosd, service_instance_uuid: params[:uuid], type: 'UPDATE', mq_server: settings.update_mqserver)
      logger.debug(method) {"update_response=#{update_response}"}
      json_error 400, "Update request for service instance '#{params[:uuid]} failled", method unless update_response

      halt 201, update_response.to_json
    rescue Exception=> e
      json_error 404, "Service instance '#{params[:uuid]}' not found", method
    end
  end

  # PUTs an update on an existing service instance, given the service instance UUID, to terminate it
  put '/complex-services/:uuid/terminate/?' do
    # TODO: implement properly, doesn't work with cloud services yet
    method = 'GtkSrv PUT /complex-services/:uuid/terminate'
    logger.debug(method) {"entered with #{params[:uuid]}"}

    # is it a valid service instance uuid?
    begin
      creation_request = Request.validate_request(service_instance_uuid: params[:uuid])
      logger.debug(method) {"creation_request=#{creation_request.inspect}"}
      logger.debug(method) {"creation_request[:service_uuid]=#{creation_request[:service_uuid]}"}
      service_instantiation_request_result = Request.create(
          request_type: "TERMINATE", service_instance_uuid: params[:uuid], service_uuid: creation_request[:service_uuid],
          egress: nil, ingress: nil
      )
      json_error 400, "Service instance '#{params[:uuid]}' termination failled", method unless service_instantiation_request_result
      logger.debug(log_msg) { "service_instantiation_request_result= #{service_instantiation_request_result}"}

      logger.debug(method) {"build_descriptors with service_uuid: #{creation_request[:service_uuid]}, service_instance_uuid: #{params[:uuid]}"}
      cosd = build_descriptors(service_uuid: creation_request[:service_uuid], service_instance_uuid: params[:uuid])

      json_error 404, "NSD not found for service uuid '#{creation_request[:service_uuid]}'", method unless cosd

      logger.debug(method) {"with nsd=#{cosd}"}

      cosd.delete('status') if cosd['status']
      descriptors_yml = YAML.dump(descriptors.deep_stringify_keys)
      logger.debug(log_msg) {"descriptors_yml=#{descriptors_yml}"}

      smresponse = settings.create_mqserver.publish( descriptors_yml.to_s, service_instantiation_request_result['id'])
      formated_descriptors = json(service_instantiation_request, { root: false })
      logger.debug(log_msg) {'returning with request='+formated_descriptors}

      terminate_response = Request.process_request(cosd: formated_descriptors, service_instance_uuid: params[:uuid], type: 'TERMINATE', mq_server: settings.terminate_mqserver)
      logger.debug(method) {"terminate_response=#{terminate_response}"}
      json_error 400, "Terminate request for service instance '#{params[:uuid]} failled", method unless terminate_response

      halt 201, terminate_response.to_json
    rescue Exception=> e
      json_error 404, "Service instance '#{params[:uuid]}' not found", method
    end
  end

  get '/admin/logs' do
    logger.debug "GtkSrv: entered GET /admin/logs"
    File.open('log/'+ENV['RACK_ENV']+'.log', 'r').read
  end

  private
  def query_string
    request.env['QUERY_STRING'].nil? ? '' : '?' + request.env['QUERY_STRING'].to_s
  end

  def request_url
    log_message = 'GtkApi::request_url'
    logger.debug(log_message) {"Schema=#{request.env['rack.url_scheme']}, host=#{request.env['HTTP_HOST']}, path=#{request.env['REQUEST_PATH']}"}
    request.env['rack.url_scheme']+'://'+request.env['HTTP_HOST']+request.env['REQUEST_PATH']
  end

  def build_descriptors(service_uuid:, service_instance_uuid:)
    log_msg = 'GtkSrv#build_descriptors'
    logger.debug(log_msg) {"entered with service_uuid=#{service_uuid}, service_instance_uuid=#{service_instance_uuid}"}

    begin
      payload={}
      payload['instance_id'] = service_instance_uuid

      service = CoService.new(settings.complex_services_catalogue, logger).find_by_uuid(service_uuid)

      unless service
        logger.error(log_msg) {"network service not found"}
        return nil
      end
      logger.debug(log_msg) { "service=#{service}"}

      cosd = service['cosd']
      cosd[:uuid] = service['uuid']
      payload['COSD']= cosd

      cosd['network_functions'].each_with_index do |function, index|
        logger.debug(log_msg) { "function=['#{function['vnf_name']}', '#{function['vnf_vendor']}', '#{function['vnf_version']}']"}
        stored_function = VFunction.new(settings.functions_catalogue, logger).find_function(function['vnf_name'],function['vnf_vendor'],function['vnf_version'])
        unless stored_function
          logger.error(log_msg) {"network function not found"}
          loop
        end
        logger.debug(log_msg) {"function#{index}=#{stored_function}"}
        vnfd = stored_function[:vnfd]
        vnfd[:uuid] = stored_function[:uuid]
        payload["VNFD#{index}"]=vnfd
        logger.debug(log_msg) {"payload[\"VNFD#{index}\"]=#{vnfd}"}
      end
      return payload
    rescue Exception => e
      logger.debug(log_msg) {e.message}
      logger.debug(log_msg) {e.backtrace.inspect}
      return nil
    end
  end
end
