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

require 'addressable/uri'
require 'pp'
require 'json'

# This Class is the Class of Sonata Cos Repository
class SonataCosRepository < Sinatra::Application
  @@cosr_schema = JSON.parse(JSON.dump(YAML.load(open('https://raw.githubusercontent.com/tobiasdierich/son-schema/master/complex-service-record/cosr-schema.yml') { |f| f.read })))
  # https and openssl libs (require 'net/https' require 'openssl') enable access to external https links behind a proxy

  DEFAULT_OFFSET = '0'
  DEFAULT_LIMIT = '10'
  DEFAULT_MAX_LIMIT = '100'

  # @method get_root
  # @overload get '/'
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_yaml
  end

  # @method get_cos-instances
  # @overload get "/cos-instances"
  # Gets all cos-instances
  get '/cos-instances' do
    uri = Addressable::URI.new
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    uri.query_values = params
    logger.info "cosr: entered GET /records/cosr/cos-instances?#{uri.query}"

    # transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Get paginated list
    headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    headers[:params] = params unless params.empty?
    # get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }
    valid_fields = [:page]
    logger.info "cosr: keyed_params.keys - valid_fields = #{keyed_params.keys - valid_fields}"
    json_error 400, "cosr: wrong parameters #{params}" unless keyed_params.keys - valid_fields == []

    requests = Cosr.paginate(page: params[:page], limit: params[:limit])
    logger.info "cosr: leaving GET /requests?#{uri.query} with #{requests.to_json}"
    halt 200, requests.to_json if requests
    json_error 404, 'csr: No requests were found'

    begin
      # Get paginated list
      cosr_json = @cosr.to_json
      if content_type == 'application/json'
        return 200, cosr_json
      elsif content_type == 'application/x-yaml'
        headers 'Content-Type' => 'text/plain; charset=utf8'
        cosr_yml = json_to_yaml(cosr_json)
        return 200, cosr_yml
      end
    rescue
      logger.error 'Error Establishing a Database Connection'
      return 500, 'Error Establishing a Database Connection'
    end
  end

  # @method get_cos-instances
  # @overload get "/cos-instances"
  # Gets cos-instances with an id
  get '/cos-instances/:id' do
    begin
      @cosinstance = Cosr.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound => e
      halt(404)
    end
    cosr_json = @cosinstance.to_json
    return 200, cosr_json
  end

  # @method post_cos-instances
  # @overload post "/cos-instances"
  # Post a new cos-instances information
  post '/cos-instances' do
    return 415 unless request.content_type == 'application/json'
    # Validate JSON format
    instance, errors = parse_json(request.body.read)
    cosr_json = instance
    return 400, errors.to_json if errors
    # Validation against schema
    errors = validate_json(cosr_json, @@cosr_schema)

    puts 'cosr: ', Cosr.to_json
    return 422, errors.to_json if errors

    begin
      instance = Cosr.find({ '_id' => instance['_id'] })
      return 409, 'ERROR: Duplicated cosr UUID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    begin
      instance = Cosr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated cosr UUID'
    end
    return 200, instance.to_json
  end

  # @method put_cos-instances
  # @overload put "/cos-instances"
  # Puts a cos-instances record
  put '/cos-instances/:id' do
    # Return if content-type is invalid
    415 unless request.content_type == 'application/json'
    # Validate JSON format
    instance, errors = parse_json(request.body.read)
    return 400, errors.to_json if errors
    # Retrieve stored version
    new_cosr = instance

    # Validation against schema
    errors = validate_json(new_cosr, @@cosr_schema)

    puts 'cosr: ', Cosr.to_json
    return 422, errors.to_json if errors

    begin
      cosr = Cosr.find_by('_id' => params[:id])
      puts 'cosr is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'csr not found'
    end

    # Update to new version
    puts 'Updating...'
    begin
      # Delete old record
      Cosr.where('_id' => params[:id]).delete
      # Create a record
      new_cosr = Cosr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated cosr UUID'
    end

    cosr_json = new_cosr.to_json
    return 200, cosr_json
  end

  delete '/cos-instances/:id' do
    # Return if content-type is invalid
    begin
      cosr = Cosr.find_by('_id' => params[:id])
      puts 'cosr is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'cosr not found'
    end

    # Delete the cosr
    puts 'Deleting...'
    begin
      # Delete the complex service record
      Cosr.where('_id' => params[:id]).delete
    end

    return 200
  end
end
