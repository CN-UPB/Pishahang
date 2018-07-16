# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from datetime import date
import urlparse

import tornado.web

class VersionHandler(tornado.web.RequestHandler):
    def initialize(self, instance):
        self._instance = instance

    def get(self):
        response = { 'version': '3.5.1',
                     'last_build':  date.today().isoformat() }
        self.write(response)
 
def get_url_target(url):
    is_operation = False
    url_parts = urlparse.urlsplit(url)
    whole_url = url_parts[2]

    url_pieces = whole_url.split("/")
    
    return url_pieces[-1]
