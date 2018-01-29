import argparse
import yaml
import json
import requests
from __builtin__ import True, exit



parser = argparse.ArgumentParser()
parser.add_argument ('-c','--configuration', help = 'important configuration inputs', nargs=3, metavar =('host','username','password'))
parser.add_argument("-df", "--drop-filter", help="drop the damn flow filter")  # option configurations, needs to be required
parser.add_argument('-i','--installation', help = 'configure the VTN', nargs =1, metavar =('vtn_name'))
parser.add_argument('-d','--delete', help = 'delete given VTN', nargs =1, metavar =('vtn_name'))
parser.add_argument ('-sf','--set-flow', help = 'set flow condition', nargs=4, metavar =('condition','source_net','dest_net', 'vtn_name'))
parser.add_argument('-m','--modify', help = 'modify the condition', nargs =1, metavar =('condition'))
args = parser.parse_args()  # pass the arguments to the parser

if args.configuration:
	host, username, password = args.configuration
	url = 'http://'+host+':8181/restconf/' #this is should be the same always
	headers = {'Content type' : 'application/json'} #also this 


if args.drop_filter:  # actions to do from the drop_filter
	s_url = 'operations/vtn-flow-filter:set-flow-filter'
	intf1 = 'if1' # needed for data 
	data = {"input": {"tenant-name":  vtn_name , "bridge-name": vbr, "interface-name":intf1, "vtn-flow-filter":[{"index": "1", "condition":cond, "vtn-drop-filter":{}}]}}
	r = requests.post(url+s_url, headers=headers, auth=(username,password), json=data)
    

# Create VTN 
if args.installation:
	vtn_name= args.installation[0]
	#create VTN 
	p_url = 'operations/vtn:update-vtn'
	data = {'input' : {'tenant-name': vtn_name}}
	
	r = requests.post(url+p_url, headers = headers, auth=(username, password), json=data) # this : curl --user "username":"pass" -H "Content-type: application/json" -X POST http://10.30.0.13:8181/restconf/operations/vtn:update-vtn -d '{"input":{"tenant-name":"vtn1"}}'
	if not r.status_code==200:
		print 'VTN ERROR ' + str(r.status_code)
		exit(1) 
	#create vbridge in VTN
	vbr = 'vbr4'
	b_url ='operations/vtn-vbridge:update-vbridge'
	data = {'input': { 'tenant-name': vtn_name, 'bridge-name' : vbr}}
	r = requests.post(url+b_url, headers = headers, auth=(username, password), json=data) # this : curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-vbridge:update-vbridge -d '{"input":{"tenant-name":"vtn1", "bridge-name":"vbr1"}}'
	print '1st Request out' + str(r.status_code)
	if not r.status_code==200:
		print 'BRIDGE ERROR ' + str(r.status_code)
		exit(1)
		
	# create and map interfaces through file 
	i_url = 'operations/vtn-vinterface:update-vinterface'
	m_url = 'operations/vtn-port-map:set-port-map'
	with open("/adaptor/configs.txt", "r+") as file:
		while True:
			interface = file.readline()
			if not interface: break
			node = file.readline()
			print (node)
			port = file.readline()		
			print (port)
			node=node[:-2]
			port=port[:-2]
			
			interface=interface[:-2]
						#create interface
			data = {'input' : {'tenant-name': vtn_name, 'bridge-name': vbr, 'interface-name':interface }} 
							
			r = requests.post(url+i_url, headers = headers, auth=(username, password), json=data)  # this : curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-vinterface:update-vinterface -d '{"input":{"tenant-name":"vtn1", "bridge-name":"vbr1", "interface-name":"if1"}}
			if not r.status_code==200:
				print 'PORT CREATION ERROR '+str(r.status_code)
				print str(data)
				exit(1)#map interface 
			
			data = {'input' : {'tenant-name': vtn_name, 'bridge-name': vbr, 'interface-name':interface, 'node': node , 'port-name' : port }}
			r = requests.post(url+m_url, headers = headers, auth=(username, password), json=data)  #this : curl --user "username":"pass" -H "Content-type: application/json" -X POST http://10.30.0.13:8181/restconf/operations/vtn-port-map:set-port-map -d '{"input":{"tenant-name":"vtn1", "bridge-name":"vbr1", "interface-name":"if2", "node":"openflow:3", "port-name":"s3-eth1"}}'
			if not r.status_code==200:
				print 'PORT MAP ERROR '+str(r.status_code)
				print str(data)
				exit(1)
			else:
				print ("Success interface mapping "+interface)
				
	print 'SUCCESS'

	
