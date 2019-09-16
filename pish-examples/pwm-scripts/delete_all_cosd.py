import wrappers
import json
from wrappers import SONATAClient

USERNAME = "sonata"
PASSWORD = "1234"

HOST_URL = "serverdemo1.cs.upb.de"


def sonata_cleanup():
    sonata_nsd = SONATAClient.Nsd(HOST_URL)
    sonata_pishahang = SONATAClient.Pishahang(HOST_URL)
    sonata_nslcm = SONATAClient.Nslcm(HOST_URL) 
    sonata_auth = SONATAClient.Auth(HOST_URL)
    sonata_vnfpkgm = SONATAClient.VnfPkgm(HOST_URL)

    print("Sonata NSD/VNFD Cleanup")

    _token = json.loads(sonata_auth.auth(
                    username=USERNAME,
                    password=PASSWORD))
    _token = json.loads(_token["data"])

    _csd_list = json.loads(sonata_pishahang.get_csd_descriptors(
                    token=_token, limit=1000,))
    _csd_list = json.loads(_csd_list["data"])

    print(len(_csd_list))
    for _csd in _csd_list:
        sonata_pishahang.delete_csd_descriptors_csdpkgid(
                    token=_token,
                    csdpkgid=_csd['uuid'])

    _cosd_list = json.loads(sonata_pishahang.get_cosd_descriptors(
                    token=_token, limit=1000))
    _cosd_list = json.loads(_cosd_list["data"])

    print(len(_cosd_list))
    for _cosd in _cosd_list:
        sonata_pishahang.delete_cosd_descriptors_cosdpkgid(
                    token=_token,
                    cosdpkgid=_cosd['uuid'])


sonata_cleanup()