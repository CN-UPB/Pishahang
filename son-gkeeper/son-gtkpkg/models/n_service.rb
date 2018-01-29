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
require 'tempfile'
require 'pp'

class NService
  
  attr_accessor :descriptor
  CLASS = self.name
  
  def initialize(catalogue, folder, username)
    @catalogue = catalogue
    @url = @catalogue.url+'/network-services'
    @descriptor = {}
    @username = username
    if folder
      @folder = File.join(folder, "service_descriptors") 
      FileUtils.mkdir @folder unless File.exists? @folder
    end
  end
  
  def to_file(content)
    GtkPkg.logger.debug "NService.to_file(#{content})"
    filename = content['name'].split('/')[-1]
    File.open(File.join( @folder, filename), 'w') {|f| YAML.dump(content, f) }
  end
  
  def from_file(filename)
    GtkPkg.logger.debug "NService.from_file(#{filename})"
    @descriptor = YAML.load_file filename
    GtkPkg.logger.debug "NService.from_file: content = #{@descriptor}"
    @descriptor
  end
  
  def store()
    GtkPkg.logger.debug "NService.store(#{@descriptor})"
    service = duplicated_service?()
    service = @catalogue.create(@descriptor, @username) unless service.any?
    GtkPkg.logger.debug "NService.store service #{service}"
    service
  end
  
  def find_by_uuid(uuid)
    GtkPkg.logger.debug "NService.find_by_uuid(#{uuid})"
    service = @catalogue.find_by_uuid(uuid)
    GtkPkg.logger.debug "NService.find_by_uuid: #{service}"
    service
  end
  
  private
  
  def duplicated_service?()
    @catalogue.find({vendor:@descriptor['vendor'], name:@descriptor['name'], version:@descriptor['version']})
  end
end
