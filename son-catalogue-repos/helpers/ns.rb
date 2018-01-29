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

# Class for Sonata_NS_Repository
class SonataNsRepository < Sinatra::Application
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

  def json_error(code, message)
    msg = {'error' => message}
    logger.error msg.to_s
    halt code, {'Content-type'=>'application/json'}, msg.to_json
  end

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

  # Checks if a JSON message is valid acording to a json_schema
  #
  # @param [JSON] message some JSON message
  # @return [Hash, nil] if the parsed message is a valid JSON
  # @return [Hash, String] if the parsed message is an invalid JSON

  def validate_json(message,schema)
    begin
      JSON::Validator.validate!(schema, message)
    rescue JSON::Schema::ValidationError => e
      logger.error "JSON validating: #{e.to_s}"
      return e.to_s + "\n"
    end
    nil
  end


  def keyed_hash(hash)
    Hash[hash.map { |(k, v)| [k.to_sym, v] }]
  end

  def interfaces_list
    [
      {
        'uri' => '/records/nsr/',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery /records/nsr/'
      },
      {
        'uri' => '/records/nsr/ns-instances',
        'method' => 'GET',
        'purpose' => 'List all NSR'
      },
      {
        'uri' => '/records/nsr/ns-instances/:id',
        'method' => 'GET',
        'purpose' => 'List specific NSR'
      },
      {
        'uri' => '/records/nsr/ns-instances',
        'method' => 'POST',
        'purpose' => 'Store a new NSR'
      }
    ]
  end
end
