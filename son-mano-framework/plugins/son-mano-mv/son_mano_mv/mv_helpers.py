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

ATOKEN = "TOKEN"

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
        if 'service' in _s.metadata.labels:
            if _s.metadata.labels['service'] == serv_id:
                # FIXME: ip should be floating ip of pod
                _uid = _s._metadata.uid

    _servers = v1.list_namespaced_service(namespace='default', watch=False)
    for _s in _servers.items:
        if 'service' in _s.metadata.labels:
            if _s.metadata.labels['service'] == serv_id:
                # FIXME: ip should be floating ip of pod
                return {
                    "ip": topology['vim_endpoint'],
                    "port": _s._spec._ports[0].node_port,
                    "uid": _uid
                }



def get_nova_server_info(serv_id, topology):
    AUTH_URL = "http://{}/identity/v3".format(topology['vim_endpoint'])
    # FIXME: Shouldnt be hardcoded, obviously
    OS_USERNAME = "admin"
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

def switch_classifier(classifier_ip, vnf_ip, vnf_port, classifier_port=8080):

    classifier_url = "http://{classifier_ip}:{classifier_port}/switch?ip={vnf_ip}&port={vnf_port}".format(
            classifier_ip=classifier_ip, 
            classifier_port=classifier_port, 
            vnf_ip=vnf_ip,
            vnf_port=vnf_port)

    r = requests.get(classifier_url, verify=False)

    LOG.debug("classifier")
    LOG.debug(classifier_url)
    LOG.debug(r.text)

    if r.status_code == requests.codes.ok:
        return True
    else:
        return False



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