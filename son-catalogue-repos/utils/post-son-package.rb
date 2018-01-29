#!/usr/bin/env ruby
# coding: utf-8

# Command line ruby script built
#   to simulate the posting of a complete
#   sonata package to son-catalogue-repos
#   and check the intelligent deletion
#   feature
#
# Requires the path to a zipped son-package filename
#   it posts the package and also
#   extracts the descriptors posting them to the appropiate
#   services

require 'rest-client'
require 'zip'
require 'yaml'
require 'pathname'

if ARGV.length < 1
  puts "\nUsage: #{File.basename($PROGRAM_NAME)} son-package-filename\n\n"
  exit(0)
end

def xtract_zip(sonpfile)
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

uuids = []
ARGV.each do |filename|
  content = xtract_zip(filename)
  puts filename
  postsonp = RestClient.post('http://localhost:4011/catalogues/api/v2/son-packages',
                             File.binread(filename),
                             :content_type => 'application/zip',
                             :'Content-Disposition' => "attachment; filename=#{filename}")

  raise 'Error trying to post son-package' unless postsonp.code == 201

  content[:vnfds].each do |vnfd|
    postvnf = RestClient.post('http://localhost:4011/catalogues/api/v2/vnfs',
                              vnfd,
                              :content_type => 'application/x-yaml')
  end

  content[:nsds].each do |vnfd|
    postnsd = RestClient.post('http://localhost:4011/catalogues/api/v2/network-services',
                              vnfd,
                              :content_type => 'application/x-yaml')
  end

  postpd = RestClient.post('http://localhost:4011/catalogues/api/v2/packages',
                           content[:manifest],
                           :content_type => 'application/x-yaml')

  uuids << YAML.load(postpd.body)['uuid']
end

# Try to delete first package sent
STDIN.gets
puts
puts uuids.join("\n")
puts

disableresp = RestClient.put('http://localhost:4011/catalogues/api/v2/packages/'+uuids[0]+'/status',
                             '{"status": "inactive"}', :content_type => 'application/json'){|response, request, result|
  response }
puts disableresp.code
puts disableresp.body
STDIN.gets

disableresp = RestClient.put('http://localhost:4011/catalogues/api/v2/packages/'+uuids[2]+'/status',
                             '{"status": "inactive"}', :content_type => 'application/json'){|response, request, result|
  response }
puts disableresp.code
puts disableresp.body
STDIN.gets

disableresp = RestClient.put('http://localhost:4011/catalogues/api/v2/packages/'+uuids[0]+'/status',
                             '{"status": "active"}', :content_type => 'application/json'){|response, request, result|
  response }
puts disableresp.code
puts disableresp.body
STDIN.gets

disableresp = RestClient.put('http://localhost:4011/catalogues/api/v2/packages/'+uuids[1]+'/status',
                             '{"status": "inactive"}', :content_type => 'application/json'){|response, request, result|
  response }
puts disableresp.code
puts disableresp.body
STDIN.gets

deleteresp = RestClient.delete('http://localhost:4011/catalogues/api/v2/packages/'+uuids[0]){|response, request, result|
  response }
puts deleteresp.code
puts deleteresp.body
puts STDIN.gets

deleteresp = RestClient.delete('http://localhost:4011/catalogues/api/v2/packages/'+uuids[2]){|response, request, result|
  response }
puts deleteresp.code
puts deleteresp.body
puts STDIN.gets

deleteresp = RestClient.delete('http://localhost:4011/catalogues/api/v2/packages/'+uuids[1]){|response, request, result|
  response }
puts deleteresp.code
puts deleteresp.body
puts STDIN.gets
