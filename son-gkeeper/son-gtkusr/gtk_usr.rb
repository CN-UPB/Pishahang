##
## Copyright (c) 2015 SONATA-NFV
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
## Neither the name of the SONATA-NFV
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).

# Set environment
ENV['RACK_ENV'] ||= 'production'

require 'sinatra'
require 'sinatra/base'
require 'sinatra/config_file'
# require 'sinatra/logger'
require 'json'
require 'yaml'
require 'jwt'
require 'mongoid'
# require 'mongoid-pagination'

require_relative 'models/init'
require_relative 'helpers/init'
require_relative 'routes/init'

# Require the bundler gem and then call Bundler.require to load in all gems
# listed in Gemfile.
require 'bundler'
Bundler.require :default, ENV['RACK_ENV'].to_sym

configure do
  # Configuration for logging

  enable :logging
  Dir.mkdir("#{settings.root}/log") unless File.exist?("#{settings.root}/log")
  log_file = File.new("#{settings.root}/log/#{settings.environment}.log", 'a+')
  log_file.sync = true
  use Rack::CommonLogger, log_file

  # STDOUT.reopen(log_file)
  STDERR.reopen(log_file)
  # STDOUT.sync = true
  STDERR.sync = true

  class Keycloak < Sinatra::Application
    register Sinatra::ConfigFile
    # Load configurations
    config_file 'config/keycloak.yml'
    Mongoid.load!('config/mongoid.yml')
    configure {
      enable :logging
    }

    before {
      env['rack.logger'] = Logger.new "#{settings.root}/log/#{settings.environment}.log"
    }

    DEFAULT_OFFSET = '0'
    DEFAULT_LIMIT = '10'
    DEFAULT_MAX_LIMIT = '100'

    # self.get_realm_public_key
    # self.get_oidc_endpoints
    # self.get_adapter_install_json
    # @@access_token = self.get_adapter_token
  end

  # set up the rest of sinatra config stuff
  # @key = create_public_key
  # set :keycloak_pub_key, @key
  set :server, :puma
  set :environment, :production
end

before do
  logger.level = Logger::DEBUG
  # refresh_adapter
end

# Configurations
# Authorization and operations class, it build sa security context based on an existing token and uses that
# to access protected resources (operation layer)
class Adapter < Sinatra::Application
  register Sinatra::ConfigFile
  # Load configurations
  config_file 'config/config.yml'
  configure {
    enable :logging
  }

  before {
    env['rack.logger'] = Logger.new "#{settings.root}/log/#{settings.environment}.log"
  }
end