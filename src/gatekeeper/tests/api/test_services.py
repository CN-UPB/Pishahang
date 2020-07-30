from gatekeeper.models.descriptors import DescriptorType


def testOnboarding(api, getDescriptorFixture):
    def uploadDescriptor(type, content):
        response = api.post(
            "/api/v3/descriptors", json={"type": type, "content": content}
        )
        assert 201 == response.status_code
        return response.get_json()

    serviceDescriptor = uploadDescriptor(
        "service", getDescriptorFixture("onboarding/root-service.yml")
    )

    vnfDescriptors = [
        uploadDescriptor(
            DescriptorType.OPENSTACK.value,
            getDescriptorFixture("onboarding/vnf-{}.yml".format(i)),
        )
        for i in range(1, 3)
    ]

    def onboardServiceDescriptorById(id: str):
        response = api.post("/api/v3/services", json={"id": id})
        return response.status_code, response.get_json()

    assert 400 == onboardServiceDescriptorById(vnfDescriptors[0]["id"])[0]

    # Onboard service descriptor
    status, service = onboardServiceDescriptorById(serviceDescriptor["id"])
    assert 201 == status

    assert service["descriptor"] == serviceDescriptor
    assert service["functionDescriptors"] == vnfDescriptors

    for attribute in ["vendor", "name", "version"]:
        assert service[attribute] == serviceDescriptor["content"][attribute]

    # Onboard service descriptor again – should work
    assert 201 == onboardServiceDescriptorById(serviceDescriptor["id"])[0]

    # Delete the first VNF descriptor
    assert (
        200 == api.delete("/api/v3/descriptors/" + vnfDescriptors[0]["id"]).status_code
    )

    # Try to onboard service descriptor with missing referenced VNF descriptor – should fail
    assert 400 == onboardServiceDescriptorById(serviceDescriptor["id"])[0]


def testGetEndpoints(api, exampleService):
    assert [exampleService] == api.get("/api/v3/services").get_json()

    assert (
        404
        == api.get("/api/v3/services/3fa85f64-5717-4562-b3fc-2c963f66afa6").status_code
    )

    response = api.get("/api/v3/services/" + exampleService["id"])
    assert 200 == response.status_code
    assert exampleService == response.get_json()


def testDelete(api, exampleService):
    response = api.delete("/api/v3/services/" + exampleService["id"])
    assert 200 == response.status_code
    assert exampleService == response.get_json()

    assert [] == api.get("/api/v3/services").get_json()
