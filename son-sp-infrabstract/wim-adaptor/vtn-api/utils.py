from newim import get_info, get_vtn
import requests
import json
import logging 
from sqlalchemy import create_engine
import pytricia

pyt = pytricia.PyTricia()
e = create_engine('sqlite:///database/wim_info.db')

def setRules(cond_name, in_seg,out_seg,ordered_pop,index):
		logging.debug("Ordered PoPs are:")
		logging.debug(ordered_pop)
		logging.info("Calling set_condition method")
		flag = set_condition(cond_name,in_seg, out_seg,index)
		logging.debug("Flag incoming:" +str(flag))
		if flag != 200:
			abort(500, message="Set condition uncompleted")
		logging.info("Condition set completed")
		flag = 200
		#TODO FIX incoming traffic 
		port_in, vbr1 = get_switch(in_seg) 
		port_out, vbr2 = get_switch(ordered_pop[0][0])
		if vbr1 == 'notsure':
			port_in = get_exit(vbr2)
		if vbr1 != vbr2 :
			port_in = get_exit(vbr2)
		bridge = vbr2 # Set final bridge
		port = port_out
		set_redirect(cond_name, vbr2, port_in, port_out,index)
		logging.info("Redirect from source to First PoP completed")
		# Redirecting through the PoPs now
		logging.debug("Redirect traffic through PoPs")
		for i in range(1,len(ordered_pop)):
			port_1, vbr1 = get_switch(ordered_pop[i-1][0])
			logging.debug("port coming is: "+port_in+" with vbridge "+vbr1)
			port_2, vbr2 = get_switch(ordered_pop[i][0])
			if vbr1 == vbr2:
				logging.debug("port to redirect is: "+port_out+" with vbridge "+vbr2)
				set_redirect(cond_name, vbr1, port_1, port_2,index)
			else:
				logging.debug("redirecting through different bridges")
				port_ex = get_exit(vbr1)
				set_redirect(cond_name, vbr1, port_1, port_ex,index)
				port_in = get_exit(vbr2)
				set_redirect(cond_name, vbr2, port_in, port_2,index)
			bridge = vbr2
			port = port_2
		logging.debug(" Inter PoP redirections completed ")
		port_out, exitbridge = get_switch(out_seg)
		if exitbridge == 'notsure':
			port_out = get_exit(bridge)
		elif exitbridge != bridge :
			logging.debug("redirecting through different bridges")
			port_ex = get_exit(bridge)
			set_redirect(cond_name, bridge, port, port_ex,index)
			port = get_exit(exitbridge)
			#set_redirect(cond_name, exitbridge, port_in, port_out)
			bridge = exitbridge
		else:
			bridge = exitbridge
		set_redirect(cond_name, bridge, port, port_out,index)
		# Need to implement (or not) going from last PoP to Outer Segment -- leaving Wan 
		#Just add to the flow array 
		logging.info("Posting new flow completed")
		return (flag)

def get_switch(seg):
	logging.debug("Incoming request for segment: "+seg)
	conn = e.connect()
	segment = pyt.get(seg)
	logging.debug("Segment to look in the database is: "+segment)
	query = conn.execute('SELECT port_id, bridge_name FROM connectivity WHERE segment="%s";'%segment)
	dt = query.fetchone()
	#TODO implement try 
	port, switch = dt[0],dt[1]
	logging.info("get_switch method completed. Returning: "+port+" "+switch+". If segment is 0.0.0.0/0, then it may not be correct")
	if segment == '0.0.0.0/0':
		switch = 'notsure'
	return (port, switch)

def get_exit(vbr):
	logging.debug("Incoming request to find exit port of vbridge: "+vbr)
	conn = e.connect()
	query = conn.execute('SELECT port_id FROM connectivity WHERE segment="0.0.0.0/0" AND bridge_name="%s";'%vbr)
	dt = query.fetchone()
	port = dt[0]
	logging.info("get_exit method completed. Returning: "+port )
	return (port )

