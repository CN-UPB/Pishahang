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

class GtkRec < Sinatra::Base

  # "/records/nsr/ns-instances"
  # "/records/vnfr/vnf-instances"
  
  get '/functions/?' do
    method = MODULE + ' GET /functions'
    logger.debug(method) {"entered with params #{params}"}

    # Remove list of wanted fields from the query parameter list
    field_list = params.delete('fields')
    logger.debug(method) {'query_string='+query_string}
    
    functions = VFunction.new(settings.functions_repository, logger).find(params)
    case functions[:status]
    when 200
      logger.debug(method) { "functions=#{functions}"}

      if field_list
        fields = field_list.split(',')
        logger.debug(method) {"fields=#{fields}"}
        response = functions[:items].to_json(:only => fields)
      else
        response = functions[:items].to_json
      end
      logger.debug(method) {"leaving with response=#{response}"}
      headers 'Record-Count'=>functions[:count].to_s
      halt 200, response
    when 400
    when 404
      logger.debug(method) {"No function with params #{query_string} was found"}
      headers 'Record-Count'=>'0'
      halt 200, '[]'
    else
      logger.debug(method) {"leaving with \"Serious error while fetching function records\""}
      halt 500, "Serious error while fetching function records"
    end
  end
  
  get '/functions/:uuid' do
    method = MODULE + ' GET /functions/:uuid'
    logger.debug(method) {"entered with :uuid=#{params[:uuid]}"}
    
    function = VFunction.new(settings.functions_repository, logger).find_by_uuid(params[:uuid])
    case function[:status]
    when 200
      logger.debug(method) {"found function: #{function[:items]}"}
      halt 200, function[:items].to_json
    when 400
      json_error 400, "Bad request uuid #{params[:uuid]} ", method
    when 404
      json_error 404, "No function with uuid #{params[:uuid]} was found", method
    else
      json_error 500, function[:message], method
    end
  end  
  
  private 
  def query_string
    request.env['QUERY_STRING'].nil? ? '' : '?' + request.env['QUERY_STRING'].to_s
  end

  def request_url
    log_message = 'GtkApi::request_url'
    logger.debug(log_message) {"Schema=#{request.env['rack.url_scheme']}, host=#{request.env['HTTP_HOST']}, path=#{request.env['REQUEST_PATH']}"}
    request.env['rack.url_scheme']+'://'+request.env['HTTP_HOST']+request.env['REQUEST_PATH']
  end
end
