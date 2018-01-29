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
# spec/spec_helper.rb
require 'rack/test'
require 'rspec'
require 'webmock/rspec'
require 'json'
require 'securerandom'
require 'pp'
require 'support/factory_bot'

ENV['RACK_ENV'] = 'test'

require File.dirname(__FILE__) + '/../gtk_api.rb'

RSpec.configure do |config|
  config.include Rack::Test::Methods
  config.mock_with :rspec do |configuration|
    #configuration.syntax = [:expect, :should]
    #configuration.syntax = :should
    configuration.syntax = :expect
  end
  config.order = 'random'
  #config.color_enabled = true
  config.tty = true
  config.formatter = :documentation
  config.profile_examples = 3
end

WebMock.disable_net_connect!() #allow_localhost: true)
