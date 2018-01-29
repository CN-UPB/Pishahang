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

class VimManagerService < ManagerService

  JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  CLASS_NAME = self.name
  LOG_MESSAGE = 'GtkApi::' + CLASS_NAME

  def self.config(url:, logger:)
    method = LOG_MESSAGE + "##{__method__}(url=#{url})"
    raise ArgumentError, CLASS_NAME+' can not be configured with nil or empty url' if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered'}
  end

  #General Case Add VIM compute and network

  def self.create_vim_rs(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {"entered"}

    saved_params = params.dup

    # Object compute-resources created from params
    #{"vim_type":String,"configuration":{"tenant_ext_router\":String, "tenant_ext_net":String, "tenant":String},
    # "city":String,"country":String, "vim_address":String,"username":String,"pass":String,"domain":String}

    cparams = {}
    cparams[:vim_type] = params[:vim_type].capitalize
    cparams[:configuration] = {}
    cparams[:country] = params[:country]
    cparams[:city] = params[:city]
    cparams[:name] = params[:name]

    is_kubernetes = cparams[:vim_type] == 'Kubernetes'

    if is_kubernetes
      cparams[:vim_address] = params[:compute_configuration][:vim_address]
      cparams[:pass] = params[:compute_configuration][:pass]
      cparams[:configuration][:cluster_ca_cert] = params[:compute_configuration][:cluster_ca_cert]
    else
      cparams[:configuration][:tenant_ext_router] = params[:compute_configuration][:tenant_ext_router]
      cparams[:configuration][:tenant_ext_net] = params[:compute_configuration][:tenant_ext_net]
      cparams[:configuration][:tenant] = params[:compute_configuration][:tenant_id]
      cparams[:vim_address] = params[:compute_configuration][:vim_address]
      cparams[:username] = params[:compute_configuration][:username]
      cparams[:pass] = params[:compute_configuration][:pass]
      cparams[:domain] = params[:compute_configuration][:domain]
    end

    # Object networking-resources created from params
    #{"vim_type":"ovs", "vim_address":"10.100.32.200","username":"operator","city":"Athens","country":"Greece","pass":"apass",
    # "configuration":{"compute_uuid":"ecff9410-4a04-4bd7-82f3-89db93debd4a"}}

    nparams = {}

    unless is_kubernetes
      nparams[:vim_type] = "ovs"
      nparams[:configuration] = {}
      nparams[:vim_address] = params[:networking_configuration][:vim_address]
      nparams[:username] = params[:networking_configuration][:username]
      nparams[:city] = params[:city]
      nparams[:name] = params[:name]
      nparams[:country] = params[:country]
      nparams[:pass] = params[:networking_configuration][:pass]
    end


    begin
      @@logger.debug(method) {"@url = " + @@url}
      # Creating compute resource
      response = postCurb(url:@@url+'/vim/compute-resources', body: cparams)
      @@logger.debug(method) {"response="+response.to_s}
      #Wait a bit for the process call
      sleep 3

      #Wait a bit for the process call
      request_uuid = response[:items][:request_uuid]
      @@logger.debug(method) {"request_uuid="+request_uuid.to_s}
      @@logger.debug(method) {"@url = " + @@url}
      sleep 2

      # Finding compute resource uuid
      response2 = getCurb(url:@@url+'/vim_requests/compute-resources/'+request_uuid, headers: JSON_HEADERS)
      @@logger.debug(method) {"response2="+response2.to_s}
      compute_uuid = response2[:items][:query_response][:uuid]
      @@logger.debug(method) {"compute_uuid="+compute_uuid.to_s}

      unless is_kubernetes
        nparams[:configuration][:compute_uuid] = compute_uuid
        @@logger.debug(method) {"@url = " + @@url}

        # Creating networking resource
        response3 = postCurb(url:@@url+'/vim/networking-resources', body: nparams)
        @@logger.debug(method) {"response3="+response3.to_s}
      end

      # Object WIM ATTACH {"wim_uuid":String, "vim_uuid":String, "vim_address":String}
      wparams={}
      wparams[:wim_uuid] = params[:wim_id]
      wparams[:vim_uuid] = compute_uuid

      # TODO: Use real network configuration ip for kubernetes
      wparams[:vim_address] = if is_kubernetes then '127.0.0.1' else params[:networking_configuration][:vim_address] end
      @@logger.debug(method) {"@url = " + @@url}

      # Creating link VIM -> WIM
      response4 = postCurb(url:@@url+'/wim/attach', body: wparams)
      @@logger.debug(method) {"response4="+response4.to_s}
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  # VIM COMPUTE-RESOURCES

  def self.find_vims_comp_rs(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {'entered'}
    begin
      response = getCurb(url:@@url+'/vim/compute-resources', headers:JSON_HEADERS)
      @@logger.debug(method) {'response='+response.to_s}
      response
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.create_vim_comp_rs(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {"entered"}

    begin
      @@logger.debug(method) {"@url = " + @@url}
      response = postCurb(url:@@url+'/vim/compute-resources', body: params)
      @@logger.debug(method) {"response="+response.to_s}
      response
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.find_vim_comp_rs_request_by_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}(#{uuid})"
    @@logger.debug(method) {'entered'}
    begin
      response = getCurb(url:@@url+'/vim_requests/compute-resources/'+uuid, headers: JSON_HEADERS)
      @@logger.debug(method) {"Got response: #{response}"}
      query_response = response[:items][:query_response]
      if query_response
        query_response
      else
        []
      end
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  # VIM NETWORKING-RESOURCES
  def self.find_vims_net_rs(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {'entered'}
    begin
      response = getCurb(url:@@url+'/vim/networking-resources', headers:JSON_HEADERS)
      @@logger.debug(method) {'response='+response.to_s}
      response
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.create_vim_net_resources(params)
    method = LOG_MESSAGE + "##{__method__}(#{params})"
    @@logger.debug(method) {"entered"}

    begin
      @@logger.debug(method) {"@url = " + @@url}
      response = postCurb(url:@@url+'/vim/networking-resources', body: params)
      @@logger.debug(method) {"response="+response.to_s}
      response
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
    end
  end

  def self.find_vim_net_rs_request_by_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}(#{uuid})"
    @@logger.debug(method) {'entered'}
    begin
      response = getCurb(url:@@url+'/vim_requests/networking-resources/'+uuid, headers: JSON_HEADERS)
      @@logger.debug(method) {"Got response: #{response}"}
      query_response = response[:items][:query_response]
      if query_response
        query_response
      else
        []
      end
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      nil
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
