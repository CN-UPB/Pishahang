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
require_relative '../spec_helper'
require 'gtk/limit'

RSpec.describe Gtk::RateLimiter do

  request_headers = {
    'Accept' => 'application/json',
    'Content-Type' => 'application/json'
  }


  include Rack::Test::Methods

  def app
    Gtk::RateLimiter
  end

  Store = Gtk::Store

  describe 'PUT /limits/:limit_id' do
    it 'returns Bad Request if field \"limit\" is missing' do
      limit_params = {period: 1}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end

    it 'returns Bad Request if field \"limit\" is not an integer' do
      limit_params = {period: "1aa"}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end

    it 'returns Bad Request if field \"limit\" is a negative value' do
      limit_params = {period: -2}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end

    it 'returns Bad Request if field \"period\" is missing' do
      limit_params = {limit: 1}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end

    it 'returns Bad Request if field \"period\" is not an integer' do
      limit_params = {period: "invalid value"}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end

    it 'returns Bad Request if field \"period\" is a negative value' do
      limit_params = {period: -2}
      put '/limits/create_account_limit', limit_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end


    it 'creates or updates limit' do
      limit_params = {limit: 1, period: 1, description: "One request per second"}
      store = class_double(Store).as_stubbed_const

      expect(store).to receive(:store_limit).exactly(1).times.with(limit_params.merge(id: "create_account_limit"))
      put '/limits/create_account_limit', limit_params.to_json, request_headers
    end

  end
  


  describe 'DELETE /limits/:limit_id' do
    it "returns Not Found if limit does not exist" do
      store = class_double(Store).as_stubbed_const
      expect(store).to receive(:find_limit).exactly(1).times.with("non_existing_limit").and_return(nil)
      delete '/limits/non_existing_limit'

      expect(last_response).to be_not_found
    end

    it 'return No Content if limit was deleted successfully' do
      store = class_double(Store).as_stubbed_const
      expect(store).to receive(:find_limit).exactly(1).times.with("some_limit").and_return({ id: "some_limit", period: 60, limit: 100 })
      expect(store).to receive(:delete_limit).exactly(1).times.with("some_limit").and_return(nil)
      delete '/limits/some_limit'

      expect(last_response.status).to eq 204 #be_no_content
    end
  end

  describe 'GET /limits/:limit_id' do
    it "returns Not Found if limit does not exist" do
      store = class_double(Store).as_stubbed_const
      expect(store).to receive(:find_limit).exactly(1).times.with("non_existing_limit").and_return(nil)
      get '/limits/non_existing_limit'

      expect(last_response).to be_not_found
    end

    it 'return Ok is limit exists' do
      store = class_double(Store).as_stubbed_const
      expect(store).to receive(:find_limit).exactly(1).times.with("some_limit").and_return({ id: "some_limit", period: 60, limit: 100 })
      get '/limits/some_limit'

      expect(last_response).to be_ok
      parsed_body = JSON.parse(last_response.body)
      expect(parsed_body["id"]).to eq "some_limit"
    end
  end


    
  describe 'GET /limits' do
    it 'returns all existing limits' do
      store = class_double(Store).as_stubbed_const
      result = [
        { "id": "other_account_operations", "period": 60, "limit": 100 }, 
        { "id": "create_account", "period": 3600, "limit": 10, "description": "Can create 10 accounts / hour" },
        { "id": "default", "period": 1, "limit": 10, "description": "Global request rate policy is 10req/s"}
      ]

      expect(store).to receive(:find_all_limits).exactly(1).times.and_return(result)

      get '/limits'
      parsed_body = JSON.parse(last_response.body)
      expect(parsed_body.size).to eq(result.size)
    end
  end
  
  describe 'POST /check' do

    it 'allows request if limit allows' do
      store = class_double(Store).as_stubbed_const
      limit_params = { "id": "some_limit_id", "period": 60, "limit": 100 }
      limit = Gtk::Limit.new(limit_params)
      bucket = limit.bucket("some_client_id")


      expect(store).to receive(:find_limit).exactly(1).times.with(limit.id).and_return(limit_params)
      expect(store).to receive(:check_request_rate_limiter).exactly(1).times.with(bucket.id, bucket.leak_rate, limit.limit, 1).and_return([true, 10])

      check_params = {limit_id: limit.id, client_id: "some_client_id"}
      post '/check', check_params.to_json, request_headers

      expect(last_response).to be_ok
      parsed_body = JSON.parse(last_response.body)
      expect(parsed_body["allowed"]).to eq true
      expect(parsed_body["remaining"]).to eq 10
    end

    it 'returns bad request id limit_id does not exist' do
      store = class_double(Store).as_stubbed_const
      check_params = {limit_id: "unexisting_limit", client_id: "some_client_id"}
      expect(store).to receive(:find_limit).exactly(1).times.with("unexisting_limit").and_return(nil)

      post '/check', check_params.to_json, request_headers
      expect(last_response).to be_bad_request
    end
  end
end
