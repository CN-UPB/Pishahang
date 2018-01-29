##
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
require 'sinatra/namespace'
require 'base64'
class GtkApi < Sinatra::Base

  register Sinatra::Namespace
  helpers GtkApiHelper
  
  namespace '/api/v2/sessions' do
    options '/?' do
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'POST,DELETE'      
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'
      halt 200
    end
    
    # AKA login
    post '/?' do
      log_message = 'GtkApi::POST /sessions/?'
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()
      body = request.body.read
      logger.debug(log_message) {"body=#{body}"}      
      
      json_error(400, 'Unprocessable entity: missing session parameters', log_message) unless body
      
      # TODO: need to decode from base64 here
      # Base64.decode64(s)
      params = JSON.parse(body, symbolize_names: true)
      logger.debug(log_message) {"entered with params=#{params}"}
      json_error(400, 'Unprocessable entity: missing user name', log_message) if (params[:username].to_s.empty?)
      json_error(400, 'Unprocessable entity: missing user password', log_message) if (params[:password].to_s.empty?)

      # We don't have a find_by_name method, and user_uuid is something hard to tackle by the end user
      # so this has to be done at the class level, instead of at instance level
      #user = User.find_by_name(params[:username])
      #if user
        #logger.debug(log_message) {"user=#{user.inspect}"}
        #session = user.authenticated?(params[:secret])
      begin
        session = User.authenticated?( username: params[:username], password: params[:password])
        logger.debug(log_message) {"leaving with session #{session}"}
        content_type :json
        # halt 200, {userid: user.uuid, username: user.username, session_started_at: user.session[:began_at]}.to_json
        halt 200, {username: params[:username], session_began_at: session[:began_at], token: session[:token]}.to_json
      rescue UserNotAuthenticatedError
          json_error 401, 'Unauthorized: user '+params[:username]+' not authenticated', log_message
      end
        #else
        #json_error 404, 'User '+params[:username]+' not found', log_message
        #end
    end

    # AKA logout
    delete '/?' do
      log_message = 'GtkApi::DELETE /sessions/?'
      began_at = Time.now.utc
      remaining = check_rate_limit(limit: 'anonymous_operations', client: settings.gatekeeper_api_client_id) if check_rate_limit_usage()

      token = get_token( request.env, began_at, method(:count_user_logout_requests), log_message)
      begin
        User.logout! token
        logger.debug(log_message) {"User successfuly logged out"}
        content_type :json
        halt 204
      rescue ArgumentError
        json_error 400, 'Unprocessable entity: problem with token', log_message
      rescue UserTokenNotActiveError
        json_error 401, 'Unauthorized: user token not active', log_message
      rescue UserNotLoggedOutError
        json_error 400, 'Unprocessable entity: problem logging out user', log_message
      end
    end
  end
  
  private
  
  def count_user_logout_requests(labels:)
    name = __method__.to_s.split('_')[1..-1].join('_')
    desc = "how many user logout requests have been made"
    User.counter_kpi({name: name, docstring: desc, base_labels: labels.merge({method: 'DELETE', module: 'users'})})
  end
end
