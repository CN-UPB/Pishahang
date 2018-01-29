#!/usr/bin/env python2
#encoding: UTF-8

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
import json,urllib2,time,socket,sys
import threading
from threading import  Thread

class PushGW(Thread):
    
    def __init__(self,url_,hld_):
        self.url = url_
        self.data = None
        self.ws_handler =  hld_
        self.update()
        
    def run(self):
        while not self.stopped.wait(2):
            self.getLastData()
            
    def update(self): 
        try:   
            dt=self.getLastData()
            self.conver2obj(dt)
            #print (self.ws_handler.nm_space_info)
            self.feedWS()
            t = threading.Timer(3.0, self.update)
            t.start()
        except:
            print "Unexpected error"
            os._exit(-1)
            pass
    
    def getData(self):
        return self.data
    
    def feedWS(self):
        if not self.data:
            return;
        for metric in self.ws_handler.nm_space_info.keys():
            if metric in self.data.keys():
                #print (self.data[metric])
                conns = self.ws_handler.nm_space_info[metric]
                for con in conns:
                    #print (con)
                    resp = {metric:[]}
                    dt = self.filter(con['filters'],self.data[metric])
                    resp[metric]= dt
                    #resp[metric]= self.data[metric]
                    if 'wsconn' in con.keys():
                        con['wsconn'].send_values(json.dumps(resp))
    
    def filter(self, filters_, data_):
        dt=[]
        if len(filters_) == 0:
            dt = data_
            return dt
        for rec in data_:
            labels= rec['labels']  
            found = 0
            for fl in filters_:
                for l in labels:
                    if fl['tag'] == "type":
                        fl['tag'] = "job"
                    if l.startswith( fl['tag'] ):
                        if fl['val'] in l:
                            found=found +1
            if found == len(filters_):
                dt.append(rec)
        print (dt)
        return dt

    def conver2obj(self, data_):
        if not data_:
            return;
        mtrObj={}
        for line in data_.splitlines():
            if line.startswith('#'):
                continue
            blks = line.split(' ')
            lbSt = line.find('{')
            lbSp = line.find('}')
            if lbSt > 0 and lbSp > 0:
                metric= line[0:lbSt]
                labels= line[lbSt+1:lbSp].split(',')
                line = line[lbSp+1:len(line)].strip()
                blks = line.split(' ')
                value = float(blks[0])
                time = None
                if len(blks) > 1:
                    time = int(blks[1])
            else:
                labels = {}
                #print line
                blks = line.split(' ')
                metric = blks[0]
                value = float(blks[1])
                time = None
                if len(blks) > 2:
                    time = int(blks[1])
            if not metric in mtrObj.keys(): 
                mtrObj[metric]=[]
            obj={}
            obj['labels']=labels
            obj['value']=value
            obj['time']=time
            mtrObj[metric].append(obj)
        self.data = mtrObj    
        #print (json.dumps(mtrObj))
        #sys.exit()
            
    
    def getLastData(self):
        try:
            req = urllib2.Request(self.url)
            req.add_header('Content-Type','application/text')
        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            self.data = response.read()
            #print json.dumps(data)
            return self.data
    
        except urllib2.HTTPError, e:
            print('Error1: '+str(e))
            pass
        except urllib2.URLError, e:
            print('Error2: '+str(e))
            pass
        except ValueError, e:
            print('Error3: '+str(e))
            pass
        except socket.timeout, e:
            print('Error4: '+str(e))
            pass
    
if __name__ == "__main__":
    ps = PushGW('http://pushgateway:9091/metrics',None)