import wrappers
import json

USERNAME = "sonata"
PASSWORD = "1234"

HOST_URL = "serverdemo1.cs.upb.de"

sonata_nsd = wrappers.SONATAClient.Nsd(HOST_URL)
sonata_auth = wrappers.SONATAClient.Auth(HOST_URL)
sonata_vnfpkgm = wrappers.SONATAClient.VnfPkgm(HOST_URL)

_token = json.loads(sonata_auth.auth(
                        username=USERNAME, 
                        password=PASSWORD))

_token = json.loads(_token["data"])

# Delete NSDs
nsd_list = json.loads(sonata_nsd.get_ns_descriptors(
                    token=_token["token"]["access_token"]))
nsd_list = json.loads(nsd_list["data"])

print(nsd_list)

for _nsd in nsd_list:
    print(_nsd["uuid"])    
    sonata_nsd.delete_ns_descriptors_nsdinfoid(token=_token["token"]["access_token"], nsdinfoid=_nsd["uuid"]) 

nsd_list = json.loads(sonata_nsd.get_ns_descriptors(
                    token=_token["token"]["access_token"]))
nsd_list = json.loads(nsd_list["data"])

print(nsd_list)

# Delete VNFDs

vnf_list = json.loads(sonata_vnfpkgm.get_vnf_packages(
                    token=_token["token"]["access_token"]))
vnf_list = json.loads(vnf_list["data"])

print(vnf_list)

for _vnfd in vnf_list:
    print(_vnfd["uuid"])    
    sonata_vnfpkgm.delete_vnf_packages_vnfpkgid(token=_token["token"]["access_token"], vnfPkgId=_vnfd["uuid"]) 

vnf_list = json.loads(sonata_vnfpkgm.get_vnf_packages(
                    token=_token["token"]["access_token"]))
vnf_list = json.loads(vnf_list["data"])

print(vnf_list)
