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
  
  namespace '/api/v2/functions' do
    before do
      content_type :json
    end

    # GET many functions
    get '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/functions/?'
      logger.debug(log_message) {'entered with '+query_string}
    
      @offset ||= params[:offset] ||= DEFAULT_OFFSET 
      @limit ||= params[:limit] ||= DEFAULT_LIMIT
      logger.debug(log_message) {"params=#{params}"}
     
      token = get_token( request.env, began_at, method(:count_functions_metadata_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_functions_metadata_queries), log_message)

      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      validate_user_authorization(token: token, action: 'get metadata for functions', uuid: '', path: '/functions', method:'GET', kpi_method: method(:count_functions_metadata_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}

      # request.env['QUERY_STRING']
      params.delete('captures') if params.keys.include?('captures')
      #functions = SONATA::CurbAdapter.find(url: ENV[GtkApi.services['functions']['env_var_url']], params: params, logger: GtkApi.logger)
      functions = FunctionManagerService.find(params)
      validate_collection_existence(collection: functions, name: 'functions', kpi_method: method(:count_functions_metadata_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"Found functions #{functions}"}
      keys_to_delete = {main_key: :vnfd, sub_keys: [:connection_points, :monitoring_rules, :virtual_deployment_units, :virtual_links]}
      filtered_functions = enhance_collection( collection: functions[:items], user: user_name, keys_to_delete: keys_to_delete)
      logger.debug(log_message) {"links: request_url=#{request_url}, limit=#{@limit}, offset=#{@offset}, total=#{functions[:count]}"}
      links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: functions[:count].to_i)
      logger.debug(log_message) {"links: #{links}"}
      headers 'Link'=> links, 'Record-Count'=> functions[:count].to_s
      count_functions_metadata_queries(labels: {result: "ok", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      halt 200, filtered_functions.to_json
    end
  
    # GET function by uuid
    get '/:uuid/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/functions/:uuid/?'
      logger.debug(log_message) {"entered with #{params[:uuid]}"}
    
      token = get_token( request.env, began_at, method(:count_function_metadata_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_function_metadata_queries), log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_function_metadata_queries), began_at: began_at, log_message: log_message)
      validate_user_authorization(token: token, action: 'get metadata for function '+params[:uuid], uuid: params[:uuid], path: '/functions', method:'GET', kpi_method: method(:count_function_metadata_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      
      function = FunctionManagerService.find_by_uuid(params[:uuid])
      validate_element_existence(uuid: params[:uuid], element: function, name: 'Function', kpi_method: method(:count_function_metadata_queries), began_at: began_at, log_message: log_message)
      validate_ownership_and_licence(element: function[:items], user_name: user_name, kpi_method: method(:count_function_metadata_queries), began_at: began_at, log_message: log_message)
      
      count_function_metadata_queries(labels: {result: "ok", uuid: params[:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      logger.debug(log_message) {"leaving with #{function}"}
      headers 'Record-Count'=> '1'
      halt 200, function[:items].to_json
    end
  end
  
  namespace '/api/v2/admin/functions' do
    get '/logs/?' do
      log_message = 'GtkApi::GET /admin/functions/logs'
      logger.debug(log_message) {'entered'}
      url = FunctionManagerService.class_variable_get(:@@url)+'/admin/logs'
      log = FunctionManagerService.get_log(url: url, log_message:log_message)
      logger.debug(log_message) {'leaving with log='+log}
      headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
      halt 200, log
    end
  end

  private
  
  def count_functions_metadata_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many function metadata queries have been made"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'functions'})})
  end

  def count_function_metadata_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many function metadata queries by uuid have been made"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'functions'})})
  end
end
