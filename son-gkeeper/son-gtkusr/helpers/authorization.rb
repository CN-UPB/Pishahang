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

  # Role check; Allows total authorization to admin roles
  def admin_check(token_content)
    realm_roles = token_content['realm_access']['roles']
    if token_content['resource_access'].include?('realm-management')
      resource_roles = token_content['resource_access']['realm-management']['roles']
      true if (realm_roles.include?('admin')) && (resource_roles.include?('realm-admin'))
    end
    false
  end

  def process_request(uri, method)
    # Parse uri path
    path = URI(uri).path.split('/')[1]
    data = URI(uri).path.split('/').last

    # Find mapped resource to path in config mapping
    # resources = @@auth_mappings['resources']
    # Gather database resources
    begin
      resource = Sp_resource.find_by({'resources.URI' => path }) # 'resources.resource_name' => new_ns['name'],
      # Continue
    rescue Mongoid::Errors::DocumentNotFound => e
      # 'The resource is not found or available'
      return nil
    end

    resource = resource.to_json
    resource, errors = parse_json(resource)
    resource_data = resource['resources'].find { |resource_data| resource_data['URI'] == path }

    operation = nil
    if path != data
      resource_data['associated_permissions'].each {|permission|
        if (permission['action'] == method) and (permission['name'] == data)
          operation = permission
        end
      }
    end
    if operation.nil?
      resource_data['associated_permissions'].each {|permission|
        operation = permission if permission['action'] == method
      }
    end

    return if operation.nil?
    logger.debug 'Adapter: Request successfully processed'
    request = {"resources" => resource_data, "policies" => resource['policies'], "operation" => operation}
  end

  def get_token_claims(token_content)
    claims = {}
    claims['name'] = token_content['name']
    claims['preferred_username'] = token_content['preferred_username']
    claims['username'] = token_content['username']
    claims['email'] = token_content['email']
    claims['realm_access'] = token_content['realm_access']
    claims['resource_access'] = token_content['resource_access']
    claims
  end

  def authorize?(user_token, request)
    refresh_adapter
    # Obtain SP Public Key
    @@sp_public_key = get_public_key if @@sp_public_key.nil?
    # Check token
    token_payload, token_header = decode_token(user_token, @@sp_public_key)

    # Evaluate request
    # 1. Get 'apply-policy' allowed roles
    # 2. Check 'policies' for allowed roles
    # 3. Check access token claims

    # log_file = File.new("#{settings.root}/log/#{settings.environment}.log", 'a+')
    # STDOUT.reopen(log_file)
    # STDOUT.sync = true
    logger.debug "Adapter: Token Payload: #{token_payload.to_s}, Token Header: #{token_header.to_s}"

    allowed_roles = request['operation']['apply_policy']
    logger.debug "Adapter: Required Role: #{allowed_roles}"

    # Check access token claims
    begin
      logger.debug "Adapter: Preferred_username=#{token_payload['preferred_username']}"
      token_realm_access_roles = token_payload['realm_access']['roles']
    rescue
      token_realm_access_roles = nil
    end
    # Resource access roles (client based roles)
    begin
      token_resource_access_roles = token_payload['resource_access']
    rescue
      token_resource_access_roles = nil
    end

    authorized = nil
    if allowed_roles.is_a?(Array)
      authorized = allowed_roles.empty?

      allowed_roles.each { |role|
        authorized = token_realm_access_roles.include?(role)
        # Alternative role check in the Keycloak server
        # code, msg = get_realm_roles({'name' => role}) if authorized
        # if msg != 'null'
        if authorized
          policy_data = request['policies'].find {|policy| policy['name'] == role}
          authorized = false if policy_data['logic'] != 'positive'
          break
        end
      }
      unless authorized
        allowed_roles.each { |role|
          token_resource_access_roles.each { |resource_access, values|
            authorized = values['roles'].include?(role)
            if authorized
              policy_data = request['policies'].find {|policy| policy['name'] == role}
              authorized = false if policy_data['logic'] != 'positive'
              break
            end
          }
          break if authorized
        }
      end
    end
    # STDOUT.sync = false

    # Response => 20X or 40X
    case authorized
      when true
        return 200, 'Authorized'
      else
        return 403, 'Not authorized'
    end
  end

  # DEPRECATED
  def authenticate(client_id, username, password, grant_type)
    http_path = "http://#{@@address.to_s}:#{@@port.to_s}/#{@@uri.to_s}/realms/#{@@realm_name}/protocol/openid-connect/token"
    #`curl -X POST --data "client_id=#{client_id}&username=#{usrname}"&
    # password=#{pwd}&grant_type=#{grt_type} #{http_path}`

    uri = URI(http_path)
    res = nil
    case grant_type
      when 'password' # -> user
        res = Net::HTTP.post_form(uri, 'client_id' => client_id,
                                  'client_secret' => password,
                                  'grant_type' => grant_type)

      when 'client_credentials' # -> service
        res = Net::HTTP.post_form(uri, 'client_id' => client_id,
                                  'username' => username,
                                  'password' => password,
                                  'grant_type' => grant_type)
      else
        halt 400
    end

    if res.body['id_token']
      parsed_res, code = parse_json(res.body)
      id_token = parsed_res['id_token']
    else
      halt 401, "ERROR: ACCESS DENIED!"
    end
  end

  # DEPRECATED
  def old_process_request(uri, method)
    # Parse uri path
    path = URI(uri).path.split('/')[1]

    # Find mapped resource to path
    # CHECK IF IS A VALID RESOURCE FROM DATABASE
    resources = @@auth_mappings['resources']


    # Gather database resources
    # Check if NS already exists in the catalogue by name, vendor and version
    # begin
    #  resource = Sp_resource.find_by({ 'resources.resource_name' => new_ns['name'],
    #                             'resources.URI' => path })
    # Continue
    #rescue Mongoid::Errors::DocumentNotFound => e
    #  json_return 401, 'Resource not found'
    #end

    resource = nil
    # p "PATHS", @@auth_mappings['paths']
    @@auth_mappings['paths'].each { |k, v|
      # puts "k, v", k, v
      v.each { |kk, vv|
        # puts "kk, vv", kk, vv
        if kk == path
          # p "Resource found", k, kk
          resource = [k, kk]
          break
        end
      }
      # p "FOUND_RESOURCE", resource
      break if resource
    }
    json_error(403, 'The resource is not available') unless resource

    unless @@auth_mappings['paths'][resource[0]][resource[1]].key?(method)
      json_error(403, 'The resource operation is not available')
    else
      operation = @@auth_mappings['paths'][resource[0]][resource[1]][method]
      puts "FOUND_OPERATION", operation
      request = {"resource" => resource[0], "type" => resource[1], "operation" => operation}
    end
  end

  # DEPRECATED
  def old_authorize?(user_token, request)
    refresh_adapter
    # Check token
    public_key = get_public_key
    token_payload, token_header = decode_token(user_token, public_key)

    # evaluate request
    # Find mapped resource to path
    # required_role is build following next pattern:
    # operation
    # operation_resource
    # operation_resource_type
    logger.debug "Adapter: Token Payload: #{token_payload.to_s}, Token Header: #{token_header.to_s}"
    required_role = 'role_' + request['operation'] + '-' + request['resource']
    logger.debug "Adapter: Required Role: #{required_role}"

    # Check token roles
    begin
      token_realm_access_roles = token_payload['realm_access']['roles']
    rescue
      json_error(403, 'No permissions')
    end

    # Resource access roles (services) will be implemented later
    token_resource_access_resources = token_payload['resource_access']
    code, realm_roles = get_realm_roles
    parsed_realm_roles, errors = parse_json(realm_roles)

    authorized = false
    token_realm_access_roles.each { |role|
      token_role_repr = parsed_realm_roles.find {|x| x['name'] == role}
      unless token_role_repr
        json_error(403, 'No permissions')
      end

      role_perms = token_role_repr['description'].tr('${}', '').split(',')
      if role_perms.include?(required_role)
        authorized = true
      end
    }

    #Response => 20X or 40X
    case authorized
      when true
        return 200, nil
      else
        return 403, 'User is not authorized'
    end
  end
end