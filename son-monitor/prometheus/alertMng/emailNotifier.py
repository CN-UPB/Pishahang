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

import smtplib, base64, os
import email.utils, re, json, urllib2
from email.mime.text import MIMEText


class emailNotifier():

    def __init__(self):
        self.mon_manager = 'http://manager:8000'
        self.msgs = []
        self.smtp={'server':'localhost','port':None,'user':None,'psw':None, 'sec_type': None, 'postfix':True}
        self.setSmtpSrv()

    def setSmtpSrv(self):
        compName = 'Alert_Manager'
        srv = self.getSmtp(self.mon_manager+'/api/v1/notification/smtp/component/'+compName+'/')
        if 'results' in srv:
            if len(srv['results']) > 0:
                cds = self.getSmtp(self.mon_manager+'/api/v1/internal/smtp/creds/'+compName)
                if 'status' in cds:
                    if cds['status'] == 'key found':
                        self.smtp['psw'] = base64.b64decode(cds['creds'])
                        self.smtp['server'] =  srv['results'][0]['smtp_server']
                        self.smtp['port'] =  srv['results'][0]['port']
                        self.smtp['user'] =  srv['results'][0]['user_name']
                        self.smtp['sec_type'] =  srv['results'][0]['sec_type']
                        self.smtp['postfix'] = False
        print self.smtp

    def getEmailPass(selfn):
        if os.environ.has_key('EMAIL_PASS'):
            key = str(os.environ['EMAIL_PASS']).strip()
            return key.decode('base64')
        else:
            return ''
            
    def msgs2send(self,msgs_):
        for notif in msgs_:
            myemail={}
            m = self.alarmStatus(notif)
            msg = MIMEText(m['body'])
            msg.set_unixfrom('Sonata Monitoring System')
            if notif['exported_job'] == 'vm':
                receivers = self.getAdminEMails()
            elif notif['exported_job'] == 'vnf':
                if 'serviceID' in notif:
                    users = self.getUsers(notif['serviceID'])
                    emails=[]
                    for u in users:
                        mail = self.getEMails(str(u))
                        if mail != '':
                            emails.append(mail)
                    receivers = emails
                else:
                    continue
            else:
                continue
            msg['To'] = email.utils.formataddr(('Recipient', receivers))
            msg['From'] = email.utils.formataddr(('Monitoring server', 'monitoring@synelixis.com'))
            msg['Subject'] = 'ALERT NOTIFICATION '+ m['status'] 
            myemail['receivers']= receivers
            myemail['obj'] = msg
            self.msgs.append(myemail)
            print(myemail['receivers'])
        self.sendMail()
            
    def getSmtp(self, url):
        try:
            print url
            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')
        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            data = json.loads(response.read())
            return data
    
        except urllib2.HTTPError, e:
            return {'error':str(e)}
        except urllib2.URLError, e:
            return {'error':str(e)}
        except ValueError, e:
            return {'error':str(e)}

    def getUsers(self, serviceID):
        us=[]
        try:
            url = self.mon_manager+'/api/v1/service/'+serviceID+"/"
            print url
            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            data = json.loads(response.read())
            if data['count'] > 0:
                srv = data['results'][0]
                if 'user' in srv:
                    us = srv['user']
                    
            print json.dumps(us)
            return us
    
        except urllib2.HTTPError, e:
            return {'error':str(e)}
        except urllib2.URLError, e:
            return {'error':str(e)}
        except ValueError, e:
            return {'error':str(e)}
        
    def getEMails(self, usrID):
        mail=''
        try:
            url = self.mon_manager+'/api/v1/user/'+usrID+"/"
            print url
            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            data = json.loads(response.read())
            if data['count'] > 0:
                user = data['results'][0]
                if 'email' in user:
                    mail = user['email']
            return mail
    
        except urllib2.HTTPError, e:
            return {'error':str(e)}
        except urllib2.URLError, e:
            return {'error':str(e)}
        except ValueError, e:
            return {'error':str(e)}
        
    def getAdminEMails(self):
        mails=[]
        try:
            url = self.mon_manager+'/api/v1/users/type/admin/'
            print url
            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            data = json.loads(response.read())
            if data['count'] > 0:
                for admin in data['results']:
                    if 'email' in admin:
                        if admin['email'] != '':
                            mails.append(admin['email'])    
            return mails
    
        except urllib2.HTTPError, e:
            return {'error':str(e)}
        except urllib2.URLError, e:
            return {'error':str(e)}
        except ValueError, e:
            return {'error':str(e)}
            
            
    def sendMail(self):
        if self.smtp['postfix']:
            for msg in self.msgs:
                try: 
                    smtp = smtplib.SMTP('localhost')
                    resp=smtp.sendmail('monitoring@sonata-nfv.eu', msg['receivers'], msg['obj'].as_string() )
                    print 'Successfully sent email via postfix'
                    smtp.close()
                except Exception , exc:
                    print "mail failed; %s" % str(exc)               
        else:
            
            try:
                if self.smtp['sec_type'].startswith('SSL'):
                    server = smtplib.SMTP_SSL(self.smtp['server'],int(self.smtp['port']))
                else:
                    server = smtplib.SMTP(self.smtp['server'],int(self.smtp['port']))
                #server.set_debuglevel(1)
                server.ehlo()
                if self.smtp['sec_type'].startswith('TLS'):
                    server.starttls()
                    server.ehlo()
                server.login(self.smtp['user'], self.smtp['psw'])
                for msg in self.msgs:
                    server.sendmail('monitoring@sonata-nfv.eu', msg['receivers'], msg['obj'].as_string())   
                    print "Successfully sent email"
                server.quit()
            except Exception , exc:
                print "mail failed; %s" % str(exc)
            
    def alarmStatus(self, obj):
        msg={}
        msg['body'] = 'Dear user, \nRule: '
        alert = obj['alertname']
        if alert == 'CPU_load_vm':
            alert = alert + ' ('+obj['core']+')'
        if obj['alertstate'] == 'firing' and obj['value'] == "1":
            msg['body'] = msg['body'] + alert + " is ACTIVE on instance "+obj['id'] + " at " + obj['time']+'\n\n'+json.dumps(obj)
            msg['status'] = "ACTIVE!!"
            
            return msg
        elif obj['alertstate'] == 'firing' and obj['value'] == "0":
            msg['body'] = msg['body'] + alert + " is DEACTIVATED on instance "+obj['id'] + " at "+ obj['time'] +'\n\n'+json.dumps(obj)
            msg['status'] = "DEACTIVATED!!"
            return msg
        elif obj['alertstate'] == 'pending' and obj['value'] == "0":
            msg['body'] = msg['body']+ alert+ " is ACTIVATED!! on instance "+obj['id'] + " at "+ obj['time'] +'\n\n'+json.dumps(obj)
            msg['status'] = "ACTIVATED!!"
            return msg
