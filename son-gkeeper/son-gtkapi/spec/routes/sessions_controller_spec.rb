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
require 'base64'

RSpec.describe GtkApi, type: :controller do
  include Rack::Test::Methods
  def app() GtkApi end

  describe 'POST /api/v2/sessions' do
    let(:now) {Time.now.utc}
    let(:secret) {Base64.strict_encode64('Unknown:None')}
    let(:auth_info) {{username: 'Unknown', password: 'None'}}
    let(:user_spied) {spy('user', username: 'Unknown', session_began_at: now, token: 'abc')}
    let(:user_info) {{uuid: SecuredRandom.uuid, username: user_spied.username}}
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}
    
    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'anonymous_operations', client_id: GtkApi::settings.gatekeeper_api_client_id}).and_return({:allowed=>true, :remaining=>0})
    end
    
    context 'with user name and password given,' do
      context 'and user is authenticated,' do
        before(:each) do
          allow(User).to receive(:authenticated?).with(username: auth_info[:username], password: auth_info[:password]).and_return(user_spied)
          post '/api/v2/sessions/', auth_info.to_json
        end
        it 'returns Ok (200)' do
          expect(last_response.status).to eq(200)
        end
        it 'calls User.authenticated?' do
          expect(User).to have_received(:authenticated?)
        end
      end
      context 'but user is not authenticated,' do
        before(:each) do
          allow(User).to receive(:authenticated?).with(username: auth_info[:username], password: auth_info[:password]).and_raise(UserNotAuthenticatedError)
          post '/api/v2/sessions/', auth_info.to_json
        end
        it 'calls User.authenticated?' do
          expect(User).to have_received(:authenticated?)
        end
        it 'returns Unauthorized (401)' do
          expect(last_response.status).to eq(401)
        end
      end

    end
    context 'without' do
      it 'user name given returns Unprocessable Entity (400)' do
        post '/api/v2/sessions/', {username: '', password:'None'}.to_json
        expect(last_response.status).to eq(400)
      end
      it 'password given returns Unprocessable Entity (400)' do
        post '/api/v2/sessions/', {username: 'Unknown', secret: ''}.to_json
        expect(last_response.status).to eq(400)
      end
    end
  end
  
  describe 'DELETE /api/v2/sessions/' do
    let(:limits) {GtkApi::settings.services['rate_limiter']['limits']}
    let(:anonymous_args) {{limit: limits['anonymous_operations']['limit'], period: limits['anonymous_operations']['period'], description: limits['anonymous_operations']['description']}}
    let(:other_args) {{limit: limits['other_operations']['limit'], period: limits['other_operations']['period'], description: limits['other_operations']['description']}}
    before do
      allow(RateLimiter).to receive(:create).with(name: 'anonymous_operations', params:anonymous_args).and_return({status: 201})
      allow(RateLimiter).to receive(:create).with(name: 'other_operations', params:other_args).and_return({status: 201})
      allow(RateLimiter).to receive(:check).with(params: {limit_id: 'anonymous_operations', client_id: GtkApi::settings.gatekeeper_api_client_id}).and_return({:allowed=>true, :remaining=>0})
    end

    context 'with token given' do
      let(:token) {'XYZ'}
      context 'and valid' do
        context 'is successfully logged out' do
          before(:each) do
            allow(User).to receive(:logout!).with(token)
            delete '/api/v2/sessions/', {}, {'HTTP_AUTHORIZATION' => 'Bearer '+token}
          end
          it 'returns No Content (204)' do
            expect(last_response.status).to eq(204)
          end
        end
      end
      context 'but not valid' do
      end
    end
    context 'returns Unprocessable entity (400)' do
      before(:each) do
        allow(User).to receive(:counter_kpi)
      end
      
      it 'without token given' do
        delete '/api/v2/sessions/', {}, {'HTTP_AUTHORIZATION' => ''}
        expect(last_response.status).to eq(401)
      end
      it 'with mal-formed token given' do
        delete '/api/v2/sessions/', {}, {'HTTP_AUTHORIZATION' => 'ABC'}
        expect(last_response.status).to eq(400)
      end
      # UserTokenNotActiveError
    end
  end
end

