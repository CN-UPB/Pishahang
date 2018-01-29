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

# Sonata class
class Sonata < Sinatra::Application
  # @method get_log
  # @overload get '/network-services/log'
  # Returns contents of log file
  # Management method to get log file of catalogue remotely
  get '/log' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    # filename = 'log/development.log'
    filename = 'log/production.log'

    # For testing purposes only
    begin
      txt = open(filename)

    rescue => err
      logger.error "Error reading log file: #{err}"
      return 500, "Error reading log file: #{err}"
    end

    halt 200, txt.read.to_s
  end

  # @method get_root
  # @overload get '/'
  # Get all available interfaces
  # -> Get all interfaces
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, api_routes.to_yaml
  end

  get '/records' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, api_routes.to_yaml
  end
end

# @see SonCatalogue
class SonataCatalogue < Sinatra::Application
  before do
    # Gatekeeper auth class

    if settings.environment == 'development'
      p 'Development settings'
    end
    # authorized?
  end

  DEFAULT_OFFSET = '0'
  DEFAULT_LIMIT = '10'
  DEFAULT_MAX_LIMIT = '100'

  # @method get_root
  # @overload get '/catalogues/'
  # Get all available interfaces
  # -> Get all interfaces
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_yaml
  end

  delete '/clean' do
    mongoid = YAML.load_file('config/mongoid.yml')
    mongoid[ENV['RACK_ENV'].to_s]['sessions'].each do |session|
      ::Mongoid::Sessions.with_name(session[0].to_sym).drop
    end
    halt 200
  end
end
