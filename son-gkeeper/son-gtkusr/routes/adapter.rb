##
## Copyright (c) 2015 SONATA-NFV
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
## Neither the name of the SONATA-NFV
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).

require 'json'
require 'sinatra'
require 'net/http'
require_relative '../helpers/init'


# Adapter class
class Adapter < Sinatra::Application
  # @method get_root
  # Get all available interfaces
  # -> Get all interfaces
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_json
  end

  # @method get_log
  # Returns contents of log file
  # Management method to get log file of adapter remotely
  get '/log' do
    logger.debug 'Adapter: entered GET /admin/log'
    headers 'Content-Type' => 'text/plain; charset=utf8'
    # filename = 'log/development.log'
    filename = 'log/production.log'

    # For testing purposes only
    begin
      txt = open(filename)

    rescue => err
      logger.error "Error reading log file: #{err}"
      json_error(500, "Error reading log file: #{err}")
    end

    halt 200, txt.read.to_s
  end

  get '/config' do
    # This endpoint returns the Keycloak public key
    logger.debug 'Adapter: entered GET /admin/config'

    begin
      keycloak_yml = YAML.load_file('config/keycloak.yml')
    rescue => err
      logger.error "Error loading config file: #{err}"
      json_error(500, "Error loading config file: #{err}")
    end
    halt 200, keycloak_yml.to_json
  end
end

