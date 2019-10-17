import requests
import json
from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client as nvclient

from kubernetes import client as k8client
from kubernetes import config as k8config

import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:mv")
LOG.setLevel(logging.INFO)

ATOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tbjRxd2oiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjQ1YmQ4OTQ3LTQxZjQtNDdiOS04ZmI2LWY3M2NkNTU3MDc4ZSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.g7x2RYwiiAj4IQxTHhF_cHFrJ80P0BD2gTMe3zNY3B6k2tNwzB0LzSbJi8FL1fbgu1SSPq8ykQ34-8jE67bpRsofJD2nPfLNwSECr9tFLeVMcYQtHL-8xyvEXcUr6o7MbMlI4Geh5J5dhdWtiq3Bo1D3BXIV1eOJ_wTYO6EekcpZB7thbKOffi6JImLbhHEywssWu4_G5U5jgbnKpRy4xp54ZoPZFvWrlS9PnSkFca2-U--HFJFNwRhg5xNREa5ON9RFZ2f0dIst2zkIriFzoYEu0iekpauE5nEVMkfWP8f-7drNFIW0KjaMzDpMZzQGleqWP-0MwTeuW9XFv1-Ylg"

def get_k8_pod_info(serv_id, topology):
    K8_URL = "https://{}".format(topology['vim_endpoint'])

    aConfiguration = k8client.Configuration()
    aConfiguration.host = K8_URL

    aConfiguration.verify_ssl = False
    aConfiguration.api_key = {"authorization": "Bearer " + ATOKEN}

    aApiClient = k8client.ApiClient(aConfiguration)

    v1 = k8client.CoreV1Api(aApiClient)
    _servers = v1.list_namespaced_pod(namespace='default', watch=False)


    for _s in _servers.items:
        if _s.metadata.labels['service'] == serv_id:
            return _s._metadata.uid


def get_nova_server_info(serv_id, topology):
    AUTH_URL = "http://{}/identity/v3".format(topology['vim_endpoint'])
    # FIXME: Shouldnt be hardcoded, obviously
    OS_USERNAME = "demo"
    OS_PASSWORD = "1234"
    OS_PROJECT = "demo"

    auth = v3.Password(auth_url=AUTH_URL,
                username=OS_USERNAME,
                password=OS_PASSWORD,
                project_name=OS_PROJECT,
                user_domain_id='default',
                project_domain_id='default')

    sess = session.Session(auth=auth)

    nova = nvclient.Client('2', session=sess)
    
    _servers = nova.servers.list()

    for _s in _servers:
        if _s.name.split(".")[2] == serv_id:
            return _s._info['OS-EXT-SRV-ATTR:instance_name']

def get_netdata_charts(instance_id, topology):
    netdata_url = "http://{host}:19999/api/v1/charts".format(host=topology['vim_endpoint'])
    r = requests.get(netdata_url, verify=False)

    LOG.debug("netdata_url")
    LOG.debug(netdata_url)
    LOG.debug(r.text)

    if r.status_code == requests.codes.ok:
        _result_json = json.loads(r.text)
        charts = [key for key in _result_json['charts'].keys() if instance_id in key.lower()]
        return charts
    else:
        return []


def get_netdata_charts_instance(charts, vim_endpoint, avg_sec=30):
    _chart_avg_url = "http://{host}:19999/api/v1/data?chart={chart_id}&format=json&after=-{last_sec_avg}&points=1"

    _instance_metrics = {}

    for _c in charts:
        _c_name = _c.split(".")[1]
        r = requests.get(_chart_avg_url.format(host=vim_endpoint, chart_id=_c, last_sec_avg=avg_sec), verify=False)
        if r.status_code == requests.codes.ok:
            _result_json = json.loads(r.text)
            if "net" in _c_name:
                if "packets" in _c_name:
                    _instance_metrics["packets"] = _result_json
                else:
                    _instance_metrics["bandwidth"] = _result_json
            else:
                _instance_metrics[_c_name] = _result_json
                

    return _instance_metrics