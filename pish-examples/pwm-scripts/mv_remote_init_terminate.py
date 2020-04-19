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

from kubernetes import client

from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client as nvclient

from heatclient import client as hclient
from dateutil import parser

TERMINATE_NS = False
CLEAR_VIM = True
CLEAR_DESCRIPTORS = True

AUTH_URL = ""
K8_URL = ""
HOST_URL = ""
ATOKEN = ""

OS_USERNAME = "admin"
OS_PASSWORD = "1234"
OS_PROJECT = "demo"

aConfiguration = client.Configuration()
aConfiguration.host = K8_URL

aConfiguration.verify_ssl = False
aConfiguration.api_key = {"authorization": "Bearer " + ATOKEN}

aApiClient = client.ApiClient(aConfiguration)

USERNAME = "pishahang"
PASSWORD = "1234"

# VNFDNAME = "transcoder_mv"
# NSDNAME = "transcoder_mv" #  Keep this same as this key _n['nsd']['name']
VNFDNAME = "cirros1_mv"
NSDNAME = "cirros1_mv" #  Keep this same as this key _n['nsd']['name']

DESCRIPTORS_PATH = "/home/ashwin/Documents/MSc/Thesis/src/Pishahang/pish-examples/pwm-scripts/descriptors/multiversion"

# #####################################################

def delete_replication_controller():

    v1 = client.CoreV1Api(aApiClient)
    ret = v1.list_namespaced_replication_controller(namespace='default', watch=False)
    for i in ret.items:
    #   print("%s\t%s" %
    #         (i.metadata.name, i.metadata.creation_timestamp))

      api_instance = client.CoreV1Api(aApiClient)
      body = client.V1DeleteOptions()
      api_response = api_instance.delete_namespaced_replication_controller(i.metadata.name, i.metadata.namespace, body=body)

def delete_pod():

    v1 = client.CoreV1Api(aApiClient)
    ret = v1.list_namespaced_pod(namespace='default', watch=False)
    for i in ret.items:
    #   print("%s\t%s" %
    #         (i.metadata.name, i.metadata.creation_timestamp))

      api_instance = client.CoreV1Api(aApiClient)
      body = client.V1DeleteOptions()
      api_response = api_instance.delete_namespaced_pod(i.metadata.name, i.metadata.namespace, body=body)

def delete_services():

    v1 = client.CoreV1Api(aApiClient)
    ret = v1.list_namespaced_service(namespace='default', watch=False)
    for i in ret.items:
    #   print("%s\t%s" %
    #         (i.metadata.name, i.metadata.creation_timestamp))

      api_instance = client.CoreV1Api(aApiClient)
      body = client.V1DeleteOptions()
      api_response = api_instance.delete_namespaced_service(i.metadata.name, i.metadata.namespace, body=body)

# #####################################################

if CLEAR_VIM:
    delete_replication_controller()
    delete_pod()
    delete_services()

    time.sleep(5)
# #####################################################
pishahang = wrappers.SONATAClient.Auth(HOST_URL)
pishahang_nsd = wrappers.SONATAClient.Nsd(HOST_URL)
pishahang_nslcm = wrappers.SONATAClient.Nslcm(HOST_URL)
pishahang_vnfpkgm = wrappers.SONATAClient.VnfPkgm(HOST_URL)
pishahang_pish = wrappers.SONATAClient.Pishahang(HOST_URL)

# #####################################################
if CLEAR_DESCRIPTORS:
    _token = json.loads(pishahang.auth(
                            username=USERNAME, 
                            password=PASSWORD))

    _token = json.loads(_token["data"])

    # Delete NSDs
    nsd_list = json.loads(pishahang_nsd.get_ns_descriptors(
                        token=_token["token"]["access_token"]))
    nsd_list = json.loads(nsd_list["data"])

    print(nsd_list)

    for _nsd in nsd_list:
        print(_nsd["uuid"])    
        pishahang_nsd.delete_ns_descriptors_nsdinfoid(token=_token["token"]["access_token"], nsdinfoid=_nsd["uuid"]) 

    nsd_list = json.loads(pishahang_nsd.get_ns_descriptors(
                        token=_token["token"]["access_token"]))
    nsd_list = json.loads(nsd_list["data"])

    print(nsd_list)

    # Delete VNFDs

    vnf_list = json.loads(pishahang_vnfpkgm.get_vnf_packages(
                        token=_token["token"]["access_token"]))
    vnf_list = json.loads(vnf_list["data"])

    print(vnf_list)

    for _vnfd in vnf_list:
        print(_vnfd["uuid"])    
        pishahang_vnfpkgm.delete_vnf_packages_vnfpkgid(token=_token["token"]["access_token"], vnfPkgId=_vnfd["uuid"]) 

    vnf_list = json.loads(pishahang_vnfpkgm.get_vnf_packages(
                        token=_token["token"]["access_token"]))
    vnf_list = json.loads(vnf_list["data"])

    print(vnf_list)

    print(pishahang_pish.delete_pd_descriptors_pdpkgid(NSDNAME))
    time.sleep(5)

# #####################################################

# extracting the token
token = json.loads(pishahang.auth(username=USERNAME, password=PASSWORD))
token = json.loads(token["data"])

# Upload VNF
VNFD_PATH = "{desc}/{name}_vnfd.yml".format(desc=DESCRIPTORS_PATH, name=VNFDNAME)
_res = pishahang_vnfpkgm.post_vnf_packages(token=token["token"]["access_token"],
                                            package_path=VNFD_PATH)
print(_res)
time.sleep(0.5)

# Upload NSD
NSD_PATH = "{desc}/{name}_nsd.yml".format(desc=DESCRIPTORS_PATH, name=NSDNAME)
_res = pishahang_nsd.post_ns_descriptors(token=token["token"]["access_token"],
                                            package_path=NSD_PATH)
print(_res)
time.sleep(0.5)

# Upload PD
PD_PATH = "{desc}/{name}_policy.yml".format(desc=DESCRIPTORS_PATH, name=NSDNAME)
_res = pishahang_pish.post_pd_descriptors(package_path=PD_PATH)
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