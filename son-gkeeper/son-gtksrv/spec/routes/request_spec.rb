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
require_relative '../spec_helper'
require 'json'

RSpec.describe GtkSrv do
  # let(:n_service) {build(:n_service, catalogues: 'http://localhost:5200/catalogues')}
  let(:uri) { 'http://0.0.0.0:5200/catalogues/network-services' }
  before    { WebMock.stub_request(:get, uri).to_return(status: 200, body: "[{\"descriptor_version\":\"1.0\",\"vendor\":\"eu.sonata-nfv.service-descriptor\",\"name\":\"sonata-demo\",\"version\":\"0.1\",\"author\":\"Sonata, sonata-nfv\",\"description\":\"\\\"The network service descriptor for the SONATA demo,\\n comprising iperf, a firewall, and tcpump.\\\"\\n\",\"network_functions\":[{\"vnf_id\":\"vnf_firewall\",\"vnf_group\":\"eu.sonata-nfv\",\"vnf_name\":\"firewall-vnf\",\"vnf_version\":\"0.1\"}],\"connection_points\":[{\"id\":\"ns:mgmt\",\"type\":\"interface\"},{\"id\":\"ns:input\",\"type\":\"interface\"},{\"id\":\"ns:output\",\"type\":\"interface\"}],\"virtual_links\":[{\"id\":\"mgmt\",\"connectivity_type\":\"E-LAN\",\"connection_points_reference\":[\"vnf_firewall:mgmt\",\"ns:mgmt\"]},{\"id\":\"input\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vnf_firewall:input\",\"ns:input\"]},{\"id\":\"output\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vnf_firewall:output\",\"ns:output\"]}],\"forwarding_graphs\":[{\"fg_id\":\"ns:fg01\",\"number_of_endpoints\":2,\"number_of_virtual_links\":2,\"constituent_vnfs\":[\"vnf_firewall\"],\"network_forwarding_paths\":[{\"fp_id\":\"ns:fg01:fp01\",\"policy\":\"none\",\"connection_points\":[{\"connection_point_ref\":\"ns:input\",\"position\":1},{\"connection_point_ref\":\"vnf_firewall:input\",\"position\":2},{\"connection_point_ref\":\"vnf_firewall:output\",\"position\":3},{\"connection_point_ref\":\"ns:output\",\"position\":4}]}]}]}]") }
  
  it 'answers to requests request' do
#    get '/api/v2/requests'
#    expect(last_response).to be_ok
#    expect(JSON.parse(last_response.body)).to be_a_kind_of(Array)
  end
  
  describe 'GET /requests' do
    it 'accepts listing requests'
  end

  describe 'POST /requests' do
    it 'accepts new valid (instantiations) requests'
    it 'publishes the instantiation request'
    it 'processes the answer to the instantiation request'
    it 'rejects new invalid (instantiations) requests'
  end

  describe 'PUT /requests' do
    it 'accepts updating valid (instantiations) requests'
    it 'rejects updating invalid (instantiations) requests'
  end
  
  describe 'PUT /requests/services/:uuid' do
    it 'rejects requests with no uuid'
    it 'rejects requests without previously registered instantiation request'
    it 'rejests requests for service instances that are not READY'
    it 'rejects requests mentioning a NSD ID that does not exist'
    it "gets the service's NSD"
    it 'creates the update request'
    it 'updates the request status while updating'
    it 'updates the request status when finished'
  end
end

#let(:extended_params) {default_params.merge({version: "0.1"})}
#it 'should call the Package Management Service model with the passed parameters plus "offset" and "limit"' do
#  allow(Package).to receive(:find).with(hash_including(extended_params)).and_return(simplest_package)
#  package = Package.find(extended_params)
#  expect(package).to include(:version)
#end  


#it "should be able to be instantiated" do
#  expect { Mail }.not_to raise_error
#end

#it "should be able to make a new email" do
#  expect(Mail.new.class).to eq Mail::Message
#end