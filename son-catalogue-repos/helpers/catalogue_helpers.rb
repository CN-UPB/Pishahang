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
class SonataCatalogue < Sinatra::Application
  require 'json'
  require 'yaml'
  require 'digest/md5'
  require 'jwt'
  require 'zip'
  require 'pathname'

  # Read config settings from config file
  # @return [String, Integer] the address and port of the API
  def read_config
    begin
      config = YAML.load_file('config/config.yml')
      puts config['address']
      puts config['port']
    rescue YAML::LoadError => e
      # If config file is not found or valid, return with errors
      logger.error "read config error: #{e}"
    end

    return config['address'], config['port']
  end

  # Checks if a JSON message is valid
  # @param [JSON] message some JSON message
  # @return [Hash, nil] if the parsed message is a valid JSON
  # @return [Hash, String] if the parsed message is an invalid JSON
  def parse_json(message)
    # Check JSON message format
    begin
      parsed_message = JSON.parse(message) # parse json message
    rescue JSON::ParserError => e
      # If JSON not valid, return with errors
      logger.error "JSON parsing: #{e}"
      return message, e.to_s + "\n"
    end
    return parsed_message, nil
  end

  # Checks if a YAML message is valid
  # @param [YAML] message some YAML message
  # @return [Hash, nil] if the parsed message is a valid YAML
  # @return [Hash, String] if the parsed message is an invalid YAML
  def parse_yaml(message)
    # Check YAML message format
    begin
      parsed_message = YAML.load(message) # parse YAML message
    rescue YAML::ParserError => e
      # If YAML not valid, return with errors
      logger.error "YAML parsing: #{e}"
      return message, e.to_s + "\n"
    end
    return parsed_message, nil
  end

  # Translates a message from YAML to JSON
  # @param [YAML] input_yml some YAML message
  # @return [Hash, nil] if the input message is a valid YAML
  # @return [Hash, String] if the input message is an invalid YAML
  def yaml_to_json(input_yml)
    begin
      output_json = JSON.dump(input_yml)
    rescue
      logger.error 'Error parsing from YAML to JSON'
    end
    output_json
  end

  # Translates a message from JSON to YAML
  # @param [JSON] input_json some JSON message
  # @return [Hash, nil] if the input message is a valid JSON
  # @return [Hash, String] if the input message is an invalid JSON
  def json_to_yaml(input_json)
    require 'json'
    require 'yaml'
    begin
      output_yml = YAML.dump(JSON.parse(input_json))
    rescue
      logger.error 'Error parsing from JSON to YAML'
    end
    output_yml
  end

  def apply_limit_and_offset(input, offset= nil, limit= nil)
    @result = input
    @result = offset ? input.drop(offset.to_i) : @result
    @result = limit ? @result.first(limit.to_i) : @result
  end

  # Builds an HTTP link for pagination
  # @param [Integer] offset link offset
  # @param [Integer] limit link limit position
  def build_http_link_ns(offset, limit)
    link = ''
    # Next link
    next_offset = offset + 1
    next_nss = Ns.paginate(page: next_offset, limit: limit)
    address, port = read_config
    begin
      link << '<' + address.to_s + ':' + port.to_s + '/catalogues/network-services?offset=' + next_offset.to_s +
          '&limit=' + limit.to_s + '>; rel="next"' unless next_nss.empty?
    rescue
      logger.error 'Error Establishing a Database Connection'
    end
    unless offset == 1
      # Previous link
      previous_offset = offset - 1
      previous_nss = Ns.paginate(page: previous_offset, limit: limit)
      unless previous_nss.empty?
        link << ', ' unless next_nss.empty?
        link << '<' + address.to_s + ':' + port.to_s + '/catalogues/network-services?offset=' + previous_offset.to_s +
            '&limit=' + limit.to_s + '>; rel="last"'
      end
    end
    link
  end

  # Builds an HTTP pagination link header
  # @param [Integer] offset the pagination offset requested
  # @param [Integer] limit the pagination limit requested
  # @return [String] the built link to use in header
  def build_http_link_vnf(offset, limit)
    link = ''
    # Next link
    next_offset = offset + 1
    next_vnfs = Vnf.paginate(page: next_offset, limit: limit)

    address, port = read_config

    link << '<' + address.to_s + ':' + port.to_s + '/catalogues/vnfs?offset=' + next_offset.to_s + '&limit=' +
        limit.to_s + '>; rel="next"' unless next_vnfs.empty?
    unless offset == 1
      # Previous link
      previous_offset = offset - 1
      previous_vnfs = Vnf.paginate(page: previous_offset, limit: limit)
      unless previous_vnfs.empty?
        link << ', ' unless next_vnfs.empty?
        link << '<' + address.to_s + ':' + port.to_s + '/catalogues/vnfs?offset=' + previous_offset.to_s +
            '&limit=' + limit.to_s + '>; rel="last"'
      end
    end
    link
  end

  # Extension of build_http_link
  def build_http_link_ns_name(offset, limit, name)
    link = ''
    # Next link
    next_offset = offset + 1
    next_nss = Ns.paginate(page: next_offset, limit: limit)
    address, port = read_config
    begin
      link << '<' + address.to_s + ':' + port.to_s + '/catalogues/network-services/name/' + name.to_s +
          '?offset=' + next_offset.to_s + '&limit=' + limit.to_s + '>; rel="next"' unless next_nss.empty?
    rescue
      logger.error 'Error Establishing a Database Connection'
    end

    unless offset == 1
      # Previous link
      previous_offset = offset - 1
      previous_nss = Ns.paginate(page: previous_offset, limit: limit)
      unless previous_nss.empty?
        link << ', ' unless next_nss.empty?
        link << '<' + address.to_s + ':' + port.to_s + '/catalogues/network-services/name/' + name.to_s +
            '?offset=' + previous_offset.to_s + '&limit=' + limit.to_s + '>; rel="last"'
      end
    end
    link
  end

  def checksum(contents)
    result = Digest::MD5.hexdigest contents #File.read
    result
  end

  def keyed_hash(hash)
    Hash[hash.map { |(k, v)| [k.to_sym, v] }]
  end

  def add_descriptor_level(descriptor_type, parameters)
    new_parameters = {}
    meta_data = %w(offset limit _id uuid status signature md5 updated_at created_at)
    parameters.each { |k, v|
      if meta_data.include? k
        if k == 'uuid'
          new_parameters.store( '_id', v)
        else
          new_parameters.store( k, v)
        end
      else
        new_parameters.store((descriptor_type.to_s + '.' + k), v)
      end
    }
    parameters = keyed_hash(new_parameters)
  end

  class Pair
    attr_accessor :one, :two
    def initialize(one, two)
      @one = one
      @two = two
    end
  end

  # Method that returns an error code and a message in json format
  def json_error(code, message)
    msg = {'error' => message}
    logger.error msg.to_s
    halt code, {'Content-type' => 'application/json'}, msg.to_json
  end

  # Method that returns a code and a message in json format
  def json_return(code, message)
    msg = {'OK' => message}
    logger.info msg.to_s
    halt code, {'Content-type' => 'application/json'}, msg.to_json
  end

  def getcurb(url, headers={})
    Curl.get(url) do |req|
      req.headers = headers
    end
  end

  def postcurb(url, body)
    Curl.post(url, body) do |req|
      req.headers['Content-type'] = 'application/json'
      req.headers['Accept'] = 'application/json'
    end
  end

  # Check if it's a valid dependency mapping descriptor
  # @param [Hash] desc The descriptor
  # @return [Boolean] true if descriptor contains name-vendor-version info
  def valid_dep_mapping_descriptor?(desc)
    (desc['name'] && desc['vendor'] && desc['version'])
  end

  # Rebuild and evaluate the package in order to generate
  #     the dependencies mapping record name-vendor-version based;
  #     Supported sonata package descriptor files:
  #     https://github.com/sonata-nfv/son-schema/tree/master/package-descriptor
  #     also expected a directory 'service_descriptors' holding the nsds
  #     and a 'function_descriptos' folder containing the vnfds
  # @param [StringIO] sonpfile The sonata package file contents
  # @param [String] sonp_id The sonata package file id
  # @return [Hash] Document containing the dependencies mapping
  def son_package_dep_mapping(sonpfile, sonp_id)
    mapping = { pd: {}, nsds: [], vnfds: [], deps: [] }
    Zip::InputStream.open(sonpfile) do |io|
      while (entry = io.get_next_entry)
        dirname = Pathname(File.path(entry.name)).split.first.to_s
        if dirname.casecmp('META-INF') == 0
          if File.basename(entry.name).casecmp('MANIFEST.MF') == 0
            desc, errors = parse_yaml(io.read)
            if valid_dep_mapping_descriptor? desc
              mapping[:pd] = { vendor: desc['vendor'],
                               version: desc['version'],
                               name: desc['name'] }
              if !desc['package_dependencies'].nil?
                desc['package_dependencies'].each do |pdep|
                  if valid_dep_mapping_descriptor? pdep
                    mapping[:deps] << { vendor: pdep['vendor'],
                                        version: pdep['version'],
                                        name: pdep['name'] }
                  end
                end
              end
            end
          end
        elsif dirname.casecmp('SERVICE_DESCRIPTORS') == 0
          if !entry.name_is_directory?
            desc, errors = parse_yaml(io.read)
            if valid_dep_mapping_descriptor? desc
              mapping[:nsds] << { vendor: desc['vendor'],
                                  version: desc['version'],
                                  name: desc['name'] }
            end
          end
        elsif dirname.casecmp('FUNCTION_DESCRIPTORS') == 0
          if !entry.name_is_directory?
            desc, errors = parse_yaml(io.read)
            if valid_dep_mapping_descriptor? desc
              mapping[:vnfds] << { vendor: desc['vendor'],
                                   version: desc['version'],
                                   name: desc['name'] }
            end
          end
        end
      end
    end
    mapping_id = SecureRandom.uuid
    mapping['_id'] = mapping_id
    mapping['son_package_uuid'] = sonp_id
    mapping['status'] = 'active'
    mapping
  end

  # Method returning packages depending on a descriptor
  # @param [Symbol] desc_type descriptor type (:vnfds, :nsds, :deps)
  # @param [Hash] desc descriptor hash
  # @param [Hash] target_package Target package to check
  # @param [Boolean] active_criteria true: checks the status of the package avoiding returning deps on inactive ones
  # @return [Boolean] true if there is some other package (different from target) depending on the descriptor
  def check_dependencies(desc_type, desc, target_package = nil, active_criteria = false)
    dependent_packages = Dependencies_mapping.where(
      { desc_type => { '$elemMatch' => { name: desc[:name],
                                         vendor: desc[:vendor],
                                         version: desc[:version] } } })
    dependent_packages.each do |dp|
      diffp_condition = true
      if target_package != nil
        diffp_condition = ( (dp.pd['name'] != target_package['name']) or
                            (dp.pd['vendor'] != target_package['vendor']) or
                            (dp.pd['version'] != target_package['version']) )
      end
      if diffp_condition
        if active_criteria
          return true if dp['status'].casecmp('ACTIVE') == 0
        else
          return true
        end
      end
    end
    return false
  end

  # Method returning boolean depending if there is some instance of a descriptor
  # @param [Symbol] desc_type Descriptor type (:vnfd, :nsd)
  # @param [Hash] descriptor Descriptor hash
  # @return [Boolean] true/false
  def instanced_descriptor?(desc_type, descriptor)
    if desc_type == :vnfd
      desc = Vnfd.where({ 'vnfd.name' => descriptor['name'],
                          'vnfd.vendor' => descriptor['vendor'],
                          'vnfd.version' => descriptor['version'] }).first
      return false if desc.nil?
      instances = Vnfr.where({ 'descriptor_reference' => desc['_id'] }).count
    elsif desc_type == :nsd
      desc = Nsd.where({ 'nsd.name' => descriptor['name'],
                         'nsd.vendor' => descriptor['vendor'],
                         'nsd.version' => descriptor['version'] }).first
      return false if desc.nil?
      instances = Nsr.where({ 'descriptor_reference' => desc['_id'] }).count
    end
    if instances > 0
      return true
    end
    return false
  end

  # Method returning descritptor information depending if there's one component instanced
  # @param [Pkgd] package Package descriptor model
  # @return [Hash] instantiated vnfds and nsds arrays
  def instanced_components(package)
    vnfds = []
    nsds = []
    begin
      pdep_mapping = Dependencies_mapping.find_by({ 'pd.name' => package.pd['name'],
                                                    'pd.version' => package.pd['version'],
                                                    'pd.vendor' => package.pd['vendor'] })
    rescue Mongoid::Errors::DocumentNotFound => e
      logger.error 'Dependencies not found: ' + e.message
      return nil
    end
    pdep_mapping.vnfds.each do |vnfd|
      if instanced_descriptor?(:vnfd, vnfd)
        vnfds << vnfd
      end
    end
    pdep_mapping.nsds.each do |nsd|
      if instanced_descriptor?(:nsd, nsd)
        nsds << nsd
      end
    end
    { vnfds: vnfds, nsds: nsds }
  end

  # Method returning Hash containing Vnfds and Nsds that can safely be disabled/deleted
  #     with no dependencies on other packages
  # @param [Pkgd] package Package descriptor model
  # @return [Hash] disable/delete and cant_disable/cant_delete vnfds and nsds
  # Method returning Hash containing Vnfds and Nsds that can safely be deleted
  #     with no dependencies on other packages
  # @param [Symbol] nodeps_sym Optional parameter key for no dependent components
  # @param [Symbol] deps_sym Optional parameter key for dependent components
  # @param [Boolean] active_criteria Optional (default false) parameter in order to ignore inactive dependencies
  # @return [Hash] delete/disable and cant_delete/cant_disable vnfds and nsds
  def intelligent_nodeps(package, nodeps_sym = :delete, deps_sym = :cant_delete, active_criteria = false)
    vnfds = []
    nsds = []
    cant_delete_vnfds = []
    cant_delete_nsds = []
    begin
      pattern = { 'pd.name' => package.pd['name'],
                  'pd.version' => package.pd['version'],
                  'pd.vendor' => package.pd['vendor'] }
      pdep_mapping = Dependencies_mapping.find_by(pattern)
    rescue Mongoid::Errors::DocumentNotFound => e
      logger.error 'Dependencies not found: ' + e.message
      # If no document found, avoid to delete descriptors blindly
      return { nodeps_sym => { vnfds: [], nsds: [] } }
    end
    pdep_mapping.vnfds.each do |vnfd|
      if check_dependencies(:vnfds, vnfd, package.pd, active_criteria)
        logger.info 'VNFD ' + vnfd[:name] + ' has more than one dependency'
        cant_delete_vnfds << vnfd
      else
        vnfds << vnfd
      end
    end
    pdep_mapping.nsds.each do |nsd|
      if check_dependencies(:nsds, nsd, package.pd, active_criteria)
        logger.info 'NSD ' + nsd[:name] + ' has more than one dependency'
        cant_delete_nsds << nsd
      else
        nsds << nsd
      end
    end
    { nodeps_sym => { vnfds: vnfds, nsds: nsds },
      deps_sym => { vnfds: cant_delete_vnfds, nsds: cant_delete_nsds } }
  end

  # Method deleting vnfds from name, vendor, version
  # @param [Array] vnfds array of hashes
  # @return [Array] Not found array
  def delete_vnfds(vnfds)
    not_found = []
    vnfds.each do |vnfd_td|
      descriptor = Vnfd.where({ 'vnfd.name' => vnfd_td['name'],
                                'vnfd.vendor' => vnfd_td['vendor'],
                                'vnfd.version' => vnfd_td['version'] }).first
      if descriptor.nil?
        logger.error 'VNFD Descriptor not found'
        not_found << vnfd_td
      else
        descriptor.destroy
      end
    end
    return not_found
  end

  # Method deleting nsds from name, vendor, version
  # @param [Array] nsds nsds array of hashes
  # @return [Array] Not found array
  def delete_nsds(nsds)
    not_found = []
    nsds.each do |nsd_td|
      descriptor = Nsd.where({ 'nsd.name' => nsd_td['name'],
                               'nsd.vendor' => nsd_td['vendor'],
                               'nsd.version' => nsd_td['version'] }).first
      if descriptor.nil?
        logger.error 'NSD Descriptor not found ' + nsd_td.to_s
        not_found << nsd_td
      else
        descriptor.destroy
      end
    end
    return not_found
  end

  # Method deleting pd and also dependencies mapping
  # @param [Hash] descriptor model hash
  # @return [void]
  def delete_pd(descriptor)
    # first find dependencies_mapping
    package_deps = Dependencies_mapping.where('pd.name' => descriptor['pd']['name'],
                                              'pd.vendor' => descriptor['pd']['vendor'],
                                              'pd.version' => descriptor['pd']['version'])
    descriptor.destroy
    package_deps.each do |package_dep|
      package_dep.destroy
    end
  end

  # Method Set status of vnfds from name, vendor, version
  # @param [Array] vnfds array of hashes
  # @param [String] status Desired status
  # @return [Array] Not found array
  def set_vnfds_status(vnfds, status)
    not_found = []
    vnfds.each do |vnfd_td|
      descriptor = Vnfd.where({ 'vnfd.name' => vnfd_td['name'],
                                'vnfd.vendor' => vnfd_td['vendor'],
                                'vnfd.version' => vnfd_td['version'] }).first
      if descriptor.nil?
        logger.error 'VNFD Descriptor not found'
        not_found << vnfd_td
      else
        descriptor.update('status' => status)
      end
    end
    return not_found
  end

  # Method Set status of nsds from name, vendor, version
  # @param [Array] nsds nsds array of hashes
  # @param [String] status Desired status
  # @return [Array] Not found array
  def set_nsds_status(nsds, status)
    not_found = []
    nsds.each do |nsd_td|
      descriptor = Nsd.where({ 'nsd.name' => nsd_td['name'],
                               'nsd.vendor' => nsd_td['vendor'],
                               'nsd.version' => nsd_td['version'] }).first
      if descriptor.nil?
        logger.error 'NSD Descriptor not found ' + nsd_td.to_s
        not_found << nsd_td
      else
        descriptor.update('status' => status)
      end
    end
    return not_found
  end

  # Method Set status of a pd
  # @param [Hash] descriptor model hash
  # @param [String] status Desired status
  # @return [void]
  def set_pd_status(descriptor, status)
    # first find dependencies_mapping
    package_deps = Dependencies_mapping.where('pd.name' => descriptor['pd']['name'],
                                              'pd.vendor' => descriptor['pd']['vendor'],
                                              'pd.version' => descriptor['pd']['version'])
    descriptor.update('status' => status)
    package_deps.each do |package_dep|
      package_dep.update('status' => status)
    end
  end

  # Method deleting pd from name, vendor, version
  # @param [Hash] pks Package model hash
  # @return [void]
  def intelligent_delete(pks)
    icomps = instanced_components(pks)
    halt 500, JSON.generate(error: 'Can\'t search for instanced components') if icomps.nil?
    if ( icomps[:vnfds].length > 0 ) or ( icomps[:nsds].length > 0 )
      halt 409, JSON.generate(error: 'Instanced elements cannot be deleted.',
                              components: { vnfds: icomps[:vnfds],
                                            nsds: icomps[:nsds] } )
    end
    todelete = intelligent_nodeps(pks)
    logger.info 'COMPONENTS WITHOUT DEPENDENCIES: ' + todelete.to_s
    not_found_vnfds = delete_vnfds(todelete[:delete][:vnfds])
    not_found_nsds = delete_nsds(todelete[:delete][:nsds])
    delete_pd(pks)
    if ( not_found_vnfds.length == 0 ) and ( not_found_nsds.length == 0 )
      logger.debug "Catalogue: leaving DELETE /api/v2/packages?#{query_string}\" with PD #{pks}"
      halt 200, JSON.generate(result: todelete)
    else
      logger.debug "Catalogue: leaving DELETE /api/v2/packages?#{query_string}\" with PD #{pks}"
      logger.info "Some descriptors where not found"
      logger.info "Vnfds not found: " + not_found_vnfds.to_s
      logger.info "Nsds not found: " + not_found_nsds.to_s
      halt 404, JSON.generate(result: todelete, not_found: { vnfds: not_found_vnfds, nsds: not_found_nsds })
    end
  end

  # Method deleting pd from name, vendor, version
  # @param [Hash] pks Package model hash
  # @return [void]
  def intelligent_disable(pks)
    todisable = intelligent_nodeps(pks, :disable, :cant_disable, true)
    logger.info 'COMPONENTS WITHOUT DEPENDENCIES: ' + todisable.to_s
    not_found_vnfds = set_vnfds_status(todisable[:disable][:vnfds], 'inactive')
    not_found_nsds = set_nsds_status(todisable[:disable][:nsds], 'inactive')
    set_pd_status(pks, 'inactive')
    if ( not_found_vnfds.length == 0 ) and ( not_found_nsds.length == 0 )
      logger.debug "Catalogue: leaving DISABLE /api/v2/packages?#{query_string}\" with PD #{pks}"
      halt 200, JSON.generate(result: todisable)
    else
      logger.debug "Catalogue: leaving DISABLE /api/v2/packages?#{query_string}\" with PD #{pks}"
      logger.info "Some descriptors where not found "
      logger.info "Vnfds not found: " + not_found_vnfds.to_s
      logger.info "Nsds not found: " + not_found_nsds.to_s
      halt 404, JSON.generate(result: todisable,
                              not_found: { vnfds: not_found_vnfds, nsds: not_found_nsds })
    end
  end

  # Method deleting pd from name, vendor, version
  # @param [Hash] pks Package model hash
  # @return [void]
  def intelligent_enable_all(pks)
    begin
      pattern = { 'pd.name' => pks.pd['name'],
                  'pd.version' => pks.pd['version'],
                  'pd.vendor' => pks.pd['vendor'] }
      pdep_mapping = Dependencies_mapping.find_by(pattern)
    rescue Mongoid::Errors::DocumentNotFound => e
      logger.error 'Dependencies not found: ' + e.message
      # If no document found, avoid to delete descriptors blindly
      return { nodeps_sym => { vnfds: [], nsds: [] } }
    end
    not_found_vnfds = set_vnfds_status(pdep_mapping.vnfds, 'active')
    not_found_nsds = set_nsds_status(pdep_mapping.nsds, 'active')
    set_pd_status(pks, 'active')
    if ( not_found_vnfds.length == 0 ) and ( not_found_nsds.length == 0 )
      logger.debug "Catalogue: leaving DISABLE /api/v2/packages?#{query_string}\" with PD #{pks}"
      halt 200, JSON.generate(result: { enable: { vnfds: pdep_mapping.vnfds,
                                                nsds: pdep_mapping.nsds } })
    else
      logger.debug "Catalogue: leaving DISABLE /api/v2/packages?#{query_string}\" with PD #{pks}"
      logger.info "Some descriptors where not found "
      logger.info "Vnfds not found: " + not_found_vnfds.to_s
      logger.info "Nsds not found: " + not_found_nsds.to_s
      halt 404, JSON.generate(result: { enable: { vnfds: pdep_mapping.vnfds,
                                                nsds: pdep_mapping.nsds } },
                              not_found: { vnfds: not_found_vnfds, nsds: not_found_nsds })
    end
  end

  # Method which lists all available interfaces
  # @return [Array] an array of hashes containing all interfaces
  def interfaces_list
    [
      {
        'uri' => '/catalogues',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery'
      },
      {
        'uri' => '/catalogues/network-services',
        'method' => 'GET',
        'purpose' => 'List all NSs or specific NS',
        'special' => 'Use version=last to retrieve NSs last version'
      },
      {
        'uri' => '/catalogues/network-services/{id}',
        'method' => 'GET',
        'purpose' => 'List a specific NS by its uuid'
      },
      {
        'uri' => '/catalogues/network-services',
        'method' => 'POST',
        'purpose' => 'Store a new NS'
      },
      {
        'uri' => '/catalogues/network-services',
        'method' => 'PUT',
        'purpose' => 'Update a stored NS specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/network-services/{id}',
        'method' => 'PUT',
        'purpose' => 'Update a stored NS by its uuid',
        'special' => 'Use status=[inactive, active, delete] to update NSD status'
      },
      {
        'uri' => '/catalogues/network-services',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific NS specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/network-services/{id}',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific NS by its uuid'
      },
      {
        'uri' => '/catalogues/vnfs',
        'method' => 'GET',
        'purpose' => 'List all VNFs or specific VNF',
        'special' => 'Use version=last to retrieve VNFs last version'
      },
      {
        'uri' => '/catalogues/vnfs/{id}',
        'method' => 'GET',
        'purpose' => 'List a specific VNF by its uuid'
      },
      {
        'uri' => '/catalogues/vnfs',
        'method' => 'POST',
        'purpose' => 'Store a new VNF'
      },
      {
        'uri' => '/catalogues/vnfs',
        'method' => 'PUT',
        'purpose' => 'Update a stored VNF specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/vnfs/{id}',
        'method' => 'PUT',
        'purpose' => 'Update a stored VNF by its uuid',
        'special' => 'Use status=[inactive, active, delete] to update VNFD status'
      },
      {
        'uri' => '/catalogues/vnfs',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific VNF specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/vnfs/{id}',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific VNF by its uuid'
      },
      {
        'uri' => '/catalogues/packages',
        'method' => 'GET',
        'purpose' => 'List all Packages or specific Package',
        'special' => 'Use version=last to retrieve Packages last version'
      },
      {
        'uri' => '/catalogues/packages/{id}',
        'method' => 'GET',
        'purpose' => 'List a specific Package by its uuid'
      },
      {
        'uri' => '/catalogues/packages',
        'method' => 'POST',
        'purpose' => 'Store a new Package'
      },
      {
        'uri' => '/catalogues/packages',
        'method' => 'PUT',
        'purpose' => 'Update a stored Package specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/packages/{id}',
        'method' => 'PUT',
        'purpose' => 'Update a stored Package by its uuid',
        'special' => 'Use status=[inactive, active, delete] to update PD status'
      },
      {
        'uri' => '/catalogues/packages',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific Package specified by vendor, name, version'
      },
      {
        'uri' => '/catalogues/packages/{id}',
        'method' => 'DELETE',
        'purpose' => 'Delete a specific Package by its uuid'
      },
      {
        'uri' => '/catalogues/packages/{id}/status',
        'method' => 'PUT',
        'purpose' => 'Updates the status of a Package {"status": "active" / "inactive"} as valid json payloads'
      },
      {
        'uri' => '/catalogues/son-packages',
        'method' => 'GET',
        'purpose' => 'List all son-packages or specific son-package'
      },
      {
        'uri' => '/catalogues/son-packages',
        'method' => 'POST',
        'purpose' => 'Store a new son-package'
      },
      {
        'uri' => '/catalogues/son-packages/{id}',
        'method' => 'GET',
        'purpose' => 'List a specific son-package by its uuid'
      },
      {
        'uri' => '/catalogues/son-packages/{id}',
        'method' => 'DELETE',
        'purpose' => 'Remove a son-package'
      }
    ]
  end

  private
  def query_string
    request.env['QUERY_STRING'].nil? ? '' : request.env['QUERY_STRING'].to_s
  end

  def request_url
    request.env['rack.url_scheme'] + '://' + request.env['HTTP_HOST'] + request.env['REQUEST_PATH']
  end
end
