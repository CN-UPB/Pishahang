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

require 'prometheus/client'
require 'prometheus/client/push'
require 'json'

class GtkKpi < Sinatra::Base  
  
  # default registry
  registry = Prometheus::Client.registry 

  def self.counter(params, pushgateway, registry)

    begin
      if (params[:base_labels] == nil) 
        base_labels = {}
      else
        base_labels = params[:base_labels]                
      end    

      if (params[:value] == nil)
        factor = 1
      else
        factor = params[:value].to_f
      end

      # if counter exists, it will be increased
      if registry.exist?(params[:name].to_sym)
        counter = registry.get(params[:name])
        counter.increment(base_labels, factor)        
        Prometheus::Client::Push.new(params[:job], params[:instance], pushgateway).replace(registry)
        
      else
        # creates a metric type counter
        counter = Prometheus::Client::Counter.new(params[:name].to_sym, params[:docstring], base_labels)
        counter.increment(base_labels, factor)
        # registers counter
        registry.register(counter)
        
        # push the registry to the gateway
        Prometheus::Client::Push.new(params[:job], params[:instance], pushgateway).add(registry) 
      end
    rescue Exception => e
      raise e
    end
  end

  def self.gauge(params, pushgateway, registry)
    
    begin
      if (params[:base_labels] == nil) 
        base_labels = {}
      else
        base_labels = params[:base_labels]                
      end

      if (params[:value] == nil)
        factor = 1
      else
        factor = params[:value].to_f
      end

      # if gauge exists, it will be updated
      if registry.exist?(params[:name].to_sym)
        gauge = registry.get(params[:name])

        value = gauge.get(base_labels)
        
        if value == nil 
          value = factor         
        else
          if params[:operation]=='dec'
            value = value.to_f - factor
          else # default operation: inc
            value = value.to_f + factor          
          end          
        end

        gauge.set(base_labels,value)
        Prometheus::Client::Push.new(params[:job], params[:instance], pushgateway).replace(registry)

      else
        # creates a metric type gauge
        gauge = Prometheus::Client::Gauge.new(params[:name].to_sym, params[:docstring], base_labels)
        gauge.set(base_labels, factor)
        # registers gauge
        registry.register(gauge)
        
        # push the registry to the gateway
        Prometheus::Client::Push.new(params[:job], params[:instance], pushgateway).add(registry) 
      end
    rescue Exception => e
      raise e
    end
  end
  
  put '/kpis/?' do
    original_body = request.body.read
    params = JSON.parse(original_body, :symbolize_names => true)
    logger.info "GtkKpi: PUT /kpis with params=#{params}"    
    pushgateway = 'http://'+settings.pushgateway_host+':'+settings.pushgateway_port.to_s

    begin

      if params[:metric_type]=='counter' 
        GtkKpi.counter(params, pushgateway, registry)
      else
        GtkKpi.gauge(params, pushgateway, registry)
      end

      logger.info 'GtkKpi: '+params[:metric_type]+' '+params[:name].to_s+' updated/created'
      halt 201
      
    rescue Exception => e
      logger.debug(e.message)
      logger.debug(e.backtrace.inspect)
      halt 400
    end           
  end

  get '/kpis/?' do
    pushgateway_query = 'http://'+settings.pushgateway_host+':'+settings.pushgateway_port.to_s    
    begin
      if params.empty?
        cmd = 'prom2json '+pushgateway_query+'/metrics | jq -c .'
        res = %x( #{cmd} )

        halt 200, res
        logger.info 'GtkKpi: sonata metrics list retrieved'
      else

        if params[:base_labels] == nil        
          logger.info "GtkKpi: entered GET /kpis with params=#{params}"        
          pushgateway_query = pushgateway_query + '/metrics | jq -c \'.[]|select(.name=="'+params[:name]+'")\''

          cmd = 'prom2json '+pushgateway_query
          res = %x( #{cmd} )
        else
          # jq -c '.[]|select(.name=="counter1")|.metrics|.[]|select(.labels=={"instance":"gtkkpi","job":"sonata","label1":"value1","label2":"value2","label3":"value3"})|.value'          
          base_labels = params['base_labels']
          metric_name = params['name']
          params.delete('base_labels')
          params.delete('name')
          labels = "{"+params.to_s[1..-2]+', '+base_labels.to_s[1..-2]+"}"          
          labels = labels.gsub('=>',':')
          labels = labels.gsub(' ','')
          pushgateway_query = pushgateway_query + '/metrics | jq -c \'.[]|select(.name=="'+metric_name+'")|.metrics|.[]|select(.labels=='+labels+')\''
          logger.debug "prom2json query: "+pushgateway_query

          cmd = 'prom2json '+pushgateway_query
          res = %x( #{cmd} )

          res = JSON.parse(eval(res).to_json)
          res["name"] = metric_name
          res = res.to_s
          res = res.gsub('=>',':')          
        end

        logger.info 'GtkKpi: '+metric_name.to_s+' retrieved: '+res
        halt 200, res
      end
    rescue Exception => e
      logger.debug(e.message)
      logger.debug(e.backtrace.inspect)
      halt 400
    end
  end
  
  get '/admin/logs' do
    log_message = 'GtkKpi GET /admin/logs'
    logger.debug(log_message) {"entered"}
    File.open('log/'+ENV['RACK_ENV']+'.log', 'r').read
  end
  
  get '/began_at/?' do
    log_message = 'GtkKpi GET /began_at'
    logger.debug(log_message) {'entered'}
    logger.debug(log_message) {"began at #{settings.began_at}"}
    halt 200, {began_at: settings.began_at}.to_json
  end
end