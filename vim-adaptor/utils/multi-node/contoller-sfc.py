
#  Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, NCSR Demokritos
#  ALL RIGHTS RESERVED.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Neither the name of the SONATA-NFV, UCL, NOKIA, NCSR Demokritos
#  nor the names of its contributors may be used to endorse or promote
#  products derived from this software without specific prior written
#  permission.
#
#  This work has been performed in the framework of the SONATA project,
#  funded by the European Commission under Grant number 671517 through
#  the Horizon 2020 and 5G-PPP programmes. The authors would like to
#  acknowledge the contributions of their colleagues of the SONATA
#  partner consortium (www.sonata-nfv.eu).
#
__author__= "Stavros Kolometsos - NCSR Demokritos, Christos Sakkas - NCSR Demokritos, Dario Valocchi(Ph.D.) - UCL"


# The SFC Agent for the controller node of the PoP
import socket
import sys
import os
import time
import json
import argparse
import parser
import logging

#### FUNCTIONS
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
   return helping
   #return "ok"


def choose_port(node):
    if node == "compute1":
        port = '2'
        return port
    elif node == "compute2":
        port = '3'
        return port
    else:
        logging.error("Cannot Compute")
        port = '0'
        return port

def order_ports(ports):
    ordered_ports = []
    for item in ports:
        ordered_ports.append((item["port"],item["order"],item["vc_id"]))
    ordered_ports.sort(key=lambda tup: tup[1])
    logger.debug("Ordered the PoP list")
    return ordered_ports

def find_node(vcid):
    path = os.getcwd() # get the path for the admin-src file
    logger.debug("Source admin file from path : "+path+"/admin-openrc.sh")
    os.popen(". "+path+"/admin-openrc.sh").read()
    node = (os.popen("openstack server show "+vcid+" | awk 'FNR == 6  {print $4}'").read())  # TODO ____ Get the node
    node = node.rstrip() # stripping new lines
    logger.info("Got node back for "+vcid+". It's "+node)
    return node

def get_nodeip(node):
    logger.info("Getting IP for node: "+node)
    nodeip = (os.popen("openstack hypervisor show "+node+" | awk 'FNR == 10  {print $4}'").read())
    nodeip = nodeip.rstrip() # stripping new lines
    logger.info("IP returned: "+nodeip)
    return nodeip

def sendChain(chain,node):
    nodeip = get_nodeip(node)
    logger.info("Openning socket to send chain to node")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data = json.dumps(chain)
    sock.connect((nodeip,55555))
    logger.debug("Sending data to node")
    sock.send(data)
    logger.debug("Waiting for response from node")
    received = sock.recv(1024)
    logger.debug("Responce got: "+received)
    sock.close()
    logging.info("Chain send to node")
    return received



