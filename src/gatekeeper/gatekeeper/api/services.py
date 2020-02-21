import requests

from ..config import config
catalogueRootUrl = config['urls']['catalogues'] + "network-services"

def getServices():
    headers = {'content-type': 'application/json'}
    return requests.get(catalogueRootUrl, headers=headers).json()