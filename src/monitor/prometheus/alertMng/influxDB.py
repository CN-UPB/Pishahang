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


from influxdb import InfluxDBClient
import json

class influx(object):
    def __init__(self, host, port, usr, psw, db_name):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = usr
        self.password = psw
        
    def query(self, query_):
        client = InfluxDBClient(self.host, self.port, self.user, self.password, self.db_name)
        result = client.query(query_)
        return result.raw
    
    def databases(self):
        client = InfluxDBClient(self.host, self.port, self.user, self.password, self.db_name)
        result = client.get_list_database()
        return result
    
    def getseries(self):
        client = InfluxDBClient(self.host, self.port, self.user, self.password, self.db_name)
        result = client.get_list_series(self.db_name)
        return result

    def checkDB(self, db_name):
        client = InfluxDBClient(self.host, self.port, self.user, self.password)
        result = client.get_list_database()
        for db in result:
            if db['name'] == db_name:
                return True
        return False