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
require 'sinatra/namespace'
class GtkApi < Sinatra::Base

  register Sinatra::Namespace
  
  namespace '/api/v2/kpis' do
    options '/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end
  
    # GET collected kpis
    get '/collected/?' do
      log_message = 'GtkApi::GET /api/v2/kpis/collected/?'
      logger.debug(log_message) {"entered with params=#{params}"}
      
      json_error(400, 'The KPI name must be given', log_message) if (params[:name].nil? || params[:name].empty?)
      json_error(400, 'The KPI start date must be given', log_message) if (params[:start].nil? || params[:start].empty?)
      json_error(400, 'The KPI end date must be given', log_message) if (params[:end].nil? || params[:end].empty?)
      json_error(400, 'The KPI step must be given', log_message) if (params[:step].nil? || params[:step].empty?)
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
    
      body = {name: params[:name], start: params[:start], end: params[:end], step: params[:step], labels: params[:labels]}
      # 200 with metrics
      # 400 Bad request when json data have syntax error
      # 415 on missinh header
      begin
        resp = Metric.get_kpis(body)
        GtkApi.logger.debug(log_message) {"received response was #{resp}"}
        GtkApi.logger.debug(log_message) {"#{resp.count} metrics were received"} 
        resp.to_json
      rescue MetricNotCollectedError => e
        logger.debug(e.message)
        logger.debug(e.backtrace.inspect)
        json_error(400, 'Error collecting the KPIs', log_message)
      end
    end  

    # GET many kpis
    get '/?' do
      log_message = 'GtkApi::GET /api/v2/kpis/?'
      logger.debug(log_message) {"entered with params=#{params}"}
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      
      begin
        resp = KpiManagerService.get_metric(params)
        GtkApi.logger.debug(log_message) {"received response was #{resp}"}
        content_type :json
        resp.to_json
      rescue MetricNotCollectedError => e
        logger.debug(e.message)
        logger.debug(e.backtrace.inspect)
        json_error(400, 'Error collecting the KPIs', log_message)
      end
    end  

    # PUT a request
    put '/?' do
      MESSAGE = "GtkApi::PUT /api/v2/kpis"
      params = JSON.parse(request.body.read)
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      unless params.nil?
        logger.debug(MESSAGE) {"entered with params=#{params}"}
        resp = KpiManagerService.update_metric(params)
        logger.debug(MESSAGE) {"resp=#{resp.inspect}"}
        case resp[:status]
        when 201            
          halt 201
        else
          json_error resp[:status], "Metric was not updated for update_metric #{params}", MESSAGE
        end                
      end
      json_error 400, 'No params specified for the create request', MESSAGE
    end
    
    # updates elapsed time
    put '/service-instantiation-time/?' do
      MESSAGE = "GtkApi::PUT /api/v2/kpis/service-instantiation-time"
      logger.debug(MESSAGE) {"entered with params=#{params}"}
      body_parsed = JSON.parse(request.body.read)
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      json_error 400, 'No params specified for storing service creation time', MESSAGE if body_parsed.nil?

      kpi={
        job:"sonata", instance:"gtksrv", metric_type:"counter", name: "service_instantiation_time", 
        docstring:"how long does it take to instantiate a service", 
        base_labels: { result:"ok", uuid: body_parsed[:uuid], elapsed_time: body_parsed[:elapsed_time], method: "PUT", module:"kpis", time_stamp: body_parsed[:time_stamp] }
      }
      resp = KpiManagerService.update_metric(kpi)
      logger.debug(MESSAGE) {"resp=#{resp.inspect}"}
      case resp[:status]
      when 201            
        halt 201
      else
        json_error resp[:status], "Metric was not updated for update_metric #{params}", MESSAGE
      end                
    end        
  end
  
  private 
  def query_string
    request.env['QUERY_STRING'].empty? ? '' : '?' + request.env['QUERY_STRING'].to_s
  end

  def request_url
    request.env['rack.url_scheme']+'://'+request.env['HTTP_HOST']+request.env['REQUEST_PATH']
  end
end
