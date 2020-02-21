import requests

from ..config import config
catalogueRootUrl = config['urls']['catalogues'] + "complex-services"


def getServices():
    headers = {'content-type': 'application/json'}
    return requests.get(catalogueRootUrl, headers=headers).json()


def getServiceById(serviceId):
    serviceIdUrl = catalogueRootUrl + "/" + serviceId
    headers = {'content-type': 'application/json'}
    response = requests.get(serviceIdUrl, headers=headers)
    # Checking response
    return response.json(), response.status_code


def deleteServiceById(serviceId):
    serviceIdUrl = catalogueRootUrl + "/" + serviceId
    headers = {'content-type': 'application/json'}
    response = requests.delete(serviceIdUrl, headers=headers)
    # Checking response
    return "Deleted", response.status_code
