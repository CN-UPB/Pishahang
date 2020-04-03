#
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
__author__= "Christos Sakkas - NCSR Demokritos, Stavros Kolometsos - NCSR Demokritos, Dario Valocchi(Ph.D.) - UCL"



import socket
import sys
import os
import time
import json
import argparse
import parser
import logging 
import glob

### Logging Config ### 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('sfc.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

### Functions ###

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

def setInOut(src,dst):
    print "PoP first-in rule:"
    logger.info("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+breth0port)
    print "ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+breth0port
    os.system("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+breth0port)
    fo.write("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")

    print "PoP traffic-out rule:" #take the incoming traffic from src to dst and pass it to br-ex
    logger.info("PoP final traffic-out rule:")
    logger.info("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port="+breth0port+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
    print "ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port="+breth0port+",nw_src="+src+",nw_dst="+dst+",actions=output:1"
    os.system("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port="+breth0port+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
    fo.write("ovs-ofctl add-flow br-eth0 priority=66,dl_type=0x0800,in_port="+breth0port+",nw_src="+src+",nw_dst="+dst+"\n")

    print "PoP in rule:" #take traffic from 1st port of br-ex and take it to phy-br-ex (to br-int essentialy)
    logger.info("PoP in rule")
    print "ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brexport
    logger.info("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brexport)
    os.system("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+",actions=output:"+brexport)
    fo.write("ovs-ofctl --strict del-flows br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+src+",nw_dst="+dst+"\n")
    logger.info( "PoP in rule; reverse") #take traffic from 1st port of br-ex and take it to phy-br-ex (to br-int essentialy)
    logger.info( "ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+",actions=output:"+brexport)
    os.system("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+",actions=output:"+brexport)
    fo.write("ovs-ofctl --strict del-flows br-ex priority=66,dl_type=0x800,in_port=1,nw_src="+dst+",nw_dst="+src+"\n")

    print "PoP out rule:" #take traffic from incoming traffic from br-int to br-eth0
    logger.info("PoP out rule")
    print "ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+src+",nw_dst="+dst+",actions=output:1"
    logger.info("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
    os.system("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+src+",nw_dst="+dst+",actions=output:1")
    fo.write("ovs-ofctl --strict del-flows br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+src+",nw_dst="+dst+"\n")
    logger.info("PoP out rule; reverse") #take traffic from incoming traffic from br-int to br-eth0
    logger.info("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+dst+",nw_dst="+src+",actions=output:1")
    os.system("ovs-ofctl add-flow br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+dst+",nw_dst="+src+",actions=output:1")
    fo.write("ovs-ofctl --strict del-flows br-ex priority=66,dl_type=0x800,in_port="+brexport+",nw_src="+dst+",nw_dst="+src+"\n")

def setSFC(src, dst, portlist):
    returnflag = 'SUCCESS'
    # Install the redirection rules
    print "Rule First: " # take the traffic from br-int to the first virtual interface 
    logger.info("Rule First: ") 
    firstport = findPort(portlist[0])
    mac = portlist[0]
    if (firstport==""):
        logger.error("Error in finding port_list")
        returnflag = "Error in finding port list"
    logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+firstport)
    print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+firstport
    os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+firstport)
    fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+brintport+",nw_src="+src+",nw_dst="+dst+"\n")

    for i in range (2,len(portlist)-1,2):   #take the traffic from one virtual interface to another 
        #print "in-> "+portlist[i-1]+" - out-> "+portlist[i]
        inport = findPort(portlist[i-1])
        if (inport==""):
            returnflag = "Error in finding port list"
            logger.error("ERROR in finding port list")
        outport = findPort(portlist[i])
        mac = portlist[i]
        if (outport==""):
            returnflag = "Error in finding port list"
            logger.error("ERROR in finding port list")
        logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+outport)
        print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+outport
        os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+",actions=mod_dl_dst:"+mac+",output:"+outport)
        fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+inport+",nw_src="+src+",nw_dst="+dst+"\n")

    print "Last Rule: " #take the traffic from the last virtual inteface to br-int 
    logger.info("Last Rule: ")
    lastport = findPort(portlist[len(portlist)-1])
    if (lastport==""):
        returnflag = "Error in finding port list"
        logger.error("ERROR in finding port list")
    logger.info("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+brintport)
    print "ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+brintport
    os.system("ovs-ofctl add-flow br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+",actions=output:"+brintport)
    fo.write("ovs-ofctl --strict del-flows br-int priority=66,dl_type=0x800,in_port="+lastport+",nw_src="+src+",nw_dst="+dst+"\n")

    return (returnflag)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

###   Main Part ###

parser = argparse.ArgumentParser()   #handler for arguments passed 
parser.add_argument("-s", "--server",help="pass the local server ip. If not, it finds it automatically",type=str)  # option configurations, needs to be required
parser.add_argument("-i", "--brint",help="pass the connection of br-int to br-ex port, or use default '2' ",type=str)
parser.add_argument("-e", "--brex",help="pass the connection of br-ex to br-int port, or use default '2' ",type=str)
parser.add_argument("-t", "--breth",help="pass the connection of br-eth0 to br-ex port, or use default '3' ",type=str)
args = parser.parse_args()  # pass the arguments to the parser
# default values for ports 
brexport = "2"
brintport = "2"
breth0port = "3"

print ""
print ""
print "===SONATA PROJECT==="
print "SFC-AGENT Initializing..."
print ""
print ""
logger.info("Started SFC-AGENT")
if args.server:  # parse the server adress passed
    server = args.server
else:
    server = get_ip() #finds IP to set up the socket 
if args.brint:
    brintport = args.brint
if args.brex:
    brexport = args.brex
if args.breth:
    breth0port = args.breth 

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (server, 55555)
print >>sys.stderr, 'starting up on %s port %s' % server_address
logger.info('starting up on %s port %s' % server_address)
sock.bind(server_address)
sock.listen(5)

while True:
    print ""
    print "Waiting for data ..."
    logger.info(" --- Waiting for data ---")
    try:
        conn, address = sock.accept()
        logger.info("connection established with "+str(address))
    except:
        logger.error("Error when establishing connection")
        logger.error( "The error: "+str(er))
        continue
    try:
        data = conn.recv(4096)
        print (address)
        logger.info("Recieved data from:" + str(address))
        jsonResponse=json.loads(data)
    except Exception as er:
        logger.error("Something went wrong when recieving data")
        logger.error( "The error: "+str(er))
        continue

    returnflag = "SUCCESS"
    try: 
        jsonMANA = jsonResponse["action"] # Check json request type 
        jsonData0 = jsonResponse["instance_id"]
    except KeyError:
        message="There is some error with json file"
        logger.error(message)
        print message 
        conn.send(message)
        conn.close()
        continue

    if (jsonMANA=="add"):
        try:
            jsonData = jsonResponse["in_segment"]
            jsonData2 = jsonResponse["out_segment"]
        except:
            message="There is some error with json file"
            print message
            logger.error(message)
            conn.send(message)
            conn.close()
            continue

        logger.info("Json message succesfully accepted: "+data)
        print ("SOURCE SEGMENT -> "+jsonData)
        print ("DESTINATION SEGMENT -> "+jsonData2)
        uuid = jsonData0
        fo = open(uuid, "w")
        src = jsonData
        dst = jsonData2
        #for the rules to be installed: print them, install and log them, ready to be deleted.
        setInOut(src,dst)
        setInOut(dst,src)

        jsonData3 = jsonResponse["port_list"] #get the port list
        portlist = []
        for item in jsonData3:
            port = item.get("port")
            order = item.get("order")
            portlist.append(port)
        list_r = portlist[::-1] #getting a reverse portlist
        revPortlist = sum(zip(list_r[1::2], list_r[::2]), ())
        
        returnflag = setSFC(src,dst,portlist)
        print returnflag
        logger.info("Got return flag from firts set of rules: " +returnflag)

        returnflag = setSFC(dst, src, revPortlist)
        # Reply Success or Error 
        print returnflag
        logger.info("Sending return flag: " +returnflag)
        conn.send(returnflag)
        fo.close()  
        conn.close()
        logger.info("Proccess Completed. Returning to Start")

    #if request is to delete, then:      
    elif (jsonMANA=="delete"):
        print "DELETING-> "+jsonData0
        logger.info("Message to delete recieved")
        logger.info(" DELETING --> "+jsonData0)
        #os.system("rm "+jsonData0)
        try:
         for fi in glob.glob(jsonData0+"*"):
            logger.info("Deleting --> "+fi)
            f = open(fi, 'r')
            for line in f:
              print line
              logger.info(line)
              os.system(line)
         logger.info("SFC Chain rules deleted")
         conn.send("SUCCESS")
         conn.close()
         logger.info("Proccess Completed. Returning to Start")
        except IOError:
          logger.error("No such name file")
          conn.send("No instance-ID SFC rules with this name")
          conn.close()
          logger.info("Returning to Start")
    # not add or delete 
    else:
        message = "This function is not supported. Please check your json file"
        logger.info("Recieved not supported function. Sending message")
        logger.info(message)
        print message
        conn.send(message)
        conn.close()
        logger.info("Proccess Completed. Returning to Start")