def set_condition(cond_name, source, dest,index):
	logging.debug("Incoming set_condition call")
	s_url = 'operations/vtn-flow-condition:set-flow-condition'
	username, password, host, url, headers = get_info()
	data = {'input': {'name': cond_name, 'vtn-flow-match': [
	    {'index': index, 'vtn-inet-match': {'source-network': source, 'destination-network': dest}}]}}
	'''
	 this curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-flow-condition:set-flow-condition
	# -d '{"input":{"name":"cond1", "vtn-flow-match":[{"index":"1",
	# "vtn-inet-match":{"source-network":"10.0.0.1/32",
	# "destination-network":"10.0.0.3/32"}}]}}'
	'''
	logging.debug("Sending request to VTN to implement condition "+cond_name)
	r = requests.post(url + s_url, headers=headers,
	                  auth=(username, password), json=data)
	logging.info("Got this as response: " +str(r) )
	if not r.status_code == 200:
	    logging.error('FLOW COND ERROR ' + str(r.status_code))
	return (r.status_code)

def delete_condition(cond_name):
    s_url = 'operations/vtn-flow-condition:remove-flow-condition'
    username, password, host, url, headers = get_info()
    data = {'input': {'name': cond_name}}
    logging.debug("Sending request to delete condition "+cond_name)
    r = requests.post(url+s_url, headers=headers, auth=(username, password), json=data)
    logging.info("Got response:" +str(r))
    if not r.status_code == 200:
    	logging.error("Condition removal ERROR " + str(r.status_code))
    return (r.status_code)

def set_redirect(cond_name, vbr, port_id_in, port_id_out,index):
	s_url = 'operations/vtn-flow-filter:set-flow-filter'
	logging.debug("Incoming set_redirect call")
	username, password, host, url, headers = get_info()
	vtn_name = get_vtn_name()
	data = {"input": {"output": "false", "tenant-name": vtn_name, "bridge-name": vbr, "interface-name": port_id_in, "vtn-flow-filter": [
	    {"index": index, "condition": cond_name, "vtn-redirect-filter": {"redirect-destination": {"bridge-name": vbr, "interface-name": port_id_out}, "output": "true"}}]}}
	'''
	 this: curl --user "username":"pass" -H "Content-type: application/json" -X POST http://localhost:8181/restconf/operations/vtn-flow-filter:set-flow-filter
	  -d '{"input":{"output":"false","tenant-name":"vtn1", "bridge-name":"vbr", interface-name":"if5", "vtn-flow-filter":[{"condition":"cond_1","index":"1","vtn-redirect-filter":
	  {"redirect-destination":{"bridge-name":"vbr1","interface-name":"if3"},"output":"true"}}]}}'
	'''
	logging.debug("Sending request to set condition: "+str(data))
	r = requests.post(url + s_url, headers=headers,
	                  auth=(username, password), json=data)
	logging.info("Got response:" +str(r))
	if not r.status_code == 200:
	    logging.error('FLOW FILTER ERROR ' + str(r.status_code))

def get_vtn_name():
	name = get_vtn()
	return name

def order_pop(pops):
	ordered_pop = []
	for item in pops:
		ordered_pop.append((item["port"],item["order"]))
	ordered_pop.sort(key=lambda tup: tup[1])
	logging.debug("Ordered the PoP list")
	return ordered_pop

def get_locations():
	logging.debug("Incoming request for location")
	conn = e.connect()
	query = conn.execute('SELECT segment, location FROM connectivity;')
	dt = query.fetchall()
	logging.debug("Show locations: " + str(dt))
	locations = []
	for d in dt:
		dicti = {"segment" : d[0], "location" : d[1]}
		locations.append(dicti)	
	return locations 	 

def pop_nets():
	logging.debug("Populating network segments table")
	conn = e.connect()
	query = conn.execute('SELECT segment FROM connectivity;')	
	dt = query.fetchall()
	logging.debug("Show segments: " + str(dt))
	for d in dt: 
		pyt[d[0]] = d[0]



