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

RSpec.describe FunctionManagerService, type: :model do
  def app() GtkApi end
  let(:function_uuid) {SecureRandom.uuid}
  let(:unknown_function_uuid) {SecureRandom.uuid}
  let(:function_to_be_created_1) {{name:'name', version:'0.1', vendor:'vendor'}}
  let(:created_function_1) {function_to_be_created_1.merge({uuid: function_uuid})}
  let(:response_function_1) {function_to_be_created_1.merge({uuid: function_uuid})}
  let(:function_to_be_created_2) {{name:'name', version:'0.2', vendor:'vendor'}}
  let(:created_function_2) {function_to_be_created_2.merge({uuid: function_uuid})}
  let(:all_functions) { [ created_function_1, created_function_2 ]}
  let(:functions_url) { FunctionManagerService.class_variable_get(:@@url) }
  let(:functions_logger) { FunctionManagerService.class_variable_get(:@@logger) }
  
  describe '#config'
  describe '#new'
  describe '#find' do
    before do
      SONATA::CurbAdapter.config(url: functions_url, logger: functions_logger)
    end
    it 'with default parameters should return two functions' do
      #resp = OpenStruct.new(header_str: "HTTP/1.1 200 OK\nRecord-Count: 2", body: all_functions.to_json)     
      WebMock.stub_request(:get, functions_url+"?limit=10&offset=0").
         with(headers: {'Accept'=>'application/json', 'Content-Type'=>'application/json'}).
         to_return(status: 200, body: all_functions.to_json, headers: {})
      resp = {status: 200, count: 2, items: all_functions, message: "OK"} 
      allow(SONATA::CurbAdapter).to receive(:find).with(params: {limit: 10, offset: 0}).and_return(resp) 
      #functions = SONATA::CurbAdapter.find(params: {limit: 10, offset: 0})
      functions = FunctionManagerService.find({limit: 10, offset: 0})
      expect(functions).to eq({status: 200, count: 2, items: all_functions, message: "OK"})      
    end
    it 'with only default offset parameter (0) should return two functions' do
      #resp = OpenStruct.new(header_str: "HTTP/1.1 200 OK\nRecord-Count: 2", body: all_functions.to_json)      
      WebMock.stub_request(:get, functions_url+"?offset=0").
         with(headers: {'Accept'=>'application/json', 'Content-Type'=>'application/json'}).
         to_return(status: 200, body: all_functions.to_json, headers: {})
      resp = {status: 200, count: 2, items: all_functions, message: "OK"} 
      allow(SONATA::CurbAdapter).to receive(:get).with(functions_url+'?offset=0').and_return(resp) 
      #functions = SONATA::CurbAdapter.find(params: {offset: 0})
      functions = FunctionManagerService.find({offset: 0})
      expect(functions).to eq({status: 200, count: 2, items: all_functions, message: "OK"})      
    end
    it 'with parameter limit 1 should return one function' do
      #resp = OpenStruct.new(header_str: "HTTP/1.1 200 OK\nRecord-Count: 2", body: created_function_1.to_json)      
      WebMock.stub_request(:get, functions_url+"?limit=1&offset=0").
         with(headers: {'Accept'=>'application/json', 'Content-Type'=>'application/json'}).
         to_return(status: 200, body: created_function_1.to_json, headers: {})
      resp = {status: 200, count: 2, items: created_function_1, :message=>"OK"} 
      allow(SONATA::CurbAdapter).to receive(:get).with(functions_url+'?limit=1&offset=0').and_return(resp) 
      #functions = SONATA::CurbAdapter.find(params: {limit: 1, offset: 0})
      functions = FunctionManagerService.find({limit: 1, offset: 0})
      expect(functions).to eq({status: 200, count: 1, items: [created_function_1], message: "OK"})      
    end
  end
  describe '#find_by_uuid' do
    it 'should find a function with a known UUID' do
      resp = OpenStruct.new(header_str: "HTTP/1.1 200 OK\nRecord-Count: 1", body: created_function_1.to_json)      
      allow(Curl).to receive(:get).with(functions_url+function_uuid).and_return(resp) 
      function = FunctionManagerService.find_by_uuid(function_uuid)
      expect(function).to eq({status: 200, count: 1, items: created_function_1, message: "OK"})      
    end
    it 'should not find a function with an unknown UUID' do
      resp = OpenStruct.new(header_str: 'HTTP/1.1 404 Not Found', body: '{}')      
      allow(Curl).to receive(:get).with(functions_url+unknown_function_uuid).and_return(resp) 
      function = FunctionManagerService.find_by_uuid(unknown_function_uuid)
      expect(function).to eq({status: 404, count: 0, items: [], message: "Not Found"})
    end
  end
  describe '#find_by_uuid!'
  describe '.load_instances'
end