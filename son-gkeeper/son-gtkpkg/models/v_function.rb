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
require 'fileutils'

class VFunction
  
  attr_accessor :descriptor
  CLASS = self.name
  
  def initialize(catalogue, folder, username)
    @catalogue = catalogue
    @descriptor = {}
    @username = username
    if folder
      @folder = File.join(folder, "function_descriptors")
      FileUtils.mkdir @folder unless File.exists? @folder
    end
  end
  
  def to_file(content)
    GtkPkg.logger.debug "VFunction.to_file(#{content})"
    filename = content['name'].split('/')[-1]
    File.open(File.join( @folder, filename), 'w') {|f| YAML.dump(content, f) }
  end
  
  def from_file(path)
    GtkPkg.logger.debug "VFunction.from_file("+path+")"
    @descriptor = YAML.load_file path
    GtkPkg.logger.debug "VFunction.from_file: content = #{@descriptor}"
    @descriptor
  end
  
  def store
    GtkPkg.logger.debug "VFunction.store #{@descriptor}"
    function = duplicated_function?()
    if function && function.any?
      GtkPkg.logger.debug "VFunction.store function #{function} is duplicated"
    else 
      function = @catalogue.create(@descriptor, @username)
    end
    GtkPkg.logger.debug "VFunction.store function #{function}"
    function
  end
  
  private
  
  def duplicated_function?()
    @catalogue.find({vendor: @descriptor['vendor'], name: @descriptor['name'], version: @descriptor['version']})
  end
end
