from .services import getServices, catalogueRootUrl


def testGetServices(requests_mock):
    requests_mock.get(catalogueRootUrl, json=[])
    assert len(getServices()) == 0

    requests_mock.get(catalogueRootUrl, json=[
                      "service1-dummy", "service2-dummy"])
    assert len(getServices()) == 2
