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

# Class model for SP user meta-data
class Sp_user
  include Mongoid::Document
  include Mongoid::Timestamps
  # include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'sp_users'

  field :username, type: String
  field :id, type: String
  field :public_key, type: String
  field :certificate, type: String
  validates :username, :public_key, :certificate, presence: true, :allow_nil => true
end

# Class model for SP micro-service resources
class Sp_resource
  include Mongoid::Document
  include Mongoid::Timestamps
  # include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'sp_resources'

  field :resource_owner_name, type: String
  field :role, type: String
  field :resources, type: Array
  field :policies, type: Array
  # field :scopes, type: Array

  validates :resource_owner_name, :role, :resources, :policies, presence: true
end
