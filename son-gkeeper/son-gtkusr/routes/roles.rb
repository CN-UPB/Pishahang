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
  # Get a role by query
  get '/roles' do
    # This endpoint allows queries for the next fields:
    # search, lastName, firstName, email, username, first, max
    logger.debug 'Adapter: entered GET /roles'
    queriables = %w(id name)
    params.each { |k, v|
      unless queriables.include? k.to_s
        json_error(400, 'Bad query')
      end
    }
    code, realm_roles = get_realm_roles(params)
    logger.debug "Adapter: gathered roles #{realm_roles}"
    json_error(404, 'No roles found') if realm_roles == 'null'
    realm_roles = parse_json(realm_roles)[0]
    if realm_roles.is_a?(Array)
      params['offset'] ||= DEFAULT_OFFSET
      params['limit'] ||= DEFAULT_LIMIT
      realm_roles = apply_limit_and_offset(realm_roles, offset=params[:offset], limit=params[:limit])
    end
    logger.debug "Adapter: leaving GET /roles with #{realm_roles}"
    halt code.to_i, {'Content-type' => 'application/json'}, realm_roles.to_json
  end

  post '/roles/?' do
    # POST /admin/realms/{realm}/roles
    # BodyParameter
    logger.debug 'Adapter: entered POST /roles'
    logger.info "Content-Type is " + request.media_type
    halt 415 unless (request.content_type == 'application/json')

    new_role_data, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
    halt 400 unless new_role_data.is_a?(Hash)

    code, msg = create_realm_role(new_role_data)
    json_error(code.to_i, msg.to_s) unless msg.empty?
    halt code.to_i
  end

  # Update a role by name
  put '/roles/?' do
    logger.debug 'Adapter: entered PUT /roles'
    # PUT /admin/realms/{realm}/roles/{id}
    # BodyParameter
    logger.info "Content-Type is " + request.media_type
    halt 415 unless (request.content_type == 'application/json')

    queriables = %w(id name)
    logger.debug "params=#{params}"
    json_error(400, 'Role Name or Id is missing') if params.empty?

    params.each { |k, v|
      logger.debug "Adapter: query #{k}=#{v}"
      unless queriables.include? k.to_s
        json_error(400, 'Bad query')
      end
    }
    code, role_data = get_realm_roles(params)
    logger.debug "Adapter: found role_data= #{role_data}"
    json_error(400, 'Indicated role not found') if role_data == 'null'
    role_data, errors = parse_json(role_data)

    new_role_data, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
    halt 400 unless new_role_data.is_a?(Hash)

    code, msg = update_realm_role(role_data['name'], new_role_data)
    halt code.to_i, {'Content-type' => 'application/json'}, msg unless msg.nil?
    halt code.to_i
  end

  # Delete a role by name
  delete '/roles/?' do
    logger.debug 'Adapter: entered DELETE /roles'
    # DELETE /admin/realms/{realm}/roles/{id}
    queriables = %w(id name)
    json_error(400, 'Role Name or Id is missing') if params.empty?

    params.each { |k, v|
      logger.debug "Adapter: query #{k}=#{v}"
      unless queriables.include? k.to_s
        json_error(400, 'Bad query')
      end
    }
    code, role_data = get_realm_roles(params)
    logger.debug "Adapter: found role_data= #{role_data}"
    json_error(400, 'Indicated role not found') if role_data == 'null'
    role_data, errors = parse_json(role_data)

    code, msg = delete_realm_role(role_data['name'])
    halt code.to_i, {'Content-type' => 'application/json'}, msg unless msg.nil?
    halt code.to_i
  end

  post '/roles/assign/?' do
    # Assign user to a role
    logger.debug 'Adapter: entered POST /roles/assign'
    logger.info "Content-Type is " + request.media_type
    halt 415 unless (request.content_type == 'application/json')

    form, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
    halt 400 unless form.is_a?(Hash)
    json_error 400, 'Username not provided' unless form.key?('username')
    json_error 400, 'Role name not provided' unless form.key?('role')

    # Translate from username to User_id
    user_id = get_user_id(form['username'])
    json_error 404, 'Username not found' if user_id.nil?

    code , msg = assign_role(form['role'], user_id)
    halt code.to_i, {'Content-type' => 'application/json'}, msg
  end

  post '/roles/unassign/?' do
    # Unassign user to a role
    logger.debug 'Adapter: entered POST /roles/unassign'
    logger.info "Content-Type is " + request.media_type
    halt 415 unless (request.content_type == 'application/json')

    form, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
    halt 400 unless form.is_a?(Hash)
    json_error 400, 'Username not provided' unless form.key?('username')
    json_error 400, 'Role name not provided' unless form.key?('role')

    #Translate from username to User_id
    user_id = get_user_id(form['username'])
    json_error 404, 'Username not found' if user_id.nil?

    code , msg = unassign_role(form['role'], user_id)
    halt code.to_i, {'Content-type' => 'application/json'}, msg
  end
end
