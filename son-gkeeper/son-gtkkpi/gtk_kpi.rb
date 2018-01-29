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
ENV['RACK_ENV'] ||= 'production'

require 'sinatra/base'
require 'sinatra/json'
require 'sinatra/config_file'
require 'sinatra/cross_origin'
require 'sinatra/reloader'
require 'sinatra/activerecord'
require 'sinatra/logger'

# Require the bundler gem and then call Bundler.require to load in all gems listed in Gemfile.
require 'bundler'
Bundler.require :default, ENV['RACK_ENV'].to_sym

['helpers', 'routes', 'models', 'lib'].each do |dir|
  Dir[File.join(File.dirname(__FILE__), dir, '**', '*.rb')].each do |file|
    require file
  end
end

# Main class supporting the Gatekeeper's Service Management micro-service
class GtkKpi < Sinatra::Base
  register Sinatra::ConfigFile
  register Sinatra::CrossOrigin
  register Sinatra::Reloader
  register Sinatra::ActiveRecordExtension
  register Sinatra::Logger
  
  helpers GtkKpiHelper
  
  set :root, File.dirname(__FILE__)
  set :public_folder, File.join(File.dirname(__FILE__), 'public')
  set :bind, '0.0.0.0'
  set :time_at_startup, Time.now.utc
  set :environments, %w(development test integration qualification demonstration)
  set :environment, ENV['RACK_ENV'] || :development
  config_file File.join( [root, 'config', 'prometheus.yml.erb'] )
  
    
  use Rack::Session::Cookie, :key => 'rack.session', :domain => 'foo.com', :path => '/', :expire_after => 2592000, :secret => '$0nata'
  
  # Logging
  MODULE='GtkKpi'
	enable :logging

  FileUtils.mkdir(File.join(settings.root, 'log')) unless File.exists? File.join(settings.root, 'log')
  logfile = File.open(File.join('log', ENV['RACK_ENV'])+'.log', 'a+')
  logfile.sync = true
  set :logger, Logger.new(logfile)
  raise 'Can not proceed without a logger file' if settings.logger.nil?
  set :logger_level, (ENV['LOGGER_LEVEL'] ||= 'debug').to_sym # can be debug, fatal, error, warn, or info
  logger.info(MODULE) {"Started at #{settings.time_at_startup}"}
  logger.info(MODULE) {"Logger level at :#{settings.logger_level}"}
    
  enable :cross_origin

  logger.info "GtkKpi started at #{settings.time_at_startup}"
end
