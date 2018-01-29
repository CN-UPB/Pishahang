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
require './models/manager_service.rb'
require 'active_support'

class ValidatorError < StandardError; end
class ValidatorGenericError < StandardError; end

class Validator < ManagerService

  LOG_MESSAGE = 'GtkApi::' + self.name
  
  #attr_accessor :available, :until
  
  def self.config(url:, logger:)
    log_message = LOG_MESSAGE + '#' + __method__.to_s
    raise ArgumentError.new('Validator model can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(log_message) {'entered with url='+url}
  end
  
  def self.valid_package?(file_path:, signature: '')
    log_message = LOG_MESSAGE + '#'+__method__.to_s
    # /validate/package
    # POST {'source':'embedded', 'file':'...', 'syntax': True, 'integrity': True, 'topology':True}
    @@logger.debug(log_message) {"entered with file name #{file_path}"}
    
    # prepare post data
    #fields_hash = {source:'embedded', syntax: true, integrity: true, topology: true, signature: signature}
    #post_data = fields_hash.map { |k, v| Curl::PostField.content(k, v.to_s) }
    #post_data << Curl::PostField.file('file', file_name)

    begin
      # post
      curl = Curl::Easy.new(@@url+'/validate/package')
      curl.multipart_form_post = true
      #curl.headers["Content-Type"] = "multipart/form-data"
      #curl.http_post(post_data)
      curl.http_post(
        Curl::PostField.content('source', 'embedded'),
        Curl::PostField.content('syntax', 'true'),
        Curl::PostField.content('integrity', 'true'),
        Curl::PostField.content('topology', 'true'),
        Curl::PostField.content('signature', signature),
        Curl::PostField.file('file', file_path)
        )
      @@logger.debug(log_message) {"curl.body_str=#{curl.body_str}"}
      resp = {status: curl.response_code, items: [JSON.parse(curl.body_str)]} # ManagerService.status_from_response_headers(curl.header_str)
      case resp[:status]
      when 200
        @@logger.debug(log_message) {"Validator result=#{resp[:items]}"}
        resp[:items].first
      when 400
        @@logger.error(log_message) {"Status 400: #{resp[:items]}"} 
        raise ValidatorError.new "Errors/warnings in validating the package: #{resp[:items]}"
      else
        @@logger.error(log_message) {"Status #{resp[:status]}"} 
        raise ValidatorGenericError.new "Error #{resp[:status]} from the Package Validator"
      end
    rescue  => e
      @@logger.error(log_message) {"Error during processing: #{$!}"}
      @@logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise ValidatorGenericError.new "There was a problem POSTing a package file to the Package validator"
    end    
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
end
