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
require File.expand_path '../../spec_helper.rb', __FILE__
#require_relative '../spec_helper'
require 'webmock/rspec'
require 'json'
require 'securerandom'
require 'pp'
require 'rspec/its'

RSpec.describe GtkApi do
  include Rack::Test::Methods
  
  def app
    GtkApi # this defines the active application for this test
  end

  describe 'GET "/api"' do
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}
    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'anonymous_operations', client_id: GtkApi::settings.gatekeeper_api_client_id}).and_return({:allowed=>true, :remaining=>0})
      stub_request(:get, 'localhost:5000').to_return(:body => File.new('./config/api.yml'), :status => 200)
      get '/api'
    end

    subject { last_response }
    its(:status) { is_expected.to eq 200 }
  end
  
  describe 'GET "/api/doc"' do
    let(:doc) {  File.new('./views/api_doc.erb')}
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}

    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'anonymous_operations', client_id: GtkApi::settings.gatekeeper_api_client_id}).and_return({:allowed=>true, :remaining=>0})
      stub_request(:get, 'localhost:5000/api-doc').to_return(body: File.new('./views/api_doc.erb'), status: 200)
      get '/api/doc'
    end

    subject { last_response }
    its(:status) { is_expected.to eq 200 }
    its(:body) { is_expected.to eq File.new('./views/api_doc.erb').read }    
  end
end
