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

# @see SonCatalogue
# class SonataCatalogue < Sinatra::Application

class CatalogueV2 < SonataCatalogue
  ### COSD API METHODS ###

  # @method get_nssSS
  # @overload get '/catalogues/complex-services/?'
  #	Returns a list of COSs
  # -> List many descriptors
  get '/complex-services/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    logger.info "Catalogue: entered GET /api/v2/complex-services?#{query_string}"

    # Split keys in meta_data and data
    # Then transform 'string' params Hash into keys
    keyed_params = add_descriptor_level('cosd', params)

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }

    # Check for special case (:version param == last)
    if keyed_params.key?(:'cosd.version') && keyed_params[:'cosd.version'] == 'last'
      # Do query for last version -> get_cosd_ns_vendor_last_version
      keyed_params.delete(:'cosd.version')

      coss = Cosd.where((keyed_params)).sort({ 'cosd.version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: COSDs=#{coss}"

      if coss && coss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/complex-services?#{query_string} with #{coss}"

        coss_list = []
        checked_list = []

        coss_name_vendor = Pair.new(coss.first.cosd['name'], coss.first.cosd['vendor'])
        checked_list.push(coss_name_vendor)
        coss_list.push(coss.first)

        coss.each do |cosd|
          if (cosd.cosd['name'] != coss_name_vendor.one) || (cosd.cosd['vendor'] != coss_name_vendor.two)
            coss_name_vendor = Pair.new(cosd.cosd['name'], cosd.cosd['vendor'])
          end
          coss_list.push(cosd) unless checked_list.any? { |pair| pair.one == coss_name_vendor.one &&
              pair.two == coss_name_vendor.two }
          checked_list.push(coss_name_vendor)
        end
      else
        logger.info "Catalogue: leaving GET /api/v2/complex-services?#{query_string} with 'No COSDs were found'"
        coss_list = []
      end
      coss = apply_limit_and_offset(coss_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      coss = Cosd.where(keyed_params)
      # Set total count for results
      headers 'Record-Count' => coss.count.to_s
      logger.info "Catalogue: COSDs=#{coss}"
      if coss && coss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/complex-services?#{query_string} with #{coss}"
        # Paginate results
        coss = coss.paginate(offset: params[:offset], limit: params[:limit])
      else
        logger.info "Catalogue: leaving GET /api/v2/complex-services?#{query_string} with 'No COSDs were found'"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = coss.to_json
      when 'application/x-yaml'
        response = json_to_yaml(coss.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method get_ns_sp_ns_id
  # @overload get '/catalogues/complex-services/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] unique identifier
  # Show a NS by internal ID (uuid)
  get '/complex-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /api/v2/complex-services/#{params[:id]}"

      begin
        cos = Cosd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The COS ID #{params[:id]} does not exist" unless cos
      end
      logger.debug "Catalogue: leaving GET /api/v2/complex-services/#{params[:id]}\" with COSD #{cos}"

      response = ''
      case request.content_type
        when 'application/json'
          response = cos.to_json
        when 'application/x-yaml'
          response = json_to_yaml(cos.to_json)
        else
          halt 415
      end
      halt 200, {'Content-type' => request.content_type}, response

    end
    logger.debug "Catalogue: leaving GET /api/v2/complex-services/#{params[:id]} with 'No COSD ID specified'"
    json_error 400, 'No COSD ID specified'
  end

  # @method post_nss
  # @overload post '/catalogues/complex-services'
  # Post a NS in JSON or YAML format
  post '/complex-services' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a COSD, the json object sent to API must contain just data inside
        # of the COSD, without the json field cosd: before
        cos, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_cos_json = yaml_to_json(cos)

        # Validate JSON format
        new_cos, errors = parse_json(new_cos_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_cos, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Validate COS
    json_error 400, 'ERROR: COS Vendor not found' unless new_cos.has_key?('vendor')
    json_error 400, 'ERROR: COS Name not found' unless new_cos.has_key?('name')
    json_error 400, 'ERROR: COS Version not found' unless new_cos.has_key?('version')

    # Check if COS already exists in the catalogue by name, vendor and version
    begin
      cos = Cosd.find_by({ 'cosd.name' => new_cos['name'], 'cosd.vendor' => new_cos['vendor'],
                         'cosd.version' => new_cos['version'] })
      json_return 200, 'Duplicated COS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end
    # Check if COSD has an ID (it should not) and if it already exists in the catalogue
    begin
      cos = Cosd.find_by({ '_id' => new_cos['_id'] })
      json_return 200, 'Duplicated COS ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Save to DB
    begin
      new_cosd = {}
      new_cosd['cosd'] = new_cos
      # Generate the UUID for the descriptor
      new_cosd['_id'] = SecureRandom.uuid
      new_cosd['status'] = 'active'
      # Signature will be supported
      new_cosd['signature'] = nil
      new_cosd['md5'] = checksum new_cos.to_s
      new_cosd['username'] = username
      cos = Cosd.create!(new_cosd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated COS ID' if e.message.include? 'E11000'
    end

    puts 'New COS has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = cos.to_json
      when 'application/x-yaml'
        response = json_to_yaml(cos.to_json)
      else
        halt 415
    end
    halt 201, {'Content-type' => request.content_type}, response
  end

  # @method update_nss
  # @overload put '/catalogues/complex-services/?'
  # Update a NS by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/complex-services/?' do
    logger.info "Catalogue: entered PUT /api/v2/complex-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Return 400 if params are empty
    json_error 400, 'Update parameters are null' if keyed_params.empty?

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a COSD, the json object sent to API must contain just data inside
        # of the COSD, without the json field cosd: before
        cos, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_cos_json = yaml_to_json(cos)

        # Validate JSON format
        new_cos, errors = parse_json(new_cos_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_cos, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate NS
    # Check if mandatory fields Vendor, Name, Version are included
    json_error 400, 'ERROR: COS Vendor not found' unless new_cos.has_key?('vendor')
    json_error 400, 'ERROR: COS Name not found' unless new_cos.has_key?('name')
    json_error 400, 'ERROR: COS Version not found' unless new_cos.has_key?('version')

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Retrieve stored version
    if keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      json_error 400, 'Update Vendor, Name and Version parameters are null'
    else
      begin
        cos = Cosd.find_by({ 'cosd.vendor' => keyed_params[:vendor], 'cosd.name' => keyed_params[:name],
                           'cosd.version' => keyed_params[:version] })
        puts 'COS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The COSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if COS already exists in the catalogue by Name, Vendor and Version
    begin
      cos = Cosd.find_by({ 'cosd.name' => new_cos['name'], 'cosd.vendor' => new_cos['vendor'],
                         'cosd.version' => new_cos['version'] })
      json_return 200, 'Duplicated COS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Update to new version
    puts 'Updating...'
    new_cosd = {}
    new_cosd['_id'] = SecureRandom.uuid # Unique UUIDs per COSD entries
    new_cosd['cosd'] = new_cos
    new_cosd['status'] = 'active'
    new_cosd['signature'] = nil
    new_cosd['md5'] = checksum new_cos.to_s
    new_cosd['username'] = username

    begin
      new_cos = Cosd.create!(new_cosd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated COS ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /api/v2/complex-services?#{query_string}\" with COSD #{new_cos}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_cos.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_cos.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method update_nss_id
  # @overload put '/catalogues/complex-services/:id/?'
  # Update a NS in JSON or YAML format
  ## Catalogue - UPDATE
  put '/complex-services/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /api/v2/complex-services/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)

      # Check for special case (:status param == <new_status>)
      if keyed_params.key?(:status)
        # Do update of Descriptor status -> update_ns_status
        logger.info "Catalogue: entered PUT /api/v2/complex-services/#{query_string}"

        # Validate NS
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          cos = Cosd.find_by({ '_id' => params[:id] })
          puts 'COS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This COSD does not exists'
        end

        # Validate new status
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            cos.update_attributes(status: keyed_params[:status])
          rescue Moped::Errors::OperationFailure => e
            json_error 400, 'ERROR: Operation failed'
          end
        else
          json_error 400, "Invalid new status #{keyed_params[:status]}"
        end
        halt 200, "Status updated to {#{query_string}}"

      else
        # Compatibility support for YAML content-type
        case request.content_type
          when 'application/x-yaml'
            # Validate YAML format
            # When updating a COSD, the json object sent to API must contain just data inside
            # of the COSD, without the json field cosd: before
            cos, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_cos_json = yaml_to_json(cos)

            # Validate JSON format
            new_cos, errors = parse_json(new_cos_json)
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_cos, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate COS
        # Check if mandatory fields Vendor, Name, Version are included
        json_error 400, 'ERROR: COS Vendor not found' unless new_cos.has_key?('vendor')
        json_error 400, 'ERROR: COS Name not found' unless new_cos.has_key?('name')
        json_error 400, 'ERROR: COS Version not found' unless new_cos.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          cos = Cosd.find_by({ '_id' => params[:id] })
          puts 'COS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The COSD ID #{params[:id]} does not exist"
        end

        # Check if COS already exists in the catalogue by name, vendor and version
        begin
          cos = Cosd.find_by({ 'cosd.name' => new_cos['name'], 'cosd.vendor' => new_cos['vendor'],
                             'cosd.version' => new_cos['version'] })
          json_return 200, 'Duplicated COS Name, Vendor and Version'
        rescue Mongoid::Errors::DocumentNotFound => e
          # Continue
        end

        if keyed_params.key?(:username)
          username = keyed_params[:username]
        else
          username = nil
        end

        # Update to new version
        puts 'Updating...'
        new_cosd = {}
        new_cosd['_id'] = SecureRandom.uuid # Unique UUIDs per COSD entries
        new_cosd['cosd'] = new_cos
        new_cosd['status'] = 'active'
        new_cosd['signature'] = nil
        new_cosd['md5'] = checksum new_cos.to_s
        new_cosd['username'] = username

        begin
          new_cos = Cosd.create!(new_cosd)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated COS ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /api/v2/complex-services/#{params[:id]}\" with COSD #{new_cos}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_cos.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_cos.to_json)
          else
            halt 415
        end
        halt 200, {'Content-type' => request.content_type}, response
      end
    end
    logger.debug "Catalogue: leaving PUT /api/v2/complex-services/#{params[:id]} with 'No COSD ID specified'"
    json_error 400, 'No COSD ID specified'
  end

  # @method delete_cosd_sp_ns
  # @overload delete '/complex-services/?'
  #	Delete a COS by vendor, name and version
  delete '/complex-services/?' do
    logger.info "Catalogue: entered DELETE /api/v2/complex-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        cos = Cosd.find_by({ 'cosd.vendor' => keyed_params[:vendor], 'cosd.name' => keyed_params[:name],
                           'cosd.version' => keyed_params[:version]} )
        puts 'COS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The COSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/complex-services?#{query_string}\" with COSD #{cos}"
      cos.destroy
      halt 200, 'OK: COSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/complex-services?#{query_string} with 'No COSD Vendor, Name, Version specified'"
    json_error 400, 'No COSD Vendor, Name, Version specified'
  end

  # @method delete_cosd_sp_ns_id
  # @overload delete '/catalogues/network-service/:id/?'
  #	  Delete a NS by its ID
  #	  @param :id [Symbol] unique identifier
  # Delete a NS by uuid
  delete '/complex-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /api/v2/complex-services/#{params[:id]}"
      begin
        cos = Cosd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The COSD ID #{params[:id]} does not exist" unless cos
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/complex-services/#{params[:id]}\" with COSD #{cos}"
      cos.destroy
      halt 200, 'OK: COSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/complex-services/#{params[:id]} with 'No COSD ID specified'"
    json_error 400, 'No COSD ID specified'
  end
end
