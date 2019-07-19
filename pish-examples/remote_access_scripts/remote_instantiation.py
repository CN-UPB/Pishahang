"""
A python script that can be used to instantiate a service in Pishahang remotely.

Requirements:
- Python3.6
- Pishahang's credential
- Pishahang's IP address
- The service descriptor UUID
"""


import wrappers
import json
import threading
import time

# the following 4 variables need to be populated with the right values
USERNAME = "USER"
PASSWORD = "PASS"
HOST_URL = "HOST"
NS_UUID  = "UUID"

pishahang = wrappers.SONATAClient.Auth(HOST_URL)
pishahang_nsd = wrappers.SONATAClient.Nsd(HOST_URL)
pishahang_nslcm = wrappers.SONATAClient.Nslcm(HOST_URL)

# extracting the token
token = json.loads(pishahang.auth(username=USERNAME, password=PASSWORD))
token = json.loads(token["data"])

# calling the service instantiation API 
instantiation = json.loads(pishahang_nslcm.post_ns_instances_nsinstanceid_instantiate(
                           token=token["token"]["access_token"], nsInstanceId=NS_UUID))
instantiation = json.loads(instantiation["data"])
print ("Service instantiation request has been sent!")


# extracting the request id
_rq_id = instantiation["id"]

loop = 1
while loop == 1:

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

    # checking if the instantion was successful
    if request["status"] == "ERROR":
        print ("Error in service instantiation")
        break
    elif request["status"] == "READY":
        print (request["status"] + " : Service has been successfully instantiated!")
        break

    # printing  the current status and sleep
    print (request["status"] + "...")
    time.sleep(2)
