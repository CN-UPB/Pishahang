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

ATOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tNXJmbjgiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImMyNjY2OThlLTkzMDktNGM1ZS04YjgzLTAyMGFkNWNiZWY2ZiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.q760MUAznU5DUm4cAfYuGd2T5-mOQvCB-bYfZE4FhBf9nSCKntE9_W_sKoBAjhmVp59GKPLb_MXBoUZJKrAXh4KcE4JByX_XvAO656bbDrQ4OyB2_d26yB4dq-JTtfos7BrXOCg3tIRnkCeXjfj7eTul71yCTdqQ9Ac0XSaZFh-rDwlqPVegK9PSIG6WAKNVFKhIih9KXOqsJmiYkw2itstXC3le81lglmrquzcW5Mcp-_vnm4t7pTYz7aVN5XpOkY4xL_Y94Q1aD3BGmZhJlHAxdy_8QTNRxMqXQLYPQ6Zwf-H0wQgy1WARh7-Zkh0SeTYXQEb8QsngQZz4CNzDaQ"

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

def get_netdata_charts(instance_id, topology, _charts_parameters):
    netdata_url = "http://{host}:19999/api/v1/charts".format(host=topology['vim_endpoint'])
    r = requests.get(netdata_url, verify=False)

    LOG.debug("netdata_url")
    LOG.debug(netdata_url)
    LOG.debug(r.text)

    # _charts_parameters = ["cpu", "net_eth0"]
    if r.status_code == requests.codes.ok:
        _result_json = json.loads(r.text)
        charts = [key for key in _result_json['charts'].keys() if instance_id in key.lower()]
        # Select only the monitoring parameters
        charts = [_c for _c in charts if any(_cp in _c for _cp in _charts_parameters)]
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
                    _instance_metrics["net"] = _result_json
            else:
                _instance_metrics[_c_name] = _result_json
                

    return _instance_metrics

def run_async(func):
	"""
		run_async(func)
			function decorator, intended to make "func" run in a separate
			thread (asynchronously).
			Returns the created Thread object

			E.g.:
			@run_async
			def task1():
				do_something

			@run_async
			def task2():
				do_something_too

			t1 = task1()
			t2 = task2()
			...
			t1.join()
			t2.join()
	"""
	from threading import Thread
	from functools import wraps

	@wraps(func)
	def async_func(*args, **kwargs):
		func_hl = Thread(target = func, args = args, kwargs = kwargs)
		func_hl.start()
		return func_hl

	return async_func
