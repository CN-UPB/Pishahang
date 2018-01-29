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

require 'yard'
require 'rspec/core/rake_task'
require 'ci/reporter/rake/rspec'
require './main'

task default: ['ci:all']

desc 'Start the service'
task :start do
  puts 'SON-CATALOGUE-REPOSITORIES STARTING...'
  puts 'Version 3.0'

  # puts ENV['MAIN_DB'].to_s, ENV['MAIN_DB_HOST'].to_s, ENV['SECOND_DB'].to_s, ENV['SECOND_DB_HOST'].to_s

  puts "VAR `MAIN_DB`=#{ENV['MAIN_DB'].inspect}"
  puts "VAR `MAIN_DB_HOST`=#{ENV['MAIN_DB_HOST'].inspect}"
  puts "VAR `SECOND_DB`=#{ENV['SECOND_DB'].inspect}"
  puts "VAR `SECOND_DB_HOST`=#{ENV['SECOND_DB_HOST'].inspect}"

  conf = File.expand_path('config.ru', File.dirname(__FILE__))
  exec("puma #{conf} -b tcp://0.0.0.0:4011")
end

desc 'Run Unit Tests'
RSpec::Core::RakeTask.new :specs do |task|
  task.pattern = Dir['spec/**/*_spec.rb']
end

YARD::Rake::YardocTask.new do |t|
  t.files = %w(main.rb helpers/*.rb routes/*.rb)
end

task :default => [:swagger]

namespace :ci do
  task all: %w(ci:setup:rspec specs)
end

namespace :db do
  task :load_config do
    require './main'
  end
end

namespace :init do
  require 'fileutils'
  desc 'Fill Catalogues with default sonata-demo package contents'
  task :load_samples, :server do |_, args|

    server = 'son-catalogue-repos:4011'
 
    firewall_sample = 'samples/sonata-demo/function-descriptor/firewall-vnfd.yml'
    iperf_sample = 'samples/sonata-demo/function-descriptor/iperf-vnfd.yml'
    tcpdump_sample = 'samples/sonata-demo/function-descriptor/tcpdump-vnfd.yml'
    nsd_sample = 'samples/sonata-demo/service-descriptor/sonata-demo.yml'
    pd_sample = 'samples/sonata-demo/package-descriptor/sonata-demo.yml'
    vnfr_random_sample = 'samples/sonata-demo/function-record/random-vnfr.yml'
    vtc_sample = 'samples/sonata-demo-1/function-descriptor/vtc-vnfd.yml'
    nsd1_sample = 'samples/sonata-demo-1/service-descriptor/sonata-demo.yml'

    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ nsd1_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/network-services"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ vtc_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/vnfs"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ firewall_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/vnfs"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ iperf_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/vnfs"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ tcpdump_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/vnfs"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ nsd_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/network-services"
    sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ pd_sample } --connect-timeout 30 http://#{ server }/catalogues/api/v2/packages"
	  sh "curl -X POST -H \"Content-Type: application/x-yaml\" --data-binary @#{ vnfr_random_sample } --connect-timeout 30 http://#{ server }/records/vnfr/vnf-instances"
  end
end
