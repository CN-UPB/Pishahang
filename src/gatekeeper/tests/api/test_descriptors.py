import copy

import pytest

from gatekeeper.models.descriptors import DescriptorType

descriptorKeys = {"id", "createdAt", "updatedAt", "type", "content"}


@pytest.mark.parametrize(
    "type", [DescriptorType.SERVICE.value, DescriptorType.OPENSTACK.value]
)
def testCrud(api, type, exampleServiceDescriptor, exampleOpenStackDescriptor):
    descriptorContent = copy.deepcopy(
        exampleServiceDescriptor
        if type == DescriptorType.SERVICE.value
        else exampleOpenStackDescriptor
    )

    # GET all descriptors
    def getDescriptors():
        return api.get("/api/v3/descriptors?type=" + type).get_json()

    assert [] == getDescriptors()

    # POST new descriptor
    descriptor = api.post(
        "/api/v3/descriptors", json={"type": type, "content": descriptorContent}
    ).get_json()
    assert descriptorKeys <= set(descriptor)

    assert [descriptor] == getDescriptors()

    # GET single descriptor
    assert descriptor == api.get("/api/v3/descriptors/" + descriptor["id"]).get_json()

    # PUT descriptor
    oldDescriptorName = descriptorContent["name"]
    newDescriptorName = oldDescriptorName + "-new"
    descriptorContent["name"] = newDescriptorName

    updatedDesriptor = api.put(
        "/api/v3/descriptors/" + descriptor["id"],
        json={"type": type, "content": descriptorContent},
    ).get_json()
    assert updatedDesriptor["id"] == descriptor["id"]
    assert updatedDesriptor != descriptor
    assert updatedDesriptor["content"]["name"] == newDescriptorName
    assert descriptorKeys <= set(updatedDesriptor)

    assert [updatedDesriptor] == getDescriptors()

    # DELETE descriptor
    deletedDescriptor = api.delete("/api/v3/descriptors/" + descriptor["id"]).get_json()
    assert deletedDescriptor == updatedDesriptor

    assert [] == getDescriptors()


@pytest.mark.parametrize(
    "type",
    [
        DescriptorType.SERVICE.value,
        DescriptorType.OPENSTACK.value,
        DescriptorType.KUBERNETES.value,
    ],
)
def testDescriptorValidation(api, type):
    assert (
        400
        == api.post(
            "/api/v3/descriptors", json={"type": type, "content": {}}
        ).status_code
    )

    assert (
        400
        == api.post(
            "/api/v3/descriptors",
            json={"type": type, "content": {"name": "my-descriptor"}},
        ).status_code
    )


def testDuplicateNames(api, exampleServiceDescriptor, exampleOpenStackDescriptor):
    exampleServiceDescriptor, exampleOpenStackDescriptor = copy.deepcopy(
        (exampleServiceDescriptor, exampleOpenStackDescriptor)
    )

    def addDescriptor(type, descriptor: dict):
        return api.post(
            "/api/v3/descriptors", json={"type": type, "content": descriptor}
        ).status_code

    assert 201 == addDescriptor("service", exampleServiceDescriptor)

    # Adding another descriptor with the same vendor, version, and name should not work
    assert 400 == addDescriptor("service", exampleServiceDescriptor)

    # Whereas with a different version...
    exampleServiceDescriptor["version"] = "0.0.0"
    assert 201 == addDescriptor("service", exampleServiceDescriptor)

    # (descriptor_type, vendor, version, name) should be unique
    assert 201 == addDescriptor(
        DescriptorType.OPENSTACK.value, exampleOpenStackDescriptor
    )
    assert 400 == addDescriptor(
        DescriptorType.OPENSTACK.value, exampleOpenStackDescriptor
    )
