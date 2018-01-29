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

RSpec.describe GtkCsrv do
  
  let(:uri) { 'http://0.0.0.0:5200/catalogues/csds' }
  before    { 
	WebMock.stub_request(:get,uri).to_return(status:200,body:"[{\"uuid\":\"464dfc44-c694-4604-a790-94df6cbe691\",\"descriptor_version\":\"vnfd-schema-01\",\"vendor\":\"eu.sonata-nfv\",\"name\":\"iperf-vnf\",\"version\":\"0.2\",\"author\":\"StevenvanRossem,iMinds\",\"description\":\"AfirstiperfVNFdescriptor.TheiperfVNFactsasatrafficsource\",\"virtual_deployment_units\":[{\"id\":\"vdu01\",\"vm_image\":\"file:///docker_files/iperf/Dockerfile\",\"vm_image_format\":\"docker\",\"resource_requirements\":{\"cpu\":{\"vcpus\":1},\"memory\":{\"size\":2,\"size_unit\":\"GB\"},\"storage\":{\"size\":10,\"size_unit\":\"GB\"}},\"connection_points\":[{\"id\":\"vdu01:cp01\",\"type\":\"interface\"},{\"id\":\"vdu01:cp02\",\"type\":\"interface\"},{\"id\":\"vdu01:cp03\",\"type\":\"interface\"}]}],\"virtual_links\":[{\"id\":\"mgmt\",\"connectivity_type\":\"E-LAN\",\"connection_points_reference\":[\"vdu01:cp01\",\"mgmt\"]},{\"id\":\"input\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vdu01:cp02\",\"input\"]},{\"id\":\"output\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vdu01:cp03\",\"output\"]}],\"connection_points\":[{\"id\":\"mgmt\",\"type\":\"interface\"},{\"id\":\"input\",\"type\":\"interface\"},{\"id\":\"output\",\"type\":\"interface\"}]}]")
	
	WebMock.stub_request(:get,uri+"/464dfc44-c694-4604-a790-94df6cbe691").to_return(status:200,body:"{\"uuid\":\"464dfc44-c694-4604-a790-94df6cbe691\",\"descriptor_version\":\"vnfd-schema-01\",\"vendor\":\"eu.sonata-nfv\",\"name\":\"iperf-vnf\",\"version\":\"0.2\",\"author\":\"StevenvanRossem,iMinds\",\"description\":\"AfirstiperfVNFdescriptor.TheiperfVNFactsasatrafficsource\",\"virtual_deployment_units\":[{\"id\":\"vdu01\",\"vm_image\":\"file:///docker_files/iperf/Dockerfile\",\"vm_image_format\":\"docker\",\"resource_requirements\":{\"cpu\":{\"vcpus\":1},\"memory\":{\"size\":2,\"size_unit\":\"GB\"},\"storage\":{\"size\":10,\"size_unit\":\"GB\"}},\"connection_points\":[{\"id\":\"vdu01:cp01\",\"type\":\"interface\"},{\"id\":\"vdu01:cp02\",\"type\":\"interface\"},{\"id\":\"vdu01:cp03\",\"type\":\"interface\"}]}],\"virtual_links\":[{\"id\":\"mgmt\",\"connectivity_type\":\"E-LAN\",\"connection_points_reference\":[\"vdu01:cp01\",\"mgmt\"]},{\"id\":\"input\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vdu01:cp02\",\"input\"]},{\"id\":\"output\",\"connectivity_type\":\"E-Line\",\"connection_points_reference\":[\"vdu01:cp03\",\"output\"]}],\"connection_points\":[{\"id\":\"mgmt\",\"type\":\"interface\"},{\"id\":\"input\",\"type\":\"interface\"},{\"id\":\"output\",\"type\":\"interface\"}]}")
	}

  
  it 'answers to cloud service request' do
    get '/cloud-services'
    expect(last_response).to be_ok
    expect(JSON.parse(last_response.body)).to be_a_kind_of(Array)
  end
  
  it 'answers to find request by uuid' do
    get '/cloud-services/464dfc44-c694-4604-a790-94df6cbe691'
    expect(last_response).to be_ok
    expect(JSON.parse(last_response.body)).to be_a_kind_of(Hash)
  end
  
end
