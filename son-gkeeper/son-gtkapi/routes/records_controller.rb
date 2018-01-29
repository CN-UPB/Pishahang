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
require 'sinatra/namespace'
class GtkApi < Sinatra::Base
  
  register Sinatra::Namespace
  
  namespace '/api/v2/records' do
    before do
      content_type :json
    end
    
    options '/*/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST,PUT'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end

    # GET many instances
    get '/:kind/?' do
      began_at = Time.now.utc
      log_message = "GtkApi::GET /api/v2/records/#{params[:kind]}"
      params.delete('splat')
      params.delete('captures')
      logger.debug(log_message) {'entered with query parameters '+query_string}
      require_param(param: 'kind', params: params, kpi_method: method(:count_records_requests), error_message: 'Kind of record', log_message: log_message, began_at: began_at)
      
      token = get_token( request.env, began_at, method(:count_records_requests), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_records_requests), log_message)
      
      validate_user_authorization(token: token, action: 'get records request', uuid: '', path: '/records', method:'GET', kpi_method: method(:count_records_requests), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
  
      @offset ||= params[:offset] ||= DEFAULT_OFFSET 
      @limit ||= params[:limit] ||= DEFAULT_LIMIT
  
      records = RecordManagerService.find_records(params)
      unless records[:status] == 200
        logger.debug(log_message) {"No #{params[:kind]} records found"}
        halt 404, '[]'
      end

      logger.debug(log_message) {"leaving with #{records}"}
      links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: records[:count])
      headers 'Link' => links
      halt 200, records[:items].to_json
    end

    # GET a specific instance
    get '/:kind/:uuid/?' do
      began_at = Time.now.utc
      log_message = "GtkApi::GET /api/v2/records/#{params[:kind]}"
      logger.debug(log_message) {"entered with #{params[:uuid]}"}
      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_single_record_queries), began_at: began_at, log_message: log_message)

      token = get_token( request.env, began_at, method(:count_single_record_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_single_record_queries), log_message)

      validate_user_authorization(token: token, action: 'get '+params[:kind]+' record '+params[:uuid]+' data', uuid: params[:uuid], path: '/records', method:'GET', kpi_method: method(:count_single_record_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      record = RecordManagerService.find_record_by_uuid(kind: params[:kind], uuid: params[:uuid])
      validate_element_existence(uuid: params[:uuid], element: record, name: 'Record', kpi_method: method(:count_single_record_queries), began_at: began_at, log_message: log_message)
      validate_ownership_and_licence(element: record[:items], user_name: user_name, kpi_method: method(:count_single_record_queries), began_at: began_at, log_message: log_message)

      unless record[:status] == 200
        count_single_record_queries(labels: {result: "Not Found", uuid: params[:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
        json_error 404, "No #{params[:kind]} record with uuid #{params[:uuid]} found", log_message
      end
      count_single_record_queries(labels: {result: "ok", uuid: params[:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      logger.debug(log_message) {"leaving with #{record}"}
      headers 'Record-Count'=> '1'
      halt 200, record[:items].to_json
    end
  
    # PUT service instance
    put '/services/:uuid/?' do
      began_at = Time.now.utc
      log_message = "GtkApi::PUT /api/v2/records/services"
      logger.debug(log_message) {"entered with #{params[:uuid]}"}
      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_service_instance_update), began_at: began_at, log_message: log_message)

      token = get_token( request.env, began_at, method(:count_single_record_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_single_record_queries), log_message)

      validate_user_authorization(token: token, action: 'put services record '+params[:uuid]+' data', uuid: params[:uuid], path: '/records', method:'GET', kpi_method: method(:count_single_record_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      # the body of the request is expected to contain the NSD UUID and the NSD's latest version      
      body_params = JSON.parse(request.body.read)
      logger.debug(log_message) {"body_params=#{body_params}"}
      unless body_params.key?('nsd_id') && body_params.key?('latest_nsd_id')
        json_error 404, 'Both :nsd_id and :latest_nsd_id must be present', log_message
      end
    
      # here we have the 
      descriptor = RecordManagerService.find_record_by_uuid(kind: 'services', uuid: body_params['latest_nsd_id'])
      json_error 404, "No descriptor with uuid=#{params[:latest_nsd_id]} found", log_message unless descriptor      
      logger.debug(log_message) {"found #{descriptor}"}

      update_request = ServiceManagerService.create_service_update_request(nsr_uuid: params[:uuid], nsd: descriptor)
      json_error 400, 'No request was created', log_message unless update_request

      logger.debug(log_message) { "update_request =#{update_request}"}
      halt 201, update_request.to_json
    end
  end
  
  namespace '/api/v2/admin/records' do
    # GET module's logs
    get '/logs/?' do
      log_message = "GtkApi::GET /api/v2/admin/records/logs"
      logger.debug(log_message) {"entered"}
      url = RecordManagerService.class_variable_get(:@@url)+'/admin/logs'
      log = RecordManagerService.get_log(url: url, log_message:log_message)
      logger.debug(log_message) {'leaving with log='+log}
      headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
      halt 200, log #.to_s
    end
  end

  private
  
  def count_records_requests(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many times service/function records have been requested"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'records'})})
  end
  
  def count_single_record_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many times a single service/function record has been requested"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'records'})})
  end
  
  def count_service_instance_update(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many times a service instance has been updated"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'PUT', module: 'records'})})
  end
end
