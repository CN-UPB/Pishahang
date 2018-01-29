# The SFC agent for the compute node of the PoP 
import socket
import logging
import json
import os
import argparse
import parser 

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def findPort(mac):
   mac = mac[9:17]
   #print mac
   helper3 = os.popen("ovs-ofctl dump-ports-desc br-int | grep "+mac).read()
   helping = ""
   for i in range(1,len(helper3)):
      #print helper3[i]
      if (helper3[i]=="("):
          break
      helping = helping+helper3[i]
   #print helping
   return helping
   #return "ok"


### Logging Config ### 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('sfc.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

## Main part 
logger.info("")
logger.info("===SONATA PROJECT===")    
logger.info("Starting SFC Node Agent")

server = get_ip()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (server, 55555)
logger.info('starting up on %s port %s' % server_address)
sock.bind(server_address)
sock.listen(5)

#configurations
parser = argparse.ArgumentParser()   #handler for arguments passed
parser.add_argument("-m", "--compute",help="pass the name of the other node",type=str)  # option configurations, needs to be required
parser.add_argument("-i", "--brint",help="pass the connection of br-int to br-tun port, or use default '1' ",type=str)
parser.add_argument("-c", "--control",help="pass the connection of br-tun to contoller, or use default '2' ",type=str)
parser.add_argument("-n", "--node",help="pass the connection of br-int to the other node, or use default '3' ",type=str)   # TODO number of nodes. and port corresponding to nodes

args = parser.parse_args()  # pass the arguments to the parser
# default values for ports
server = get_ip()

if args.compute:  # parse the server adress passed
    compute = args.compute
if args.brint:
    brintport = args.brint
else:
	brintport = '1'
if args.control:
   brcontrol = args.control
else:
	brcontrol = '2'
if args.node:
    brnode = args.node
else: 
	brnode = '3'


while True:
	logger.info(" --- Waiting for data ---")
	conn, address = sock.accept()
	logger.info("connection established with "+str(address))
	data = conn.recv(4096)
	jsonResponse=json.loads(data)
	returnflag = "SUCCESS"
	try:
	    jsonMANA = jsonResponse["action"] # Check json request type
	    #uuid = jsonResponse["instance_id"]
	    # TODO ----- ADD uuid in message send from controller
	    uuid = jsonResponse["instance_id"]
	    exit = jsonResponse["exit"] 
	except KeyError:
	    message="There is some error with json file"
	    logger.error(message)
	    conn.send(message)
	    conn.close()
	    continue
	if (jsonMANA=="add"):
	    try:
			src = jsonResponse["in_segment"]
			dst = jsonResponse["out_segment"]
			enter = jsonResponse['enter']
			exit = jsonResponse['exit']
			pairs = jsonResponse["pairs"] #get the unordered port list
	    except:
	        message="There is some error with json file"
	        logger.error(message)
	        conn.send(message)
	        conn.close()
	        continue
		logger.info("Json message succesfully ACCEPTED : "+data)
		logger.info("SOURCE SEGMENT -> "+src)
		logger.info("DESTINATION SEGMENT -> "+dst)
		fo = open(uuid, "w")	
		portlist = []
		for item in pairs:
		    port = item.get("in")
		    portlist.append(port[0])
		    port = item.get("out")
		    portlist.append(port[0])
		logger.info("Create port list for SFC rules: "+ str(portlist))
		
		# TODO __ FIX recognise if traffic from control or some other node
		if enter == 'control':
			logger.info("Taking traffic from br-tun to br-int")
			logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+brcontrol+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
			os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+brcontrol+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
			fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x800,in_port="+brcontrol+",nw_src="+src+",nw_dst="+dst+"\n")
		elif enter == compute:
			logger.info("Taking traffic from br-tun to br-int")
			logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+brnode+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
			os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+brnode+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
			fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x800,in_port="+brnode+",nw_src="+src+",nw_dst="+dst+"\n")
		

		logger.info("Rule First: ") 
		firstport = findPort(portlist[0])
		if (firstport==""):
		    logger.error("Error in finding port_list")
		    returnflag = "Error in finding port list"
		logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+firstport)
		os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+firstport)
		fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

		logger.info("And in reverse:")
		logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+",actions=output:"+firstport)
		os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+",actions=output:"+firstport)
		fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+"\n")

		for i in range (2,len(portlist)-1,2):   #take the traffic from one virtual interface to another 
		    #print "in-> "+portlist[i-1]+" - out-> "+portlist[i]
		    inport = findPort(portlist[i-1])
		    if (inport==""):
		        returnflag = "Error in finding port list"
		        logger.error("ERROR in finding port list")
		    outport = findPort(portlist[i])
		    if (outport==""):
		        returnflag = "Error in finding port list"
		        logger.error("ERROR in finding port list")

		    logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+outport)
		    print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+outport
		    os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+outport)
		    fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+"\n")

		    logger.info("And in reverse:")
		    logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+dst+",nw_dst="+src+",actions=output:"+outport)
		    print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+dst+",nw_dst="+src+",actions=output:"+outport
		    os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+dst+",nw_dst="+src+",actions=output:"+outport)
		    fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+dst+",nw_dst="+src+"\n")


		print "Last Rule: " #take the traffic from the last virtual inteface to br-int 
		logger.info("Last Rule: ")

		lastport = findPort(portlist[len(portlist)-1])
		if (lastport==""):
		    returnflag = "Error in finding port list"
		    logger.error("ERROR in finding port list")

		logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
		print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:1"
		os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
		fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+"\n")

		logger.info("And in reverse:")
		logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+dst+",nw_dst="+src+",actions=output:1")
		print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+dst+",nw_dst="+src+",actions=output:1"
		os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+dst+",nw_dst="+src+",actions=output:1")
		fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+dst+",nw_dst="+src+"\n")        

		# TODO -- recognize where to send the traffic 
		if exit == 'control':
			logger.info("Taking traffic from br-tun to outside")
			logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brcontrol)
			os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brcontrol)
			fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")
		elif exit == compute:
			logger.info("Taking traffic from br-tun to outside")
			logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brnode)
			os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brnode)
			fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

		# Reply Success or Error 
		print returnflag
		logger.info("Sending return flag: " +returnflag)
		conn.send(returnflag)
		conn.close()
		fo.close()       
		logger.info("Proccess Completed. Returning to Start")


	elif (jsonMANA=='delete'):
		conn.send(returnflag)
		conn.close()
		continue

	else:
		message = "This function is not supported. Please check your json file"
		logger.info("Recieved not supported function. Sending message")
		logger.info(message)
		conn.send(message, address)
		conn.close()
		logger.info("Proccess Completed. Returning to Start")

	#logging.info("Data received: "+jsonResponse)
conn.send("SUCCESS")
conn.close()