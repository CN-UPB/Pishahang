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

# @see VNFRepository
class SonataVnfRepository < Sinatra::Application
  
  @@vnfr_schema=JSON.parse(JSON.dump(YAML.load(open('https://raw.githubusercontent.com/tobiasdierich/son-schema/master/function-record/vnfr-schema.yml'){|f| f.read})))
  # https and openssl libs (require 'net/https' require 'openssl') enable access to external https links behind a proxy

  before do
    # Gatekeepr authn. code will go here for future implementation
    # --> Gatekeeper authn. disabled

    if settings.environment == 'development'
      return
    end
    #authorized?
  end

  # @method get_root
  # @overload get '/'
  # Get all available interfaces
  # -> Get all interfaces
  get '/' do
      headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_yaml
  end

  # @method get_log
  # @overload get '/vnf-instances/log'
  #	Returns contents of log file
  # Management method to get log file of repository remotely
  get '/vnf-instances/log' do
    filename = 'log/development.log'

    # For testing purposes only
    begin
      txt = open(filename)

    rescue => err
      logger.error "Error reading log file: #{err}"
      return 500, "Error reading log file: #{err}"
    end

    return 200, txt.read.to_s
  end

  # @method get_vnfs
  # @overload get '/vnf-instances'
  #	Returns a list of VNFRs
  # List all VNFRs in JSON or YAML
  #   - JSON (default)
  #   - YAML including output parameter (e.g /vnf-instances?output=YAML)
  get '/vnf-instances' do
    params[:offset] ||= 1
    params[:limit] ||= 10

    # Only accept positive numbers
    params[:offset] = 1 if params[:offset].to_i < 1
    params[:limit] = 2 if params[:limit].to_i < 1

    # Get paginated list
    vnfs = Vnfr.paginate(page: params[:offset], limit: params[:limit])
    logger.debug(vnfs)
    # Build HTTP Link Header
    headers['Link'] = build_http_link(params[:offset].to_i, params[:limit])

    if params[:output] == 'YAML'
      content_type = 'application/x-yaml'
    else
      content_type = 'application/json'
    end

    begin
      # Get paginated list
      vnfs = Vnfr.paginate(page: params[:offset], limit: params[:limit])
      logger.debug(vnfs)
      # Build HTTP Link Header
      headers['Link'] = build_http_link(params[:offset].to_i, params[:limit])
      vnfs_json = vnfs.to_json
      if content_type == 'application/json'
        return 200, vnfs_json
      elsif content_type == 'application/x-yaml'
        vnfs_yml = json_to_yaml(vnfs_json)
        return 200, vnfs_yml
      end
    rescue
      logger.error 'Error Establishing a Database Connection'
      return 500, 'Error Establishing a Database Connection'
    end
  end

  # @method get_vnf-instances
  # @overload get "/vnf-instances"
  # Gets vnf-instances with an id
  # Return JSON or YAML
  #   - JSON (default)
  #   - YAML including output parameter (e.g /vnf-instances?output=YAML)
  get '/vnf-instances/:id' do
    begin
      @vnfInstance = Vnfr.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound => e
      halt (404)
    end

    if params[:output] == 'YAML'
      content_type = 'application/x-yaml'
    else
      content_type = 'application/json'
    end
    vnfs_json = @vnfInstance.to_json
    if content_type == 'application/json'
      return 200, vnfs_json
    elsif content_type == 'application/x-yaml'
      vnfs_yml = json_to_yaml(vnfs_json)
      return 200, vnfs_yml
    end
  end

  # @method post_vnfrs
  # @overload post '/vnf-instances'
  # Post a VNF in YAML format
  # @param [YAML/JSON]
  # Post a vnfr
  # Return JSON or YAML depending on content_type
  post '/vnf-instances' do

    if request.content_type ==  'application/json'
      instance, errors = parse_json(request.body.read)
      return 400, errors.to_json if errors
      vnf_json = instance
    elsif request.content_type == 'application/x-yaml'
      instance, errors = parse_yaml(request.body.read)
      return 400, errors.to_json if errors
      vnf_json = yaml_to_json(instance)
      instance, errors = parse_json(vnf_json)
      return 400, errors.to_json if errors
    end
    puts 'vnf: ', Vnfr.to_json
    errors = validate_json(vnf_json,@@vnfr_schema)
    return 422, errors.to_json if errors

    begin
      instance = Vnfr.find( instance['id'] )
      return 409, 'ERROR: Duplicated VNF ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Save to DB
    begin
      instance = Vnfr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated VNF ID' if e.message.include? 'E11000'
    end

    puts 'New VNF has been added'
    vnf_json = instance.to_json
    if request.content_type == 'application/json'
      return 200, vnf_json
    elsif request.content_type == 'application/x-yaml'
      vnf_yml = json_to_yaml(vnf_json)
      return 200, vnf_yml
    end
  end

  # @method put_vnfrs
  # @overload put '/vnf-instances'
  # Put a VNF in YAML format
  # @param [JSON/YAML]
  # Put a vnfr
  # Return JSON or YAML depending on content_type
  put '/vnf-instances/:id' do

    if request.content_type ==  'application/json'
      instance, errors = parse_json(request.body.read)
      return 400, errors.to_json if errors
      vnf_json = instance
    elsif request.content_type == 'application/x-yaml'
      instance, errors = parse_yaml(request.body.read)
      return 400, errors.to_json if errors
      vnf_json = yaml_to_json(instance)
      instance, errors = parse_json(vnf_json)
      return 400, errors.to_json if errors
    end

    begin
      vnfr = Vnfr.find( instance['id'] )
      puts 'VNF is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'This VNFR does not exists'
    end

    puts 'validating entry: ', vnf_json
    errors = validate_json(vnf_json,@@vnfr_schema)
    return 422, errors.to_json if errors

    # Update to new version
    puts 'Updating...'
    begin
      # Delete old record
      Vnfr.where( {'id' => params[:id] }).delete
      # Create a record
      new_vnfr = Vnfr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated NS ID' if e.message.include? 'E11000'
    end

    puts 'New VNF has been updated'
    vnf_json = instance.to_json
    if request.content_type == 'application/json'
      return 200, vnf_json
    elsif request.content_type == 'application/x-yaml'
      vnf_yml = json_to_yaml(vnf_json)
      return 200, vnf_yml
    end
  end

  # @method delete_vnfr_external_vnf_id
  # @overload delete '/vnf-instances/:id'
  #	Delete a vnf by its ID
  #	@param [Integer] external_vnf_id vnf external ID
  # Delete a vnf
  delete '/vnf-instances/:id' do
    begin
      vnf = Vnfr.find_by( {'id' =>  params[:id]})
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404,'ERROR: Operation failed'
    end
    vnf.destroy
    return 200, 'OK: vnfr removed'
  end
end