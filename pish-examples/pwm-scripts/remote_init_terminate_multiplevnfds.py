"""
A python script that can be used to instantiate a service in Pishahang remotely.
Requirements:
- Python3.6
- python-mano-wrappers
- Pishahang's credential
- Pishahang's IP address
- The service descriptor UUID
"""

import wrappers
import json
import threading
import time
import glob, os

# the following 4 variables need to be populated with the right values
USERNAME = "sonata"
PASSWORD = "1234"
HOST_URL = "serverdemo1.cs.upb.de"

VNFDNAME = "cirros" 
NSDNAME = "cirros_3VNFS-2" #  Keep this same as this key _n['nsd']['name']
VNF_DESCRIPTORS_PATH = "/home/ashwin/Documents/WHB-Hadi/src/Pishahang/pish-examples/pwm-scripts/descriptors/multi/vnfs"
NSD_PATH = "/home/ashwin/Documents/WHB-Hadi/src/Pishahang/pish-examples/pwm-scripts/descriptors/multi/cirros2_3vnfs_nsd.yml"

TERMINATE_NS = True

pishahang = wrappers.SONATAClient.Auth(HOST_URL)
pishahang_nsd = wrappers.SONATAClient.Nsd(HOST_URL)
pishahang_nslcm = wrappers.SONATAClient.Nslcm(HOST_URL)
pishahang_vnfpkgm = wrappers.SONATAClient.VnfPkgm(HOST_URL)

# extracting the token
token = json.loads(pishahang.auth(username=USERNAME, password=PASSWORD))
token = json.loads(token["data"])

# Upload VNFs
for _file in os.listdir(VNF_DESCRIPTORS_PATH):
    print(os.path.join(VNF_DESCRIPTORS_PATH, _file))

    VNFD_PATH = (os.path.join(VNF_DESCRIPTORS_PATH, _file))
    _res = pishahang_vnfpkgm.post_vnf_packages(token=token["token"]["access_token"],
                                                package_path=VNFD_PATH)

print(_res)
time.sleep(0.5)

# Upload NSD
_res = pishahang_nsd.post_ns_descriptors(token=token["token"]["access_token"],
                                            package_path=NSD_PATH)
print(_res)
time.sleep(0.5)

# Get NSD UUID and init
_nsd_list = json.loads(pishahang_nsd.get_ns_descriptors(token=token["token"]["access_token"], limit=1000))
_nsd_list = json.loads(_nsd_list["data"])

_ns = None
for _n in _nsd_list:
    if NSDNAME == _n['nsd']['name']:            
        _ns = _n['uuid']
        print("UUID")
        print(_ns)
        continue

if _ns:
    # calling the service instantiation API 
    instantiation = json.loads(pishahang_nslcm.post_ns_instances_nsinstanceid_instantiate(
                            token=token["token"]["access_token"], nsInstanceId=_ns))
    instantiation = json.loads(instantiation["data"])
    print ("Service instantiation request has been sent!")


    # extracting the request id
    _rq_id = instantiation["id"]

    # checking the service instantiation status
    counter, timeout, sleep_interval = 0, 60, 2

    while counter < timeout:

        #calling the request API
        request = json.loads(pishahang_nslcm.get_ns_instances_request_status(
                            token=token["token"]["access_token"], nsInstanceId=_rq_id))
        request = json.loads(request["data"])

        # checking if the call was successful
        try:
            request_status = request["status"]
        except:
            print ("Error in request status chaeking!")
            break

        # checking if the instantiation was successful
        if request["status"] == "ERROR":
            print ("Error in service instantiation")
            break
        elif request["status"] == "READY":
            print (request["status"] + " : Service has been successfully instantiated!")

            if TERMINATE_NS:
                time.sleep(30)

                term_res = json.loads(
                                pishahang_nslcm.post_ns_instances_nsinstanceid_terminate(
                                token=token["token"]["access_token"], nsInstanceId=request['service_instance_uuid']))
                print("NS Terminating...")
                print(term_res)

            break

        # printing the current status and sleep
        print (request["status"] + "...")
        time.sleep(sleep_interval)
        counter += sleep_interval

    if counter > timeout:
        print ("Error: service instantiation remained incomplete")
else:
    print("Could not upload and instantiate NS")