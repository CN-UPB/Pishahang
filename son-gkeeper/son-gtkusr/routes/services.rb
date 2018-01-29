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

# Adapter-Keycloak API class
class Keycloak < Sinatra::Application

  post '/register/service' do
    logger.debug 'Adapter: entered POST /register/service'
    logger.info "Content-Type is " + request.media_type
    halt 415 unless request.content_type == 'application/json'

    # Compatibility support for JSON content-type
    # Parses and validates JSON format
    parsed_form, errors = parse_json(request.body.read)
    logger.debug "Service form errors#{errors}"
    halt 400, errors.to_json if errors

    logger.info 'Registering new Service client'
    client_id, code, msg = register_client(parsed_form)

    if client_id.nil?
      logger.debug "client_id error=#{code}, #{msg.to_s}"
      delete_client(parsed_form['clientId'])
      json_error(400, 'Service client registration failed')
    end

    # To solve predefined roles dependency, create a new role based on client registration
    # New role should have Client Id (name) of service

    client_data, role_data, error_code, error_msg = set_service_roles(parsed_form['clientId'])
    if error_code != nil
      delete_client(parsed_form['clientId'])
      halt error_code, {'Content-type' => 'application/json'}, error_msg.to_json
    end

    code, error_msg = set_service_account_roles(client_data['id'], role_data)
    if code != 204
      delete_client(parsed_form['clientId'])
      halt code, {'Content-type' => 'application/json'}, error_msg
    end
    logger.info "New Service client #{parsed_form['clientId']} registered"
    response = {'clientId' => parsed_form['clientId'], 'id' => client_id.to_s}
    halt 201, {'Content-type' => 'application/json'}, response.to_json
  end

  post '/login/service' do
    logger.debug 'Adapter: entered POST /login/service'
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    pass = request.env["HTTP_AUTHORIZATION"].split(' ').last
    plain_pass  = Base64.decode64(pass)

    client_id = plain_pass.split(':').first
    secret = plain_pass.split(':').last
    logger.info "Service #{client_id} has accessed to log-in"

    credentials = {"type" => "client_credentials", "value" => secret.to_s}
    log_code, log_msg = login(client_id, credentials)
    if log_code != 200
      logger.info "Service #{client_id} has failed to log-in"
      logger.debug 'Adapter: exit POST /login/service'
      halt log_code, {'Content-type' => 'application/json'}, log_msg
    end
    logger.info "Service #{client_id} has logged-in successfully"
    logger.debug 'Adapter: exit POST /login/service'
    halt log_code, {'Content-type' => 'application/json'}, log_msg
  end

  get '/services' do
    # This endpoint allows queries for the next fields: name
    logger.debug 'Adapter: entered GET /services'
    queriables = %w(name id)

    if params.length > 1
      json_error(400, 'Too many arguments')
    end

    if params.first
      k, v = params.first
      unless queriables.include? k
        json_error(400, 'Bad query')
      end
    end

    reg_clients = JSON.parse(get_clients(params))
    logger.debug "Keycloak: registered clients #{reg_clients}"
    reg_clients = [reg_clients] unless reg_clients.is_a?(Array)

    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    reg_clients = apply_limit_and_offset(reg_clients, offset=params[:offset], limit=params[:limit])
    logger.debug 'Adapter: leaving GET /services'
    halt 200, {'Content-type' => 'application/json'}, reg_clients.to_json
  end

  put '/services' do
    # TODO: TO BE IMPLEMENTED
  end

  delete '/services' do
    # This endpoint allows queries for the next fields: name
    logger.debug 'Adapter: entered DELETE /services'
    logger.debug "Adapter: required query #{params}"
    queriables = %w(name id)
    protected_services = %w(account adapter admin-cli broker realm-management security-admin-console)

    json_error(400, 'Bad query') if params.empty?
    if params.length > 1
      json_error(400, 'Too many arguments')
    end

    k, v = params.first
    unless queriables.include? k
      json_error(400, 'Bad query')
    end

    case k
      when 'id'
        reg_client, errors = parse_json(get_clients(params))
        logger.debug "Keycloak: delete request for client #{reg_client}"
        halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
        halt 400 if reg_client.empty?
        halt 400 if protected_services.include?(reg_client['clientId'])
        delete_client(v)
        logger.debug 'Adapter: leaving DELETE /services'
        halt 204
      when 'name'
        logger.debug "Keycloak: delete request for client #{v}"
        halt 400 if protected_services.include?(v)
        reg_client, errors = parse_json(get_clients(params))
        halt 400 if reg_client.empty?
        halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
        delete_client(reg_client['id'])
        logger.debug 'Adapter: leaving DELETE /services'
        halt 204
      else
        json_error(400, 'Bad query')
    end

    get '/sessions/services' do
      # Get all service client sessions
      # Returns a list of service client sessions
      logger.debug 'Adapter: entered GET /sessions/services'
      ses_code, ses_msg = get_sessions('service', nil)

      params['offset'] ||= DEFAULT_OFFSET
      params['limit'] ||= DEFAULT_LIMIT
      ses_msg = apply_limit_and_offset(JSON.parse(ses_msg), offset=params[:offset], limit=params[:limit])
      halt ses_code.to_i, {'Content-type' => 'application/json'}, ses_msg.to_json
    end

    get '/sessions/services/:clientId/?' do
      # Get service client sessions
      # Returns a list of sessions associated with the client service user
    end
  end

  get '/sessions/services' do
    # Get all service client sessions
    # Returns a list of service client sessions
    logger.debug 'Adapter: entered GET /sessions/services'
    ses_code, ses_msg = get_sessions('service', nil)

    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    ses_msg = apply_limit_and_offset(JSON.parse(ses_msg), offset=params[:offset], limit=params[:limit])
    halt ses_code.to_i, {'Content-type' => 'application/json'}, ses_msg.to_json
  end

  get '/sessions/services/:clientId/?' do
    # Get service client sessions
    # Returns a list of sessions associated with the client service user
  end
end
