# Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
# ALL RIGHTS RESERVED.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
# nor the names of its contributors may be used to endorse or promote 
# products derived from this software without specific prior written 
# permission.
# 
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through 
# the Horizon 2020 and 5G-PPP programmes. The authors would like to 
# acknowledge the contributions of their colleagues of the SONATA 
# partner consortium (www.sonata-nfv.eu).
# encoding: utf-8
module GtkVimHelper
  def correct(val, default_val)
    return defalt_val unless val
    return 0 if val < 0
    val
  end

  def json_error(code, message)
    msg = {'error' => message}
    logger.error msg.to_s
    halt code, {'Content-type'=>'application/json'}, msg.to_json
  end

  def valid?(uuid)
    uuid.match /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}/
    uuid == $&
  end

  def keyed_hash(hash)
    Hash[hash.map{|(k,v)| [k.to_sym,v]}]
  end
end

