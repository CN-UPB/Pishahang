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
require_relative '../spec_helper'
require 'webmock/rspec'
require 'json'
require 'securerandom'
require 'pp'
require 'rspec/its'

RSpec.describe GtkApi, type: :controller do
  include Rack::Test::Methods
  def app() GtkApi end

  describe 'GET /api/v2/services', type: :controller do
    let(:token) {'abc'}
    let(:service1) {{
      name: "sonata-demo-1",
      author: "Felipe Vicens, Atos IT Solutions and Services Iberia",
      version:"0.1",
      created_at: "2016-11-11T10:21:00.007+00:00",
      updated_at:"2016-11-11T10:21:00.007+00:00",
      username: 'sonata',
      uuid: SecureRandom.uuid
    }}
    let(:returned_service1) {{status: 200, count: 2, items: service1, message: "OK"}}
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}
    
    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'other_operations', client_id: 'sonata'}).and_return({:allowed=>true, :remaining=>0})
      allow(User).to receive(:authorized?).with(token: token, params: {path: '/services', method: 'GET'}).and_return(true)
      allow(User).to receive(:find_username_by_token).with(token).and_return('sonata')
      allow(ServiceManagerService).to receive(:counter_kpi)
    end
    
    context 'with UUID given' do      
      let(:serv_man) {class_double("ServiceManagerService", find_service_by_uuid: service1[:uuid])}
      before(:each) do
        allow(ServiceManagerService).to receive(:find_service_by_uuid).with(uuid: service1[:uuid]).and_return(returned_service1)
        #allow(serv_man).to receive(:find_service_by_uuid).with(uuid: service1[:uuid]).and_return(returned_service1)
        allow(LicenceManagerService).to receive(:find).with({service_uuid: service1[:uuid], user_uuid: service1[:username]}).and_return([])
        get '/api/v2/services/'+service1[:uuid], {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
      end
    
      it 'returns Ok (200)' do
        expect(last_response).to be_ok
      end

    end
    context 'without UUID given' do
      let(:service2) {{
        name: "sonata-demo-1",
        author: "Felipe Vicens, Atos IT Solutions and Services Iberia",
        version:"0.2",
        created_at: "2016-11-11T10:21:00.007+00:00",
        updated_at:"2016-11-11T10:21:00.007+00:00",
        username: 'sonata',
        uuid: SecureRandom.uuid
      }}
      let(:all_services) { [ service1, service2 ]}
      let(:returned_all_services) {{status: 200, count: 2, items: all_services, message: "OK"}}
      let(:default_params) {{'captures'=>[], 'offset'=>GtkApi::DEFAULT_OFFSET, 'limit'=>GtkApi::DEFAULT_LIMIT}}
      let(:tokenized_default_params) {default_params.merge({'token'=>token})}
      before(:each) do        
        allow(ServiceManagerService).to receive(:find_services).with(default_params).and_return(returned_all_services)
        allow(LicenceManagerService).to receive(:find).with({service_uuid: service1[:uuid], user_uuid: service1[:username]}).and_return([])
        allow(LicenceManagerService).to receive(:find).with({service_uuid: service2[:uuid], user_uuid: service2[:username]}).and_return([])
        get '/api/v2/services', {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
      end
        
      it 'calls ServiceManagerService' do
        expect(ServiceManagerService).to have_received(:find_services)
      end
      it 'returns Ok (200)' do
        expect(last_response).to be_ok
      end
      it 'returns a list of two services' do
        expect(last_response.body).to eq(returned_all_services[:items].to_json)
      end
    end
  end
  
  describe 'PUT /api/v2/services/:uuid' do
    context 'with UUID given' do
      context 'and found' do
        context 'and successfully updated'
        context 'but not successfully updated'
      end
      context 'but not found' do
      end
    end
    context 'without UUID given' do
    end
  end
end
