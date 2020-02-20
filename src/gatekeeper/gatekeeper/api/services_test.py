from gatekeeper.api.services import getServices

def testGetServices():
    services = getServices()
    assert len(services) == 1