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
class LicenceManagerService < ManagerService
  
  JSON_HEADERS = { 'Accept'=> 'application/json', 'Content-Type'=>'application/json'}
  LOG_MESSAGE = 'GtkApi::' + self.name
  LICENCES_URL = '/api/v1/licenses/'
  
  def self.config(url:, logger:)
    method = LOG_MESSAGE + "#config(url=#{url})"
    raise ArgumentError.new('LicenceManagerService can not be configured with nil or empty url') if url.to_s.empty?
    @@url = url
    @@logger = logger
    @@logger.debug(method) {'entered'}
  end
  
  def self.valid?(params)
    # service_uuid, string, mandatory
    # user_uuid, string, mandatory
    # license_uuid, string, mandatory
    # license_type, string, mandatory
    # description, string
    # validation_url, string
    # status, string, mandatory

    
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered: params=#{params}"}
    #raise ArgumentError, 'User must be valid' unless User.valid? params[:user_uuid]
    raise ArgumentError, 'Service must be valid' unless ServiceManagerService.valid? params[:service_uuid]
    @@logger.debug(method) {"Leaving with valid licence data service #{params[:service_uuid]} and user #{params[:user_uuid]}"}
    true
  end
  
  def self.create(params)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered: params=#{params}"}
    #headers = {'Content-Type'=>'application/x-www-form-urlencoded'}

    begin
      self.valid?(params)
      params[:description] = 'Default description'
      licence = postCurb(url: @@url+LICENCES_URL, body: params) #, headers: headers)
      @@logger.debug(method) {"licence=#{licence}"}
      
      #D, [2017-09-26T08:44:27.147075 #9] DEBUG -- GtkApi::LicenceManagerService#create: licence={:status=>201, :count=>1, :items=>{:status_code=>201, :data=>{:status=>"ACTIVE", :validation_url=>"http://example.com", :description=>"Default description", :license_uuid=>"2a3d5ed4-dd0b-4cee-99d8-ed0c3115c45e", :service_uuid=>"2044a18c-2a85-4420-b68d-e748e9782d48", :license_type=>"PRIVATE", :user_uuid=>"f3806ea0-32b6-43b9-b4b5-8d2237adb7b5"}, :description=>"License successfully created", :error=>""}, :message=>"OK"}
      
      case licence[:status]
      when 200, 201
        {status: 201, count: 1, items: licence[:items][:data], message: 'Created'}
      else
        {status: licence[:status], count: 0, items: [], message: licence[:error]}
      end
    rescue  ArgumentError => ae
      {status: 422, count: 0, items:[], message: 'Unprocessable Entity'}
    rescue => e
      @@logger.error(method) {"Error during processing: #{$!}"}
      @@logger.error(method) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
      {error: 'Licence type not created', licence: e.backtrace}
    end
  end

  def self.find_by_uuid(uuid)
    method = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(method) {"entered: uuid=#{uuid}"}

    licence = getCurb(url: @@url + LICENCES_URL + uuid + '/', params: {}, headers: JSON_HEADERS)
    @@logger.debug(method) {"licence=#{licence}"}
    case licence[:status]
    when 200
      # D, [2017-09-26T14:20:43.950053 #6] DEBUG -- GtkApi::LicenceManagerService#find_by_uuid: licence={:status=>200, :count=>1, :items=>{:status_code=>200, :data=>{:status=>"ACTIVE", :validation_url=>"http://example.com", :description=>"Default description", :license_uuid=>"bf799b2b-91a6-4824-9f2c-570baec38cda", :service_uuid=>"b21cf770-e99d-4f61-8dde-96ad381dc08e", :license_type=>"PRIVATE", :user_uuid=>"8d6fcbcb-3fa7-4607-b7f7-d687bde35dab"}, :description=>"License is valid", :error=>""}, :message=>"OK"}
      {status: 200, count: 1, items: licence[:items][:data], message: "OK"}
    when 400
    when 404
      {status: licence[:status], count: 0, items: [], message: "Not Found"}
    else
      {status: licences[:status], count: 0, items: [], message: "Error"}
    end
  end
    
  def self.find(params)
    log_message = LOG_MESSAGE + "##{__method__}"
    @@logger.debug(log_message) {"entered: params=#{params}"}
    licences = getCurb(url: @@url + LICENCES_URL, params: params, headers: JSON_HEADERS)
    @@logger.debug(log_message) {"licences=#{licences}"}
    case licences[:status]
    when 200
      {status: 200, count: licences[:items][:data][:licenses].count, items: licences[:items][:data][:licenses], message: "OK"}
    when 400
    when 404
      {status: 200, count: 0, items: [], message: "OK"}
    else
      {status: licences[:status], count: 0, items: [], message: "Error"}
    end
  end
  
  def self.began_at
    log_message=LOG_MESSAGE+"##{__method__}"
    @@logger.debug(log_message) {'entered'}    
    response = getCurb(url: @@url + '/began_at')
    @@logger.debug(log_message) {"response=#{response}"}
    response
  end
  
  #def user
  #  @user ||= User.find(params[:user_id]) || halt(404)
  #end

  #def service
   # @service ||= user.services.find(params[:service_id]) || halt(404)
  #end

  #def task_date
  #  @task_date ||= Date.iso8601(params[:task_date])
  #rescue ArgumentError
  #  halt 400
  #end

  #def tasks
  #  @tasks ||= project.tasks_due_on(task_date)
  #end
  
  # now use this with
  #get '/users/:user_id/projects/:project_id/tasks-due-on/:task_date' do
  #  tasks.to_json
  #end
end
