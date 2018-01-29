## SONATA - Gatekeeper
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
require 'json' 
require 'pp'

class GtkPkg < Sinatra::Base

  LOG_MESSAGE = 'GtkPkg::'

  # Receive the Java package
  post '/packages/?' do
    log_message = LOG_MESSAGE + ' POST /packages'
    logger.info(log_message) {"params = #{params}"}
    package_filename = params['package']['filename']
    logger.info(log_message) {"filename = #{package_filename}"}
    username = params.delete('username')
    package = Package.new(catalogue: settings.packages_catalogue, params: {io: params[:package][:tempfile][:tempfile]}, username: username)
    unless package
      json_error 400, 'No package created', log_message
    end
      
    logger.debug(log_message) {"package=#{package.inspect}"}
    descriptor = package.from_file()
    unless descriptor
      json_error 400, 'Error generating package descriptor', log_message
    end
    logger.info(log_message) {"descriptor is #{descriptor}"}
    
    if descriptor.key?('name') && descriptor.key?('vendor') && descriptor.key?('version')
      logger.debug(log_message) {"Package is duplicated"}
      error_message = "Version #{descriptor['version']} of package '#{descriptor['name']}' from vendor '#{descriptor['vendor']}' already exists"
      json_error 409, error_message, log_message
    end
    
    json_error 400, 'Oops.. something terribly wrong happened here!', log_message unless descriptor.key?('uuid')
    
    logger.debug(log_message) {"Storing son-package contents in catalogue"}
    son_package_inst = Package.new(catalogue: settings.son_packages_catalogue, params: {io: params[:package][:tempfile][:tempfile]}, username: username)
    logger.debug(log_message) {"son-package contents stored in catalogue"}
    son_package = son_package_inst.store_package_file(package_filename)
    unless son_package && son_package['uuid']
      json_error 400, 'Error storing son-package.', log_message         
    end
    
    logger.debug(log_message) {"Adding meta-data info from #{descriptor} to son-package file #{son_package['uuid']}"}
    response = son_package_inst.add_sonpackage_meta(son_package['uuid'], descriptor['pd'])
    logger.debug(log_message) {"Meta-data info for son-package file #{son_package['uuid']} response: #{response}"}
    package = Package.new(catalogue: settings.packages_catalogue, params: {io: params[:package][:tempfile][:tempfile]}, username: username)
    response = package.add_sonpackage_id(descriptor['uuid'], son_package['uuid'])
    unless response.nil?
      json_error 400, "Error storing son-package-uuid in descriptor: " + response, log_message
    end
    
    descriptor.store("son-package-uuid", son_package['uuid'])
    logger.info(log_message) {"leaving with package #{descriptor.to_json}"}
    halt 201, {'Location' => "/son-packages/#{descriptor['son-package-uuid']}"}, descriptor.to_json
  end
 
  # GET package descriptor
  get '/packages/:uuid' do
    log_message = 'GtkPkg.get /packages/:uuid'
    unless params[:uuid].nil?
      logger.debug(log_message) { "entered with uuid=\"#{params[:uuid]}\""}
      package = settings.packages_catalogue.find_by_uuid( params[:uuid])
      if package && package.is_a?(Hash) && package['uuid'] && package['pd']
        logger.debug(log_message) { "leaving with package found. Package: #{package}"}
        halt 200, package.to_json
      else
        json_error 400, "No package with UUID=#{params[:uuid]} was found", log_message     
      end
    end
    json_error 400, 'No package UUID specified', log_message   
  end
  
  get '/packages/:uuid/file/?' do
    MESSAGE = "GtkPkg::GET /packages/:uuid/package"
    logger.debug(MESSAGE) {'entered with uuid='+params[:uuid]}
    unless params[:uuid].nil?
      # curl -i -X POST -H "Content-Type: multipart/form-data" -F "image=@./image" -F "data=@./imagedata.json" http://localhost:4567/images
      # TODO: save the file and use send_file, don't use send_data
      package_file = Package.fetch_package_file(params[:uuid])
      if package_file
        send_file package_file
      else
        logger.debug(MESSAGE) {"leaving with \"No package UUID specified\""}
        json_error 400, 'No package file found'
      end
    end
    logger.debug(MESSAGE) {"leaving with \"No package UUID specified\""}
    json_error 400, 'No package UUID specified'
  end

  get '/son-packages/:uuid/?' do
    unless params[:uuid].nil?
      package = settings.son_packages_catalogue.find_by_uuid(params[:uuid])
      if package
        logger.info "GtkPkg: leaving GET /son-packages/#{params[:uuid]} with son-package found, UUID=#{params[:uuid]}"
        halt 200, package        
      else
        logger.error "GtkPkg: leaving GET \"/son-packages/#{params[:uuid]}\" with \"No son-package with UUID=#{params[:uuid]} was found\""
        json_error 400, "No son-package with UUID=#{params[:uuid]} was found"       
      end  
    end
    logger.error "GtkPkg: leaving GET \"/son-packages/#{params[:uuid]}\" with \"No son-package UUID specified\""
    json_error 400, 'No package UUID specified' 
  end

  get '/packages/?' do
    message = LOG_MESSAGE + ' GET "/packages/'+query_string+'"'
    logger.debug(message) {"entered"}

    packages = settings.packages_catalogue.find(params)
    logger.debug(message) {"packages: #{packages}"}
    if packages && packages.is_a?(Array)
      logger.debug(message) {"leaving with #{packages.size} package(s) found"}
      [200, {}, packages.to_json]
    else
      json_error 404, "No package with params #{params} was found", message
    end
  end
  
  delete '/packages/:uuid/?' do
    log_message = LOG_MESSAGE + ' DELETE /packages/:uuid'
    logger.info(log_message) {"uuid = #{params[:uuid]}"}
    json_error 404, 'Could not delete package with uuid='+params[:uuid], message unless settings.packages_catalogue.delete(params[:uuid])
    [204, {}, '']
  end
  
  get '/admin/logs/?' do
    logger.debug "GtkPkg: entered GET /admin/logs"
    File.open('log/'+ENV['RACK_ENV']+'.log', 'r').read
  end
  
  get '/began_at/?' do
    log_message = LOG_MESSAGE + ' /began_at'
    logger.debug(log_message) {'entered'}
    logger.debug(log_message) {"began at #{settings.began_at}"}
    halt 200, {began_at: settings.began_at}.to_json
  end
end
