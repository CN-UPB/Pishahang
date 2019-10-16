
import kubernetes.client
from kubernetes.client.rest import ApiException
from pprint import pprint

from kubernetes import client, config

ATOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tbjRxd2oiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjQ1YmQ4OTQ3LTQxZjQtNDdiOS04ZmI2LWY3M2NkNTU3MDc4ZSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.g7x2RYwiiAj4IQxTHhF_cHFrJ80P0BD2gTMe3zNY3B6k2tNwzB0LzSbJi8FL1fbgu1SSPq8ykQ34-8jE67bpRsofJD2nPfLNwSECr9tFLeVMcYQtHL-8xyvEXcUr6o7MbMlI4Geh5J5dhdWtiq3Bo1D3BXIV1eOJ_wTYO6EekcpZB7thbKOffi6JImLbhHEywssWu4_G5U5jgbnKpRy4xp54ZoPZFvWrlS9PnSkFca2-U--HFJFNwRhg5xNREa5ON9RFZ2f0dIst2zkIriFzoYEu0iekpauE5nEVMkfWP8f-7drNFIW0KjaMzDpMZzQGleqWP-0MwTeuW9XFv1-Ylg"
K8_URL = "https://131.234.29.235"

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


delete_replication_controller()
delete_pod()
delete_services()