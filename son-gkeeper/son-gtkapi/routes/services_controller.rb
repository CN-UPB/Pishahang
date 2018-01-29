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
  helpers GtkApiHelper
  
  namespace '/api/v2/services' do
    before do
      content_type :json
    end

    options '/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST,PUT'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end

    # GET many services
    get '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi:: GET /api/v2/services'    
      logger.debug(log_message) {'entered with '+query_string}
    
      @offset ||= params['offset'] ||= DEFAULT_OFFSET
      @limit ||= params['limit'] ||= DEFAULT_LIMIT
      logger.debug(log_message) {"offset=#{@offset}, limit=#{@limit}"}
      logger.debug(log_message) {"params=#{params}"}
      
      token = get_token( request.env, began_at, method(:count_services_metadata_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_services_metadata_queries), log_message)

      validate_user_authorization(token: token, action: 'get metadata for services', uuid: '', path: '/services', method:'GET', kpi_method: method(:count_services_metadata_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      services = ServiceManagerService.find_services(params)
      validate_collection_existence(collection: services, name: 'services', kpi_method: method(:count_services_metadata_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"Found services #{services}"}
      keys_to_delete = {main_key: :nsd, sub_keys: [:connection_points, :forwarding_graphs, :virtual_links, :service_specific_managers, :network_functions]}
      filtered_services = enhance_collection( collection: services[:items], user: user_name, keys_to_delete: keys_to_delete)
      logger.debug(log_message) {"links: request_url=#{request_url}, limit=#{@limit}, offset=#{@offset}, total=#{filtered_services.count}"}
      links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: filtered_services.count)
      logger.debug(log_message) {"links: #{links}"}
      headers 'Link'=> links, 'Record-Count'=> filtered_services.count.to_s
      count_services_metadata_queries(labels: {result: "ok", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      halt 200, filtered_services.to_json
    end
  
    # GET a specific service
    get '/:uuid/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi:: GET /api/v2/services/:uuid'
      logger.debug(log_message) {"entered with #{params}"}

      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_service_metadata_queries), began_at: began_at, log_message: log_message)

      token = get_token( request.env, began_at, method(:count_service_metadata_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_service_metadata_queries), log_message)
      validate_user_authorization(token: token, action: "get metadata for services #{params[:uuid]}", uuid: params[:uuid], path: '/services', method:'GET', kpi_method: method(:count_service_metadata_queries), began_at: began_at, log_message: log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
    
      # TODO: mind that, besides the URL-based uuid we might as well pass other params, like fields we want to show
      #params.delete :uuid
      service = ServiceManagerService.find_service_by_uuid(uuid: params[:uuid]) #, params: params)
      validate_element_existence(uuid: params[:uuid], element: service, name: 'Service', kpi_method: method(:count_service_metadata_queries), began_at: began_at, log_message: log_message)
      validate_ownership_and_licence(element: service[:items], user_name: user_name, kpi_method: method(:count_service_metadata_queries), began_at: began_at, log_message: log_message)
      
      count_service_metadata_queries(labels: {result: "ok", uuid: params[:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      logger.debug(log_message) {"leaving with #{service}"}
      headers 'Record-Count'=> '1'
      halt 200, service[:items].to_json
    end
  end
  
  namespace '/api/v2/admin/services' do
    get '/logs/?' do
      log_message = 'GtkApi::GET /admin/services/logs'
      logger.debug(log_message) {'entered'}
      headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
      url = ServiceManagerService.class_variable_get(:@@url)+'/admin/logs'
      log = ServiceManagerService.get_log(url: url, log_message:log_message)
      logger.debug(log_message) {'leaving with log='+log}
      halt 200, log
    end
  end
  
  private
  
  def count_services_metadata_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many service metadata queries have been made"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'services'})})
  end

  def count_service_metadata_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many service metadata queries by uuid have been made"
    ServiceManagerService.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'services'})})
  end
end
