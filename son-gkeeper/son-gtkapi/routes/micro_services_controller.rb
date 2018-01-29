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

  namespace '/api/v2/micro-services' do
    options '/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST,PUT'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end
    
    # POST new micro-services
    # POST .../api/v2/micro-services: To register a micro-service
    post '/?' do
      log_message = 'GtkApi::POST /api/v2/micro-services/?'
      params = JSON.parse(request.body.read, symbolize_names: true)
      
      logger.info(log_message) {"entered with params=#{params}"}
      
      # { "clientId": "son-catalogue", "clientAuthenticatorType": "client-secret", "secret": "1234", "redirectUris": [ "/auth/son-catalogue"]}
      
      json_error 400, 'Micro-service client ID is missing' unless (params.key?(:clientId) && !params[:clientId].empty?)
      json_error 400, 'Micro-service secret is missing' unless (params.key?(:secret) && !params[:secret].empty?)
      json_error 400, 'Micro-service redirect URIs are missing' unless (params.key?(:redirectUris) && !params[:redirectUris].empty?)
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    
      begin
        micro_service = MicroService.create(params)
        logger.info(log_message) {"leaving with user #{micro_service.inspect}"}
        # headers content_type: 'application/json' #, authorization: 'Bearer '+micro_service.token
        halt 201, {'Content-type' => 'application/json'}, {'clientId' => params[:clientId]}.to_json  # '' #micro_service.client_id
      rescue MicroServiceNotCreatedError => e 
        json_error 400, "Error creating micro-service #{params}", log_message
      rescue MicroServiceAlreadyCreatedError => e
        json_error 409, "Micro-service #{params} was already created", log_message
      end
    end

    # GET .../api/v2/micro-services: To get the token (both login and refresh), providing Authorization header: 'basic <clientId:secret>
    get '/?' do
      log_message = 'GtkApi:: GET /api/v2/micro-services'
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      if request.env['HTTP_AUTHORIZATION']
        logger.debug(log_message) {'authorization='+request.env['HTTP_AUTHORIZATION']}
        credentials = basic_authentication request.env['HTTP_AUTHORIZATION']
        json_error(400, 'Micro-service basic authentication is needed', log_message) if credentials.empty?

        begin
          # micro_service = MicroService.find_by_credentials(Base64.strict_encode64(credentials))
          micro_service = MicroService.find_by_credentials(credentials)
          logger.debug(log_message) {"Found micro-service #{micro_service}"}
          # headers content_type: :json
          halt 200, {'Content-type' => 'application/json'}, micro_service.to_json # (only: [:token])
        rescue MicroServiceNotFoundError => e
          json_error 400, 'No micro-service with basic authentication '+credentials+' was found', log_message
        end
      else
        # If here, it's the common 'index' action
        logger.debug(log_message) {'entered with '+query_string}
    
        @offset ||= params['offset'] ||= DEFAULT_OFFSET
        @limit ||= params['limit'] ||= DEFAULT_LIMIT
        logger.debug(log_message) {"offset=#{@offset}, limit=#{@limit}"}
        logger.debug(log_message) {"params=#{params}"}
    
        begin
          micro_services = MicroService.find(params)
          logger.debug(log_message) {"Found micro-services #{micro_services}"}
          unless micro_services.empty?
            logger.debug(log_message) {"links: request_url=#{request_url}, limit=#{@limit}, offset=#{@offset}, total=#{micro_services.count}"}
            links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: micro_services.count)
            logger.debug(log_message) {"links: #{links}"}
            headers 'Content-Type'=>'application/json', 'Link'=>links, 'Record-Count'=> micro_services.count.to_s
            halt 200, micro_services.to_json
          else
            json_error 404, "No micro-services with #{params} were found", log_message
          end
        rescue MicroServiceNotFoundError => e 
          json_error 400, "No micro-service with params #{params} was found", log_message
        end
      end
    end

    # GET .../api/v2/micro-services/users/public-key: To get the UM's public-key:
    get '/public-key/?' do
      log_message = 'GtkApi:: GET /api/v2/micro-services/public-key'
      logger.debug(log_message) {"entered with #{params}"}
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    
      begin
        pk = MicroService.public_key
        logger.debug(log_message) {"leaving with #{pk}"}
        halt 200, pk.to_json
      rescue PublicKeyNotFoundError
        json_error 404, "No public key for the User Management micro-service was found", log_message
      end
    end

    #get '/admin/users/logs/?' do
    #  log_message = 'GtkApi::GET /admin/services/logs'
    #  logger.debug(log_message) {'entered'}
    #  headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
    #  log = ServiceManagerService.get_log(url:ServiceManagerService.class_variable_get(:@@url)+'/admin/logs', log_message:log_message)
    #  logger.debug(log_message) {'leaving with log='+log}
    #  halt 200, log
    #end
  end
  
  private
  
  def basic_authentication(auth_header)
    authentication = auth_header.split(' ')
    authentication.first.downcase == 'basic' ? authentication.last : ''
  end
end

    
    
=begin
1. requests from ‘clients’ will start to include the token, right?
Yes.
- Requests from Users (developers, customers) (from SDK, BSS, GUI), once they are authenticated, will include the token.
- Requests from Micro-services (SP internal components, concretely Monitoring and Catalogue) once they are authenticated, will include the token.

2. And the GK API validating it, right?
Yes again.
- Validating the request: GK API receives the request, then asks to the UM to validate (authorization check).

3. Validation is done within the UM, with the GK API passing it the ‘client name’ + token, right?
Validation done in the UM. However, UM needs the token and the resource that is being requested to access + the HTTP method. Let's do an example:

I) Developer 'devname' wants to POST a package file to the Catalogue

II) GK API receives 'devname' request:
POST url = URI("http://sp.int3.sonata-nfv.eu:32001/api/v2/packages") 
request["authorization"] = 'Bearer eyJhbGciOiJSX0NpUUhmTm9nIn0...' 
request.body = sonata-demo.son

III) GK API asks UM to validate (authorize) 'devname' request. TO do that, GK API sends the next request to the UM:
GET 
url = URI("http://son-gtkusr:5600/api/v1/authorize?path=/packages&method=POST")
request["authorization"] = 'Bearer eyJhbGciOiJSX0NpUUhmTm9nIn0...'

IV) UM decodes the token to authenticate 'devname' and obtain his roles and permissions. With path=/packages&method=POST, UM learns that 'devname' wants to access the Catalogue to write a package. Then evaluates if the request can be authorized, returning a '200: OK' or '401: Forbidden'

V) GK API proceeds based on UM response. If it is '200', stores the package in the Catalogue, or if it is '401, tells to 'devname' that he is not allowed to request that.
=end    
