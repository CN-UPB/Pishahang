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

#Comment about ROLES
=begin
Large number of roles approach will quickly become unmanageable and it
may be better of using an ACL or something in the application itself.

It is more often implemented as ACLs rather than RBAC.
RBAC is usually used for things like 'manager' has read/write access to a
group of resources, rather than 'user-a' has read access to 'resource-a'.
=end

# Adapter-Keycloak API class
class Keycloak < Sinatra::Application
  # Routes for management operations of resources and associated permissions

  get '/resources/?' do
    logger.debug 'Adapter: entered GET /resources'

    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT

    keyed_params = keyed_hash(params)
    headers = {'Accept' => 'application/json', 'Content-Type' => 'application/json'}
    headers[:params] = params unless params.empty?

    # Get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }

    # Do the query
    resource_data = Sp_resource.where(keyed_params)

    if resource_data && resource_data.size.to_i > 0
      logger.info "Adapter: leaving GET /resources?#{query_string} with #{resource_data}"
      # resource_data = resource_data.paginate(offset: params[:offset], limit: params[:limit])
    else
      # We could not find the resource you are looking for
      logger.info "Adapter: leaving GET /resources?#{query_string} with no resources found"
    end

    response = resource_data.to_json
    halt 200, {'Content-Type' => 'application/json'}, response
  end

  post '/resources' do
    logger.debug 'Adapter: entered POST /resources'

    json_error(415, 'Only "Content-type: application/json" is supported') unless
        request.content_type == 'application/json'

    # Compatibility support for JSON content-type
    # Parses and validates JSON format
    new_resource, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors

    # Validate Resource object
    json_error 400, 'ERROR: Resource Vendor not found' unless new_resource.has_key?('resource_owner_name')
    json_error 400, 'ERROR: Resource Name not found' unless new_resource.has_key?('role')
    json_error 400, 'ERROR: Resource Version not found' unless new_resource.has_key?('resources')
    json_error 400, 'ERROR: Resource Version not found' unless new_resource.has_key?('policies')

    # Check if resource already exists in the database
    begin
      resource = Sp_resource.find_by({'resource_owner_name' => new_resource['resource_owner_name']})
      json_error 409, 'Duplicated resource object'
    rescue Mongoid::Errors::DocumentNotFound => e
      logger.debug 'Resource not found, proceeding to save...'
      # Continue
    end

    # Automatically generate 'role' if it does not exists
    f_role = parse_json(get_realm_roles({'name' => new_resource['role']})[1])[0]
    if f_role.nil?
      code, msg = create_realm_role({'name' => new_resource['role'], 'scopeParamRequired' => false,
                                     'composite' => false, 'clientRole' => false})
      json_error 400 unless code.to_i == 201
    end

    # Save to DB
    begin
      # Generate the UUID for the resource object
      new_resource['_id'] = SecureRandom.uuid
      resource = Sp_resource.create!(new_resource)
    rescue Moped::Errors::OperationFailure => e
      json_error 400, e.to_s
    end

    logger.debug "New resource object added with id=#{new_resource['_id']}"
    halt 201, {'Content-type' => 'application/json'}, resource.to_json
  end

  put '/resources/?' do
    logger.debug 'Adapter: entered PUT /resources'

    keyed_params = keyed_hash(params)
    headers = {'Accept' => 'application/json', 'Content-Type' => 'application/json'}

    json_error 400, 'Resource id or clientId is not provided' unless keyed_params.key?(:id) or
        keyed_params.key?(:clientId)

    resource = nil
    if keyed_params.has_key?(:clientId)
      begin
        resource = Sp_resource.find_by({ 'clientId' => keyed_params[:clientId] })
        logger.debug 'Resource is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "Resource object #{keyed_params[:clientId]} not found"
      end
    elsif keyed_params.has_key?(:id)
      begin
        resource = Sp_resource.find(keyed_params[:id])
        logger.debug 'Resource is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error "DocumentNotFound error for #{keyed_params[:id]}"
        json_error 404, "Resource object #{keyed_params[:id]} not found" unless resource
      end
    else
      logger.debug 'Adapter: leaving DELETE /resources? with no valid resource object specified'
      json_error 400, 'No valid resource object specified'
    end
    json_error 404, 'Resource object not found' if resource.nil?

    new_resource, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors

    # Validate Resource object
    json_error 400, 'Resource clientId not provided' unless new_resource.has_key?('clientId')
    json_error 400, 'Resource resource_owner_name not provided' unless new_resource.has_key?('resource_owner_name')
    json_error 400, 'Resource role not provided' unless new_resource.has_key?('role')
    json_error 400, 'Resource resources not provided' unless new_resource.has_key?('resources')
    json_error 400, 'Resource policies not provided' unless new_resource.has_key?('policies')

    # Automatically generate 'role' if it does not exists
    f_role = parse_json(get_realm_roles({'name' => new_resource['role']})[1])[0]
    if f_role.nil?
      code, msg = create_realm_role({'name' => new_resource['role'], 'scopeParamRequired' => false,
                                     'composite' => false, 'clientRole' => false})
      json_error 400 unless code.to_i == 201
    end

    # Save to DB
    begin
      resource.update_attributes(clientId: new_resource['clientId'],
                                 resource_owner_name: new_resource['resource_owner_name'],
                                 role: new_resource['role'],
                                 resources: new_resource['resources'],
                                 policies: new_resource['policies'])
    rescue Moped::Errors::OperationFailure => e
      json_error 400, e.to_s
    end

    logger.debug "New resource object updated with id=#{resource['_id']}"
    halt 200, {'Content-type' => 'application/json'}, resource.to_json
  end

  delete '/resources/?' do
    logger.debug 'Adapter: entered DELETE /resources'
    # logger.info "Content-Type is " + request.media_type
    # halt 415 unless (request.content_type == 'application/json')

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)
    headers = {'Accept' => 'application/json', 'Content-Type' => 'application/json'}
    # headers[:params] = params unless params.empty?

    json_error 400, 'Resource id or clientId is not provided' unless keyed_params.key?(:id) or
        keyed_params.key?(:clientId)

    if keyed_params.has_key?(:clientId)
      begin
        resource = Sp_resource.find_by({ 'clientId' => keyed_params[:clientId] })
        logger.debug 'Resource is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "Resource object #{keyed_params[:clientId]} not found"
      end
      logger.debug "Adapter: leaving DELETE /resources? with resource object #{keyed_params[:clientId]} deleted"
      resource.destroy
      halt 204
    elsif keyed_params.has_key?(:id)
      begin
        resource = Sp_resource.find(keyed_params[:id])
        logger.debug 'Resource is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "Resource object #{keyed_params[:id]} not found" unless resource
      end
      logger.debug "Adapter: leaving DELETE /resources? with resource object #{keyed_params[:id]} deleted"
      resource.destroy
      halt 204
    else
      logger.debug 'Adapter: leaving DELETE /resources? with no valid resource object specified'
      json_error 400, 'No valid resource object specified'
    end
  end
end
