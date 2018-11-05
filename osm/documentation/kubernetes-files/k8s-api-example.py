####################################### IMPORTANT ########################################
#                                                                                        #
# Kubernetes python API requires specifically version 0.32.0 of the 'websocket-client'   #
# Python 3 additionally requires the package 'certifi'                                   #
#                                                                                        #
# That means:                                                                            #
# Python 2                                                                               #
# sudo pip uninstall websocket-client && sudo pip install -Iv websocket-client==0.32.0   #
#                                                                                        #
# Python 3                                                                               #
# sudo pip3 uninstall websocket-client && sudo pip3 install -Iv websocket-client==0.32.0 #
# pip3 install certifi                                                                   #
#                                                                                        #
#                                                                                        #
# Add clusterrolebinding to allow serviceaccount to access API                           #  
# alternatively: clusterrole=view or clusterrole=cluster-admin                           #
#                                                                                        #
# kubectl create clusterrolebinding default-edit \                                       #
#   --clusterrole=edit \                                                                 #
#   --serviceaccount=default:default \                                                   #
#   --namespace=default                                                                  #
#                                                                                        #
##########################################################################################

from kubernetes import client

token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tYzJ0bGIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjRlNTYwNzE3LTg2OGUtMTFlOC1iNWI2LTBjYzQ3YTBmYWZhZiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.ysw0cuEx8490g2d9TQqGjbIqh_0d48rsUWrVGd4eHdIc2Vj3DXycPwmJVUL5e2BBbzJtghCPPN1HVSYcObiZRzUzmRgdRkwN7lb2fH6qF70qpfaHWo3gzfF36i_OlveeFMWwWsp0Iv6jkaN65QVi2DlMDrVaSyGyie7iIT0sXmqnib_lW1NPOq1jjL6Eh7sCgSq9F0p6_-SfszqbyVzviVXyHCxGXBqg0v-j18G6wNZFjz40KpTpDOcvRFCxrgzUXS46NQ0Xj0NiVFLJP54gCKYL8yXKTTIQXo7Iz7u83y4VYVBMNsQKuRJ_wJDY6WgLE2Q3-uWrUza9kYpVwKlpyw' # kubectl describe secret
ip = '10.0.0.5' # IP of the k8s machine
port = '6443'
ca_cert_location = '/home/user/ca.crt' # assuming a copy of '/etc/kubernetes/pki/ca.crt'
                                       # from the k8s machine can be found here

configuration = client.Configuration()
configuration.api_key["authorization"] = token
configuration.api_key_prefix['authorization'] = 'Bearer'
configuration.host = 'https://{ip}:{port}'.format(ip=ip, port=port)
configuration.ssl_ca_cert = ca_cert_location

core = client.CoreV1Api(client.ApiClient(configuration))
beta = client.ExtensionsV1beta1Api(client.ApiClient(configuration))

print core.list_pod_for_all_namespaces()
print beta.list_deployment_for_all_namespaces()
