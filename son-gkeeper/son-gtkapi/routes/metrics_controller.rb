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
  
  namespace '/api/v2/functions' do
    before do
      content_type :json
    end
    
    get '/metrics/names/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/functions/metrics/list/?'
      logger.debug(log_message) {'entered with '+query_string}

      #@offset ||= params[:offset] ||= DEFAULT_OFFSET 
      #@limit ||= params[:limit] ||= DEFAULT_LIMIT
      logger.debug(log_message) {"params=#{params}"}
     
      token = get_token( request.env, began_at, method(:count_functions_metrics_queries), log_message)
      user_name = get_username_by_token( token, began_at, method(:count_functions_metrics_queries), log_message)

      remaining = check_rate_limit(limit: 'other_operations', client: user_name) if check_rate_limit_usage()

      validate_user_authorization(token: token, action: "get functions's metrics", uuid: '', path: '/functions/metrics', method:'GET', kpi_method: method(:count_functions_metrics_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"User authorized"}

      metrics = Metric.find(params)
      #validate_collection_existence(collection: metrics, name: 'metrics', kpi_method: method(:count_functions_metrics_queries), began_at: began_at, log_message: log_message)
      logger.debug(log_message) {"Found metrics #{metrics}"}
      #json_error metrics[:status], "Error in fetching metrics list", log_message unless metrics[:status] == 200
      
      #metrics_count = metrics[:count].empty? ? 0 : metrics[:count].to_i
      #logger.debug(log_message) {"links: request_url=#{request_url}, limit=#{@limit}, offset=#{@offset}, total=#{metrics_count}"}
      #links = build_pagination_headers(url: request_url, limit: @limit.to_i, offset: @offset.to_i, total: metrics_count)
      #logger.debug(log_message) {"links: #{links}"}
      #headers 'Link'=> links, 'Record-Count'=> metrics_count.to_s
      metric_names = []
      metrics.each { |metric| metric_names << metric.name}
      count_functions_metrics_queries(labels: {result: "ok", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      halt 200, { metric_names: metric_names}.to_json
    end
    
    # TODO: how to address multiple metrics like in
    # .../metric=cpu_util,disk_usage,packets_sent&...
    
    # GET Asynchronous data request
    get '/metrics/:instance_uuid/:vdu_id/:vc_uuid/asynch-mon-data/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/functions/metrics/:instance_uuid/:vdu_id/:vc_uuid/asynch-mon-data/?'
      logger.debug(log_message) {"entered with params #{params}"}
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      
      logger.debug(log_message) { 'query_string='+request.env['QUERY_STRING']}
      params.delete('splat')
      params.delete('captures')
      params.merge(parse_query_string(request.env['QUERY_STRING']))
      
      EXPECTED_PARAMS = [
        { name: 'instance_uuid', message: 'Function instance uuid'},
        { name: 'vdu_id', message: 'VDU id'},
        { name: 'vc_uuid', message: 'Virtual component uuid'},
        { name: 'metrics', message: 'Metrics list'},
        { name: 'since', message: 'Starting date'},
        { name: 'until', message: 'Ending date'},
        { name: 'step', message: 'Step of collection'}
      ]
      
      EXPECTED_PARAMS.each do |param|
        require_param(param: param[:name], params: params, kpi_method: method(:count_synch_monitoring_data_requests),
          error_message: param[:message], log_message: log_message, began_at: began_at)
      end
      
      token = get_token( request.env, began_at, method(:count_asynch_monitoring_data_requests), log_message)
      validate_user_authorization(
        token: token, action: 'request asynch monitoring data', uuid: params[:vc_uuid], 
        path: '/functions/metrics', method: 'GET', kpi_method: method(:count_synch_monitoring_data_requests),
        began_at: began_at, log_message: log_message
      )
      
      # only function owned by requesting user are allowed to be monitored
      validate_function_ownership( token: token, instance_uuid: params[:instance_uuid], kpi_method: method(:count_asynch_monitoring_data_requests),
        began_at: began_at, log_message: log_message)
      
      # Remove list of wanted fields from the query parameter list
      metrics_names = params.delete('metrics').split(',')
      logger.debug(log_message) { "params without metrics=#{params}"}
      
      metrics = Metric.validate_and_create(metrics_names)
      status = nil
      requested_data = []
        
      # TODO: we're assuming this is treated one metric at a time
      metrics.each do |metric|
        logger.debug(log_message) { "Metric: #{metric}"}
        begin
          resp = metric.asynch_monitoring_data({
            start: params[:since].to_s, end: params[:until].to_s,
            step: params[:step], vnfc_id: params[:vc_uuid]
          })
          # In the end, :status will be the one of the last metric processed
          status = resp[:status]
          requested_data << resp
        rescue AsynchMonitoringDataRequestNotCreatedError
          logger.debug(log_message) {'Failled request with params '+params.to_s+ ' for metric '+metric.name}
          next
        end
      end
      count_asynch_monitoring_data_requests(labels: {result: "ok", uuid: params[:vc_uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      return_data = {
        status: status,
        function_instance_uuid: params[:instance_uuid],
        vdu_id: params[:vdu_id],
        vc_uuid: params[:vc_uuid],
        metrics: metrics_names,
        requested_data: requested_data
      }
      logger.debug(log_message) {"Leaving with #{return_data}"}
      halt 200, return_data.to_json
    end
    
    # GET synchronous data request
    get '/metrics/:instance_uuid/:vdu_id/:vc_uuid/synch-mon-data/?' do
      began_at = Time.now.utc
      log_message = 'GtkApi::GET /api/v2/functions/metrics/:instance_uuid/:vdu_id/:vc_uuid/synch-mon-data/?'
      logger.debug(log_message) {"entered with params #{params}"}
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      
      logger.debug(log_message) { 'query_string='+request.env['QUERY_STRING']}
      params.delete('splat')
      params.delete('captures')
      params.merge(parse_query_string(request.env['QUERY_STRING'])) # TODO: check this?!?
      
      require_param(param: 'instance_uuid', params: params, error_message: 'Function instance uuid', log_message: log_message, began_at: began_at)
      require_param(param: 'vdu_id', params: params, error_message: 'VDU id', log_message: log_message, began_at: began_at)
      require_param(param: 'vc_uuid', params: params, error_message: 'Virtual component uuid', log_message: log_message, began_at: began_at)
      require_param(param: 'metrics', params: params, error_message: 'Metrics list ', log_message: log_message, began_at: began_at)

      token = get_token( request.env, began_at, method(:count_synch_monitoring_data_requests), log_message)
      validate_user_authorization(
        token: token, action: 'request synch monitoring data', uuid: params[:vc_uuid], 
        path: '/functions/metrics', method: 'GET', kpi_method: method(:count_synch_monitoring_data_requests),
        began_at: began_at, log_message: log_message
      )
       
      # do not treat 'for=<length in seconds> now
      unless params['for'].to_s.empty?
        logger.debug(log_message) {"Currently we're not processing the 'for=<length in seconds>' parameter"}
        params.delete('for')
      end
      
      validate_function_ownership( token: token, instance_uuid: params[:instance_uuid], kpi_method: method(:count_synch_monitoring_data_requests),
        began_at: began_at, log_message: log_message)
      
      # Remove list of wanted fields from the query parameter list
      metrics_names = params.delete('metrics').split(',')
      logger.debug(log_message) { "params without metrics=#{params}"}
      
      metrics = Metric.validate_and_create(metrics_names)
      ws_url = ''
      status = nil
        
      # TODO: we're assuming this is treated one metric at a time
      metrics.each do |metric|
        logger.debug(log_message) { "Metric: #{metric.inspect}"}
        begin
          resp = metric.synch_monitoring_data(params[:vc_uuid])
          # {"status": "SUCCESS","metric": [<metric_name1>,<matric_name2>], "ws_url":"ws://<ws_server_ip>:8002/ws/<ws_id>"}
          # In the end, :status and :ws_url will be the ones of the last metric processed
          ws_url = resp[:ws_url]
          status = resp[:status]
        rescue SynchMonitoringDataRequestNotCreatedError
          logger.debug(log_message) {'Failled request with params '+params.to_s+ ' for metric '+metric.name}
          next
        end
      end
      count_synch_monitoring_data_requests(labels: {result: "ok", uuid: params[:vc_uuid], elapsed_time: (Time.now.utc-began_at).to_s})
      return_data = {
        status: status,
        function_instance_uuid: params[:instance_uuid],
        vdu_id: params[:vdu_id],
        vc_uuid: params[:vc_uuid],
        metrics: metrics_names,
        ws_url: ws_url
      }
      halt 200, return_data.to_json
    end
  end
  
  private
  
  def parse_query_string(q_string)
    params = {}
    
    # Example:
    # {"metric":"vm_cpu_perc","filters":["id='123456asdas255sdas'","type='vnf'"]}
    # metrics=vm_cpu_perc,xyz&id=123456asdas255sdas&type=vnf
    list = q_string.split('&')
    list.each do |element|
      var=element.split('=')
      sub_list = var[1].split(',')
      sub_list.size == 1 ? params[var[0].to_sym] = (var[0] == 'metrics' ? [var[1]] : var[1]) : params[var[0].to_sym] = sub_list        
    end
    logger.debug(__method__.to_s) {'params='+params.to_s}
    params
  end
  
  def count_asynch_monitoring_data_requests(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many asynchronous monitoring data requests have been made"
    Metric.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'metrics'})})
  end
  
  def count_synch_monitoring_data_requests(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many synchronous monitoring data requests have been made"
    Metric.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'metrics'})})
  end
  
  def count_functions_metrics_queries(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many function metrics queries have been made"
    Metric.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'GET', module: 'metrics'})})
  end
end
