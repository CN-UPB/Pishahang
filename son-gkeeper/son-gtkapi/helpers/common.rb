# Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
# ALL RIGHTS RESERVED.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
# nor the names of its contributors may be used to endorse or promote 
# products derived from this software without specific prior written 
# permission.
# 
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through 
# the Horizon 2020 and 5G-PPP programmes. The authors would like to 
# acknowledge the contributions of their colleagues of the SONATA 
# partner consortium (www.sonata-nfv.eu).
module GtkApiHelper
  
  def content
    #@content ||= Package.decode(package_file_path) || halt 404
  end  

  def json_error(code, message, log_message='')
    content_type :json
    msg = {'error' => { 'code'=>code, 'message'=>message}}.to_json
    if log_message.empty?
      logger.error msg
    else
      logger.error(log_message) {"leaving with #{msg}"}
    end
    halt code, msg
  end

  def valid?(uuid)
    uuid.match /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}/
    uuid == $&
  end
  
  def format_error(backtrace)
    first_line = backtrace[0].split(":")
    "In "+first_line[0].split("/").last+", "+first_line.last+": "+first_line[1]
  end
  
  def keyed_hash(hash)
    Hash[hash.map{|(k,v)| [k.to_sym,v]}]
  end
  
  def build_pagination_headers(url:, limit:, offset:, total:)
    raise ArgumentError.new('A url can not be empty or nil') if (url.empty? || url.nil?)
    raise ArgumentError.new('A (positive) value for total is required') if total < 0
    raise ArgumentError.new('A (positive) value for limit is required') if limit <= 0
    raise ArgumentError.new('A (positive) value for offset is required') if offset < 0
    #raise ArgumentError.new('Offset can not be greater than zero when total is less than limit') if (total < limit && offset > 0)

    logger.debug('GtkApiHelper.build_pagination_headers') {"url: #{url}, limit: #{limit}, offset: #{offset}, total: #{total}"}
    
    last_offset = [(total - 1)/limit, 0].max
    links = []
    links << %(<#{url}?offset=#{offset-1}&limit=#{limit}>; rel="prev") if (offset > 0 && total > limit)
    links << %(<#{url}?offset=#{offset+1}&limit=#{limit}>; rel="next") if (offset+1)*limit < total
    links << %(<#{url}?offset=0&limit=#{limit}>; rel="first")
    links << %(<#{url}?offset=#{last_offset}&limit=#{limit}>; rel="last")
    links.join(",")
  end
  
  def get_token( env, began_at, method, log_message)    
    if (env['HTTP_AUTHORIZATION'].to_s.empty?)
      method.call(labels: {result: "Unauthorized", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s}) if method
      json_error(401, 'Unauthorized: missing authorization header', log_message) 
    end
    logger.debug(log_message) {"entered with request.env['HTTP_AUTHORIZATION']="+env['HTTP_AUTHORIZATION']}

    authorization=env['HTTP_AUTHORIZATION']
    logger.debug(log_message) {'authorization='+authorization}

    bearer_token = authorization.split(' ')
    unless (bearer_token.size == 2 && bearer_token[0].downcase == 'bearer')
      method.call(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s}) if method
      json_error(400, 'Unprocessable entity: authorization header must be "Bearer <token>"', log_message)
    end
    bearer_token[1]
  end
  
  def get_username_by_token( token, began_at, method, log_message)
    begin
      user_name = User.find_username_by_token(token)
    rescue UserTokenNotActiveError
      method.call(labels: {result: "unauthorized", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      json_error 401, "Unauthorized: token #{token} is not active", log_message
    rescue UserNotFoundError
      method.call(labels: {result: "not found", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s})
      json_error 404, "Not found: user with token #{token}", log_message
    end
  end
  
  def get_signature(env, log_message)
    logger.debug(log_message) {"entered with request.env['HTTP_SIGNATURE']=#{env['HTTP_SIGNATURE']}"}
    env['HTTP_SIGNATURE'] ? env['HTTP_SIGNATURE'] : ''
  end

  def require_param(param:, params:, kpi_method: nil, error_message:, log_message:, began_at:)
    log_message = "GtkApiHelper.#{__method__}"
    logger.debug(log_message) {"param=#{param}, params=#{params}"}
    if (!params.key?(param) || params[param].to_s.empty?)
      kpi_method.call(labels: {result: "bad request", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 400, error_message+' is missing', log_message
    end 
  end

  def validate_user_authorization(token:, action: '', uuid:, path:, method:, kpi_method: nil, began_at:, log_message: '')
    unless User.authorized?(token: token, params: {path: path, method: method})
      kpi_method.call(labels: {result: "forbidden", uuid: uuid, elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 403, 'Forbidden: user could not be authorized to '+action, log_message
    end
  end
  
  def validate_uuid(uuid:, kpi_method: nil, began_at:, log_message: '')
    uuid.match /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}/
    unless uuid == $&
      kpi_method.call(labels: {result: "bad request", uuid: uuid, elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 404, "UUID #{uuid} not valid", log_message
    end
  end
  
  def validate_element_existence(uuid:, element:, name:, kpi_method:, began_at:, log_message:)
    log_message = "GtkApiHelper##{__method__}"
    logger.debug(log_message) {"Entered with uuid=#{uuid}, element=#{element}, name=#{name}"}
    if element[:count]==0 || element[:items].empty?
      kpi_method.call(labels: {result: "not found", uuid: uuid, elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 404, name+" "+uuid+" not found", log_message
    end
  end
  
  def validate_collection_existence(collection:, name:, kpi_method:, began_at:, log_message:)
    log_message = "GtkApiHelper##{__method__}"
    logger.debug(log_message) {"Entered with collection=#{collection}, name=#{name}"}
    if collection && collection[:status] && collection[:status] != 200
      kpi_method.call(labels: {result: "not found", uuid: '', elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 404, "No #{name} were found", log_message
    end
  end
  
  def validate_ownership_and_licence(element:, user_name:, kpi_method:, began_at:, log_message:)
    if element[:licence].to_s.empty? || element[:licence][:type] == 'public' || element[:username] == user_name
      # public by default or explicitely public or owner
      return
    end

    user_uuid = User.find_by_name(user_name).uuid
    licenced_elements = LicenceManagerService.find({service_uuid: element[:uuid], user_uuid: user_uuid})
    if licenced_elements[:items].empty?
      # there's no licence for this element for this username
      kpi_method.call(labels: {result: "forbidden", uuid: element[:uuid], elapsed_time: (Time.now.utc-began_at).to_s}) if kpi_method
      json_error 403, 'Package/service/function '+element[:uuid]+' is private, not owned and not licensed to user '+user_name, log_message
    end
  end  
  
  def validate_function_ownership(token:, instance_uuid:, kpi_method:, began_at:, log_message:)
    log_message = "GtkApiHelper##{__method__}"
    user_name = User.find_username_by_token(token)
    record = RecordManagerService.find_record_by_uuid(kind: 'functions', uuid: instance_uuid)
    logger.debug(log_message) {"record=#{record}"}
    #validate_element_existence(uuid: instance_uuid, element: record[:items], name: 'Record', kpi_method: kpi_method, began_at: began_at, log_message: log_message)
    descriptor = FunctionManagerService.find_by_uuid(record[:items][:descriptor_reference])
    logger.debug(log_message) {"descriptor=#{descriptor}"}
    validate_element_existence(uuid: instance_uuid, element: descriptor, name: 'Function', kpi_method: kpi_method, began_at: began_at, log_message: log_message)
    validate_ownership_and_licence(element: descriptor[:items], user_name: user_name, kpi_method: kpi_method, began_at: began_at, log_message: log_message)
  end

  def enhance_collection(collection:, user:, keys_to_delete:)
    log_message = "GtkApiHelper##{__method__}"
    logger.debug(log_message) {'collection='+collection.inspect}
    return collection if (collection.empty? || collection.first.empty?)

    collection.each do |element|
      logger.debug(log_message) {'element='+element.inspect}
      
      next unless element.key?(:nsd)
      
      licences=element[:nsd][:licences]
      # No licence implies 'public' licence
      if licences.to_s.empty? || licences[0][:type] == 'public'
        logger.debug(log_message) {'user licence set to "public"'}
        element[:user_licence] = 'public'
        next
      end

      # it's private
      if element[:username] == user
        logger.debug(log_message) {'user licence set to "owned"'}
        element[:user_licence] = 'owned'
        next
      end
      
      user_uuid = User.find_by_name(user).uuid
      licenced_collection = LicenceManagerService.find({service_uuid: element[:uuid], user_uuid: user_uuid})
      logger.debug(log_message) {"licenced_collection=#{licenced_collection}"}
      
      
      if licenced_collection[:items].empty?
        # when the user needs to buy, we do not pass the juice to him
        keys_to_delete[:sub_keys].each { |key| element[keys_to_delete[:main_key]].delete(key)}
    
        logger.debug(log_message) {'user licence set to "to buy"'}
        element[:user_licence] = 'to buy'
        next
      end
      licenced_collection[:items].each do |licenced_element|
        logger.debug(log_message) {"licenced_element=#{licenced_element}"}
        element[:user_licence] = 'licensed' if licenced_element[:service_uuid] == element[:uuid]
        logger.debug(log_message) {"user licence set to \"#{element[:user_licence]}\""}
      end
    end
    logger.debug(log_message) {"returning collection=#{collection}"}
    collection
  end
end
