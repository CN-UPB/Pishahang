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

RSpec.describe GtkApi do
  describe 'GET /records' do
    context 'with UUID given' do      
      before do
        stub_request(:get, 'localhost:5100/packages').to_return(:status=>200, :body=>response_body.to_json, :headers=>{ 'Content-Type'=>'application/json' })
        get '/services'
      end
    
      subject { last_response }
      #its(:status) { is_expected.to eq 200 }

    end
    context 'without UUID given' do
    end
  end
  
  describe 'PUT /records/services/:uuid' do
    context 'with UUID given' do
      context 'with record found' do
      end
      context 'without record found' do
      end
    end
    context 'without UUID given' do
    end
  end
end
