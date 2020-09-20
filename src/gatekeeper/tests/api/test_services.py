from gatekeeper.models.descriptors import DescriptorType


class EqualsEverything:
    def __eq__(self, other):
        return True


doesNotMatter = EqualsEverything()


def testOnboarding(api, getDescriptorFixture, mocker):
    repository = mocker.patch("gatekeeper.api.services.repository")

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
            getDescriptorFixture(f"onboarding/vnf-{i}.yml"),
        )
        for i in range(1, 3)
    ]

    def onboardServiceById(id: str):
        response = api.post("/api/v3/services", json={"id": id})
        return response.status_code, response.get_json()

    assert 400 == onboardServiceById(vnfDescriptors[0]["id"])[0]

    # Onboard service
    status, service = onboardServiceById(serviceDescriptor["id"])
    assert 201 == status
    repository.post.assert_called()

    # Ignore the ids in the following comparisons
    service["descriptor"]["id"] = doesNotMatter
    for d in service["functionDescriptors"]:
        d["id"] = doesNotMatter

    assert service["descriptor"] == serviceDescriptor
    assert service["functionDescriptors"] == vnfDescriptors

    for attribute in ["vendor", "name", "version"]:
        assert service[attribute] == serviceDescriptor["content"][attribute]

    # Onboard service again – should work
    assert 201 == onboardServiceById(serviceDescriptor["id"])[0]

    # Delete the first VNF descriptor
    assert (
        200 == api.delete("/api/v3/descriptors/" + vnfDescriptors[0]["id"]).status_code
    )

    # Try to onboard service descriptor with missing referenced VNF descriptor – should fail
    assert 400 == onboardServiceById(serviceDescriptor["id"])[0]


def testGetEndpoints(api, exampleService):
    assert [exampleService] == api.get("/api/v3/services").get_json()

    assert (
        404
        == api.get("/api/v3/services/3fa85f64-5717-4562-b3fc-2c963f66afa6").status_code
    )

    response = api.get("/api/v3/services/" + exampleService["id"])
    assert 200 == response.status_code
    assert exampleService == response.get_json()


def testDelete(api, exampleService, mocker):
    repository = mocker.patch("gatekeeper.api.services.repository")

    response = api.delete("/api/v3/services/" + exampleService["id"])
    assert 200 == response.status_code
    assert exampleService == response.get_json()
    repository.delete.assert_called()

    assert [] == api.get("/api/v3/services").get_json()
