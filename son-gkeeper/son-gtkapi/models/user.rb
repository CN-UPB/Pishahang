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
require './models/manager_service.rb'
require 'base64'
require 'date'

class UserNotCreatedError < StandardError; end
class UserNotAuthenticatedError < StandardError; end
class UserNotFoundError < StandardError; end
class UsersNotFoundError < StandardError; end
class UserNotUpdatedError < StandardError; end
class UserNameAlreadyInUseError < StandardError; end
class UserNotLoggedOutError < StandardError; end
class UserTokenNotActiveError < StandardError; end
class UserTokenDoesNotMatchError < StandardError; end
class UserPublicKeyNotUpdatedError < StandardError; end
class UserNotUpdatedError < StandardError; end

class User < ManagerService

  LOG_MESSAGE = 'GtkApi::' + self.name
  
  attr_accessor :uuid, :username, :password, :secret, :created_at, :user_type, :email, :last_name, :first_name, :phone_number, :public_key, :certificate
  attr_accessor :instances_public_key, :instances_private_key
  
  # {"username" => "sampleuser", "enabled" => true, "totp" => false, "emailVerified" => false, "firstName" => "User", "lastName" => "Sample", "email" => "user.sample@email.com.br", "credentials" => [ {"type" => "password", "value" => "1234"} ], "requiredActions" => [], "federatedIdentities" => [], "attributes" => {"developer" => ["true"], "customer" => ["false"], "admin" => ["false"]}, "realmRoles" => [], "clientRoles" => {}, "groups" => ["developers"]}
  
  def self.config(url:, logger:)
    method = LOG_MESSAGE + __method__.to_s
    raise ArgumentError.new('UserManagerService can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered with url='+url}
  end
  
  def initialize(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params #{params}"}
    raise ArgumentError.new('UserManagerService can not be instantiated without a user name') unless (params.key?(:username) && !params[:username].empty?)

    @username = params[:username]
    @secret = Base64.strict_encode64(params[:username]+':'+params[:password]) if params[:password]
    @uuid = params[:uuid]
    @created_at = params[:created_at]
    @user_type = params[:user_type]
    @email = params[:email]
    @phone_number = params[:phone_number] if params[:phone_number]
    @last_name = params[:last_name] if params[:last_name]
    @first_name = params[:first_name] if params[:first_name]
    @public_key = params[:public_key] if params[:public_key]
    @certificate = params[:certificate] if params[:certificate]
    @instances_public_key = params[:instances_public_key] if params[:instances_public_key]
    @instances_private_key = params[:instances_private_key] if params[:instances_private_key]
  end

  def self.create(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with #{params}"}

    saved_params = params.dup
    
    params[:firstName] = params.delete(:first_name) if params[:first_name]
    params[:lastName] = params.delete(:last_name) if params[:last_name]
    
    # Transform password
    params[:credentials] = [{type: 'password', value: params.delete(:password)}]
    
    # Transform user type
    params[:attributes] = {}
    params[:attributes][:userType] = [params.delete(:user_type)]
    params[:attributes][:phone_number] = [params.delete(:phone_number)] if params[:phone_number]
    params[:attributes][:certificate] = [params.delete(:certificate)] if params[:certificate]
    params[:attributes][:public_key] = [params.delete(:public_key)] if params[:public_key]
    @@logger.debug(method) {"params = #{params}"}
    
    begin
      resp = postCurb(url: @@url+'/api/v1/register/user', body: params)
      case resp[:status]
      when 200..202
        user = resp[:items]
        raise UserNotCreatedError.new "User not created with params #{params}" unless user.key? :userId
        @@logger.debug(method) {"user=#{user}"}
        unless user.empty?
          saved_params[:uuid] = user[:userId]
          saved_params[:created_at] = user[:created_at]
        end
        User.new(saved_params)
      when 409
        @@logger.debug(method) {"Status 409"} 
        raise UserNameAlreadyInUseError.new "User name #{params[:username]} already in use"
      else
        @@logger.error(method) {"Status #{resp[:status]}"} 
        raise UserNotCreatedError.new "User not created with params #{params}"
      end
      #rescue  => e
      #@@logger.debug(method) {"resp=#{resp}"}
      #@@logger.error(method) {"Error during processing: #{$!}"}
      #@@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      #raise UserNotCreatedError.new "User not created with params #{params}"
    end
  end

  def self.authenticated?(username:, password:)
    method = "#{LOG_MESSAGE}##{__method__}"
    raise ArgumentError.new 'Authentication needs the user name' if (username.to_s.empty?)
    raise ArgumentError.new 'Authentication needs the user password' if (password.to_s.empty?)
    
    secret = Base64.strict_encode64(username+':'+password)
    @@logger.debug(method) {"entered with secret=#{secret}"}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Basic '+secret}
    begin
      resp = postCurb(url: @@url+'/api/v1/login/user', body: {}, headers: headers)
      @@logger.debug(method) {"response=#{resp}"}
      case resp[:status]
      when 200
        token = resp[:items]
        @@logger.debug(method) {"token=#{token}"}
        {began_at: Time.now.utc, token: token, user_type: find_user_type_by_username(username)}
      when 401
        @@logger.error(method) {"Status 401"} 
        raise UserNotAuthenticatedError.new "User not authenticated with params #{secret}"
      else
        @@logger.error(method) {"Status #{resp[:status]}"} 
        raise UserNotAuthenticatedError.new "User not authenticated with params #{secret}"
      end
      #rescue  => e
      #@@logger.error(method) {"Error during processing: #{$!}"}
      #@@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      #raise UserNotAuthenticatedError.new "User not authenticated with params #{secret}"
    end
  end

  def self.logout!(token)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new 'Logging out requires the login token' if (token.nil? || token.empty?)
    @@logger.debug(method) {"entered"}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Bearer '+token}

    resp = postCurb(url: @@url+'/api/v1/logout', body: {}, headers: headers)
    case resp[:status]
    when 204
      @@logger.debug(method) {"User logged out"}
      {lasted_for: Time.now.utc}
    when 401
      @@logger.error(method) {"Status 401: token not active"} 
      raise UserTokenNotActiveError.new "User token was not active"
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      raise UserNotLoggedOutError.new "User not logged out with the given token"
    end
  end
  
  def self.authorized?(token:, params:)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires the login token' if token.to_s.empty?
    raise ArgumentError.new __method__.to_s+' requires a path and a method to be authorized' if (params.to_s.empty? || !params.key?(:method) || !params.key?(:path))
    @@logger.debug(method) {"entered with token #{token} and params #{params}"}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Bearer '+token}

    resp = postCurb(url: @@url+'/api/v1/userinfo', body: params, headers: headers)
    # {:sub=>"fe53ac4f-052a-4a41-b7cd-914d4c64c2f8", :name=>"", :preferred_username=>"jbonnet", :email=>"jbonnet@alticelabs.com"}
    case resp[:status]
    when 200
      @@logger.debug(method) {"User authorized to #{params}"}
      true
    when 401
      @@logger.error(method) {"Status 401: User not authorized to #{params}"} 
      false
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      false
    end
  end
  
  def update(fields, token)
    log_message = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires a hash with arguments' if fields.to_s.empty?
    @@logger.debug(log_message) {"entered with fields=#{fields}"}
    fields.each do |key, value|
      @@logger.debug(log_message) {"key=#{key}, value=#{value}"}
      setter = :"#{key}="
      @@logger.debug(log_message) {"setter is #{setter}"}
      if respond_to?(setter)
        @@logger.debug(log_message) {"user responds to #{setter}"}
        public_send(setter, value)
        new_val = instance_variable_get("@#{key}")
        @@logger.debug(log_message) {"variable @#{key} set to #{new_val}"}
      else
        @@logger.debug(log_message) {"user does not respond to #{setter}"}
      end
    end
    save(token: token)
  end

  def save(token:)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered"}
    body={public_key: @public_key, certificate: @certificate}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Bearer '+token}
    resp = User.putCurb(url: @@url+'/api/v1/users?username='+@username, body: export(), headers: headers)
    case resp[:status]
    when 204 # data was successfully saved
      @@logger.debug(method) {"User data saved"}
      self
    when 400 # Provided username does not match with Access Token, No username specified or Developer public key not provided
      @@logger.debug(method) {'Username '+@username+' does not match with token'}
      raise UserTokenDoesNotMatchError.new 'Username '+@username+' does not match with token'
    when 401 # Token is not valid
      @@logger.debug(method) {'Username '+@username+' provided a token that is not valid'}
      raise UserTokenNotActiveError.new 'Username '+@username+' provided a token that is not valid'
    when 404 # Username is not found
      @@logger.debug(method) {'Username '+@username+' was not found'}
      raise UserNotFoundError.new 'Username '+@username+' was not found'
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      raise UserNotUpdatedError.new 'User public-key not updated'
    end
  end
   
  def save_public_key(params, token)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires the login token' if token.to_s.empty?
    @@logger.debug(method) {"entered"}
    
    @public_key = params[:public_key]
    @certificate = params[:certificate] if params[:certificate]
    body={public_key: @public_key, certificate: @certificate}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Bearer '+token}
    resp = User.putCurb(url: @@url+'/api/v1/signatures/'+@username, body: body, headers: headers)
    case resp[:status]
    when 204 # signature is successfully updated
      @@logger.debug(method) {"User public-key updated"}
      self
    when 400 # Provided username does not match with Access Token, No username specified or Developer public key not provided
      @@logger.debug(method) {'Username '+@username+' does not match with token'}
      raise UserTokenDoesNotMatchError.new 'Username '+@username+' does not match with token'
    when 401 # Token is not valid
      @@logger.debug(method) {'Username '+@username+' provided a token that is not valid'}
      raise UserTokenNotActiveError.new 'Username '+@username+' provided a token that is not valid'
    when 404 # Username is not found
      @@logger.debug(method) {'Username '+@username+' was not found'}
      raise UserNotFoundError.new 'Username '+@username+' was not found'
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      raise UserPublicKeyNotUpdatedError.new 'User public-key not updated'
    end
  end
  
  def self.valid?(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params #{params}"}
    User.find_by_uuid(params[:user_uuid])
  end
  
  def self.find_by_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with uuid #{uuid}"}
    begin
      response = getCurb(url:@@url + '/api/v1/users?id=' + uuid, headers: JSON_HEADERS)
      @@logger.debug(method) {"Got response: #{response}"}
      raise UserNotFoundError.new "User with uuid #{uuid} was not found" unless response[:status] == 200
      if response[:items].empty? || (user = response[:items].first).empty?
        raise UserNotFoundError.new "User with uuid #{uuid} was not found (code #{response[:status]})"
      end
      User.new( User.import(user))
    end
  end

  def self.find_by_name(name)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with name #{name}"}

    begin
      response = getCurb(url:@@url + '/api/v1/users?username=' + name, headers: JSON_HEADERS)
      @@logger.debug(method) {"Got response: #{response}"}
      raise UserNotFoundError.new "User with name #{name} was not found (code #{response[:status]})" unless response[:status] == 200
  
      if response[:items].empty? || (user = response[:items].first).empty?
        raise UserNotFoundError.new "User with name #{name} was not found (code #{response[:status]})"
      end
      User.new( User.import(user))
    end
  end
  
  def self.find(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with params #{params}"}

    begin
      response = getCurb(url:@@url + '/api/v1/users', headers: JSON_HEADERS)
      @@logger.debug(method) {"Got response: #{response}"}
      case response[:status]
      when 200
        @@logger.debug(method) {'response[:items].empty? '+(response[:items].empty? ? 'yes' : 'no')}
        raise UsersNotFoundError.new "No users with params #{params} were found" if response[:items].empty?
        retrieved_users = []
        response[:items].each do |user|
          retrieved_users << User.new( User.import(user))
        end
        retrieved_users
      when 404
        raise UsersNotFoundError.new "Users with params #{params} were not found (code 404)"
      else 
        raise UsersNotFoundError.new "Users with params #{params} were not found(code #{response[:code]})"
      end
      #rescue StandardError => e
      #@@logger.error(method) {"Error during processing: #{$!}"}
      #@@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      #[]
    end
  end
  
  def self.find_username_by_token(token)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires the login token' if (token.to_s.empty?)
    @@logger.debug(method) {"entered with token #{token}"}

    translated_token = self.translate_token token    
    translated_token[:preferred_username]
  end
  
  def self.find_email_by_token(token)
    method = LOG_MESSAGE + "##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires the login token' if (token.to_s.empty?)
    @@logger.debug(method) {"entered with token #{token}"}
    
    translated_token = self.translate_token token
    translated_token[:email]
  end

  def self.find_user_type_by_username(username)
    # GET url = URI("http://<address>:<port>/api/v1/users?username=user01")
    # from the response, you can obtain it:
    # [ { "id": "5e1ef7d8-b5cd-4835-8bcb-68b182140fa9", "createdTimestamp": 1492094414797, "username": "user01", "enabled": true, "totp": false, "emailVerified": false, "firstName": "User", "lastName": "Sample", "email": "user.sample@email.com", "attributes": { "userType": [ "developer" ] }, "disableableCredentialTypes": [ "password" ], "requiredActions": [] } ]
    # e.g.: "attributes": { "userType": [ "developer" ] }
    method = "#{LOG_MESSAGE}##{__method__}"
    raise ArgumentError.new __method__.to_s+' requires the user name' if (username.to_s.empty?)
    @@logger.debug(method) {"entered"}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json'} #, 'Authorization'=>'Bearer '+token}

    resp = getCurb(url: @@url+'/api/v1/users?username='+username, params: {}, headers: headers)
    @@logger.debug(method) {"resp=#{resp}"}
    case resp[:status]
    when 200
      @@logger.debug(method) {"resp[:items]=#{resp[:items]}"}
      user = resp[:items].first
      user[:attributes][:userType].first
    when 404
      @@logger.error(method) {"Status 404: username #{username} not found"} 
      raise UserNotFoundError.new "User username #{username} not found"
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      raise UserNotFoundError.new "User not found with the given username"
    end  
  end
  
  def self.public_key
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {'entered'}
    begin
      p_key = getCurb(url: @@url+'/api/v1/public-key', params: {}, headers: {})
      @@logger.debug(method) {"p_key=#{p_key}"}
      p_key
    rescue  => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      raise PublicKeyNotFoundError.new('No public key received from User Management micro-service')
    end
  end
  
  def self.is_admin?(token)
    find_user_type_by_username(find_username_by_token(token)) == 'admin'
  end

  def to_h
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered"}
    self.instance_variables.each_with_object({}) { |var,hash| hash[var[1..-1].to_sym] = self.instance_variable_get(var) }
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
  
  private 
  
  def self.import(original_user)
    # [{"id":"d6ec8201-3a9e-4cd3-a766-1ec93529c9d2","createdTimestamp":1493025941990,"username":"test5","enabled":true,"totp":false,"emailVerified":false,"firstName":"firstName","lastName":"lastName","email":"mail4@mail.com","attributes":{"phone_number":["654654654"],"userType":["customer"]},"disableableCredentialTypes":["password"],"requiredActions":[]}]
    user = {}
    user[:uuid] = original_user[:id]
    if original_user.key? :createdTimestamp
      seconds = original_user[:createdTimestamp]/1000
      user[:created_at] = DateTime.strptime(seconds.to_s,'%s')
    end
    user[:username] = original_user[:username]
    user[:email] = original_user[:email]
    user[:user_type] = original_user[:attributes][:userType].first
    user[:first_name] = original_user[:firstName] if original_user[:firstName]
    user[:last_name] = original_user[:lastName] if original_user[:lastName]
    user[:phone_number] = original_user[:attributes][:phone_number].first if original_user[:attributes][:phone_number]
    user[:instances_private_key] = original_user[:attributes][:instances_private_key]
    user[:instances_public_key] = original_user[:attributes][:instances_public_key]
    user
  end

  def export()
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}
    user = {}
      
    user[:firstName] = first_name if first_name
    user[:lastName] = last_name if last_name
    user[:email] = email if email
    
    # Transform password
    user[:credentials] = [{type: 'password', value: password}]
    
    # Transform user type
    user[:attributes] = {}
    user[:attributes][:userType] = [user_type]
    user[:attributes][:phone_number] = [phone_number] if phone_number
    user[:attributes][:certificate] = [certificate] if certificate
    user[:attributes][:public_key] = [public_key] if public_key
    @@logger.debug(log_message) {"user = #{user}"}
    user
  end
  
  def self.translate_token(token)
    # [23/05/2017, 09:33:28] Daniel Guija: url = URI("http://<address>:<port>/api/v1/userinfo")
    #  request["authorization"] = 'Bearer eyJhbGciOiJSkxX0NpUUhmTm9nIn0...'
    # [23/05/2017, 09:33:46] Daniel Guija: the response is:
    #  {"sub":"8031545e-d4da-4086-8cb2-a417f3460de2","name":"myName myLastName","preferred_username":"tester01","given_name":"myName","family_name":"myLastName","email":"myname.company@email.com"}

    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered with token #{token}"}
    headers = {'Content-type'=>'application/json', 'Accept'=> 'application/json', 'Authorization'=>'Bearer '+token}

    resp = postCurb(url: @@url+'/api/v1/userinfo', body: {}, headers: headers)
    @@logger.debug(method) {"response= #{resp}"}
    case resp[:status]
    when 200
      @@logger.debug(method) {"resp[:items]=#{resp[:items]}"}
      resp[:items]
    when 401
      @@logger.error(method) {"Status 401: token not active"} 
      raise UserTokenNotActiveError.new "User token was not active"
    else
      @@logger.error(method) {"Status #{resp[:status]}"} 
      raise UserNotFoundError.new "User not found with the given token"
    end  
  end
end