### Logging Config ###
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('sfc_controller.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


#configurations
parser = argparse.ArgumentParser()   #handler for arguments passed
parser.add_argument("-s", "--server",help="pass the local server ip. If not, it finds it automatically",type=str)  # option configurations, needs to be required
parser.add_argument("-i", "--brint",help="pass the connection of br-int to br-tun port, or use default '2' ",type=str)
parser.add_argument("-p", "--provider",help="pass the connection of br-provider to br-int port, or use default '2' ",type=str)

parser.add_argument("-t", "--tun",help="pass the connection of br-tun to br-int port, or use default '2' ",type=str)   # TODO number of nodes. and port corresponding to nodes

args = parser.parse_args()  # pass the arguments to the parser
# default values for ports
brintTun = "2"
brintport = "2"
brprovider = "2"

logger.info("")
logger.info("===SONATA PROJECT===")    
logger.info("Starting SFC Agent")

if args.server:  # parse the server adress passed
    server = args.server
else:
    server = get_ip() #finds IP to set up the socket
if args.brint:
    brintport = args.brint
if args.tun:
   brintTun = tun
if args.provider:
    brprovider = args.provider


# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = (server, 55555)
logger.info('starting up on %s port %s' % server_address)
sock.bind(server_address)
sock.listen(5)

while True:
    logger.info(" --- Waiting for data ---")
    conn, address = sock.accept()
    logger.info("connection established with "+str(address))
    data = conn.recv(4096)
    jsonResponse=json.loads(data)
    returnflag = "SUCCESS"
    try:
        jsonMANA = jsonResponse["action"] # Check json request type
        uuid = jsonResponse["instance_id"]
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
            ports = jsonResponse["port_list"] #get the unordered port list
            logging.debug("Starting ordering PoPs")
            portlist = order_ports(ports) # pass it the function to order it
        except:
            message="There is some error with json file"
            logger.error(message)
            conn.send(message)
            conn.close()
            continue

        logger.info("Json message succesfully ACCEPTED : "+data)
        logger.info("SOURCE SEGMENT -> "+src)
        logger.info("DESTINATION SEGMENT -> "+dst)
        fo = open("instances/"+uuid, "w")
        # Starting to place rules, beggining from driving external traffic inside to br-tun
        logger.info("PoP incoming traffic to br-provider :")
        logger.info("ovs-ofctl add-flow br-provider priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brprovider)
        os.system("ovs-ofctl add-flow br-provider priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brprovider)
        fo.write("ovs-ofctl --strict del-flows br-provider priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

        # From br-int towards br-tun
        logger.info("PoP from br-int to br-tun :")
        logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brintport)
        os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brintport)
        fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")
        #Now the traffic is inside br-tun, and logic must be applied to find out at which node has to go
        logging.debug("Grabbing the port list")
        ports = jsonResponse["port_list"]
        logging.info("Ordering the list of ports")
        portlist = order_ports(ports) # pass it the function to order it
        logging.debug(portlist)
        pairs = []
        for i in range(0,len(portlist),2):
            pair= { "in": portlist[i], "out": portlist[i+1], 'order': i }
            pairs.append(pair)
        print ("second for")
        for pair in pairs:
            vc_id = pair["in"][2]
            print vc_id
            logging.debug("Got instance: "+ vc_id)
            node = 1
            logging.info("Looking for the node of instance")
            node = find_node(vc_id)
            pair['node'] = node
        # create chain
        chain = {'action': 'add', 'pairs': pairs[0], 'exit' : "control", 'in_segment' : src, 'out_segment' : dst, 'enter': 'control' }  # Declared more than needed, just for clarity
        chained_list = [pairs[0]]
        nodeS = pairs[0]['node']
        # SEND DATA to NODE with ovs-ofctl
        logger.info("PoP from br-tun to node("+nodeS+") :")
        port = choose_port(nodeS)
        logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+port)
        os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+port)
        fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

        for num in range(1,len(pairs),1):
            if pairs[num]['node'] == pairs[num-1]['node']:

                chained_list.append(pairs[num])
            else:
                chain['pairs'] = chained_list
                chain['exit'] = pairs[num]['node']
                nodeS = pairs[num-1]['node'] # node to be send off to
                logger.debug("Splitting chain ("+str(chain)+") and sending it to node: "+nodeS)
                resev = sendChain(chain,nodeS) #SEND chain to node
                logger.info("Chain Send. Answer recieved: "+resev)

                chained_list = pairs[num] #Create clear chain with the new one
                nodeS = pairs[num]['node'] # Set new node to be sent
                chain['enter'] = nodeS

        chain['pairs'] = chained_list
        chain['exit'] = "control"
        logger.debug("Sending final chain ("+str(chain)+") to node: "+node)
        resev = sendChain(chain,nodeS)
        logger.info("Chain Send. Answer recieved: "+resev)
        logger.info("Chains send to respective node(s)")
        # Taking the traffic from node back outside 
        port = choose_port(nodeS)
        logger.info("Traffic from br-tun to br-int :")
        logger.info("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+port+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        os.system("ovs-ofctl add-flow br-tun priority=66,dl_type=0x800,in_port="+port+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        fo.write("ovs-ofctl --strict del-flows br-tun priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")
        #Traffic from br-int to br-provider
        logger.info("Traffic from br-int to br-provider :")
        logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")
        # Traffic from br-provider to outside
        logger.info("Traffic from br-provider to outside :")
        logger.info("ovs-ofctl add-flow br-provider priority=66,dl_type=0x0800,in_port="+brprovider+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        os.system("ovs-ofctl add-flow br-provider priority=66,dl_type=0x0800,in_port="+brprovider+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
        fo.write("ovs-ofctl --strict del-flows br-provider priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

        conn.send(returnflag)
        conn.close()

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