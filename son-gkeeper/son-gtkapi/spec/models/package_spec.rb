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

RSpec.describe Package, type: :model do
  let(:user) {{username: 'Unknown', password: 'None'}}
  let(:secret) {Base64.strict_encode64(user[:username]+':'+user[:password])}
  let(:session) {{began_at: Time.now.utc, token: 'abc'}}
  # Just with the user for the moment
  let(:package) {{token: 'abc'}}
  
  describe '#find_by_uuid' do
    it 'should GET /catalogues/packages/:uuid from catalogues'
  end
  describe '#find' do
    it 'should GET /catalogues/packages from catalogues'
  end
  describe '#create' do
    it 'should POST /catalogues/packages to catalogues'
    context 'with a valid' do
      context 'and authorized user' do
        before(:each) do
          allow(User).to receive(:authenticated?).with(secret).and_return(session)
          allow(User).to receive(:authorized?).and_return(true)
          allow(User).to receive(:find_username_by_token).with(session[:token]).and_return(user[:username])
          allow(RestClient).to receive(:post).and_return(status: 200, body: "", headers: {})
          Package.create(package)
        end
        # Just pointers for the moment        
        it 'checks user authentication' do
          #expect(User).to have_received(:authenticated?)
        end
        it 'checks user authorization' do
          #expect(User).to have_received(:authorized?)
        end
      end
    end
  end
end