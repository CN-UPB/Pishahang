'''
Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote 
products derived from this software without specific prior written 
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through 
the Horizon 2020 and 5G-PPP programmes. The authors would like to 
acknowledge the contributions of their colleagues of the SONATA 
partner consortium (www.sonata-nfv.eu).
'''

import json,urllib2

class Http(object):
    def __init__(self):
        self
        
    def GET(self,url_,headers_):
	try: 
            req = urllib2.Request(url_)
            req.add_header('Content-Type','application/json')
            response=urllib2.urlopen(req)
            code = response.code
            data = json.loads(response.read())
            return data
        
        except urllib2.HTTPError, e:
            return e.code
        except urllib2.URLError, e: 
            return e
        except ValueError, e:
            return e

    def POST(self, url_,headers_,data_):
        try: 
            req = urllib2.Request(url_)
            req.add_header('Content-Type','text/html')
            req.get_method = lambda: 'POST'
            response=urllib2.urlopen(req,data_)
            code = response.code  
            return code
        except urllib2.HTTPError, e:
            return e.code
        except urllib2.URLError, e:
            return e

    def DELETE(self, url_,headers_):  #karpa
        try: 
            req = urllib2.Request(url_)
            req.add_header('Content-Type','text/html')
            req.get_method = lambda: 'DELETE'
            response=urllib2.urlopen(req)
            code = response.code  
            return code
        except urllib2.HTTPError, e:
            return e.code
        except urllib2.URLError, e:
            return e