#set the flow between the source and destination address and then enable filter
if args.set_flow:
	cond, source_net, dest_net, vtn_name = args.set_flow
	cond = "green"
	vbr = 'vbr4'
	s_url = 'operations/vtn-flow-condition:set-flow-condition'
	data = {'input' : {'name': cond, 'vtn-flow-match': [{'index': '1','vtn-inet-match':{ 'source-network': source_net, 'destination-network': dest_net }}]}}
	r = requests.post(url+s_url, headers=headers, auth=(username,password), json=data) # this curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-flow-condition:set-flow-condition -d '{"input":{"name":"cond1", "vtn-flow-match":[{"index":"1", "vtn-inet-match":{"source-network":"10.0.0.1/32", "destination-network":"10.0.0.3/32"}}]}}'
	if not r.status_code==200:
		print 'FLOW COND ERROR '+str(r.status_code)
		exit(1)

	s_url = 'operations/vtn-flow-filter:set-flow-filter'
	intf8 = 'if8' # needed for data 
	intf10 = 'if10'
	data = {"input": { "output": "false", "tenant-name":  vtn_name , "bridge-name": vbr, "interface-name":intf8, "vtn-flow-filter":[{"index": "1", "condition":cond, "vtn-redirect-filter":{"redirect-destination": {"bridge-name": vbr, "interface-name": intf10}, "output": "true"}}]}}
	r = requests.post(url+s_url, headers=headers, auth=(username,password), json=data) # this: curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-flow-filter:set-flow-filter -d -d '{"input":{"output":"false","tenant-name":"vtn1", "bridge-name": "vbr1", "interface-name":"if5","vtn-flow-filter":[{"condition":"cond_1","index":"1","vtn-redirect-filter":{"redirect-destination":{"bridge-name":"vbr1","interface-name":"if3"},"output":"true"}}]}}'
	if not r.status_code==200: 
		print 'FLOW FILTER ERROR '+str(r.status_code)
		exit(1)
	else:
		print 'SUCCESS'
	
# Delete VTN 
if args.delete:
	vtn = args.delete[0]
	d_url = 'operations/vtn:remove-vtn'
	data = {'input': {'tenant-name': vtn }}
	r = requests.post(url + d_url, headers = headers, auth=(username,password), json= data) # this: curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn:remove-vtn -d '{"input":{"tenant-name":"vtn1"}}'
	if not r.status_code==200:
		print 'VTN DEL ERROR '+str(r.status_code)
		exit(1)
	else:
		print 'SUCCESS'

if args.modify:
	cond = args.modify[0]
	vtn_name = "vtn7"
	cond = "green"
	s_url = 'operations/vtn-flow-filter:set-flow-filter'
	vbr = "vbr4"
	intf8 = 'if8' # needed for data 
	intf6= 'if6'
	data = {"input": { "output": "false", "tenant-name":  vtn_name , "bridge-name": vbr, "interface-name":intf8, "vtn-flow-filter":[{"index": "1", "condition":cond, "vtn-redirect-filter":{"redirect-destination": {"bridge-name": vbr, "interface-name": intf6}, "output": "true"}}]}}
	r = requests.post(url+s_url, headers=headers, auth=(username,password), json=data) # this: curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-flow-filter:set-flow-filter -d -d '{"input":{"output":"false","tenant-name":"vtn1", "bridge-name": "vbr1", "interface-name":"if5","vtn-flow-filter":[{"condition":"cond_1","index":"1","vtn-redirect-filter":{"redirect-destination":{"bridge-name":"vbr1","interface-name":"if3"},"output":"true"}}]}}'
	if not r.status_code==200: 
		print 'FLOW FILTER ERROR '+str(r.status_code)
		exit(1)
	else:
		print 'SUCCESS' 
