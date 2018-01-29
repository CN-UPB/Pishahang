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
require_relative '../spec_helper'
require 'webmock/rspec'
require 'json'
require 'securerandom'
require 'pp'
require 'rspec/its'

RSpec.describe GtkPkg do
  #include Rack::Test::Methods
  #def app
  #  GtkPkg # this defines the active application for this test
  #end
  
  let(:response_body) {{ 'uuid'=> "dcfb1a6c-770b-460b-bb11-3aa863f84fa0", 'descriptor_version' => "1.0", 'package_group' => "eu.sonata-nfv.package", 'name' => "simplest-example", 'package_version' => "0.1", 'package_maintainer' => "Michael Bredel, NEC Labs Europe"}}

  describe 'POST /packages' do
    context 'with correct parameters' do
      # curl -F "package=@simplest-example.son" localhost:5000/packages

      let(:package_file_name) {'simplest-example.son'}
      let(:package_file) {Rack::Test::UploadedFile.new('../../son-schema/package-descriptor/examples/sonata-demo.son','application/octet-stream', true)}
      let(:package) {{ :filename=>package_file_name, :type=> 'application/octet-stream', :name=> 'package', :tempfile=> package_file, 
        :head=> "Content-Disposition: form-data; name=\"package\"; filename=\"#{package_file_name}\"\r\nContent-Type: application/octet-stream\r\n"
        }}
      let(:package_io) { File.open('../../son-schema/package-descriptor/examples/'+package_file_name, 'rb').read }
      let(:pkgmgr) {stub_request(:post, 'http://localhost:5100/packages').to_return(:status=>201, :body=>response_body, :headers=>{ 'Content-Type'=>'application/json' })}
      # .with(:headers => { 'Content-Type' => 'application/octet-stream' })
      let(:params) {
        {
          "filename"=>"sonata-demo.son", 
          "type"=>"application/octet-stream", 
          "name"=>"package", 
          "tempfile"=>{
            :filename=>package_file_name,
            :type=>"text/plain",
            :name=>"package[tempfile]",
            :tempfile=>package_file, #File.open('../../son-schema/package-descriptor/examples/'+package_file_name, 'rb').read,
            :head=>"Content-Disposition: form-data; name=\"package[tempfile]\"; filename=\"sonata-demo.son\"\r\nContent-Type: text/plain\r\n"}, "head"=>"Content-Disposition: form-data; name=\"package\"; filename=\"sonata-demo.son\"\r\nContent-Type: application/octet-stream\r\n"
          }
      }  
      before do
        WebMock.stub_request(:post, 'localhost:5100/packages').to_return(:status=>201, :body=>response_body.to_json)
        post '/packages/', package: Rack::Test::UploadedFile.new('../../son-schema/package-descriptor/examples/sonata-demo.son','application/octet-stream')
      end

      #subject { last_response }
      #its(:status) { is_expected.to eq 201 }

#      it 'returns the JSON related to the resource creation' do
#        expect(last_response.headers['Content-Type']).to include 'application/json'
#        parsed_body = JSON.parse(JSON.parse(last_response.body, :quirks_mode => true))
#        expect(parsed_body).to be_an_instance_of(Hash)
#        expect(parsed_body).to eq response_body
#      end

#      it 'should return a UUID' do
        # /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}/
#        parsed_body = JSON.parse(JSON.parse(last_response.body, :quirks_mode => true))
#        uuid = parsed_body.fetch('uuid')
#        expect(uuid).to be_an_instance_of(String)
#        expect(uuid.length).to eq 36
#      end
    end
  
    context 'with invalid parameters given' do
    end
  end

  describe 'GET /packages' do
    context 'with (UU)ID given' do      
      before do
        stub_request(:get, 'localhost:5200/packages').to_return(:status=>200, :body=>response_body.to_json, :headers=>{ 'Content-Type'=>'application/json' })
        get '/packages/dcfb1a6c-770b-460b-bb11-3aa863f84fa0'
      end
      subject { last_response }
      #its(:status) { is_expected.to eq 200 }
    end
    context 'with query parameters given' do
    end
    context 'without any query parameter given' do
    end
  end
end

# it 'saves string to the file system' do
#  string_changer = StringChanger.new
#  File.stub(:write)
#
#  string_changer.reverse_and_save('example string')
#
#  expect(File).
#    to have_received(:write).
#    with('example_file', 'gnirts elpmaxe').
#    once
#end


#    it "redirects to /play" do
#      follow_redirect!
#      last_request.path.should == '/play'
#    end
