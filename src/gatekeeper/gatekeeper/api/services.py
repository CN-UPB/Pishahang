import requests

from ..config import config
catalogueRootUrl = config['urls']['catalogues'] + "complex-services"

def getServices():
    headers = {'content-type': 'application/json'}
    return requests.get(catalogueRootUrl, headers=headers).json()