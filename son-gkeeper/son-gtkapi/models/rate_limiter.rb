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

class RateLimitNotCreatedError < StandardError; end
class RateLimitNotCheckedError < StandardError; end

class RateLimiter < ManagerService

  LOG_MESSAGE = 'GtkApi::' + self.name
  
  def self.config(url:, logger:)
    method = LOG_MESSAGE + __method__.to_s
    raise ArgumentError.new('RateLimit model can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered with url='+url}
  end
  
  # TODO: adapt all this to the true Rate Limiter
  
  def initialize()
    method = LOG_MESSAGE + __method__.to_s
    @@logger.debug(method) {"entered"}
  end
  
  def self.create(name:, params:) # period:, limit:, description:
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{params}"}
    raise ArgumentError.new('RateLimit can not be created with nil or empty name') if (name.to_s.empty?)
    raise ArgumentError.new('RateLimit can not be created with nil or empty period') if (params[:period].to_s.empty?)
    raise ArgumentError.new('RateLimit can not be created with nil or empty limit') if (params[:limit].to_s.empty?)
    
    resp = self.putCurb(url: @@url+'/limits/'+name, body: params)
    @@logger.debug(message) {"resp=#{resp}"}
    raise RateLimitNotCreatedError.new('RateLimit creation failled') unless (resp && resp[:status] == 201)
    resp[:items]
  end
  
  def self.check(params:) # limit_id:, client_id:
    message = LOG_MESSAGE+"##{__method__}"
    @@logger.debug(message) {"entered with #{params}"}
    raise ArgumentError.new('RateLimit check can not be used with nil or empty limit_id') if (params[:limit_id].to_s.empty?)
    raise ArgumentError.new('RateLimit check can not be used with nil or empty client_id') if (params[:client_id].to_s.empty?)

    #begin
    resp = self.postCurb(url: @@url+'/check', body: params)
    @@logger.debug(message) {"resp=#{resp}"}
    raise RateLimitNotCheckedError.new('RateLimit check failled') unless (resp && resp[:status] == 200)
    resp[:items]
  end
end
