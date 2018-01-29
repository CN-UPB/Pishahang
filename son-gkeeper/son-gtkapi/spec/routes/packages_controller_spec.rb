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
require File.expand_path '../../spec_helper.rb', __FILE__

RSpec.describe GtkApi, type: :controller do
  include Rack::Test::Methods
  def app() GtkApi end
  
  let(:simplest_package) {{
    descriptor_version: "1.0", 
    vendor: "eu.sonata-nfv.package", 
    name: "simplest-example",
    version: "0.1",
    maintainer: "Michael Bredel, NEC Labs Europe"
  }}
  let(:default_params) {{offset: 0, limit: 10}}
  
  describe 'GET /packages' do
    describe 'with no (UU)ID given' do
      context 'and with no query parameters,' do
        it 'should call the Package Management Service model with only the default "offset" and "limit" parameters' do
          allow(Package).to receive(:find).with(hash_including(default_params)).and_return(simplest_package)
          package = Package.find(default_params)
          expect(package).to include(:name, :vendor, :version)
        end
      end
      context 'and with query parameters,' do
        let(:extended_params) {default_params.merge({version: "0.1"})}
        it 'should call the Package Management Service model with the passed parameters plus "offset" and "limit"' do
          allow(Package).to receive(:find).with(hash_including(extended_params)).and_return(simplest_package)
          package = Package.find(extended_params)
          expect(package).to include(:version)
        end  
      end
    end
    describe 'with (UU)ID given,' do
      it 'should raise an error if the UUID is invalid'      
      context 'and with no query parameters,' do
        it 'should call the Package Management Service model with the UUID parameter'
      end
      context 'and with query parameters,' do
        it 'should call the Package Management Service model with only the UUID parameter'
      end
    end
    describe 'with may packages found' do
      it 'should return a package list'
    end    
    describe 'with only one package found' do
      it 'should return a package file'
    end
  end
  
  describe 'POST /packages' do
    context 'with a valid request' do
      it 'should return the package meta-data'
    end
    context 'with repeated package' do
      it 'should return a duplicated package error'
    end
    context 'with invalid request' do
      it 'should return an error'
    end
  end
end
