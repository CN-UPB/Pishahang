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

# @see CSRepository
class SonataCsRepository < Sinatra::Application

  require 'json'
  require 'yaml'


  # Checks if a JSON message is valid
  #
  # @param [JSON] message some JSON message
  # @return [Hash, nil] if the parsed message is a valid JSON
  # @return [Hash, String] if the parsed message is an invalid JSON
  def parse_json(message)
    # Check JSON message format
    begin
      parsed_message = JSON.parse(message) # parse json message
    rescue JSON::ParserError => e
      # If JSON not valid, return with errors
      logger.error "JSON parsing: #{e.to_s}"
      return message, e.to_s + "\n"
    end

    return parsed_message, nil
  end

  # Checks if a JSON message is valid acording to a json_schema
  #
  # @param [JSON] message some JSON message
  # @return [Hash, nil] if the parsed message is a valid JSON
  # @return [Hash, String] if the parsed message is an invalid JSON
  def validate_json(message,schema)
    begin
      JSON::Validator.validate!(schema,message)
    rescue JSON::Schema::ValidationError => e
      logger.error "JSON validating: #{e.to_s}"
      return e.to_s + "\n"
    end
    nil
  end

  # Checks if a YAML message is valid
  #
  # @param [YAML] message some YAML message
  # @return [Hash, nil] if the parsed message is a valid YAML
  # @return [Hash, String] if the parsed message is an invalid YAML
  def parse_yaml(message)
    # Check YAML message format
    begin
      parsed_message = YAML.load(message) # parse YAML message
    rescue YAML::ParserError => e
      # If YAML not valid, return with errors
      logger.error "YAML parsing: #{e.to_s}"
      return message, e.to_s + "\n"
    end
    return parsed_message, nil
  end

  # Translates a message from YAML to JSON
  #
  # @param [YAML] input_yml some YAML message
  # @return [Hash, nil] if the input message is a valid YAML
  # @return [Hash, String] if the input message is an invalid YAML
  def yaml_to_json(input_yml)
    puts 'Parsing from YAML to JSON'
    begin
      output_json = JSON.dump(input_yml)
    rescue
      logger.error 'Error parsing from YAML to JSON'
    end
    output_json
  end

  # Translates a message from JSON to YAML
  #
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

  # Builds an HTTP link for pagination
  #
  # @param [Integer] offset link offset
  # @param [Integer] limit link limit position
  def build_http_link(offset, limit)
    link = ''
    # Next link
    next_offset = offset + 1
    next_cls = Cls.paginate(page: next_offset, limit: limit)
    begin
      link << '<localhost:4011/cloud-services?offset=' + next_offset.to_s + '&limit=' + limit.to_s + '>; rel="next"' unless next_cls.empty?
    rescue
      logger.error 'Error Establishing a Database Connection'
    end

    unless offset == 1
      # Previous link
      previous_offset = offset - 1
      previous_cls = Cls.paginate(page: previous_offset, limit: limit)
      unless previous_cls.empty?
        link << ', ' unless next_cls.empty?
        link << '<localhost:4011/cloud-services?offset=' + previous_offset.to_s + '&limit=' + limit.to_s + '>; rel="last"'
      end
    end
    link
  end

  # Extension of build_http_link
  def build_http_link_name(offset, limit, name)
    link = ''
    # Next link
    next_offset = offset + 1
    next_cls = Cls.paginate(page: next_offset, limit: limit)
    begin
      link << '<localhost:4011/cloud-services/name/' + name.to_s + '?offset=' + next_offset.to_s + '&limit=' + limit.to_s + '>; rel="next"' unless next_cls.empty?
    rescue
      logger.error 'Error Establishing a Database Connection'
    end

    unless offset == 1
      # Previous link
      previous_offset = offset - 1
      previous_cls = Cls.paginate(page: previous_offset, limit: limit)
      unless previous_cls.empty?
        link << ', ' unless next_cls.empty?
        link << '<localhost:4011/cloud-services/name/' + name.to_s + '?offset=' + previous_offset.to_s + '&limit=' + limit.to_s + '>; rel="last"'
      end
    end
    link
  end

  def interfaces_list
    [
        {
            'uri' => '/records/csr/',
            'method' => 'GET',
            'purpose' => 'REST API Structure and Capability Discovery for /records/csr/'
        },
        {
            'uri' => '/records/csr/cs-instances',
            'method' => 'GET',
            'purpose' => 'List all CSR'
        },
        {
            'uri' => '/records/csr/cs-instances/:id',
            'method' => 'GET',
            'purpose' => 'List specific CSR'
        },
        {
            'uri' => '/records/csr/cs-instances',
            'method' => 'POST',
            'purpose' => 'Store a new CSR'
        }
    ]
  end
end
