import requests
import json

URI = "http://sp.int3.sonata-nfv.eu:4002/catalogues/"
#URI = "http://127.0.0.1:4011/catalogues/"

packages = "packages"

# Get all services
headers = {'content-type': 'application/json'}
response= requests.get((URI + packages), headers=headers)

data = response.json()

# Delete all services by its uuid
for item in data:
    #print item
    try:
        id = item['uuid']
        print "Deleting " + id
        payload = {'some':'data'}
        headers = {'content-type': 'application/json'}
        print  URI + packages + '/' + str(id)
        r = requests.delete((URI + packages + '/' + str(id)), headers=headers)
    except:
        continue