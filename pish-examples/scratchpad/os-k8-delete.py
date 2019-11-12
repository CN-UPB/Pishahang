from kubernetes import client

from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client as nvclient

from heatclient import client as hclient
from dateutil import parser
import time

AUTH_URL = "http://131.234.250.117/identity/v3"
K8_URL = "https://131.234.250.178"

OS_USERNAME = "demo"
OS_PASSWORD = "1234"

ATOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tNXJmbjgiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImMyNjY2OThlLTkzMDktNGM1ZS04YjgzLTAyMGFkNWNiZWY2ZiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.q760MUAznU5DUm4cAfYuGd2T5-mOQvCB-bYfZE4FhBf9nSCKntE9_W_sKoBAjhmVp59GKPLb_MXBoUZJKrAXh4KcE4JByX_XvAO656bbDrQ4OyB2_d26yB4dq-JTtfos7BrXOCg3tIRnkCeXjfj7eTul71yCTdqQ9Ac0XSaZFh-rDwlqPVegK9PSIG6WAKNVFKhIih9KXOqsJmiYkw2itstXC3le81lglmrquzcW5Mcp-_vnm4t7pTYz7aVN5XpOkY4xL_Y94Q1aD3BGmZhJlHAxdy_8QTNRxMqXQLYPQ6Zwf-H0wQgy1WARh7-Zkh0SeTYXQEb8QsngQZz4CNzDaQ"

aConfiguration = client.Configuration()
aConfiguration.host = K8_URL

aConfiguration.verify_ssl = False
aConfiguration.api_key = {"authorization": "Bearer " + ATOKEN}

aApiClient = client.ApiClient(aConfiguration)


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

def get_pod_service():

    v1 = client.CoreV1Api(aApiClient)
    ret = v1.list_namespaced_pod(namespace='default', watch=False)
    for i in ret.items:
    #   print("%s\t%s" %
    #         (i.metadata.name, i.metadata.creation_timestamp))
        pass

    ret = v1.list_namespaced_service(namespace='default', watch=False)

    for i in ret.items:
    #   print("%s\t%s" %
    #         (i.metadata.name, i.metadata.creation_timestamp))
        pass


def get_count(init_time):

    v1 = client.CoreV1Api(aApiClient)
    print("Listing pods with their IPs:")
    _servers = v1.list_namespaced_pod(namespace='default', watch=False)

    active_count = 0
    build_count = 0
    error_count = 0

    for _s in _servers.items:
        # print(_s.status.phase)
        if int(_s.metadata.creation_timestamp.strftime("%s")) > int(init_time) :
            if _s.status.container_statuses[0].ready:
                active_count += 1
            elif _s.status.phase in ['Pending']:
                build_count += 1
            elif _s.status.phase in ['Failed', 'Unknown']:
                error_count += 1
            else:
                print("Other Status")
                print(_s.status.phase)

    return active_count, build_count, error_count


def delete_stacks():
    auth = v3.Password(auth_url=AUTH_URL,
                    username=OS_USERNAME,
                    password=OS_PASSWORD,
                    project_name='demo',
                    user_domain_id='default',
                    project_domain_id='default')
    sess = session.Session(auth=auth)
    heat = hclient.Client('1', session=sess)

    for s in heat.stacks.list():
        try:
            s.delete()
        except Exception as e:
            print(e)


def get_nova_server_info():
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


delete_replication_controller()
delete_pod()
delete_services()
# delete_stacks()
# get_count(0)
# get_nova_server_info()

# get_pod_service()

    # i._spec._ports[0].port

    # '9fc00ef8-625a-42c9-b890-2abc5ce3652b'
    # _s._metadata.uid
    
    # 1ee6b3cd-1a3c-45fe-a180-1fff18c9de70: