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
module GtkPkgHelpers
  def validate_manifest(manifest, options={})

    schema = File.read(settings.manifest_schema)

    # Get the schema from url if exists
    if manifest.has_key?('$schema')
      begin
        schema = RestClient.get(manifest['$schema']).body
      rescue => e
        remove_leftover(options[:files])
        puts e.response
        halt e.response.code, e.response.body
      end
    end

    # Validate agains the schema
    begin
      JSON::Validator.validate!(schema, manifest.to_json)
    rescue JSON::Schema::ValidationError
      remove_leftover(options[:files])
      logger.error "JSON validation: #{$!.message}"
      halt 400, $!.message + "\n"
    end

    # Validate name
    halt 400, 'Package name invalid' unless (manifest['name'].downcase == manifest['name']) && (manifest['name'] =~ /^[a-zA-Z\-\d\s]*$/)
    # Validate version
    halt 400, 'Package version format is invalid' unless manifest['version'] =~ /\A\d+(?:\.\d+)*\z/
  end

  def remove_leftover(files)
    files.each do |f|
      logger.info "Removing #{f}"
      FileUtils.rm_rf(f)
    end
  end

  def json_error(code, error_message, log_message='')
    content_type :json
    msg = {'error' => { 'code'=>code, 'message'=>error_message}}.to_json
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

  def normalize_filename(original)
    return original['filename'] if original.has_key? 'filename'
    return original[:filename] if original[:filename]
    ''
  end
  
  def keyed_hash(hash)
    Hash[hash.map{|(k,v)| [k.to_sym,v]}]
  end
  
  def format_error(backtrace)
    first_line = backtrace[0].split(":")
    "In "+first_line[0].split("/").last+", "+first_line.last+": "+first_line[1]
  end
  
  def header_json
    {'Accept'=>'application/json', 'Content-Type'=>'application/json'}
  end
end