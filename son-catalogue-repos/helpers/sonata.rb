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
require 'yaml'
require 'jwt'
require 'sinatra'
require 'net/http'
require 'uri'
require 'base64'

# Sonata class for API routes
class Sonata < Sinatra::Application
  require 'json'
  require 'yaml'

  # Root routes
  def api_routes
    [
      {
        'uri' => '/',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery'
      },
      {
        'uri' => '/records/nsr/',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery nsr'
      },
      {
        'uri' => '/records/vnfr/',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery vnfr'
      },
      {
        'uri' => '/catalogues/',
        'method' => 'GET',
        'purpose' => 'REST API Structure and Capability Discovery catalogues'
      }
  ]
  end
end

def parse_json(message)
  # Check JSON message format
  begin
    parsed_message = JSON.parse(message)
  rescue JSON::ParserError => e
    # If JSON not valid, return with errors
    return message, e.to_s + "\n"
  end
  return parsed_message, nil
end

def get_public_key(address, port, api_ver, path)
  request_url = "http://#{address}:#{port}#{api_ver}#{path}"
  url = URI.parse(request_url)
  full_path = (url.query.blank?) ? url.path : "#{url.path}?#{url.query}"
  http = Net::HTTP.new(url.host, url.port)
  request = Net::HTTP::Get.new(full_path)
  begin
    response = http.request(request)
    return response.code, nil unless response.code.to_i == 200
    return response.code, response.body
  rescue => e
    return '503', e.to_s
  end

  # unless response.code.to_i == 200  # raise 'Error: Public key not available'
  # Writes the Keycloak public key to a config file
  # File.open('config/public_key', 'w') do |f|
  #   f.puts response.body
  # end
  # return response.code, response.body
end

def register_service(address, port, api_ver, path)
  # READ REGISTRATION FROM CONFIG_FORM
  catalogue_reg = JSON.parse(File.read('config/catalogue_registration.json'))
  # repos_reg = JSON.parse(File.read('config/repos_registration.json'))

  request_url = "http://#{address}:#{port}#{api_ver}#{path}"
  url = URI.parse(request_url)
  full_path = (url.query.blank?) ? url.path : "#{url.path}?#{url.query}"
  http = Net::HTTP.new(url.host, url.port)
  request = Net::HTTP::Post.new(full_path)
  request["content-type"] = 'application/json'

  request.body = catalogue_reg.to_json
  response = http.request(request)
  case response.code.to_i
    when 201
      puts 'SON-CATALOGUE Service client: Registered'
      return true
    when 409
      puts 'SON-CATALOGUE Service client: Already registered'
      return true
    else
      puts 'Error: registration failure'
      return false
  end
end

def login_service(address, port, api_ver, path)
  adapter_yml = YAML.load_file('config/adapter.yml')
  request_url = "http://#{address}:#{port}#{api_ver}#{path}"
  url = URI.parse(request_url)
  full_path = (url.query.blank?) ? url.path : "#{url.path}?#{url.query}"
  http = Net::HTTP.new(url.host, url.port)
  request = Net::HTTP::Get.new(full_path)
  credentials =  Base64.strict_encode64("#{adapter_yml['catalogue_client']}:#{adapter_yml['catalogue_secret']}")
  # credentials = {'clientId' => adapter_yml['catalogue_client'], 'secret' => adapter_yml['catalogue_secret']}
  request['authorization'] = "Basic #{credentials}"
  # request["content-type"] = 'application/json'
  # request.body = credentials.to_json
  # request.basic_auth(adapter_yml[repos_client], adapter_yml[repos_secret])
  response = http.request(request)

  if response.code.to_i == 200
    parsed_res, errors = parse_json(response.body)
    if errors
      puts 'SON-CATALOGUE Service client: Error while parsing response'
      nil
    end
    # Write access token
    # File.open('config/catalogue_token', 'w') do |f|
      # File.open('config/repos_token.json', 'w') do |f|
    #   f.puts parsed_res['access_token']
    # end
    puts 'SON-CATALOGUE Service client: Logged-in'
    parsed_res['access_token']
  else
    puts 'SON-CATALOGUE Service client: Login failed'
    nil
  end
end

# def authorized?(address, port, api_ver, path, token)
#   CHECK IF A PROVIDED TOKEN IS VALID
# end

def decode_token(token, pub_key)
  begin
    decoded_payload, decoded_header = JWT.decode token, pub_key, true, { :algorithm => 'RS256' }
    return true
  rescue JWT::DecodeError
    puts 'Decode token: DecodeError'
    return false
  rescue JWT::ExpiredSignature
    puts 'Decode token: ExpiredSignature'
    return false
  rescue JWT::InvalidIssuerError
    puts 'Decode token: InvalidIssuerError'
    return false
  rescue JWT::InvalidIatError
    puts 'Decode token: InvalidIatError'
    return false
  end
end

