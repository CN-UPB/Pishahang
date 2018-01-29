# encoding: utf-8
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
class GtkApi < Sinatra::Base
  
  DEFAULT_OFFSET = ENV['PAGE_NUMBER'] || "0"
  DEFAULT_LIMIT = ENV['PAGE_SIZE'] || "10"
  DEFAULT_MAX_LIMIT = "100"

  # Root
  get '/api/?' do
    remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    headers 'Content-Type' => 'text/plain; charset=utf8', 'Location' => '/'
    api = open('./config/api.yml')
    halt 200, api.read.to_s
  end
  
  # API documentation
  get '/api/doc/?' do
    remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    erb :api_doc
  end
  
  get '/api/v2/available-services/?' do
    now = Time.now.utc
    log_message = 'GtkApi::GET /api/v2/available-services/?'
    logger.debug(log_message) {'entered'}
    remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    
    content_type :json
    services = GtkApi.services.keys
    url = request.url
    url.slice!('/available-services')
    available_services = []
    available_services << {name: 'api', url: url, alive_since: settings.began_at, seconds: now-settings.began_at}
    services.each do |service_name|
      properties = GtkApi.services[service_name]
      model = Object.const_get(properties['model'])
      url = model.class_variable_get(:@@url) 
      
      unless model.respond_to? :began_at
        available_services << { name: service_name, url: url, alive_since: nil, seconds: nil} 
        next
      end
      
      resp = model.began_at
      logger.debug(log_message) {"resp = #{resp}"}
      unless resp[:status] == 200
        available_services << { name: service_name, url: url, alive_since: nil, seconds: nil}
        next
      end
      began_at = resp[:items][:began_at]
      available_services << { name: service_name, url: url, alive_since: began_at, seconds: now-Time.parse(began_at)}
    end
    halt 200, available_services.to_json 
  end
  
  error Sinatra::NotFound do
    json_error 404, request.path+' not supported'
  end
  
  error do
    json_error 500, params['captures'].first.inspect
  end
end