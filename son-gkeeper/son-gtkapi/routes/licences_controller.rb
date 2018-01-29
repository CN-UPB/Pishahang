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
  namespace '/api/v2/licences' do
    before do
      content_type :json
    end
    
    options '/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST,PUT'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end

    # GET many licences
    get '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/licences/?'
      logger.debug(log_message) {'entered with '+query_string}
    
      @offset ||= params[:offset] ||= DEFAULT_OFFSET
      @limit ||= params[:limit] ||= DEFAULT_LIMIT

      token = get_token( request.env, began_at, method(:count_licences_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_licences_queries), log_message)
      validate_user_authorization(token: token, action: 'get metadata for licences', uuid: '', path: '/licences', method:'GET', kpi_method: method(:count_licences_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      licences = LicenceManagerService.find(params)
      json_error 404, "No licences with #{params} were found", log_message unless licences[:status] == 200
      logger.debug(log_message) {"Found licences #{licences}"}
      logger.debug(log_message) {"links: request_url=#{request_url}, limit=#{@limit}, offset=#{@offset}, total=#{licences[:count]}"}
      links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: licences[:count].to_i)
      logger.debug(log_message) {"links: #{links}"}
      headers 'Link'=> links, 'Record-Count'=> licences[:count]
      halt 200, licences[:items].to_json
    end

    # GET a specific licence
    get '/:uuid/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/licences/:uuid/?'
      logger.debug(log_message) {"entered with #{params[:uuid]}"}
      
      require_param(param: 'uuid', params: params, kpi_method: method(:count_single_licence_queries), error_message: 'No licence UUID specified', log_message: log_message, began_at: began_at)
      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_single_licence_queries), began_at: began_at, log_message: log_message)

      token = get_token( request.env, began_at, method(:count_single_licence_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_single_licence_queries), log_message)
      validate_user_authorization(token: token, action: "get metadata for licence #{params[:uuid]}", uuid: params[:uuid], path: '/licences', method:'GET', kpi_method: method(:count_single_licence_queries), began_at: began_at, log_message: log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
      
      licence = LicenceManagerService.find_by_uuid(params[:uuid])
      validate_element_existence(uuid: params[:uuid], element: licence, name: 'Licence', kpi_method: method(:count_single_licence_queries), began_at: began_at, log_message: log_message)
        
      logger.debug(log_message) {"leaving with licence #{licence}"}
      count_single_licence_queries(labels: {result: "ok", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      halt 200, licence[:items].to_json
    end
    
    post '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::POST /api/v2/licences/?'
      params = JSON.parse(request.body.read, symbolize_names: true)
      logger.info(log_message) {"entered with params=#{params}"}
    
      require_param(param: :service_uuid, params: params, kpi_method: method(:count_licences_creations), error_message: "No service uuid specified: #{params}", log_message: log_message, began_at: began_at)
      
      token = get_token( request.env, began_at, method(:count_licences_creations), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_licences_creations), log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
      
      # 'type_uuid', String *
      # 'service_uuid', String *
      # 'user_uuid', String *
      # 'license_uuid', String *
      # 'description', String
      # 'startingDate', DateTime
      # 'expiringDate', DateTime * 
      # 'status', String
      
      user = User.find_by_name user_name
      params[:user_uuid] = user.uuid

      licence = LicenceManagerService.create(params)
      logger.debug(log_message) {"licence=#{licence.inspect}"}
      case licence[:status]
      when 201
        logger.info(log_message) {"leaving with licence: #{licence[:items]}"}
        count_licences_creations(labels: {result: "ok", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
        headers 'Location'=> LicenceManagerService.class_variable_get(:@@url)+"/licences/#{licence[:uuid]}"
        halt 201, licence[:items].to_json
      when 400
        json_error 400, '{}', 'Bad request'
      when 409
        json_error 409, "Licence #{params} already exists", 'Conflict'
      when 422
        json_error 422, '{}', 'Unprocessable entity'
      else
        json_error 500, "Internal error while trying to create a licence with params #{params}"
      end
    end
  end
  
  namespace '/api/v2/admin/licences' do
    get '/logs/?' do
      log_message = 'GtkApi::GET /api/v2/admin/licences/logs'
      logger.debug(log_message) {'entered'}
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      url = LicenceManagerService.class_variable_get(:@@url)+'/admin/logs'
      log = LicenceManagerService.get_log(url: url, log_message:log_message)
      logger.debug(log_message) {'leaving with log='+log}
      headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
      halt 200, log
    end
  end
  
  def count_licences_creations(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many licences have been created"
    LicenceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'POST', module: 'licences'})})
  end

  def count_single_licence_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many single licences have been queried"
    LicenceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'licences'})})
  end

  def count_licences_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many licences have been queried"
    LicenceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'licences'})})
  end
end
