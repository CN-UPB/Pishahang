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
# Set environment
ENV['RACK_ENV'] ||= 'production'

require 'sinatra/base'
require 'sinatra/config_file'
require 'sinatra/cross_origin'
require 'sinatra/reloader'
require 'zip'
require 'sinatra/logger'
require 'sinatra/namespace'
require 'securerandom'
#require 'active_support/all'

# Require the bundler gem and then call Bundler.require to load in all gems listed in Gemfile.
require 'bundler'
Bundler.require :default, ENV['RACK_ENV'].to_sym

['helpers', 'routes', 'models'].each do |dir|
  Dir[File.join(File.dirname(__FILE__), dir, '**', '*.rb')].each do |file|
    require file
  end
end

# Concentrates all the REST API of the Gatekeeper
class GtkApi < Sinatra::Base
  register Sinatra::ConfigFile
  register Sinatra::CrossOrigin
  register Sinatra::Reloader
  register Sinatra::Logger
  register Sinatra::Namespace
  
  helpers GtkApiHelper

  set :root, File.dirname(__FILE__)
  set :public_folder, File.join(File.dirname(__FILE__), 'public')
  set :bind, '0.0.0.0'
  set :files, File.join(settings.public_folder, 'files')
  set :began_at, Time.now.utc
  set :environments, %w(development test integration qualification demonstration)
  set :environment, ENV['RACK_ENV'] || :development
  config_file File.join(root, 'config', 'services.yml')
  
  use Rack::Session::Cookie, key: 'rack.session', domain: 'foo.com', path: '/', expire_after: 2592000, secret: '$0nata'
  
  # Logging
	enable :logging
  FileUtils.mkdir(File.join(settings.root, 'log')) unless File.exists? File.join(settings.root, 'log')
  logfile = File.open(File.join('log', ENV['RACK_ENV'])+'.log', 'a+')
  logfile.sync = true
  set :logger, Logger.new(logfile)
  raise 'Can not proceed without a logger file' if settings.logger.nil?
  set :logger_level, (ENV['LOGGER_LEVEL'] || settings.level ||= 'debug').to_sym # can be debug, fatal, error, warn, or info
  settings.logger.info('GtkApi') {"Started at #{settings.began_at}"}
  settings.logger.info('GtkApi') {"Logger level at :#{settings.logger_level} level"}
  
  enable :cross_origin
  #enable :method_override
  
  # TODO: generalize this (not only for RATE LIMIT)
  enable :use_rate_limit
  if ENV['USE_RATE_LIMIT']
    set :use_rate_limit, ENV['USE_RATE_LIMIT'].downcase == 'yes'
  end
  
  if settings.use_rate_limit
    set :gatekeeper_api_client_id, SecureRandom.uuid 
    disable :rate_limits_created
  end
  
  settings.services.each do |service, properties|
    # do not use properties['url']: they're depprecated, in favor of ANSIBLE configuration
    # set it from the ENV var instead
    url = ENV[properties['env_var_url']]
    settings.logger.debug('GtkApi') {"Service #{service.upcase}: URL set from ENV[#{properties['env_var_url']}] is #{url}"}
    if url.to_s.empty? 
      settings.logger.info('GtkApi') {"Service #{service} not configured"}
      next
    end

    if Object.const_defined?(properties['model'])
      Object.const_get(properties['model']).config(url: url, logger: settings.logger)
    else
      settings.logger.info('GtkApi') {"Model class #{properties['model']} for service #{service} does not exist"}
      Process.kill('TERM', Process.pid)
    end
  end  

  Zip.setup do |c|
    c.unicode_names = true
    c.on_exists_proc = true
    c.continue_on_exists_proc = true
  end
  
  def create_rate_limits()
    log_message = 'GtkApi.'+__method__.to_s
    settings.logger.debug(log_message) {'entered'}
    limits = settings.services['rate_limiter']['limits']
    settings.logger.debug(log_message) {"limits are #{limits}"}
    limits.each do |name, values|
      settings.logger.debug(log_message) {"limit is #{name}"}
      settings.logger.debug(log_message) {"values are #{values}"}
      params = {limit: values['limit'], period: values['period'], description: values['description']}
      begin
        resp = Object.const_get(settings.services['rate_limiter']['model']).create(name: name, params: params)
        settings.logger.debug(log_message) {"resp = #{resp}"}
        settings.logger.error(log_message) {'Rate limiter is in place, but could not create a limit'} unless (resp || resp[:status] == 201)
      rescue RateLimitNotCreatedError => e
        settings.logger.error(log_message) {'Failled to create rate limit'}
        halt 500, {error: { code: 500, message:'There seems to have been a problem with rate limit creation'}}.to_json
      end
    end
    settings.logger.debug(log_message) {'Setting rate_limits_created to true...'} 
    settings.rate_limits_created=true
    settings.logger.debug(log_message) {"...set (#{settings.rate_limits_created})!"} 
  end

  def check_rate_limit(limit: , client:)
    log_message = 'GtkApi.'+__method__.to_s
    settings.logger.debug(log_message) {'entered'}
    if settings.services['rate_limiter']
      settings.logger.debug(log_message) {"settings.services['rate_limiter']=#{settings.services['rate_limiter']}"}
      create_rate_limits() unless settings.rate_limits_created

      begin
        resp = Object.const_get(settings.services['rate_limiter']['model']).check(params: {limit_id: limit, client_id: client})
        settings.logger.debug(log_message) {"resp is #{resp}"}
        halt 429, {error: { code: 429, message:'GtkApi: Too many user creation requests were made'}}.to_json unless resp[:allowed]
        resp[:remaining]
      rescue RateLimitNotCheckedError => e
        halt 400, {error: { code: 400, message:'There seems to have been a problem with user creation rate limit validation'}}.to_json
        '0' # Allows this request to proceed
      end
    end
  end
  
  def check_rate_limit_usage()
    settings.use_rate_limit && !(settings.services['rate_limiter'].to_s.empty?)
  end
      
  def query_string
    log_message = 'GtkApi::query_string'
    settings.logger.debug('GtkApi') {"query_string=#{request.env['QUERY_STRING']}"}
    request.env['QUERY_STRING'].empty? ? '' : '?' + request.env['QUERY_STRING'].to_s
  end

  def request_url
    log_message = 'GtkApi::request_url'
    settings.logger.debug('GtkApi') {"Schema=#{request.env['rack.url_scheme']}, host=#{request.env['HTTP_HOST']}, path=#{request.env['REQUEST_PATH']}"}
    "#{request.env['rack.url_scheme']}://#{request.env['HTTP_HOST']}#{request.env['REQUEST_PATH']}"
  end
end
