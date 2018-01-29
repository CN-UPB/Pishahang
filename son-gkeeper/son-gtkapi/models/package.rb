##
## Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
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
## Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
# encoding: utf-8
require 'tempfile'
require './models/manager_service.rb'

class Package < ManagerService

  LOG_MESSAGE = 'GtkApi::' + self.name

  def self.url
    @@url
  end

  def self.config(url:, logger:)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new('Package can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@catalogue_url = ENV[GtkApi.services['catalogue']['env_var_url']]
    @@logger.debug(method) {'entered with url='+url}
    @@logger.debug(method) {"@@catalogue_url=#{@@catalogue_url}"}
  end

   def initialize(params)
=begin
{
    "created_at": "2017-06-29T13:34:48.049+00:00", 
    "md5": "49ce3e2f15aec5c012ef35575255ebfb", 
    "pd": {
        "description": "SONATA RING service for qualification environment", 
        "descriptor_version": "1.0", 
        "entry_service_template": "/service_descriptors/sonata-qual-1vnf-1pop.yml", 
        "maintainer": "Felipe Vicens, ATOS, felipe.vicens@atos.net", 
        "name": "sonata-ring-service", 
        "package_content": [
            {
                "content-type": "application/sonata.service_descriptor", 
                "md5": "3480169189d000dc70dfe5b022629c21", 
                "name": "/service_descriptors/sonata-qual-1vnf-1pop.yml"
            }, 
            {
                "content-type": "application/sonata.function_descriptor", 
                "md5": "7dac616660f603911ac6268aa3846095", 
                "name": "/function_descriptors/vring-vnf-vnfd.yml"
            }
        ], 
        "schema": "https://raw.githubusercontent.com/sonata-nfv/son-schema/master/package-descriptor/pd-schema.yml", 
        "sealed": true, 
        "vendor": "eu.sonata-nfv.package", 
        "version": "0.1"
    }, 
    "signature": null, 
    "son-package-uuid": "e7856eec-b8b1-4c1a-9d0d-7aed074cdd13", 
    "status": "active", 
    "updated_at": "2017-06-29T13:34:48.049+00:00", 
    "username": "sonata", 
    "uuid": "d6b0d11b-8a06-4123-a882-c1bd1d4fd91d"
}
=end     
   end
  
  def self.create(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params #{params}"}
    raise ArgumentError.new('Package can not be created without a user token') unless params.key?(:token)
    token = params.delete(:token)
    # {"path": "/packages", "method": "POST"}
    unless User.authorized?(token: token, params: {path: '/packages', method: 'POST'})
      @@logger.debug(method) {"User not authorized to create packages"}
      return { status: 403, count: 0, data: {}, message: 'Forbidden: user could not be authorized'}
    end
    @@logger.debug(method) {"User authorized"}
    
    username = User.find_username_by_token(token)
    if (username.to_s.empty?)
      @@logger.debug(method) {"User name not found from token"}
      return { status: 404, count: 0, data: {}, message: 'Not Found: user name not found from token'}
    end
    @@logger.debug(method) {"User name found: #{username}"}
    
    uri = @@url+'/packages'
    begin
      # from http://www.rubydoc.info/gems/rest-client/1.6.7/frames#Result_handling
      @@logger.debug(method) {"POSTing to "+uri+ " with params #{params}"}
      RestClient.post(uri, params.merge({username: username})){ |response, request, result, &block|
        @@logger.debug(method) {"response=#{response.inspect}"}
        case response.code
        when 201
          { status: 201, count: 1, data: JSON.parse(response.body, symbolize_names: true), message: 'Created'}
        when 409
          { status: 409, count: 0, data: JSON.parse(response.body, symbolize_names: true), message: 'Conflict'}
        when 400
          { status: 400, count: 0, data: {}, message: "Bad Request: #{params}"}
        else
          { status: response.code, count: 0, data: {}, message: 'Unexpected code'}
        end
      }
    rescue  => e #RestClient::Conflict
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      { status: 500, count: 0, data: {}, message: e.backtrace.join("\n\t")}
    end
  end
  
  def self.find_by_uuid(uuid)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with uuid #{uuid}"}
    response = getCurb(url: @@url + '/packages/'+uuid)
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end

  def self.find_package_file_name(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {'entered with uuid='+uuid}
    begin
      response = RestClient.get(@@url+"/son-packages/#{uuid}", JSON_HEADERS)
      @@logger.debug(method) {"response #{response}"}
      if response.code == 200
        JSON.parse(response, symbolize_names: true)[:grid_fs_name]
      else
        ""
      end
    rescue => e
      e.to_json
    end
  end

  def self.find(params)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered with params #{params}"}
    response = getCurb(url: @@url + '/packages', params: params)
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
  
  def self.download(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new('Package can not be downloaded if uuid is not given') if uuid.nil?
    
    @@logger.debug(method) {'entered with uuid='+uuid}
    
    # TODO: validate user permission
    # TODO: validate throttle
    
    #package_file_meta_data = self.find_package_file_meta_data_by_uuid(uuid)
    #@@logger.debug(method) {"package_file_meta_data=#{package_file_meta_data}"}
    #raise 'No package file meta-data found with package file uuid='+uuid if package_file_meta_data.empty?
    
    file_name = self.save_package_file(uuid) #package_file_meta_data)
    @@logger.debug(method) {"file_name=#{file_name}"}
    raise "Package file with file_name=#{file_name} failled to be saved" if (file_name.nil? || file_name.empty?)
    file_name
  end
  
  def self.find_package_file_meta_data_by_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {'entered with uuid='+uuid}
    headers = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
    begin
      response = RestClient.get(@@catalogue_url+"/son-packages/#{uuid}", headers)
      @@logger.debug(method) {"response.code=#{response.code}"}
      if response.code == 200
        JSON.parse(response, symbolize_names: true)
      else
        {}
      end
    rescue => e
      e.to_json
    end
  end
  
  def self.save_package_file(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with package_file_meta_data=#{uuid}"}
    
    # Get data
    url = URI(@@catalogue_url)
    http = Net::HTTP.new(url.host, url.port)
    request = Net::HTTP::Get.new(@@catalogue_url+"/son-packages/#{uuid}")
    # These fields are mandatory
    request["content-type"] = 'application/zip'
    request["content-disposition"] = 'attachment; filename=<filename.son>'
    response = http.request(request)
    @@logger.debug("Catalogue response.code: #{response.code}")
    case response.code
    when '200'
      data = response.read_body
      
      # Save temporary file
      tmp_dir = File.join(GtkApi.root, 'tmp')
      FileUtils.mkdir(tmp_dir) unless File.exists?(tmp_dir)
      package_file_name = uuid+'-'+'filename.son' #package_file_meta_data[:uuid]+'-'+package_file_meta_data[:grid_fs_name]
      package_file_path = File.join(tmp_dir, package_file_name)
      File.open(package_file_path, 'wb') { |file| file.write(data) }
      # pass back the name
      package_file_path
    else
      nil
    end
  end
    
  def self.delete(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {'entered'}
    headers = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
    begin
      response = RestClient.delete(@@url+'/packages/'+uuid, headers)
      @@logger.debug(method) {"response #{response}"}
      response
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end
  
  def is_licensed?(user_id)
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
  
end
