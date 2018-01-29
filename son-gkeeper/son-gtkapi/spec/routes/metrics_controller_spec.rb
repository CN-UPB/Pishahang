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
require 'json'
require 'securerandom'
require 'pp'
require 'rspec/its'
require 'base64'

RSpec.describe GtkApi, type: :controller do
  include Rack::Test::Methods
  def app() GtkApi end

  # .../functions/metrics/:instance_uuid/:vdu_id/:vnfc_id/asynch-mon-data?metric=vm_cpu_perc&since=…&until=…
  describe 'GET /api/v2/functions/metrics/:instance_uuid/:vdu_id/:vnfc_id/asynch-mon-data/?' do
    let(:function_uuid) {SecureRandom.uuid}
    let(:instance_uuid) {SecureRandom.uuid}
    let(:vdu_id) {'vdu0'}
    let(:known_vnfc_uuid) {SecureRandom.uuid}
    let(:unknown_vnfc_uuid) {SecureRandom.uuid}
    let(:since_date) {'2017-04-11T11:31:31Z'}
    let(:until_date) {'2017-04-11T11:31:31Z'}
    let(:single_metric_name) {'vm_cpu_perc'}
    let(:single_metric_list) {[single_metric_name]}
    let(:spied_function) {spy('function', uuid: function_uuid, instances: [instance_uuid], username: 'sonata')}
    let(:spied_metric) {spy('metric', name: single_metric_list, instances: [instance_uuid])}
    let(:spied_record) {spy('record', descriptor_reference: SecureRandom.uuid)}
    let(:token) {'abc'}
    let(:base_url) {'/api/v2/functions/metrics/'}
    let(:since_param) {'since='+since_date}
    let(:until_param) {'until='+until_date}
    let(:step_param) {'step=10s'}
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}

    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'anonymous_operations', client_id: GtkApi::settings.gatekeeper_api_client_id}).and_return({:allowed=>true, :remaining=>0})
      allow(User).to receive(:authorized?).with(token: token, params: {path: '/functions/metrics', method: 'GET'}).and_return(true)
      allow(User).to receive(:find_username_by_token).with(token).and_return('sonata')
      allow(GtkApiHelper).to receive(:validate_function_ownership)
      allow(GtkApiHelper).to receive(:validate_element_existence)
      allow(Metric).to receive(:counter_kpi)
    end

    context 'should return Ok (200)' do
      let(:url) {base_url+instance_uuid+'/'+vdu_id+'/'+known_vnfc_uuid+'/asynch-mon-data?metrics='+single_metric_name+'&'+since_param+'&'+until_param+'&'+step_param}
      it 'when all that is needed is given' do
        allow(RecordManagerService).to receive(:find_record_by_uuid).with({kind: 'functions', uuid: instance_uuid}).and_return({status: 200, count: 1, items: spied_record, message: "OK"})
        allow(FunctionManagerService).to receive(:find_by_uuid).with(spied_record[:descriptor_reference]).and_return({status: 200, count: 1, items: {uuid: function_uuid, username: 'sonata'}, message: "OK"})
        allow(Metric).to receive(:validate_and_create).with(single_metric_list).and_return(spied_metric)
        allow(Metric).to receive(:find_by_name).with(single_metric_list.first).and_return(spied_metric)
        get url, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
        expect(last_response.status).to eq(200)
      end
    end
    
    context 'should return Not Found (404)' do
      #it 'with unknown instance' do        
      #  allow(spied_function).to receive(:load_instances).and_return(spied_function.instances)
      #  allow(FunctionManagerService).to receive(:find_by_uuid!).with(known_function_uuid).and_return(spied_function)
      #  get '/api/v2/functions/'+known_function_uuid+'/instances/'+unknown_instance_uuid+'/asynch-mon-data?metrics=vm_cpu_perc&since='+since_date+'&until='+until_date
      #  expect(last_response.status).to eq(404)
      #end
    end
    
    context 'should return Unprocessable Entity (400)' do
      before(:each) do
        allow(Metric).to receive(:find_by_name).with(single_metric_list).and_return(spied_metric)
        allow(Metric).to receive(:validate_and_create).with(single_metric_list).and_return(spied_metric)
      end
        
      it 'without list of metrics ' do
        get base_url+instance_uuid+'/'+vdu_id+'/'+known_vnfc_uuid+'/asynch-mon-data?'+since_param+'&'+until_param+'&'+step_param, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
        expect(last_response.status).to eq(400)
      end
      context 'with missing limits:' do
        let (:fixed_url) {base_url+instance_uuid+'/'+vdu_id+'/'+known_vnfc_uuid+'/asynch-mon-data?metrics='+single_metric_name}
        it 'without start date' do
          get fixed_url+'&'+until_param+'&'+step_param, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
          expect(last_response.status).to eq(400)
        end
        it 'without end date' do
          get fixed_url+'&'+since_param+'&'+step_param, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
          expect(last_response.status).to eq(400)
        end
        it 'without any date' do
          get fixed_url+'&'+step_param, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
          expect(last_response.status).to eq(400)
        end
        it 'without step' do
          get fixed_url+'&'+since_param+'&'+until_param, {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
          expect(last_response.status).to eq(400)
        end
      end
    end
  end

  # …/functions/metrics/:instance_uuid/:vdu_id/:vnfc_uuid/synch-mon-data?metrics=vm_cpu_perc&for=<number of seconds>
  describe 'GET /api/v2/functions/metrics/:instance_uuid/:vdu_id/:vnfc_uuid/synch-mon-data/?' do
    context 'with all that is needed'
    context 'with unknown function'
    context 'with unknown instance'
    context 'with missing list of metrics'
  end
  
  describe 'GET /api/v2/functions/metrics/?' do
    #let(:service2) {{
    #  name: "sonata-demo-1",
    #  author: "Felipe Vicens, Atos IT Solutions and Services Iberia",
    #  version:"0.2",
    #  created_at: "2016-11-11T10:21:00.007+00:00",
    #  updated_at:"2016-11-11T10:21:00.007+00:00",
    #  username: 'sonata',
    #  uuid: SecureRandom.uuid
    #}}
    #let(:all_services) { [ service1, service2 ]}
    #let(:returned_all_services) {{status: 200, count: 2, items: all_services, message: "OK"}}
    #let(:default_params) {{'offset'=>GtkApi::DEFAULT_OFFSET, 'limit'=>GtkApi::DEFAULT_LIMIT}}
    #let(:tokenized_default_params) {default_params.merge({'token'=>token})}
    #before(:each) do        
    #  allow(ServiceManagerService).to receive(:find_services).with(default_params).and_return(returned_all_services)
    #  allow(LicenceManagerService).to receive(:find).with({service_uuid: service1[:uuid], user_uuid: service1[:username]}).and_return([])
    #  allow(LicenceManagerService).to receive(:find).with({service_uuid: service2[:uuid], user_uuid: service2[:username]}).and_return([])
    #  get '/api/v2/services', {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
    #end
    
    #it 'calls ServiceManagerService' do
    #  expect(ServiceManagerService).to have_received(:find_services)
    #end
  
    #it 'returns Ok (200)' do
    #  expect(last_response.status).to eq(200)
    #end
    #it 'returns a list of two services' do
    #  expect(last_response.body).to eq(returned_all_services[:items].to_json)
    #end
  end
end
