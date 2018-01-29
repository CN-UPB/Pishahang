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

# Convert BSON ID to String
module BSON
  class ObjectId
    def to_json(*)
      to_s.to_json
    end

    def as_json(*)
      to_s.as_json
    end
  end
end

# Sonata class for Catalogue Services
class Ns
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  # include Mongoid::Versioning
  include Mongoid::Attributes::Dynamic
  store_in collection: 'nsd'

  field :vendor, type: String
  field :name, type: String
  field :version, type: String
  field :status, type: String
  validates :vendor, :name, :version, presence: true
end

# New API v2 item structure for meta-data and descriptor data
class Nsd
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'nsd'

  field :nsd, type: Hash
  field :status, type: String
  field :signature, type: String
  field :username, type: String
  validates :nsd, presence: true
end

# Sonata class for Catalogue Services
class Cos
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  # include Mongoid::Versioning
  include Mongoid::Attributes::Dynamic
  store_in collection: 'cosd'

  field :vendor, type: String
  field :name, type: String
  field :version, type: String
  field :status, type: String
  validates :vendor, :name, :version, presence: true
end

# New API v2 item structure for meta-data and descriptor data
class Cosd
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'cosd'

  field :cosd, type: Hash
  field :status, type: String
  field :signature, type: String
  field :username, type: String
  validates :cosd, presence: true
end

# Sonata class for Catalogue Functions
class Vnf
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'vnfd'

  field :vendor, type: String
  field :name, type: String
  field :version, type: String
  validates :vendor, :name, :version, presence: true
end

# New API v2 item structure for meta-data and descriptor data
class Vnfd
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'vnfd'

  field :vnfd, type: Hash
  field :status, type: String
  field :signature, type: String
  field :username, type: String
  validates :vnfd, presence: true
end

# Sonata class for Catalogue Cloud Services
class Cls
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'csd'

  field :vendor, type: String
  field :name, type: String
  field :version, type: String
  validates :vendor, :name, :version, presence: true
end

# New API v2 item structure for meta-data and descriptor data
class Clsd
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'csd'

  field :csd, type: Hash
  field :status, type: String
  field :signature, type: String
  field :username, type: String
  validates :csd, presence: true
end

# Sonata class for Catalogue Packages
class Package
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'pd'

  field :vendor, type: String
  field :name, type: String
  field :version, type: String
  validates :vendor, :name, :version, presence: true
end

# New API v2 item structure for meta-data and descriptor data
class Pkgd
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'pd'

  field :pd, type: Hash
  field :status, type: String
  field :signature, type: String
  field :username, type: String
  validates :pd, presence: true
end

# Class model for binary data storage on database
# require 'mongoid/grid_fs'
# Sonata API v2 class for Catalogue son-packages
class FileContainer
  require 'mongoid/grid_fs'

  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'file_containers'

  field :grid_fs_id, type: String
  field :grid_fs_name, type: String
  # field :vendor, type: String
  # field :name, type: String
  # field :version, type: String
  field :signature, type: String
  field :md5, type: String
  field :username, type: String
end

# Sonata class for Catalogue Element Dependencies
class Dependencies_mapping
  include Mongoid::Document
  include Mongoid::Timestamps
  include Mongoid::Pagination
  include Mongoid::Attributes::Dynamic
  store_in collection: 'mapping_db'

  field :son_package_uuid, type: String
  field :pd, type: Hash
  field :nsds, type: Array
  field :vnfds, type: Array
  field :deps, type: Array
  field :status, type: String
  validates :son_package_uuid, :pd, :nsds, :vnfds, :status, :presence => true
end
