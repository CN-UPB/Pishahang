## SONATA - Gatekeeper
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
require 'yaml'
require 'pp'
require 'securerandom'
require 'rubygems'
require 'zip'
require 'json'

class Package

  DEFAULT_META_DIR = 'META-INF'
  DEFAULT_MANIFEST_FILE_NAME = 'MANIFEST.MF'
  DEFAULT_PATH = File.join(DEFAULT_META_DIR, DEFAULT_MANIFEST_FILE_NAME)
  CLASS = self.name
  
  attr_accessor :descriptor
    
  def initialize(catalogue:, params:, username:)
    method = "GtkPkg: #{CLASS}.#{__method__}"
    GtkPkg.logger.debug(method) {"entered with catalogue=#{catalogue}, params=#{params}, username=#{username}"}
    raise ArgumentError.new(method + ': no Catalogue has been provided') unless catalogue
    raise ArgumentError.new(method + ': no parameters has been provided') unless params
    raise ArgumentError.new(method + ': no username has been provided') if username.to_s.empty?

    @service = {}
    @functions = []
    @username = username
    @@catalogue = catalogue
    GtkPkg.logger.debug(method) {"@@catalogue=#{@@catalogue.inspect}"}
    
    @url = @@catalogue.url
    if params[:descriptor]
      @descriptor = params[:descriptor]
      @input_folder = File.join('tmp', SecureRandom.hex)
      FileUtils.mkdir_p @input_folder unless File.exists? @input_folder
      @output_folder = File.join( 'public', 'packages', @descriptor['uuid'])
      FileUtils.mkdir_p @output_folder unless File.exists? @output_folder
    elsif params[:io]
      @package_file = params[:io]
    else
      GtkPkg.logger.error 'Package.initialize: either @descriptor or @io must be given'
    end
  end
    
  # Builds a package file from its descriptors, and returns a handle to it
  def to_file()
    log_message = CLASS+__method__.to_s
    @descriptor = clear_unwanted_parameters(@descriptor)
    save_package_descriptor()
    GtkPkg.logger.debug(log_message) {"@descriptor=#{@descriptor}"}
    @descriptor[:package_content].each do |p_cont|
      GtkPkg.logger.debug(log_message) {"p_cont=#{p_cont}"}
      if p_cont['name'] =~ /service_descriptors/
        GtkPkg.logger.debug(log_message) { "p_cont['name']=#{p_cont['name']}"}
        @service = NService.new(GtkPkg.settings.services_catalogue, @input_folder)
        @service.to_file(p_cont)
      end
      if p_cont['name'] =~ /function_descriptors/
        GtkPkg.logger.debug(log_message) { "p_cont['name']=#{p_cont['name']}"}
        function = VFunction.new(GtkPkg.settings.functions_catalogue, @input_folder)
        function.to_file(p_cont)
        @functions << function
      end
    end
    output_file = File.join(@output_folder, @descriptor[:name]+'.son')
    
    # Cleans things up before generating
    FileUtils.rm output_file if File.file? output_file
    zip_it output_file
    GtkPkg.logger.debug(log_message) {"output_file #{output_file}"}
    output_file
  end

  # Unbuilds a package file from its file, and returns a descriptor to it
  def from_file()
    log_message = 'Package.'+__method__.to_s
    files = unzip_it @package_file
    #@service = {}
    @functions = []
    
    # first treat the META-INF
    files.each do |file|
      splited = file.split('/')
      file_name = splited[-1]
      path = File.join(splited.first splited.size-1)
      GtkPkg.logger.debug(log_message) { "path=#{path}, file_name = #{file_name}"}
      if path =~ /META-INF/
        @descriptor = YAML.load_file(file) 
        GtkPkg.logger.debug(log_message) { "@descriptor=#{@descriptor}"}
        break
      end
    end
    GtkPkg.logger.debug(log_message) {" before calling duplicated_package?, @@catalogue=#{@@catalogue.inspect}"}
    
    unless duplicated_package?().empty?
      dup = {}
      dup['vendor'] = @descriptor['vendor']
      dup['version'] = @descriptor['version']
      dup['name'] = @descriptor['name']
      return dup
    end
        
    # and now Services and Functions
    files.each do |file|
      splited = file.split('/')
      file_name = splited[-1]
      path = File.join(splited.first splited.size-1)
      GtkPkg.logger.debug(log_message) { "path=#{path}, file_name = #{file_name}"}

      if path =~ /service_descriptors/
        @service = NService.new(GtkPkg.settings.services_catalogue, nil, @username)
        GtkPkg.logger.debug(log_message) { "service=#{@service}"}
        @service.from_file(file)
      end
      if path =~ /function_descriptors/
        function = VFunction.new(GtkPkg.settings.functions_catalogue, nil, @username)
        function.from_file(file)
        GtkPkg.logger.debug(log_message) { "function=#{function}"}
        @functions << function
      end
    end
    GtkPkg.logger.debug(log_message) { "@descriptor is #{@descriptor}"}
    GtkPkg.logger.debug(log_message) { "@service is #{@service}"}
    GtkPkg.logger.debug(log_message) { "@functions is #{@functions}"}
    
    unless valid_descriptor()
      GtkPkg.logger.error(log_message) { "invalid descriptor (#{stored_descriptor})"}
      nil # bad habit!
    end
    stored_descriptor = store_package_service_and_functions()
    unless stored_descriptor
      GtkPkg.logger.error(log_message) { "could not store package based on descriptor=#{stored_descriptor}"}
      nil # bad habit!
    end
    GtkPkg.logger.debug(log_message) { "stored package based on descriptor=#{stored_descriptor}"}
    stored_descriptor
  end

  def self.find_by_uuid(uuid)
    GtkPkg.logger.debug "Package#find_by_uuid: #{uuid}"
    package = @@catalogue.find_by_uuid(uuid)
    GtkPkg.logger.debug "Package#find_by_uuid: #{package}"
    package
  end
  
  def self.find(params)
    GtkPkg.logger.debug "Package#find: #{params}"
    GtkPkg.logger.debug "Package#find: @@catalogue=#{@@catalogue.inspect}"
    packages = @@catalogue.find(params)
    GtkPkg.logger.debug "Package#find: #{packages}"
    packages
  end
  
  def self.delete(uuid)
    method = CLASS + '#' + __method__.to_s
    GtkPkg.logger.debug(method) {'entered with uuid='+uuid}
    @@catalogue.delete(uuid)
  end

  def store_package_file(filename)
    log_message = CLASS + '.' + __method__.to_s
    GtkPkg.logger.debug(log_message) {"entered with #{filename}"}
    create_zip_response = @@catalogue.create_zip(@package_file, filename, @username)
    if create_zip_response
      GtkPkg.logger.debug(log_message) {"catalogue_response is #{create_zip_response}"}
      JSON.parse(create_zip_response)
    else
      GtkPkg.logger.debug(log_message) {'failled to store zip with no response'}
      nil
    end
  end
  
  def add_sonpackage_id(desc_uuid, sonp_uuid)
    response = @@catalogue.set_sonpackage_id(desc_uuid, sonp_uuid)
    if response.nil?
      GtkPkg.logger.debug('Package.add_sonpackage_id'){'Updated descriptor with params: descriptor_uuid=' + desc_uuid + ', sonpackage_uuid=' + sonp_uuid}
      nil
    else
      GtkPkg.logger.debug('Package.add_sonpackage_id'){'Failed to store son-package-uuid in package descriptor'}
      response
    end
  end

  def add_sonpackage_meta(sonp_uuid, desc)
    response = @@catalogue.set_sonpackage_trio_meta(sonp_uuid, desc)
    if response.nil?
      GtkPkg.logger.debug('Package.add_sonpackage_meta'){'Updated descriptor with params: sonp_uuid= '+sonp_uuid+', desc_vendor= '+desc['vendor']+', desc_name= '+desc['name']+', desc_version= '+desc['version']}
      nil
    else
      GtkPkg.logger.debug('Package.add_sonpackage_meta'){'Failed to store son-package-uuid in package descriptor'}
      response
    end
  end

  private
  
  def duplicated_package?()
    log_message = 'Package.'+__method__.to_s
    GtkPkg.logger.debug(log_message) { "verifying duplication of package with @descriptor=#{@descriptor}"}
    GtkPkg.logger.debug(log_message) { "@@catalogue=#{@@catalogue.inspect}"}
    package = Package.find({vendor: @descriptor['vendor'], version: @descriptor['version'], name: @descriptor['name']})
    GtkPkg.logger.debug(log_message) { "returned package is #{package.inspect}"}
    package
  end
  
  def keyed_hash(hash)
    GtkPkg.logger.debug "Package.keyed_hash hash=#{hash}"
    #Hash[hash.map{|(k,v)| v.is_a?(Hash) ? [k.to_sym,keyed_hash(v)] : [k.to_sym,v]}]
    Hash[hash.map{|(k,v)| [k.to_sym,v]}]
  end
  
  def clear_unwanted_parameters(hash)
    GtkPkg.logger.debug "Package.clear_unwanted_parameters hash=#{hash}"
    keyed_hash = keyed_hash(hash)
    [:uuid, :created_at, :updated_at].each { |k| keyed_hash.delete(k) }
    GtkPkg.logger.debug "Package.clear_unwanted_parameters keyed_hash=#{keyed_hash}"
    keyed_hash
  end

  def save_package_descriptor()
    meta_dir = FileUtils.mkdir(File.join(@input_folder, DEFAULT_META_DIR))[0]
    fname = File.join(meta_dir, DEFAULT_MANIFEST_FILE_NAME)
    File.open( fname, 'w') {|f| YAML.dump(@descriptor, f) }
  end

  def zip_it(zipfile_name)
    entries = Dir.entries(@input_folder) - %w(. ..)
    ::Zip::File.open(zipfile_name, ::Zip::File::CREATE) do |io|
      write_entries entries, '', io
    end
  end
  
  def write_entries(entries, path, io)
    entries.each do |e|
      zip_file_path = path == '' ? e : File.join(path, e)
      disk_file_path = File.join(@input_folder, zip_file_path)

      if File.directory? disk_file_path
        recursively_deflate_directory(disk_file_path, io, zip_file_path)
      else
        put_into_archive(disk_file_path, io, zip_file_path)
      end
    end
  end
  
  def recursively_deflate_directory(disk_file_path, io, zip_file_path)
    io.mkdir zip_file_path
    subdir = Dir.entries(disk_file_path) - %w(. ..)
    write_entries subdir, zip_file_path, io
  end

  def put_into_archive(disk_file_path, io, zip_file_path)
    io.get_output_stream(zip_file_path) { |f| f.puts(File.open(disk_file_path, 'rb').read) }
  end
  
  def unzip_it(io)    
    files = []
    GtkPkg.logger.debug "Package.unzip_it: io = #{io.inspect}"
    #@logger.debug "Package.unzip_it: io is " + (io.closed? ? "closed" : "opened")
    #io.rewind
    #@logger.debug "Package.unzip_it: io is " + (io.closed? ? "closed" : "opened")
    unzip_folder = FileUtils.mkdir_p(File.join('tmp', SecureRandom.hex))
    
    # Extract the zipped file into a directory
    Zip::InputStream.open(io) do |zip_file|
      GtkPkg.logger.debug "Package.unzip_it: zip_file = #{zip_file}"
      while (entry = zip_file.get_next_entry)
        GtkPkg.logger.debug "Package.unzip_it: entry.name = #{entry.name}"
        if valid_entry_name? entry.name
          disk_file_path = File.join(unzip_folder, entry.name) 
          entry_name_splited = entry.name.split('/')          
          if entry_name_splited.size == 1
            # just a folder
            FileUtils.mkdir_p disk_file_path unless File.exists? disk_file_path
            GtkPkg.logger.debug "Package.unzip_it: disk_file_path"+disk_file_path+" is a directory"
          else
            # a file, and maybe a folder
            file_name = entry_name_splited.pop
            file_folders = File.join(unzip_folder, entry_name_splited)
            FileUtils.mkdir_p file_folders unless File.exists? file_folders
            GtkPkg.logger.debug "Package.unzip_it: disk_file_path is a file "+disk_file_path
            File.open(disk_file_path, 'w') { |f| f.write entry.get_input_stream.read}
            files << disk_file_path
          end
        end
      end
    end
    GtkPkg.logger.debug "Package.unzip_it: files = #{files}"
    files
  end
  
  def valid_entry_name?(name)
    (name =~ /function_descriptors/ || name =~ /service_descriptors/ || name =~ /META-INF/)
  end
  
  def valid_descriptor()
    # use @descriptor
    true # TODO: validate the descriptor here
  end
  
  def store()
    GtkPkg.logger.debug('Package.store') {"descriptor "+@descriptor.to_s}
    saved_descriptor = @@catalogue.create(@descriptor, @username)
    if saved_descriptor && saved_descriptor['uuid']
      GtkPkg.logger.debug('Package.store') {"saved_descriptor is "+saved_descriptor.to_s}
      saved_descriptor
    else
      GtkPkg.logger.debug('Package.store') {"failled to store #{@descriptor} with no response"}
      nil
    end
  end

  def store_package_service_and_functions
    log_message = 'Package.'+__method__.to_s
    GtkPkg.logger.debug(log_message) {"@package is #{@package}"}
    GtkPkg.logger.debug(log_message) {"@service is #{@service}"}
    GtkPkg.logger.debug(log_message) {"@functions is #{@functions}"}
    
    # The verification of duplicates may have to migrate to the router, in order to make it return '200' instead of '201' 
    package_descriptor = duplicated_package?()
    if package_descriptor.one?
      GtkPkg.logger.error(log_message) {"package exists: #{package_descriptor[0]}"}
      package_descriptor[0]
    else
      saved_descriptor=store()
      if saved_descriptor
        GtkPkg.logger.debug(log_message) {"stored package #{saved_descriptor}"}
        if @service #.size > 0
          GtkPkg.logger.debug(log_message) {"service is #{@service.inspect}"}
          stored_service = @service.store()
          if stored_service
            GtkPkg.logger.debug(log_message) {"stored service #{stored_service}"}
          else
            # TODO: what if storing a service goes wrong?
            # rollback!
            GtkPkg.logger.debug(log_message) {"service and package rollback should happen here"}
          end
        end
        if @functions.size > 0
          @functions.each do |vf|
            GtkPkg.logger.debug(log_message) {"vf = #{vf}"}
            function = vf.store()
            if function
              GtkPkg.logger.debug(log_message) {"stored function #{function}"}
              # TODO: rollback if failled
            else
              GtkPkg.logger.debug(log_message) {"function, service and package rollback should happen here"}
            end
          end
        end
        GtkPkg.logger.debug(log_message) {"saved_descriptor is #{saved_descriptor}"}
        saved_descriptor
      else
        GtkPkg.logger.debug(log_message) { "failled to store package with descriptor=#{@descriptor}"}
        {}
      end
    end
  end
end
