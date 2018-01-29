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
class CatalogueV1 < SonataCatalogue
  # require 'addressable/uri'

  ### NSD API METHODS ###

  # @method get_nssSS
  # @overload get '/catalogues/network-services/?'
  #	Returns a list of NSs
  # -> List many descriptors
  get '/network-services/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT

    #uri = Addressable::URI.new
    #uri.query_values = params
    # puts 'params', params
    # puts 'query_values', uri.query_values
    #logger.info "Catalogue: entered GET /network-services?#{uri.query}"
    logger.info "Catalogue: entered GET /network-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)
    #puts 'keyed_params', keyed_params

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
    # puts 'keyed_params(1)', keyed_params

    # Check for special case (:version param == last)
    if keyed_params.key?(:version) && keyed_params[:version] == 'last'
      # Do query for last version -> get_nsd_ns_vendor_last_version

      keyed_params.delete(:version)
      # puts 'keyed_params(2)', keyed_params

      nss = Ns.where((keyed_params)).sort({ 'version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: NSDs=#{nss}"
      # nss = nss.sort({"version" => -1})
      # puts 'nss: ', nss.to_json

      if nss && nss.size.to_i > 0
        logger.info "Catalogue: leaving GET /network-services?#{query_string} with #{nss}"

        # Paginate results
        # nss = nss.paginate(:offset => params[:offset], :limit => params[:limit]).sort({"version" => -1})

        nss_list = []
        checked_list = []

        nss_name_vendor = Pair.new(nss.first.name, nss.first.vendor)
        # p 'nss_name_vendor:', [nss_name_vendor.one, nss_name_vendor.two]
        checked_list.push(nss_name_vendor)
        nss_list.push(nss.first)

        nss.each do |nsd|
          # p 'Comparison: ', [nsd.name, nsd.vendor].to_s + [nss_name_vendor.one, nss_name_vendor.two].to_s
          if (nsd.name != nss_name_vendor.one) || (nsd.vendor != nss_name_vendor.two)
            nss_name_vendor = Pair.new(nsd.name, nsd.vendor)
            # p 'nss_name_vendor(x):', [nss_name_vendor.one, nss_name_vendor.two]
            # checked_list.each do |pair|
            #  p [pair.one, nss_name_vendor.one], [pair.two, nss_name_vendor.two]
            #  p pair.one == nss_name_vendor.one && pair.two == nss_name_vendor.two
          end
          nss_list.push(nsd) unless checked_list.any? { |pair| pair.one == nss_name_vendor.one &&
              pair.two == nss_name_vendor.two }
          checked_list.push(nss_name_vendor)
        end
        # puts 'nss_list:', nss_list.each {|ns| p ns.name, ns.vendor}
      else
        # logger.error "ERROR: 'No NSDs were found'"
        logger.info "Catalogue: leaving GET /network-services?#{query_string} with 'No NSDs were found'"
        # json_error 404, "No NSDs were found"
        nss_list = []
      end
      # nss = nss_list.paginate(:page => params[:offset], :per_page =>params[:limit])
      nss = apply_limit_and_offset(nss_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      nss = Ns.where(keyed_params)
      logger.info "Catalogue: NSDs=#{nss}"
      # puts nss.to_json
      if nss && nss.size.to_i > 0
        #logger.info "Catalogue: leaving GET /network-services?#{uri.query} with #{nss}"
        logger.info "Catalogue: leaving GET /network-services?#{query_string} with #{nss}"

        # Paginate results
        nss = nss.paginate(offset: params[:offset], limit: params[:limit])

      else
        #logger.info "Catalogue: leaving GET /network-services?#{uri.query} with 'No NSDs were found'"
        logger.info "Catalogue: leaving GET /network-services?#{query_string} with 'No NSDs were found'"
        # json_error 404, "No NSDs were found"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = nss.to_json
      when 'application/x-yaml'
        response = json_to_yaml(nss.to_json)
      else
        halt 415
    end
    halt 200, response
  end

  # @method get_ns_sp_ns_id
  # @overload get '/catalogues/network-services/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] unique identifier
  # Show a NS by internal ID (uuid)
  get '/network-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /network-services/#{params[:id]}"

      begin
        ns = Ns.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The NSD ID #{params[:id]} does not exist" unless ns
      end
      logger.debug "Catalogue: leaving GET /network-services/#{params[:id]}\" with NSD #{ns}"

      response = ''
      case request.content_type
        when 'application/json'
          response = ns.to_json
        when 'application/x-yaml'
          response = json_to_yaml(ns.to_json)
        else
          halt 415
      end
      halt 200, response

    end
    logger.debug "Catalogue: leaving GET /network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end

  # @method post_nss
  # @overload post '/catalogues/network-services'
  # Post a NS in JSON or YAML format
  post '/network-services' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a NSD, the json object sent to API must contain just data inside
        # of the nsd, without the json field nsd: before
        ns, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_ns_json = yaml_to_json(ns)

        # Validate JSON format
        new_ns, errors = parse_json(new_ns_json)
        # puts 'ns: ', new_ns.to_json
        # puts 'new_ns id', new_ns['_id'].to_json
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_ns, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate NS
    json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
    json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
    json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

    # --> Validation disabled
    # Validate NSD
    # begin
    #   postcurb settings.nsd_validator + '/nsds', ns.to_json, :content_type => :json
    # rescue => e
    #   halt 500, {'Content-Type' => 'text/plain'}, "Validator mS unreachable."
    # end

    # Check if NS already exists in the catalogue by name, vendor and version
    begin
      ns = Ns.find_by({ 'name' => new_ns['name'], 'vendor' => new_ns['vendor'], 'version' => new_ns['version'] })
      json_return 200, 'Duplicated NS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end
    # Check if NSD has an ID (it should not) and if it already exists in the catalogue
    begin
      ns = Ns.find_by({ '_id' => new_ns['_id'] })
      json_return 200, 'Duplicated NS ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Save to DB
    begin
      new_nsd = {}
      # Generate the UUID for the descriptor
      # new_nsd['nsd'] = new_ns
      new_nsd = new_ns
      new_nsd['_id'] = SecureRandom.uuid
      new_nsd['status'] = 'active'
      new_nsd['signature'] = 'null'
      ns = Ns.create!(new_nsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
    end

    puts 'New NS has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = ns.to_json
      when 'application/x-yaml'
        response = json_to_yaml(ns.to_json)
      else
        halt 415
    end
    halt 201, response
  end

  # @method update_nss
  # @overload put '/catalogues/network-services/?'
  # Update a NS by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/network-services/?' do
    # uri = Addressable::URI.new
    # uri.query_values = params
    # puts 'params', params
    # puts 'query_values', uri.query_values
    logger.info "Catalogue: entered PUT /network-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)
    # puts 'keyed_params', keyed_params

    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Return 400 if params are empty
    json_error 400, 'Update parameters are null' if keyed_params.empty?

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a NSD, the json object sent to API must contain just data inside
        # of the nsd, without the json field nsd: before
        ns, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_ns_json = yaml_to_json(ns)

        # Validate JSON format
        new_ns, errors = parse_json(new_ns_json)
        # puts 'ns: ', new_ns.to_json
        # puts 'new_ns id', new_ns['_id'].to_json
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_ns, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate NS
    # Check if same vendor, Name, Version do already exists in the database
    json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
    json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
    json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

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
        ns = Ns.find_by({ 'vendor' => keyed_params[:vendor], 'name' => keyed_params[:name],
                          'version' => keyed_params[:version] })
        puts 'NS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The NSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if NS already exists in the catalogue by name, group and version
    begin
      ns = Ns.find_by({ 'name' => new_ns['name'], 'vendor' => new_ns['vendor'], 'version' => new_ns['version'] })
      json_return 200, 'Duplicated NS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Update to new version
    puts 'Updating...'
    new_ns['_id'] = SecureRandom.uuid # Unique UUIDs per NSD entries
    nsd = new_ns

    # --> Validation disabled
    # Validate NSD
    # begin
    #	  postcurb settings.nsd_validator + '/nsds', nsd.to_json, :content_type => :json
    # rescue => e
    #	  logger.error e.response
    #	return e.response.code, e.response.body
    # end

    begin
      new_ns = Ns.create!(nsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /network-services?#{query_string}\" with NSD #{new_ns}"

    begin
      new_ns = Ns.create!(new_nsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /network-services?#{query_string}\" with NSD #{new_ns}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_ns.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_ns.to_json)
      else
        halt 415
    end
    halt 200, response
  end

  # @method update_nss_id
  # @overload put '/catalogues/network-services/:id/?'
  # Update a NS in JSON or YAML format
  ## Catalogue - UPDATE
  put '/network-services/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /network-services/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)
      # puts 'keyed_params', keyed_params

      # Check for special case (:status param == <new_status>)
      p 'Special case detected= new_status'
      if keyed_params.key?(:status)
        p 'Detected key :status'
        # Do update of Descriptor status -> update_ns_status
        # uri = Addressable::URI.new
        # uri.query_values = params
        logger.info "Catalogue: entered PUT /network-services/#{query_string}"

        # Validate NS
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          ns = Ns.find_by({ '_id' => params[:id] })
          puts 'NS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This NSD does not exists'
        end

        # Validate new status
        p 'Validating new status(keyed_params): ', keyed_params[:status]
        # p "Validating new status(params): ", params[:new_status]
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            # ns.update_attributes(:status => params[:new_status])
            ns.update_attributes(status: keyed_params[:status])
          rescue Moped::Errors::OperationFailure => e
            json_error 400, 'ERROR: Operation failed'
          end
        else
          json_error 400, "Invalid new status #{keyed_params[:status]}"
        end

        # --> Validation disabled
        # Validate NSD
        # begin
        #	  postcurb settings.nsd_validator + '/nsds', nsd.to_json, :content_type => :json
        # rescue => e
        #	  logger.error e.response
        #	  return e.response.code, e.response.body
        # end

        halt 200, "Status updated to {#{query_string}}"

      else
        # Compatibility support for YAML content-type
        case request.content_type
          when 'application/x-yaml'
            # Validate YAML format
            # When updating a NSD, the json object sent to API must contain just data inside
            # of the nsd, without the json field nsd: before
            ns, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_ns_json = yaml_to_json(ns)

            # Validate JSON format
            new_ns, errors = parse_json(new_ns_json)
            # puts 'ns: ', new_ns.to_json
            # puts 'new_ns id', new_ns['_id'].to_json
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_ns, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate NS
        # Check if same vendor, Name, Version do already exists in the database
        json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
        json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
        json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          ns = Ns.find_by({ '_id' => params[:id] })
          puts 'NS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The NSD ID #{params[:id]} does not exist"
        end

        # Check if NS already exists in the catalogue by name, vendor and version
        begin
          ns = Ns.find_by({ 'name' => new_ns['name'], 'vendor' => new_ns['vendor'], 'version' => new_ns['version'] })
          json_return 200, 'Duplicated NS Name, Vendor and Version'
        rescue Mongoid::Errors::DocumentNotFound => e
          # Continue
        end

        # Update to new version
        puts 'Updating...'
        new_ns['_id'] = SecureRandom.uuid
        nsd = new_ns

        # --> Validation disabled
        # Validate NSD
        # begin
        #	  postcurb settings.nsd_validator + '/nsds', nsd.to_json, :content_type => :json
        # rescue => e
        #	  logger.error e.response
        #	  return e.response.code, e.response.body
        # end

        begin
          new_ns = Ns.create!(nsd)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /network-services/#{params[:id]}\" with NSD #{new_ns}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_ns.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_ns.to_json)
          else
            halt 415
        end
        halt 200, response
      end
    end
    logger.debug "Catalogue: leaving PUT /network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end

  # @method delete_nsd_sp_ns
  # @overload delete '/network-services/?'
  #	Delete a NS by vendor, name and version
  delete '/network-services/?' do
    # uri = Addressable::URI.new
    # uri.query_values = params
    # puts 'params', params
    # puts 'query_values', uri.query_values
    logger.info "Catalogue: entered DELETE /network-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)
    # puts 'keyed_params', keyed_params

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        ns = Ns.find_by({ 'vendor' => keyed_params[:vendor], 'name' => keyed_params[:name],
                          'version' => keyed_params[:version]} )
        puts 'NS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The NSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /network-services?#{query_string}\" with NSD #{ns}"
      ns.destroy
      halt 200, 'OK: NSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /network-services?#{query_string} with 'No NSD Vendor, Name, Version specified'"
    json_error 400, 'No NSD Vendor, Name, Version specified'
  end

  # @method delete_nsd_sp_ns_id
  # @overload delete '/catalogues/network-service/:id/?'
  #	  Delete a NS by its ID
  #	  @param :id [Symbol] unique identifier
  # Delete a NS by uuid
  delete '/network-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /network-services/#{params[:id]}"
      begin
        ns = Ns.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The NSD ID #{params[:id]} does not exist" unless ns
      end
      logger.debug "Catalogue: leaving DELETE /network-services/#{params[:id]}\" with NSD #{ns}"
      ns.destroy
      halt 200, 'OK: NSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end
end

class CatalogueV2 < SonataCatalogue
  ### NSD API METHODS ###

  # @method get_nssSS
  # @overload get '/catalogues/network-services/?'
  #	Returns a list of NSs
  # -> List many descriptors
  get '/network-services/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    logger.info "Catalogue: entered GET /api/v2/network-services?#{query_string}"

    # Split keys in meta_data and data
    # Then transform 'string' params Hash into keys
    keyed_params = add_descriptor_level('nsd', params)

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
    if keyed_params.key?(:'nsd.version') && keyed_params[:'nsd.version'] == 'last'
      # Do query for last version -> get_nsd_ns_vendor_last_version
      keyed_params.delete(:'nsd.version')

      nss = Nsd.where((keyed_params)).sort({ 'nsd.version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: NSDs=#{nss}"
      # nss = nss.sort({"version" => -1})

      if nss && nss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/network-services?#{query_string} with #{nss}"

        nss_list = []
        checked_list = []

        # nss_name_vendor = Pair.new(nss.first.name, nss.first.vendor)
        nss_name_vendor = Pair.new(nss.first.nsd['name'], nss.first.nsd['vendor'])
        checked_list.push(nss_name_vendor)
        nss_list.push(nss.first)

        nss.each do |nsd|
          # if (nsd.name != nss_name_vendor.one) || (nsd.vendor != nss_name_vendor.two)
          if (nsd.nsd['name'] != nss_name_vendor.one) || (nsd.nsd['vendor'] != nss_name_vendor.two)
            # nss_name_vendor = Pair.new(nsd.name, nsd.vendor)
            nss_name_vendor = Pair.new(nsd.nsd['name'], nsd.nsd['vendor'])
            # checked_list.each do |pair|
          end
          nss_list.push(nsd) unless checked_list.any? { |pair| pair.one == nss_name_vendor.one &&
              pair.two == nss_name_vendor.two }
          checked_list.push(nss_name_vendor)
        end
      else
        logger.info "Catalogue: leaving GET /api/v2/network-services?#{query_string} with 'No NSDs were found'"
        nss_list = []
      end
      nss = apply_limit_and_offset(nss_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      nss = Nsd.where(keyed_params)
      # Set total count for results
      headers 'Record-Count' => nss.count.to_s
      logger.info "Catalogue: NSDs=#{nss}"
      if nss && nss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/network-services?#{query_string} with #{nss}"
        # Paginate results
        nss = nss.paginate(offset: params[:offset], limit: params[:limit])
      else
        logger.info "Catalogue: leaving GET /api/v2/network-services?#{query_string} with 'No NSDs were found'"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = nss.to_json
      when 'application/x-yaml'
        response = json_to_yaml(nss.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method get_ns_sp_ns_id
  # @overload get '/catalogues/network-services/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] unique identifier
  # Show a NS by internal ID (uuid)
  get '/network-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /api/v2/network-services/#{params[:id]}"

      begin
        ns = Nsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The NSD ID #{params[:id]} does not exist" unless ns
      end
      logger.debug "Catalogue: leaving GET /api/v2/network-services/#{params[:id]}\" with NSD #{ns}"

      response = ''
      case request.content_type
        when 'application/json'
          response = ns.to_json
        when 'application/x-yaml'
          response = json_to_yaml(ns.to_json)
        else
          halt 415
      end
      halt 200, {'Content-type' => request.content_type}, response

    end
    logger.debug "Catalogue: leaving GET /api/v2/network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end

  # @method post_nss
  # @overload post '/catalogues/network-services'
  # Post a NS in JSON or YAML format
  post '/network-services' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a NSD, the json object sent to API must contain just data inside
        # of the nsd, without the json field nsd: before
        ns, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_ns_json = yaml_to_json(ns)

        # Validate JSON format
        new_ns, errors = parse_json(new_ns_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_ns, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Validate NS
    json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
    json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
    json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

    # Check if NS already exists in the catalogue by name, vendor and version
    begin
      ns = Nsd.find_by({ 'nsd.name' => new_ns['name'], 'nsd.vendor' => new_ns['vendor'],
                         'nsd.version' => new_ns['version'] })
      json_return 200, 'Duplicated NS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end
    # Check if NSD has an ID (it should not) and if it already exists in the catalogue
    begin
      ns = Nsd.find_by({ '_id' => new_ns['_id'] })
      json_return 200, 'Duplicated NS ID'
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
      new_nsd = {}
      new_nsd['nsd'] = new_ns
      # Generate the UUID for the descriptor
      new_nsd['_id'] = SecureRandom.uuid
      new_nsd['status'] = 'active'
      # Signature will be supported
      new_nsd['signature'] = nil
      new_nsd['md5'] = checksum new_ns.to_s
      new_nsd['username'] = username
      ns = Nsd.create!(new_nsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
    end

    puts 'New NS has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = ns.to_json
      when 'application/x-yaml'
        response = json_to_yaml(ns.to_json)
      else
        halt 415
    end
    halt 201, {'Content-type' => request.content_type}, response
  end

  # @method update_nss
  # @overload put '/catalogues/network-services/?'
  # Update a NS by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/network-services/?' do
    logger.info "Catalogue: entered PUT /api/v2/network-services?#{query_string}"

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
        # When updating a NSD, the json object sent to API must contain just data inside
        # of the nsd, without the json field nsd: before
        ns, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_ns_json = yaml_to_json(ns)

        # Validate JSON format
        new_ns, errors = parse_json(new_ns_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_ns, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate NS
    # Check if mandatory fields Vendor, Name, Version are included
    json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
    json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
    json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

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
        ns = Nsd.find_by({ 'nsd.vendor' => keyed_params[:vendor], 'nsd.name' => keyed_params[:name],
                          'nsd.version' => keyed_params[:version] })
        puts 'NS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The NSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if NS already exists in the catalogue by Name, Vendor and Version
    begin
      ns = Nsd.find_by({ 'nsd.name' => new_ns['name'], 'nsd.vendor' => new_ns['vendor'],
                         'nsd.version' => new_ns['version'] })
      json_return 200, 'Duplicated NS Name, Vendor and Version'
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
    new_nsd = {}
    new_nsd['_id'] = SecureRandom.uuid # Unique UUIDs per NSD entries
    new_nsd['nsd'] = new_ns
    new_nsd['status'] = 'active'
    new_nsd['signature'] = nil
    new_nsd['md5'] = checksum new_ns.to_s
    new_nsd['username'] = username

    begin
      new_ns = Nsd.create!(new_nsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /api/v2/network-services?#{query_string}\" with NSD #{new_ns}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_ns.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_ns.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method update_nss_id
  # @overload put '/catalogues/network-services/:id/?'
  # Update a NS in JSON or YAML format
  ## Catalogue - UPDATE
  put '/network-services/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /api/v2/network-services/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)

      # Check for special case (:status param == <new_status>)
      if keyed_params.key?(:status)
        # Do update of Descriptor status -> update_ns_status
        logger.info "Catalogue: entered PUT /api/v2/network-services/#{query_string}"

        # Validate NS
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          ns = Nsd.find_by({ '_id' => params[:id] })
          puts 'NS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This NSD does not exists'
        end

        # Validate new status
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            ns.update_attributes(status: keyed_params[:status])
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
            # When updating a NSD, the json object sent to API must contain just data inside
            # of the nsd, without the json field nsd: before
            ns, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_ns_json = yaml_to_json(ns)

            # Validate JSON format
            new_ns, errors = parse_json(new_ns_json)
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_ns, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate NS
        # Check if mandatory fields Vendor, Name, Version are included
        json_error 400, 'ERROR: NS Vendor not found' unless new_ns.has_key?('vendor')
        json_error 400, 'ERROR: NS Name not found' unless new_ns.has_key?('name')
        json_error 400, 'ERROR: NS Version not found' unless new_ns.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          ns = Nsd.find_by({ '_id' => params[:id] })
          puts 'NS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The NSD ID #{params[:id]} does not exist"
        end

        # Check if NS already exists in the catalogue by name, vendor and version
        begin
          ns = Nsd.find_by({ 'nsd.name' => new_ns['name'], 'nsd.vendor' => new_ns['vendor'],
                             'nsd.version' => new_ns['version'] })
          json_return 200, 'Duplicated NS Name, Vendor and Version'
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
        new_nsd = {}
        new_nsd['_id'] = SecureRandom.uuid # Unique UUIDs per NSD entries
        new_nsd['nsd'] = new_ns
        new_nsd['status'] = 'active'
        new_nsd['signature'] = nil
        new_nsd['md5'] = checksum new_ns.to_s
        new_nsd['username'] = username

        begin
          new_ns = Nsd.create!(new_nsd)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated NS ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /api/v2/network-services/#{params[:id]}\" with NSD #{new_ns}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_ns.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_ns.to_json)
          else
            halt 415
        end
        halt 200, {'Content-type' => request.content_type}, response
      end
    end
    logger.debug "Catalogue: leaving PUT /api/v2/network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end

  # @method delete_nsd_sp_ns
  # @overload delete '/network-services/?'
  #	Delete a NS by vendor, name and version
  delete '/network-services/?' do
    logger.info "Catalogue: entered DELETE /api/v2/network-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        ns = Nsd.find_by({ 'nsd.vendor' => keyed_params[:vendor], 'nsd.name' => keyed_params[:name],
                          'nsd.version' => keyed_params[:version]} )
        puts 'NS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The NSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/network-services?#{query_string}\" with NSD #{ns}"
      ns.destroy
      halt 200, 'OK: NSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/network-services?#{query_string} with 'No NSD Vendor, Name, Version specified'"
    json_error 400, 'No NSD Vendor, Name, Version specified'
  end

  # @method delete_nsd_sp_ns_id
  # @overload delete '/catalogues/network-service/:id/?'
  #	  Delete a NS by its ID
  #	  @param :id [Symbol] unique identifier
  # Delete a NS by uuid
  delete '/network-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /api/v2/network-services/#{params[:id]}"
      begin
        ns = Nsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The NSD ID #{params[:id]} does not exist" unless ns
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/network-services/#{params[:id]}\" with NSD #{ns}"
      ns.destroy
      halt 200, 'OK: NSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/network-services/#{params[:id]} with 'No NSD ID specified'"
    json_error 400, 'No NSD ID specified'
  end
end
