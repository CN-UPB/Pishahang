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

class GtkFnct < Sinatra::Base

  before do
    content_type :json
  end
  
  get '/functions/?' do
    log_message="GtkFnct GET /functions"
    logger.debug(log_message) {"entered with params #{params}"}

    # Remove list of wanted fields from the query parameter list
    field_list = params.delete('fields')
    logger.debug(log_message) { 'query_string='+query_string}
    logger.debug(log_message) { "params without fields=#{params}"}
    
    resp = settings.functions_catalogue.find(params)
    unless resp[:status] == 200
      logger.debug(log_message) { "leaving with \"No function with params #{query_string} was found\""}
      json_error 404, "No function with params #{query_string} was found"
    end

    logger.debug(log_message) { "functions=#{resp[:data]}"}
    if field_list
      fields = field_list.split(',')
      logger.debug(log_message) {"fields=#{fields}"}
      functions = resp[:data].to_json(:only => fields)
    else
      functions = resp[:data].to_json
    end
    logger.debug(log_message) { "leaving with functions="+functions}
    headers 'Record-Count' => resp[:count]
    halt 200, functions
  end
  
  get '/functions/:uuid' do
    log_message = "GtkFnct GET /functions/:uuid"
    if params[:uuid].nil?
      logger.error(log_message) { "leaving with \"No function UUID specified\""}
      json_error 400, 'No function UUID specified'
    end
    logger.debug(log_message) {"entered with uuid=#{params[:uuid]}"}
    resp = settings.functions_catalogue.find_by_uuid(params[:uuid])
    unless resp[:status] == 200
      logger.error(log_message) { "leaving with \"No function with UUID=#{params[:uuid]} was found\""}
      json_error 404, "No function with UUID=#{params[:uuid]} was found"
    end
    logger.info(log_message) { "found function #{resp[:data]}"}
    headers 'Record-Count' => '1'
    halt 200, resp[:data].to_json
  end
  
  get '/admin/logs' do
    logger.debug "GtkFnct: entered GET /admin/logs"
    File.open('log/'+ENV['RACK_ENV']+'.log', 'r').read
  end
  
  get '/functions/began_at/?' do
    log_message = 'GtkFnct GET /began_at'
    logger.debug(log_message) {'entered'}
    logger.debug(log_message) {"began at #{settings.began_at}"}
    halt 200, {began_at: settings.began_at}.to_json
  end
  
  private
    
  def query_string
    request.env['QUERY_STRING'].nil? ? '' : '?' + request.env['QUERY_STRING'].to_s
  end

  def request_url
    request.env['rack.url_scheme']+'://'+request.env['HTTP_HOST']+request.env['REQUEST_PATH']
  end
end
