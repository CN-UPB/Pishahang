import os
import subprocess
import sys
import zmq


SDN_CONTROLLER_ADDRESS = "131.234.250.116"

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://{}:50165".format(SDN_CONTROLLER_ADDRESS))

mapping = {}


name = sys.argv[1]
vlan = sys.argv[2]

cn_id = subprocess.check_output('sudo docker ps -q -f name=k8s_{0}'.format(name), shell=True)
cn_id = cn_id.strip()
print ("cn_id= %s" % cn_id)

pid = subprocess.check_output("sudo docker inspect --format '{{ .State.Pid }}' %s" % (cn_id), shell=True)
pid = pid.strip()
print ("pid= %s" % pid)

mac = subprocess.check_output("sudo nsenter -t %s -n ifconfig eth0 | grep 'HWaddr' | cut -d 'H' -f 2 | cut -d ' ' -f 2" % pid, shell=True)
mac = mac.strip()
print ("mac= %s" % mac)


ip = subprocess.check_output("sudo nsenter -t %s -n ifconfig eth0 | grep 'inet addr' | cut -d ':' -f 2 | cut -d ' ' -f 1"% pid, shell=True)
ip = ip.strip()
print ("ip= %s" % ip)


if_name = subprocess.check_output("sudo route | grep %s |grep 'romana' | cut -d '-' -f 2" % ip, shell=True)
if_name = if_name.strip()
if_name = "romana-"+if_name
print ("if_name= %s" % if_name)

rules = subprocess.check_output("sudo ovs-vsctl add-port pish-int %s " % if_name, shell=True)
print (rules+rules)

routes = subprocess.check_output("sudo route del -net %s netmask 255.255.255.255 dev %s" % (ip, if_name), shell=True)
print (routes+routes)

mapping = {"VLAN": vlan, "IP":ip, "MAC":mac}

#mapping = {'IP': '10.112.0.16', 'MAC':'ea:f2:4b:a8:6d:ba','VLAN':'10'}
socket.send_json(mapping)
print("Received " + socket.recv_json()["reply"] + " event.")
