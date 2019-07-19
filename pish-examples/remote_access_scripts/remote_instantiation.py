import wrappers
import json
import threading
import time

USERNAME = "USER"
PASSWORD = "PASS"
HOST_URL = "HOST"
NS_UUID  = "UUID"

pishahang = wrappers.SONATAClient.Auth(HOST_URL)
pishahang_nsd = wrappers.SONATAClient.Nsd(HOST_URL)
pishahang_nslcm = wrappers.SONATAClient.Nslcm(HOST_URL)

token = json.loads(pishahang.auth(username=USERNAME, password=PASSWORD))
token = json.loads(token["data"])

instantiation = json.loads(pishahang_nslcm.post_ns_instances_nsinstanceid_instantiate(
                           token=token["token"]["access_token"], nsInstanceId=NS_UUID))
instantiation = json.loads(instantiation["data"])

print ("Service instantiation request has been sent!")
_rq_id = instantiation["id"]

loop = 1
while loop == 1:
    request = json.loads(pishahang_nslcm.get_ns_instances_request_status(
                            token=token["token"]["access_token"], nsInstanceId=_rq_id))
    request = json.loads(request["data"])

    try:
        request_status = request["status"]
    except:
        print ("Error in request status chaeking!")
        break

    if request["status"] == "ERROR":
        print ("Error in service instantiation")
        break
    elif request["status"] == "READY":
        print (request["status"] + " : Service has been successfully instantiated!")
        break

    print (request["status"] + "...")
    time.sleep(2)
