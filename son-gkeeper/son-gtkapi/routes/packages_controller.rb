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
require 'sinatra/base'
require 'sinatra/namespace'
require 'sinatra/streaming'
require 'base64'

class GtkApi < Sinatra::Base

  register Sinatra::Namespace
  helpers Sinatra::Streaming
  
  namespace '/api/v2/packages' do
    before do
      content_type :json
    end
    
    # POST of packages
    post '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::POST /api/v2/packages/?'
      logger.info(log_message) {"entered with params=#{params}"}
    
      require_param(param: 'package', params: params, kpi_method: method(:count_package_on_boardings), error_message: "No package file specified: #{params}", log_message: log_message, began_at: began_at)
      require_param(param: :tempfile, params: params['package'], kpi_method: method(:count_package_on_boardings), error_message: "Temp file name", log_message: log_message, began_at: began_at)
      GtkApi.logger.error(log_message) {"file name is #{params[:package][:tempfile]}"}
      
      token = get_token( request.env, began_at, method(:count_package_on_boardings), log_message)
      signature = get_signature( request.env, log_message)
      user_name = get_username_by_token( token, began_at, method(:count_package_on_boardings), log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
      
      begin
        # Validate validator's existence first here
        validation_results = Validator.valid_package?(file_path: params[:package][:tempfile].path, signature: signature)
      rescue ValidatorError => e
        count_package_on_boardings(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
        json_error 400, "Error validating package #{params}", log_message
      rescue ValidatorGenericError => e
        count_package_on_boardings(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
        GtkApi.logger.error(log_message) {"Error during processing: #{$!}"}
        GtkApi.logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
        json_error 400, "Error validating package #{params}", log_message
      end
      
      if (validation_results['error_count'] != 0 || validation_results['warning_count'] != 0)
        count_package_on_boardings(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
        json_error 400, "Errors or warnings: #{validation_results}", log_message
      end
      
      begin
        params[:package][:tempfile].rewind
        resp = Package.create(params.merge({token: token}))
        logger.debug(log_message) {"resp=#{resp.inspect}"}

        case resp[:status]
        when 201
          logger.info(log_message) {"leaving with package: #{resp[:data][:uuid]}"}
          count_package_on_boardings(labels: {result: "ok", uuid: resp[:data][:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
          headers 'Location'=> Package.class_variable_get(:@@url)+"/packages/#{resp[:data][:uuid]}", 'Content-Type'=> 'application/json'
          halt 201, resp[:data].to_json
        when 400
          count_package_on_boardings(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
          json_error 400, "Error creating package #{params}", log_message
        when 403
          count_package_on_boardings(labels: {result: "forbidden", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
          json_error 403, "User not allowed to create package #{params}", log_message
        when 404
          count_package_on_boardings(labels: {result: "not found", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
          json_error 404, "User name not found", log_message
        when 409
          logger.error(log_message) {"leaving with duplicated package: #{resp[:data]}"}
          count_package_on_boardings(labels: {result: "duplicated", uuid: resp[:data][:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
          halt 409, resp[:data].to_json
        else
          count_package_on_boardings(labels: {result: "other error", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
          json_error resp[:status], "Unknown status: #{resp[:status]} for package #{params}", log_message
        end
      rescue ArgumentError => e
        count_package_on_boardings(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
        json_error 400, "Error creating package #{params}", log_message
      end
    end

  # GET a specific package
    get '/:uuid/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/packages/:uuid/?'
      logger.debug(log_message) {'entered'}
      
      require_param(param: 'uuid', params: params, kpi_method: method(:count_single_package_queries), error_message: 'No package UUID specified', log_message: log_message, began_at: began_at)
      validate_uuid(uuid: params[:uuid], kpi_method: method(:count_single_package_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"params[:uuid]=#{params[:uuid]}"}

      token = get_token( request.env, began_at, method(:count_single_package_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_single_package_queries), log_message)
      validate_user_authorization(token: token, action: "get metadata for package #{params[:uuid]}", uuid: params[:uuid], path: '/packages', method:'GET', kpi_method: method(:count_single_package_queries), began_at: began_at, log_message: log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
      
      package = Package.find_by_uuid(params[:uuid])
      validate_element_existence(uuid: params[:uuid], element: package, name: 'Package', kpi_method: method(:count_single_package_queries), began_at: began_at, log_message: log_message)
      validate_ownership_and_licence(element: package[:items], user_name: user_name, kpi_method: method(:count_single_package_queries), began_at: began_at, log_message: log_message)
        
      logger.debug(log_message) {"leaving with package #{package}"}
      count_single_package_queries(labels: {result: "ok", uuid: params[:uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      halt 200, package[:items].to_json
    end
  
    # GET a specific package's file
    get '/:uuid/download/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/packages/:uuid/download/?'
      logger.debug(log_message) {'entered with uuid='+params['uuid']}

      require_param(param: 'uuid', params: params, kpi_method: method(:count_package_downloads), error_message: 'No package UUID specified', log_message: log_message, began_at: began_at)
      validate_uuid(uuid: params['uuid'], kpi_method: method(:count_package_downloads), began_at: began_at, log_message: log_message)
      token = get_token( request.env, began_at, method(:count_package_downloads), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_package_downloads), log_message)
      validate_user_authorization(token: token, action: "download package #{params[:uuid]}", uuid: params['uuid'], path: '/packages/download', method:'GET', kpi_method: method(:count_single_package_queries), began_at: began_at, log_message: log_message)
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
        
      package = Package.find_by_uuid(params[:uuid])
      logger.debug(log_message) {"package=#{package}"}
      validate_element_existence(uuid: params[:uuid], element: package, name: 'Package', kpi_method: method(:count_package_downloads), began_at: began_at, log_message: log_message)
      validate_ownership_and_licence(element: package[:items], user_name: user_name, kpi_method: method(:count_package_downloads), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"Found package #{package[:items]}"}
      logger.debug(log_message) {"Looking for the package file name for package file #{package[:items][:son_package_uuid]}..."}
      file_name = Package.download(package[:items][:son_package_uuid])
      count_package_downloads(labels: {result: "ok", uuid: params['uuid'], elapsed_time: (Time.now.utc-began_at).to_s})
      send_file file_name, type: 'application/zip', filename: :son_package_uuid.to_s
    end

    # GET potentially many packages
    get '/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/packages/?'
      logger.debug(log_message) {'entered with '+query_string}
    
      @offset ||= params[:offset] ||= DEFAULT_OFFSET
      @limit ||= params[:limit] ||= DEFAULT_LIMIT

      token = get_token( request.env, began_at, method(:count_packages_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_packages_queries), log_message)
      validate_user_authorization(token: token, action: 'get metadata for packages', uuid: '', path: '/packages', method:'GET', kpi_method: method(:count_packages_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      packages = Package.find(params)
      validate_collection_existence(collection: packages, name: 'packages', kpi_method: method(:count_packages_queries), began_at: began_at, log_message: log_message)
      keys_to_delete = {main_key: :vnfd, sub_keys: [:entry_service_template, :package_content]}
      enhanced_packages = enhance_collection( collection: packages[:items], user: user_name, keys_to_delete: keys_to_delete)
      logger.debug(log_message) { "leaving with #{enhanced_packages}"}
      # TODO: total must be returned from the PackageManagement service
      links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: enhanced_packages.size)
      headers 'Link'=> links
      halt 200, enhanced_packages.to_json
    end
  
    # DELETE
    delete '/:uuid/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::DELETE /api/v2/packages/:uuid/?'
      json_error 404, 'Package uuid needed', log_message if params[:uuid].nil?
      
      logger.info(log_message) { "entered with package id #{params[:uuid]}"}
      token = get_token( request.env, began_at, method(:count_packages_deletions), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_packages_deletions), log_message)
      
      # is any user allowed to delete any one's package? Or just public and his/her own?
      validate_user_authorization(token: token, action: 'get metadata for packages', uuid: '', path: '/packages', method:'DELETE', kpi_method: method(:count_packages_deletions), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}
      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()
      package = Package.delete(params[:uuid])
      json_error 404, 'No package found with uuid='+params[:uuid], log_message unless package

      logger.debug(log_message) { "deleted package with uuid=#{params[:uuid]}"}
      [204, {}, '']
    end
  end
  
  namespace '/api/v2/admin/packages' do
    get '/logs/?' do
      log_message = 'GtkApi::GET /api/v2/admin/packages/logs'
      logger.debug(log_message) {'entered'}
      url = Package.class_variable_get(:@@url)+'/admin/logs'
      log = Package.get_log(url: url, log_message:log_message)
      logger.debug(log_message) {'leaving with log='+log}
      headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
      halt 200, log #.to_s
    end
  end
  
  def count_package_on_boardings(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many packages have been on-boarded"
    Package.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'POST', module: 'packages'})})
  end
  
  def count_package_downloads(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many package file downloads have been requested"
    Package.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'packages'})})
  end
  
  def count_single_package_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many single package have been requested"
    Package.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'packages'})})
  end

  def count_packages_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many packages have been requested"
    Package.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'packages'})})
  end
  
  def count_packages_deletions(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many package deletions have been requested"
    Package.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'DELETE', module: 'packages'})})
  end
end