# Adapter-Keycloak API class
class Keycloak < Sinatra::Application

  @@access_token = nil
  @@sp_public_key = nil

  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_json
  end

  post '/config' do
    logger.debug 'Adapter: entered POST /config'
    # log_file = File.new("#{settings.root}/log/#{settings.environment}.log", 'a+')
    # STDOUT.reopen(log_file)
    # STDOUT.sync = true
    begin
      keycloak_address = Resolv::Hosts.new.getaddress(ENV['KEYCLOAK_ADDRESS'])
    rescue
      keycloak_address = Resolv::DNS.new.getaddress(ENV['KEYCLOAK_ADDRESS'])
    end
    logger.debug "Checking #{request.ip.to_s} with #{keycloak_address.to_s}"

    # Check if the request comes from keycloak docker.
    halt 401 if request.ip.to_s !=  keycloak_address.to_s
    json_error(409, 'Secret key is already defined') if defined? @@client_secret

    @@client_secret = params['secret']
    get_oidc_endpoints
    get_adapter_install_json
    @@access_token = self.get_adapter_token
    logger.debug 'Adapter: POST /config obtained access_token'
    @@sp_public_key = get_public_key if @@sp_public_key.nil?
    logger.debug 'Adapter: POST /config obtained platform public key'

    begin
      logger.debug 'Adapter: Loading default resource file'
      default_resource = File.read('config/initial-resource.json')
      resource_hash = JSON.parse(default_resource)
      begin
        # Generate the UUID for the resource object
        # new_resource['_id'] = SecureRandom.uuid
        resource = Sp_resource.create!(resource_hash)
        logger.debug "Adapter: POST /config added default permissions #{resource.to_s} to MongoDB"
        @@enabled_db = true
      rescue Moped::Errors::OperationFailure => e
        logger.debug "Adapter: POST /config MongoDB could not be reached or configured: #{e}"
        @@enabled_db = false
      rescue => e
        logger.error "Adapter: POST /config error=#{e}"
        @@enabled_db = false
      end
    rescue => e
      logger.error "Adapter: POST /config connecting MongoDB error: #{e}"
    end
    logger.debug 'Adapter: exit POST /config with secret and access_token configured'
    logger.info 'User Management is configured and ready'
    # STDOUT.sync = false
    halt 200
  end

  get '/public-key' do
    # This endpoint returns the Keycloak public key
    logger.debug 'Adapter: entered GET /public-key'
    keycloak_yml = YAML.load_file('config/keycloak.yml')
    unless keycloak_yml['realm_public_key']
      Keycloak.get_realm_public_key
      keycloak_yml = YAML.load_file('config/keycloak.yml')
    end

    response = {"public-key" => keycloak_yml['realm_public_key'].to_s}
    halt 200, {'Content-type' => 'application/json'}, response.to_json
  end

  get '/refresh' do
    # This endpoint forces the Adapter to refresh the token
    logger.debug 'Adapter: entered GET /refresh'
    code, access_token = refresh_adapter
    logger.debug "Adapter: exit from GET /refresh with token #{access_token}"
    halt code.to_i
  end

  post '/authorize' do
    # The authorize endpoint returns OK if the user’s has enabling permissions to access to the endpoint
    logger.debug 'Adapter: entered POST /authorize'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    # 1. Get authorization token
    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
    unless user_token
      logger.debug 'Adapter: exit POST /authorize without access token'
      json_error(400, 'Access token is not provided')
    end

    # 2. Validate token
    res, code = token_validation(user_token)
    logger.debug "Adapter: Token validation is #{res.to_s}"
    logger.debug 'Adapter: exit POST /authorize with unauthorized access token' unless code == '200'
    json_error(400, res.to_s) unless code == '200'
    token_content = JSON.parse(res)

    # 3. Check token expiration
    result = is_active?(res)
    logger.debug "Adapter: Token status is #{result.to_s}"
    logger.debug 'Adapter: exit POST /authorize with invalid access token'
    json_error(401, 'Token not active') unless result
    logger.debug "Adapter: Token contents #{token_content}"

    # 4. Direct Access for Admins
    # Role check; Allows total authorization to admin roles
    result = admin_check(token_content)
    if result
      logger.info "Adapter: Authorized access to administrator Id=#{token_content['sub']}"
      halt 200
    end

    logger.info 'Authorization started at /authorize'
    # 5. Fetch request data
    logger.info "Content-Type is " + request.media_type

    # Compatibility support for JSON content-type
    # Parses and validates JSON format
    case request.content_type
      # when 'application/x-www-form-urlencoded'
        # Validate format
        # form_encoded, errors = request.body.read
        # halt 400, errors.to_json if errors
        # form = Hash[URI.decode_www_form(form_encoded)]
        # keyed_params = keyed_hash(form)
        # halt 401 unless (keyed_params[:'path'] and keyed_params[:'method'])

      when 'application/json'
        request_data, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
        logger.info "Request parameters are #{request_data.to_s}"
        keyed_params = keyed_hash(request_data)
        json_error(401, 'Parameters "path=" and "method=" not found') unless
            (keyed_params[:path] and keyed_params[:method])
      else
        # Request is a QUERY TYPE
        logger.info "Request parameters are #{params}"
        keyed_params = keyed_hash(params)
        # params examples: {:path=>"/catalogues", :method=>"GET"}
        json_error(401, 'Parameters "path=" and "method=" not found') unless
            (keyed_params[:path] and keyed_params[:method])
    end

    # The permissions are used to restrict access to an API endpoint and control users actions
    # The authorize endpoint essentially returns true if any of the user’s permission has access to the endpoint
    # Check the provided path to the resource and the HTTP method, then build the request
    # if @@enabled_db...
    request = process_request(keyed_params[:path], keyed_params[:method])
    json_error(401, 'Resource unavaliable') if request.nil?

    # 6. Evaluate Authorization
    logger.info 'Evaluating Authorization request'
    # Authorization process (Authorization algorithm is permission based)
    auth_code, auth_msg = authorize?(user_token, request)
    logger.info "Authorization result: #{auth_code}"
    halt auth_code.to_i if auth_code.to_i == 200
    json_error(auth_code, auth_msg)
  end

  # DEPRECATED!
  post '/authenticate' do
    logger.debug 'Adapter: entered POST /authenticate'
    logger.info 'POST /authenticate is deprecated! It returns an ID token which is currently unused'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]
    keyed_params = params

    case keyed_params[:grant_type]
      when 'password' # -> user
        authenticate(keyed_params[:client_id],
                     keyed_params[:username],
                     keyed_params[:password],
                     keyed_params[:grant_type])

      when 'client_credentials' # -> service
        authenticate(keyed_params[:client_id],
                     nil,
                     keyed_params[:client_secret],
                     keyed_params[:grant_type])
      else
        json_error(400, 'Bad request')
    end
  end

  get '/token-status' do
    logger.debug 'Adapter: entered GET /token-status'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
    json_error(400, 'Access token is not provided') unless user_token

    # Validate token
    res, code = token_validation(user_token)
    if code == '200'
      result = is_active?(res)
      case result
        when false
          halt 401
        else
          halt 200
      end
    else
      json_error(400, res.to_s)
    end
  end

  get '/token-check' do
    logger.debug 'Adapter: entered GET /token-check'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
    unless user_token
      json_error(400, 'Access token is not provided')
    end

    # Validate token
    res = token_expired?(user_token)
    json_error(401, res) if res != 200
    halt 200
  end
end