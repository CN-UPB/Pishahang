##
## Copyright (c) 2015 SONATA-NFV
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
## Neither the name of the SONATA-NFV
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).

require 'json'
require 'sinatra'
require 'net/http'
require 'net/ssh'
require 'openssl'
require_relative '../helpers/init'

# Adapter-Keycloak API class
class Keycloak < Sinatra::Application

  post '/register/user' do
    logger.debug 'Adapter: entered POST /register/user'
    # Return if content-type is not valid
    logger.info "Content-Type is " + request.media_type
    json_error(415, 'Only Content-type: application/json is supported') unless (request.content_type == 'application/json')

    # Compatibility support for JSON content-type
    # Parses and validates JSON format
    form, errors = parse_json(request.body.read)
    halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
    unless form.key?('enabled')
      form = form.merge({'enabled'=> true})
    end

    # pkey and cert will be nil if they does not exist
    begin
      pkey = form['attributes']['public_key']
      form['attributes'].delete('public_key')

      cert = form['attributes']['certificate']
      form['attributes'].delete('certificate')

      if pkey || cert
        if form['attributes']['userType'].is_a?(Array)
          if form['attributes']['userType'].include?('developer')
            # proceed
          else
            logger.debug 'Adapter: leaving POST /register/user with userType error'
            json_error(400, 'Registration failed! Only developer role support public_key attribute')
          end
        elsif form['attributes']['userType']
          case form['attributes']['userType']
            when 'developer'
              # proceed
            else
              logger.debug 'Adapter: leaving POST /register/user with userType error'
              json_error(400, 'Bad userType! Only developer role support public_key attribute')
          end
        end
      end
    rescue
      logger.error 'Adapter: Failed to read registration JSON object'
      halt json_error(400, 'Bad registration form')
    end

    instances_private_key = nil
    instances_public_key = nil

    if form['attributes']['userType'].is_a?(Array)
      if form['attributes']['userType'].include?('admin')
        # Return if Authorization is invalid
        logger.debug 'Adapter: leaving POST /register/user '
        halt 400 unless request.env["HTTP_AUTHORIZATION"]
        user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
        unless user_token
          logger.debug 'Adapter: Failed due to access token required'
          json_error(400, 'Access token is not provided')
        end

        # Validates the token
        logger.debug "Evaluating token=#{user_token}"
        code, user_info = userinfo(user_token)
        if code != '200'
          halt code.to_i, {'Content-type' => 'application/json'}, user_info
        end
        logger.debug "Adapter: User info: #{user_info}"

        # Allow custom name service-account-$
        unless user_info['username'] == 'service-account-adapter'
          res, code = token_validation(user_token)
          logger.debug "Adapter: Token validation is #{res.to_s}"
          json_error(400, res.to_s) unless code == '200'

          result = is_active?(res)
          logger.debug "Adapter: Token status is #{result.to_s}"
          json_error(401, 'Token not active') unless result
        end

        logger.debug "Adapter: Querying user info: #{parse_json(user_info)[0]['sub']}"
        code, user_data = get_user(parse_json(user_info)[0]['sub'])
        if code != '200'
          halt code.to_i, {'Content-type' => 'application/json'}, user_data
        end
        user_data = parse_json(user_data)[0]

        unless user_data['attributes']['userType'].include?('admin')
          logger.debug 'Adapter: leaving POST /register/user with userType error'
          json_error(400, 'Registration failed! Only admin users can register a new admin')
        end

      elsif form['attributes']['userType'].include?('customer')
        # Randomly generate a instantiation-keypair to store in the database
        key = OpenSSL::PKey::RSA.new 2048
        instances_private_key = key.to_pem
        # instances_public_key = key.public_key.to_pem
        type = key.ssh_type
        data = [ key.to_blob ].pack('m0')

        instances_public_key = "#{type} #{data}"  # openssh_format
      end
    end

    logger.info "Registering new user"
    user_id, error_code, error_msg = register_user(form)

    if user_id.nil?
      if error_code == 409
        halt error_code, {'Content-type' => 'application/json'}, error_msg
      end
      delete_user(form['username'])
      halt error_code, {'Content-type' => 'application/json'}, error_msg
    end

    form['attributes']['userType'].each { |attr|
      logger.debug "Adding new user to groups"
      res_code, res_msg = set_user_groups(attr, user_id)
      if res_code != 204
        delete_user(form['username'])
        halt res_code.to_i, {'Content-type' => 'application/json'}, res_msg
      end
      logger.debug "Adding new user roles"
      res_code, res_msg = set_user_roles(attr, user_id)
      if res_code != 204
        delete_user(form['username'])
        halt res_code.to_i, {'Content-type' => 'application/json'}, res_msg
      end
    }

    # Check if username already exists in the database
    begin
      user = Sp_user.find_by({ 'username' => form['username']})
      delete_user(form['username'])
      json_error 409, 'Duplicated username'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end
    # Check if user ID already exists in the database
    begin
      user = Sp_user.find_by({ '_id' => user_id })
      delete_user(form['username'])
      json_error 409, 'Duplicated user ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Save to DB
    begin
      new_user = {}
      new_user['_id'] = user_id
      new_user['username'] = form['username']
      new_user['public_key'] = pkey
      new_user['certificate'] = cert
      new_user['instances_private_key'] = instances_private_key
      new_user['instances_public_key'] = instances_public_key
      user = Sp_user.create!(new_user)
    rescue Moped::Errors::OperationFailure => e
      delete_user(form['username'])
      json_error 409, 'Duplicated user ID' if e.message.include? 'E11000'
    end

    logger.debug "Database: New user #{form['username']} with ID #{user_id} has been added"
    logger.info "New user #{form['username']} has been registered"
    response = {'username' => form['username'], 'userId' => user_id.to_s, 'created_at' => user['created_at']}
    halt 201, {'Content-type' => 'application/json'}, response.to_json
  end

  post '/login/user' do
    logger.debug 'Adapter: entered POST /login/user'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    pass = request.env["HTTP_AUTHORIZATION"].split(' ').last
    plain_pass  = Base64.decode64(pass)

    # plain_pass = plain_pass.to_s.force_encoding('UTF-8')
    # puts  "PLAIN", plain_user_pass.split(':').first
    # puts  "PLAIN", plain_user_pass.split(':').last
    username = plain_pass.split(':').first # params[:username]
    password = plain_pass.split(':').last # params[:password]

    logger.info "User #{username} has accessed to log-in"

    credentials = {"type" => "password", "value" => password.to_s}
    log_code, log_msg = login(username, credentials)
    if log_code != 200
      logger.info "User #{username} has failed to log-in"
      logger.debug 'Adapter: exit POST /login/user'
      halt log_code, {'Content-type' => 'application/json'}, log_msg
    end
    logger.info "User #{username} has logged-in succesfully"
    logger.debug 'Adapter: exit POST /login/user'
    halt log_code, {'Content-type' => 'application/json'}, log_msg
  end

  post '/userinfo' do
    logger.debug 'Adapter: entered POST /userinfo'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
    unless user_token
      json_error(400, 'Access token is not provided')
    end

    # Validates the token
    logger.debug "Evaluating token= #{user_token}"
    res, code = token_validation(user_token)
    if code == '200'
      result = is_active?(res)
      case result
        when false
          json_error(401, 'Token not active')
        else
          code, user_info = userinfo(user_token)
          halt code.to_i, {'Content-type' => 'application/json'}, user_info
      end
    else
      json_error(400, res.to_s)
    end
  end

  get '/userid' do
    logger.debug 'Adapter: entered POST /userid'
    # Return if Authorization is invalid
    halt 400 unless request.env["HTTP_AUTHORIZATION"]

    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
    unless user_token
      json_error(400, 'Access token is not provided')
    end

    # Validate token
    res, code = token_validation(user_token)
    token_contents = JSON.parse(res)
    if code == '200'
      result = is_active?(res)
      case result
        when false
          json_error(401, 'Token not active')
        else
          # continue
      end
    else
      json_error(400, res.to_s)
    end

    keyed_params = keyed_hash(params)
    if keyed_params.include? :username
      user_id = get_user_id(keyed_params[:username])
      response = {'userId' => user_id}
      halt 200, {'Content-type' => 'application/json'}, response.to_json
    elsif token_contents['sub']
      response = {'userId' => token_contents['sub']}
      halt 200, {'Content-type' => 'application/json'}, response.to_json
    else
      json_error(400, 'Bad token or incorrect username')
    end
  end

  post '/logout' do
    logger.debug 'Adapter: entered POST /logout'
    halt 400 unless request.env["HTTP_AUTHORIZATION"]
    user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last

    unless user_token
      json_error(400, 'Access token is not provided')
    end

    # Validate token
    res, code = token_validation(user_token)

    if code == '200'
      result = is_active?(res)
      case result
        when false
          json_error(401, 'Token not active')
        else
          # continue
      end
    else
      halt 400, {'Content-type' => 'application/json'}, res
    end

    log_code = logout(user_token, user=nil, realm=nil)
    halt log_code
  end

  get '/users' do
    # This endpoint allows queries for the next fields:
    # search, lastName, firstName, email, username, first, max
    logger.debug 'Adapter: entered GET /users'
    logger.debug "Adapter: Query parameters #{params}"
    queriables = %w(id lastName firstName email username)

    logger.debug "Adapter: Optional query #{queriables}"

    if params.length > 1
      json_error(400, 'Too many arguments')
    end

    if params.first
      k, v = params.first
      unless queriables.include? k
        json_error(400, 'Bad query')
      end
    else
      k, v = nil, nil
    end
    case k
      when 'id'
        code, user_data = get_user(v)
        if code.to_i != 200
          halt 200, {'Content-type' => 'application/json'}, [].to_json
        end
        reg_users = [JSON.parse(user_data)]
        logger.debug "Adapter: get_user value #{reg_users}"
      else
        reg_users = JSON.parse(get_users(params))
    end

    # reg_users is an array of hashes
    new_reg_users = []
    reg_users.each do |user_data|
      user_id = user_data['id']
      # call mongoDB to receive user_extra_data
      begin
        user_extra_data = Sp_user.find_by({ '_id' => user_id })
        user_extra_data = user_extra_data.to_json(:except => [:_id, :id, :username, :updated_at, :created_at])
        user_extra_data = {'attributes' => parse_json(user_extra_data)[0]}
        merged_user_data = user_data.deep_merge(user_extra_data)
        new_reg_users << merged_user_data
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.debug 'Adapter: Error caused by DocumentNotFound in user database'
        new_reg_users << user_data
      end
    end

    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    new_reg_users = apply_limit_and_offset(new_reg_users, offset=params[:offset], limit=params[:limit])
    halt 200, {'Content-type' => 'application/json'}, new_reg_users.to_json
  end

  put '/users' do
    # This endpoint allows queries for the next fields:
    # id username
    logger.debug 'Adapter: entered PUT /users'
    logger.debug "Adapter: query parameters #{params}"
    queriables = %w(id username)
    not_updatables = %w(id username) # removed email
    logger.debug "Adapter: Optional query #{queriables}"
    json_error(400, 'Bad query') if params.empty?
    if params.length > 1
      json_error(400, 'Too many arguments')
    end

    k, v = params.first
    unless queriables.include? k
      logger.debug 'Adapter: Query includes forbidden parameter'
      json_error(400, 'Bad query')
    end
    form, errors = parse_json(request.body.read)

    logger.debug "Adapter: Received User-data: #{form}"

    pkey = nil
    cert = nil
    new_creds = {}

    # Check form keys
    form.each { |att, val|
      if not_updatables.include? att
        json_error(400, 'Bad query')
      end

      case att
        when 'attributes'
          begin
            pkey = form['attributes']['public_key']
            form['attributes'].delete('public_key')
          rescue
            # pkey = nil
          end
          begin
            cert = form['attributes']['certificate']
            form['attributes'].delete('certificate')
          rescue
            # cert = nil
          end
        when 'credentials'
          begin
            new_creds['credentials'] = form['credentials']
            form.delete('credentials')
          rescue
            logger.debug 'Adapter: leaving PUT /users'
            json_error(400, 'Password update failed')
          end
        else
      end
    }

    case k
      when 'id'
        code, @msg = update_user(nil, v, form) # @msg should have user_id
      when 'username'
        code, @msg = update_user(v, nil, form)
      else
        code = 400
        json_error(400, 'Bad query')
    end

    if new_creds['credentials']
      logger.debug 'Adapter: Updating user credentials'
      # handle password updates
      # use PUT /auth/admin/realms/master/users/{id}/reset-password
      # {id} is the user id in keycloak (not the login)

      # sample body:
      # { "type": "password", "temporary": false, "value": "my-new-password" }
      user_id, code, msg = set_password(@msg, new_creds)
      if code.nil? # update requiredActions to blank
        user_id, code, msg = clear_actions(@msg)
        logger.debug 'Adapter: User credentials successfully updated'
      end
    end

    if form['attributes']['userType'].is_a?(Array)
      if form['attributes']['userType'].include?('developer')
        u_type = 'developer'
      elsif form['attributes']['userType'].include?('customer')
        u_type = 'customer'
      else
        logger.debug 'Adapter: leaving PUT /users'
        halt 204
      end
    elsif form['attributes']['userType']
      case form['attributes']['userType']
        when 'developer'
          u_type = 'developer'
        when 'customer'
          u_type = 'customer'
        else
          logger.debug 'Adapter: leaving PUT /users'
          halt 204
      end
    else
      # Check userType in user stored data
      u_code, u_data = get_user(@msg)
      if u_code.to_i != 200
        json_error(400, 'Update failed')
      else
        if u_data['attributes']['userType'].is_a?(Array)
          if u_data['attributes']['userType'].include?('developer')
            # proceed
          elsif form['attributes']['userType'].include?('customer')
            u_type = 'customer'
          else
            logger.debug 'Adapter: leaving PUT /users'
            halt 204
          end
        elsif u_data['attributes']['userType']
          case u_data['attributes']['userType']
            when 'developer'
              u_type = 'developer'
            when 'customer'
              u_type = 'customer'
            else
              logger.debug 'Adapter: leaving PUT /users'
              halt 204
          end
        end
      end
    end

    if u_type == 'developer'
      begin
        user_extra_data = Sp_user.find_by({ '_id' => @msg })
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.debug 'Adapter: Error caused by DocumentNotFound in user database'
        halt 204, {'Content-type' => 'application/json'}, 'Updated with DocumentNotFound error'
      end
      case pkey
        when nil
        else
          begin
            user_extra_data.update_attributes(public_key: pkey)
          rescue Moped::Errors::OperationFailure => e
            json_error(400, e)
          end
      end
      case cert
        when nil
        else
          begin
            user_extra_data.update_attributes(certificate: cert)
          rescue Moped::Errors::OperationFailure => e
            json_error(400, e)
          end
      end
      logger.debug 'Adapter: leaving PUT /users'
      halt 204, {'Content-type' => 'application/json'}, @msg

    elsif u_type == 'customer'
      begin
        user_extra_data = Sp_user.find_by({ '_id' => @msg })
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.debug 'Adapter: Error caused by DocumentNotFound in user database'
        halt 204, {'Content-type' => 'application/json'}, 'Updated with DocumentNotFound error'
      end

      # Should handle usertype transitions such developer - customer/customer - developer ?
      # Randomly generate a instantiation-keypair to store in the database
      key = OpenSSL::PKey::RSA.new 2048
      instances_private_key = key.to_pem
      type = key.ssh_type
      data = [ key.to_blob ].pack('m0')
      instances_public_key = "#{type} #{data}"  # openssh_format

      begin
        user_extra_data.update_attributes(instances_private_key: instances_private_key)
        user_extra_data.update_attributes(instances_public_key: instances_public_key)
      rescue Moped::Errors::OperationFailure => e
        json_error(400, e)
      end

      logger.debug 'Adapter: leaving PUT /users'
      halt 204, {'Content-type' => 'application/json'}, @msg
    end
    halt 204, {'Content-type' => 'application/json'}, @msg
  end

  delete '/users' do
    # This endpoint allows queries for the next fields:
    # search, lastName, firstName, email, username, first, max
    logger.debug 'Adapter: entered DELETE /users'
    logger.debug "Adapter: required query #{params}"
    queriables = %w(id username)

    logger.debug "Adapter: Available queriables #{queriables}"

    json_error(400, 'Bad query') if params.empty?
    if params.length > 1
      json_error(400, 'Too many arguments')
    end

    k, v = params.first
    unless queriables.include? k
      json_error(400, 'Bad query')
    end

    case k
      when 'id'
        code, msg = delete_user_by_id(nil, v)
      when 'username'
        code, msg = delete_user_by_id(v, nil)
      else
        json_error(400, 'Bad query')
    end
    if code.nil?
      begin
        user_extra_data = Sp_user.find_by({ '_id' => msg })
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.debug 'Adapter: Error caused by DocumentNotFound in user database'
        halt 204
      end
      user_extra_data.destroy
      logger.debug 'Adapter: leaving DELETE /users'
      halt 204
    end
    halt code
  end

  get '/sessions/users' do
    # Get all user sessions
    # Returns a list of user sessions associated with the adapter client
    # GET /admin/realms/{realm}/clients/{id}/user-sessions
    logger.debug 'Adapter: entered GET /sessions/users'
    adapter_id = get_client_id('adapter')
    ses_code, ses_msg = get_sessions('user', adapter_id)

    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    ses_msg = apply_limit_and_offset(JSON.parse(ses_msg), offset=params[:offset], limit=params[:limit])
    halt ses_code.to_i, {'Content-type' => 'application/json'}, ses_msg.to_json
  end

  get '/sessions/users/:username/?' do
    # Get user sessions
    # Returns a list of sessions associated with the user
    unless params[:username].nil?
      logger.debug "Adapter: entered GET /sessions/users/#{params[:username]}"

      user_id = get_user_id(params[:username])
      if user_id.nil?
        json_error(404, 'Username not found')
      end
      ses_code, ses_msg = get_user_sessions(user_id)

      params['offset'] ||= DEFAULT_OFFSET
      params['limit'] ||= DEFAULT_LIMIT
      ses_msg = apply_limit_and_offset(JSON.parse(ses_msg), offset=params[:offset], limit=params[:limit])
      halt ses_code.to_i, {'Content-type' => 'application/json'}, ses_msg.to_json
    end
    logger.debug 'Adapter: leaving GET /sessions/users/ with no username specified'
    json_error 400, 'No username specified'
  end

  put '/signatures/:username/?' do
    # Update user public key and certificate attributes
    unless params[:username].nil?
      logger.debug "Adapter: entered PUT /signatures/#{params[:username]}"

      json_error(400, 'Authorization header not set') unless request.env["HTTP_AUTHORIZATION"]
      user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
      unless user_token
        json_error(400, 'Access token is not provided')
      end

      # Validate token
      res, code = token_validation(user_token)
      token_contents = JSON.parse(res)

      if code == '200'
        result = is_active?(res)
        case result
          when false
            json_error(401, 'Token not active')
          else
            # continue
        end
      else
        json_error(400, res.to_s)
      end
      logger.debug "Adapter: Token contents #{token_contents}"
      logger.debug "Adapter: Username #{params[:username]}"

      if token_contents['username'].to_s == params[:username].to_s
        logger.debug "Adapter: #{params[:username]} matches Access Token"
        # Translate from username to User_id
        user_id = get_user_id(params[:username])
        if user_id.nil?
          json_error(404, 'Username not found')
        end
        logger.info "Content-Type is " + request.media_type
        halt 415 unless (request.content_type == 'application/json')

        form, errors = parse_json(request.body.read)
        halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors

        halt 400 unless form.is_a?(Hash)
        unless form.key?('public_key')
          json_error(400, 'Developer public key not provided')
        end

        unless form.key? ('certificate')
          form['certs'] = nil
        end

        # Get user public key and certificate
        # Check if user ID already exists in the database
        begin
          user = Sp_user.find_by({ '_id' => user_id })
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error(404, 'Username not found')
        end

        # Add new son-package attribute fields
        begin
          user.update_attributes(public_key: form['public_key'], certificate: form['certificate'])
        rescue Moped::Errors::OperationFailure => e
          json_error(400, 'Update failed')
        end
      else
        json_error(400, 'Provided username does not match with Access Token')
      end
      halt 204 # 'User signature successfully updated'
    end
    logger.debug 'Adapter: leaving PUT /signatures/ with no username specified'
    json_error(400, 'No username specified')
  end

  put '/attributes/:username/?' do
    # Update user account attributes
    unless params[:username].nil?
      logger.debug "Adapter: entered PUT /attributes/#{params[:username]}"

      user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
      unless user_token
        json_error(400, 'Access token is not provided')
      end

      # Validate token
      res, code = token_validation(user_token)
      logger.debug "Adapter: Token validation is #{res.to_s}"
      json_error(400, res.to_s) unless code == '200'
      token_contents = JSON.parse(res)

      result = is_active?(res)
      logger.debug "Adapter: Token status is #{result.to_s}"
      json_error(401, 'Token not active') unless result

      logger.debug "Adapter: Token contents #{token_contents}"
      logger.debug "Adapter: Username #{params[:username]}"

      if token_contents['username'].to_s == params[:username].to_s
        logger.debug "Adapter: #{params[:username]} matches Access Token"
        # Translate from username to User_id
        user_id = get_user_id(params[:username])
        if user_id.nil?
          json_error 404, 'Username not found'
        end
        logger.info "Content-Type is " + request.media_type
        halt 415 unless (request.content_type == 'application/json')

        form, errors = parse_json(request.body.read)
        halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors

        halt 400 unless form.is_a?(Hash)
        unless form.key?('public_key')
          json_error 400, 'Developer public key not provided'
        end

        # Get user attributes
        # user_data = get_users({'id' => user_id})
        # parsed_user_data = JSON.parse(user_data)[0]
        # logger.debug "parsed_user_data #{parsed_user_data}"

        # DEVELOPER'S PUBLIC KEY AND CERTIFICATE WILL BE STORED IN MONGODB
        # user_attributes = parsed_user_data['attributes']
        # logger.debug "user_attributes #{user_attributes}"
        # unless user_attributes['userType'][0] == 'developer'
        #   json_error 400, 'User is not a developer'
        # end

        # Update attributes
        # new_attributes = {"public-key" => [form['public-key']], "certificate" => [form['certificate']]}
        # logger.debug "new_attributes #{new_attributes}"
        # new_user_attributes = user_attributes.merge(new_attributes)
        # logger.debug "new_user_attributes #{new_user_attributes}"
        # upd_code, upd_msg = update_user_pkey(user_id, new_user_attributes)
        # else
        # json_error 400, 'Provided username does not match with Access Token'
      end
      # halt upd_code.to_i, {'Content-type' => 'application/json'}, upd_msg
    end
    logger.debug 'Adapter: leaving PUT /attributes/ with no username specified'
    json_error 400, 'No username specified'
  end

  put '/usertypes/:username/?' do
    # Update user account usertypes and roles
    unless params[:username].nil?
      logger.debug "Adapter: entered PUT /usertypes/#{params[:username]}"

      user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
      unless user_token
        json_error(400, 'Access token is not provided')
      end

      # Validate token
      res, code = token_validation(user_token)
      logger.debug "Adapter: Token validation is #{res.to_s}"
      json_error(400, res.to_s) unless code == '200'
      token_contents = JSON.parse(res)

      result = is_active?(res)
      logger.debug "Adapter: Token status is #{result.to_s}"
      json_error(401, 'Token not active') unless result

      logger.debug "Adapter: Token contents #{token_contents}"
      logger.debug "Adapter: Username #{params[:username]}"

      if token_contents['username'].to_s == params[:username].to_s
        logger.debug "Adapter: #{params[:username]} matches Access Token"
        # Translate from username to User_id
        user_id = get_user_id(params[:username])
        json_error 404, 'Username not found' if user_id.nil?

        logger.info "Content-Type is " + request.media_type
        halt 415 unless (request.content_type == 'application/json')

        form, errors = parse_json(request.body.read)
        halt 400, {'Content-type' => 'application/json'}, errors.to_json if errors
        halt 400 unless form.is_a?(Hash)
        json_error 400, 'Usertype not provided' unless form.key?('userType')

        # Get user attributes
        user_data = get_users({'id' => user_id})
        user_data = JSON.parse(user_data)[0]
        logger.debug "parsed_user_data #{user_data}"

        if form['userType'].is_a?(Array)
          form['userType'].each { |k|
            user_data['attributes']['userType'] << k
          }
        else
          user_data['attributes']['userType'] << form['userType']
        end

        # Update attributes
        code, msg = update_user(params[:username], nil, user_data)
        logger.debug "Update_attributes code #{code}"
        logger.debug "Update_attributes user_id=#{msg}"
        json_error(code, msg) unless code.nil?

        # Update roles
        form['userType'] = [form['userType']] unless form['userType'].is_a?(Array)
        form['userType'].each { |role|
          # puts "SETTING_USER_ROLE", attr
          logger.debug "Adding new user to groups"
          res_code, res_msg = set_user_groups(role, user_id)
          if res_code != 204

            delete_user(form['username'])

            halt res_code.to_i, {'Content-type' => 'application/json'}, res_msg
          end
          # Update groups
          logger.debug "Adding new user roles"
          res_code, res_msg = set_user_roles(role, user_id)
          if res_code != 204

            delete_user(form['username'])

            halt res_code.to_i, {'Content-type' => 'application/json'}, res_msg
          end
        }
      end
      logger.debug 'Adapter: leaving PUT /attributes/ with invalid username'
      json_error 400, 'Provided username do not match token owner'
    end
    logger.debug 'Adapter: leaving PUT /attributes/ with no username specified'
    json_error 400, 'No username specified'
  end

  delete '/usertypes/:username/?' do
    # Delete user account usertypes and roles
    unless params[:username].nil?
      logger.debug "Adapter: entered DELETE /usertypes/#{params[:username]}"

      user_token = request.env["HTTP_AUTHORIZATION"].split(' ').last
      unless user_token
        json_error(400, 'Access token is not provided')
      end
    end
  end

  # ADD ADMIN USERS OPERATIONS
  get '/console' do
    # ADMIN OPS http://sp.int3.sonata-nfv.eu:5601/auth/admin/sonata/console/
    redirect "http://#{@@address.to_s}:#{@@port.to_s}/#{@@uri.to_s}/auth/admin/#{@@realm_name}/console/"
  end
end