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
require 'tempfile'
require 'json'
require 'pp'

class CatalogueRecordNotCreatedError < StandardError; end
class CatalogueRecordNotFoundError < StandardError; end
class CatalogueRecordsNotFoundError < StandardError; end

class Catalogue
  
  attr_accessor :url
  
  JSON_HEADERS = {'Accept'=>'application/json', 'Content-Type'=>'application/json'}
  
  def initialize(url, logger)
    log_message='Catalogue.'+__method__.to_s
    @url = url
    @logger = logger
    @logger.debug(log_message) {"initiaized: url="+url+", logger=#{logger}"}
  end
    
  def create(descriptor)
    log_message='Catalogue.'+__method__.to_s
    @logger.debug(log_message) {"entered with #{descriptor}"}
    begin
      response = RestClient.post( @url, descriptor.to_json, content_type: :json, accept: :json)     
      object = JSON.parse response
      @logger.debug(log_message) { "object=#{object}"}
      object
    rescue => e
      @logger.error(log_message) {"Error during processing: #{$!}"}
      @logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise CatalogueRecordNotCreatedError.new "There was a problem saving descriptor #{descriptor}"
    end
  end
  
  def find_by_uuid(uuid)
    log_message='Catalogue.'+__method__.to_s
    @logger.debug(log_message) { "entered with uuid #{uuid})"}
    begin
      _response = RestClient.get(@url+"/#{uuid}", JSON_HEADERS) 
      @logger.debug(log_message) { "response=#{_response}"}
      parsed_response = JSON.parse _response #.body
      @logger.debug(log_message) { "parsed_response=#{parsed_response}"}
      parsed_response
    rescue => e
      @logger.error(log_message) {"Error during processing: #{$!}"}
      @logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise CatalogueRecordNotFoundError.new 'Record with uuid '+uuid+' was not found'
    end
  end
  
  def find(params)
    log_message='Catalogue.'+__method__.to_s
    headers = JSON_HEADERS
    headers[:params] = params unless params.empty?
    @logger.debug(log_message) {"entered, with params #{params} and headers #{headers}"}
    result={}
    begin
      # First fetch all records without any restriction
      @logger.debug(log_message) {"calling url "+@url+" whith headers #{JSON_HEADERS}"}
      unrestricted = RestClient.get(@url, JSON_HEADERS)
      @logger.debug(log_message) {"unrestricted #{unrestricted}"}
      
      json_unrestricted = JSON.parse unrestricted.body
      @logger.debug(log_message) {"json_unrestricted #{json_unrestricted}"}

      if json_unrestricted.empty?
        @logger.debug(log_message) {"unrestricted has no records"}
        result = {count: 0, items: {}}
      elsif json_unrestricted.count == 1
        # If there's only one, that's it
        @logger.debug(log_message) {"unrestricted has only one record"}
        result = {count: 1, items: json_unrestricted[0]}
      else # Should have more than one record
        @logger.debug(log_message) {"unrestricted has more than one record"}
        result[:count] = json_unrestricted.count
        
        # Now fetch the real result
        @logger.debug(log_message) {"calling url "+@url+" whith headers #{headers}"}
        records = RestClient.get(@url, headers)
        @logger.debug(log_message) {"records #{records}"}
        result[:items] = JSON.parse records.body
      end
      result
    rescue => e
      @logger.error(log_message) {"Error during processing: #{$!}"}
      @logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise CatalogueRecordsNotFoundError.new "Records with params #{params} were not found"
    end
  end
  
  def update(uuid)
    log_message='Catalogue.'+__method__.to_s
    @logger.debug "Catalogue.update(#{uuid})"
  end
  
  def delete(uuid)
    log_message='Catalogue.'+__method__.to_s
    @logger.debug "Catalogue.delete(#{uuid})"
  end
  
  private
  
  def format_error(backtrace)
    log_message='Catalogue.'+__method__.to_s
    first_line = backtrace[0].split(":")
    "In "+first_line[0].split("/").last+", "+first_line.last+": "+first_line[1]
  end
end