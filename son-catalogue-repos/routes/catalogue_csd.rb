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

class CatalogueV2 < SonataCatalogue
  ### CSD API METHODS ###

  # @method get_csds
  # @overload get '/catalogues/csds/?'
  #	Returns a list of CSDs
  # -> List many descriptors
  get '/csds/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    logger.info "Catalogue: entered GET /api/v2/csds?#{query_string}"

    # Split keys in meta_data and data
    # Then transform 'string' params Hash into keys
    keyed_params = add_descriptor_level('csd', params)

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
    if keyed_params.key?(:'csd.version') && keyed_params[:'csd.version'] == 'last'
      keyed_params.delete(:'csd.version')

      csds = Clsd.where((keyed_params)).sort({ 'csd.version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: CSDs=#{csds}"

      if csds && csds.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/csds?#{query_string} with #{csds}"

        csds_list = []
        checked_list = []

        csds_name_vendor = Pair.new(csds.first.csd['name'], csds.first.csd['vendor'])
        checked_list.push(csds_name_vendor)
        csds_list.push(csds.first)

        csds.each do |csd|
          if (csd.csd['name'] != csds_name_vendor.one) || (csd.csd['vendor'] != csds_name_vendor.two)
            csds_name_vendor = Pair.new(csd.csd['name'], csd.csd['vendor'])
          end
          csds_list.push(csd) unless checked_list.any? { |pair| pair.one == csds_name_vendor.one &&
              pair.two == csds_name_vendor.two }
          checked_list.push(csds_name_vendor)
        end
      else
        logger.info "Catalogue: leaving GET /api/v2/csds?#{query_string} with 'No CSDs were found'"
        csds_list = []

      end
      csds = apply_limit_and_offset(csds_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      csds = Clsd.where(keyed_params)
      # Set total count for results
      headers 'Record-Count' => csds.count.to_s
      logger.info "Catalogue: CSDs=#{csds}"
      if csds && csds.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/csds?#{query_string} with #{csds}"
        # Paginate results
        csds = csds.paginate(offset: params[:offset], limit: params[:limit])
      else
        logger.info "Catalogue: leaving GET /api/v2/csds?#{query_string} with 'No CSDs were found'"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = csds.to_json
      when 'application/x-yaml'
        response = json_to_yaml(csds.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method get_csds_id
  # @overload get '/catalogues/csds/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] id CSD ID
  # Show a CSD by internal ID (uuid)
  get '/csds/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /api/v2/csds/#{params[:id]}"

      begin
        csd = Clsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The CSD ID #{params[:id]} does not exist" unless csd
      end
      logger.debug "Catalogue: leaving GET /api/v2/csds/#{params[:id]}\" with CSD #{csd}"

      response = ''
      case request.content_type
        when 'application/json'
          response = csd.to_json
        when 'application/x-yaml'
          response = json_to_yaml(csd.to_json)
        else
          halt 415
      end
      halt 200, {'Content-type' => request.content_type}, response

    end
    logger.debug "Catalogue: leaving GET /api/v2/csds/#{params[:id]} with 'No CSD ID specified'"
    json_error 400, 'No CSD ID specified'
  end

  # @method post_csds
  # @overload post '/catalogues/csds'
  # Post a CSD in JSON or YAML format
  post '/csds' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a CSD, the json object sent to API must contain just data inside
        # of the csd, without the json field csd: before
        cs, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_cs_json = yaml_to_json(cs)

        # Validate JSON format
        new_cs, errors = parse_json(new_cs_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_cs, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Validate CSD
    json_error 400, 'ERROR: CSD Vendor not found' unless new_cs.has_key?('vendor')
    json_error 400, 'ERROR: CSD Name not found' unless new_cs.has_key?('name')
    json_error 400, 'ERROR: CSD Version not found' unless new_cs.has_key?('version')

    # Check if CSD already exists in the catalogue by name, vendor and version
    begin
      cs = Clsd.find_by({ 'csd.name' => new_cs['name'], 'csd.vendor' => new_cs['vendor'],
                           'csd.version' => new_cs['version'] })
      json_return 200, 'Duplicated CSD Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Check if CSD has an ID (it should not) and if it already exists in the catalogue
    begin
      cs = Clsd.find_by({ '_id' => new_cs['_id'] })
      json_return 200, 'Duplicated CSD ID'
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
      new_csd = {}
      new_csd['csd'] = new_cs
      # Generate the UUID for the descriptor
      new_csd['_id'] = SecureRandom.uuid
      new_csd['status'] = 'active'
      new_csd['signature'] = nil
      new_csd['md5'] = checksum new_cs.to_s
      new_csd['username'] = username
      cs = Clsd.create!(new_csd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated CSD ID' if e.message.include? 'E11000'
    end

    puts 'New CSD has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = cs.to_json
      when 'application/x-yaml'
        response = json_to_yaml(cs.to_json)
      else
        halt 415
    end
    halt 201, {'Content-type' => request.content_type}, response
  end

  # @method update_csds
  # @overload put '/csds/?'
  # Update a CSD by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/csds/?' do
    logger.info "Catalogue: entered PUT /api/v2/csds?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Return if params are empty
    json_error 400, 'Update parameters are null' if keyed_params.empty?

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a CSD, the json object sent to API must contain just data inside
        # of the csd, without the json field csd: before
        cs, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_cs_json = yaml_to_json(cs)

        # Validate JSON format
        new_cs, errors = parse_json(new_cs_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_cs, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate CSD
    # Check if mandatory fields Vendor, Name, Version are included
    json_error 400, 'ERROR: CSD Vendor not found' unless new_cs.has_key?('vendor')
    json_error 400, 'ERROR: CSD Name not found' unless new_cs.has_key?('name')
    json_error 400, 'ERROR: CSD Version not found' unless new_cs.has_key?('version')

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
        cs = Clsd.find_by({ 'csd.vendor' => keyed_params[:vendor], 'csd.name' => keyed_params[:name],
                             'csd.version' => keyed_params[:version] })
        puts 'CS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The CSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if CS already exists in the catalogue by Name, Vendor and Version
    begin
      cs = Clsd.find_by({ 'csd.name' => new_cs['name'], 'csd.vendor' => new_cs['vendor'],
                           'csd.version' => new_cs['version'] })
      json_return 200, 'Duplicated CSD Name, Vendor and Version'
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
    new_csd = {}
    new_csd['_id'] = SecureRandom.uuid # Unique UUIDs per CSD entries
    new_csd['csd'] = new_cs
    new_csd['status'] = 'active'
    new_csd['signature'] = nil
    new_csd['md5'] = checksum new_cs.to_s
    new_csd['username'] = username

    begin
      new_cs = Cls.create!(new_csd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated CSD ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /api/v2/csds?#{query_string}\" with CSD #{new_cs}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_cs.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_cs.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method update_csds_id
  # @overload put '/catalogues/csds/:id/?'
  #	Update a CSD by its ID in JSON or YAML format
  ## Catalogue - UPDATE
  put '/csds/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /api/v2/csds/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)

      # Check for special case (:status param == <new_status>)
      if keyed_params.key?(:status)
        logger.info "Catalogue: entered PUT /api/v2/csds/#{query_string}"

        # Validate CSD
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          cs = Clsd.find_by({ '_id' => params[:id] })
          puts 'CSD is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This CSD does not exists'
        end

        #Validate new status
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            cs.update_attributes(status: keyed_params[:status])
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
            # When updating a CSD, the json object sent to API must contain just data inside
            # of the csd, without the json field csd: before
            cs, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_cs_json = yaml_to_json(cs)

            # Validate JSON format
            new_cs, errors = parse_json(new_cs_json)
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_cs, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate CSD
        # Check if mandatory fields Vendor, Name, Version are included
        json_error 400, 'ERROR: CSD Vendor not found' unless new_cs.has_key?('vendor')
        json_error 400, 'ERROR: CSD Name not found' unless new_cs.has_key?('name')
        json_error 400, 'ERROR: CSD Version not found' unless new_cs.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          cs = Clsd.find_by({ '_id' => params[:id] })
          puts 'CSD is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The CSD ID #{params[:id]} does not exist"
        end

        # Check if CSD already exists in the catalogue by name, vendor and version
        begin
          cs = Clsd.find_by({ 'csd.name' => new_cs['name'], 'csd.vendor' => new_cs['vendor'],
                               'csd.version' => new_cs['version'] })
          json_return 200, 'Duplicated CS Name, Vendor and Version'
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
        new_csd = {}
        new_csd['_id'] = SecureRandom.uuid # Unique UUIDs per CSD entries
        new_csd['csd'] = new_cs
        new_csd['status'] = 'active'
        new_csd['signature'] = nil
        new_csd['md5'] = checksum new_cs.to_s
        new_csd['username'] = username

        begin
          new_cs = Clsd.create!(new_csd)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated CSD ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /api/v2/csds/#{params[:id]}\" with CSD #{new_cs}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_cs.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_cs.to_json)
          else
            halt 415
        end
        halt 200, {'Content-type' => request.content_type}, response
      end
    end
    logger.debug "Catalogue: leaving PUT /api/v2/csds/#{params[:id]} with 'No CSD ID specified'"
    json_error 400, 'No CSD ID specified'
  end

  # @method delete_csds_sp_cs
  # @overload delete '/csds/?'
  #	Delete a CSD by vendor, name and version
  delete '/csds/?' do
    logger.info "Catalogue: entered DELETE /api/v2/csds?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        cs = Clsd.find_by({ 'csd.vendor' => keyed_params[:vendor], 'csd.name' => keyed_params[:name],
                             'csd.version' => keyed_params[:version] })
        puts 'CSD is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The CSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/csds?#{query_string}\" with CSD #{cs}"
      cs.destroy
      halt 200, 'OK: CSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/csds?#{query_string} with 'No CSD Vendor, Name, Version specified'"
    json_error 400, 'No CSD Vendor, Name, Version specified'
  end

  # @method delete_csds_sp_cs_id
  # @overload delete '/catalogues/csds/:id/?'
  #	  Delete a CSD by its ID
  #	  @param :id [Symbol] id CSD ID
  # Delete a CSD by uuid
  delete '/csds/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /api/v2/csds/#{params[:id]}"
      begin
        cs = Clsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The CSD ID #{params[:id]} does not exist" unless cs
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/csds/#{params[:id]}\" with CSD #{cs}"
      cs.destroy
      halt 200, 'OK: CSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/csds/#{params[:id]} with 'No CSD ID specified'"
    json_error 400, 'No CSD ID specified'
  end
end