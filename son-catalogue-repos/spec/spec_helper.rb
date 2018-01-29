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

# spec/spec_helper.rb
require 'rack/test'
require 'rspec'
require 'webmock/rspec'
require 'zip'

ENV['RACK_ENV'] ||= 'test'

WebMock.allow_net_connect!

$LOAD_PATH << File.expand_path('../..', __FILE__)
require './main'

RSpec.configure do |config|
  config.include Rack::Test::Methods
  config.mock_with :rspec
  config.include WebMock::API
end

def xtract_sonp(sonpfile)
  manifest = nil
  vnfds = []
  nsds = []
  Zip::InputStream.open(sonpfile) do |io|
    while (entry = io.get_next_entry)
      if entry.name.casecmp('META-INF/MANIFEST.MF') == 0
        manifest = io.read
      else
        dirname = Pathname(File.path(entry.name)).split.first.to_s
        if dirname.casecmp('SERVICE_DESCRIPTORS') == 0
          if !entry.name_is_directory?
            puts entry
            nsds << io.read
          end
        elsif dirname.casecmp('FUNCTION_DESCRIPTORS') == 0
          if !entry.name_is_directory?
            puts entry
            vnfds << io.read
          end
        end
      end
    end
  end
  {manifest: manifest, vnfds: vnfds, nsds: nsds}
end
