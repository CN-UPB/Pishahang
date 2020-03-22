import copy

import pytest

from gatekeeper.models.descriptors import DescriptorType

descriptorKeys = {"id", "createdAt", "updatedAt", "type", "descriptor"}

descriptorTypeValues = [t.value for t in DescriptorType]


@pytest.mark.parametrize("type", descriptorTypeValues)
def testCrud(api, type, exampleCsd, exampleVnfd):
    descriptorContent = copy.deepcopy(
        exampleCsd if type == DescriptorType.SERVICE.value else exampleVnfd)

    # GET all descriptors
    def getDescriptors():
        return api.get('/api/v3/descriptors?type=' + type).get_json()

    assert [] == getDescriptors()

    # POST new descriptor
    descriptor = api.post(
        '/api/v3/descriptors',
        json={'type': type, 'descriptor': descriptorContent}
    ).get_json()
    assert descriptorKeys <= set(descriptor)

    assert [descriptor] == getDescriptors()

    # GET single descriptor
    assert descriptor == api.get('/api/v3/descriptors/' + descriptor['id']).get_json()

    # PUT descriptor
    oldDescriptorName = descriptorContent["name"]
    newDescriptorName = oldDescriptorName + "-new"
    descriptorContent["name"] = newDescriptorName

    updatedDesriptor = api.put(
        '/api/v3/descriptors/' + descriptor["id"],
        json={'type': type, 'descriptor': descriptorContent}
    ).get_json()
    assert updatedDesriptor['id'] == descriptor['id']
    assert updatedDesriptor != descriptor
    assert updatedDesriptor['descriptor']['name'] == newDescriptorName
    assert descriptorKeys <= set(updatedDesriptor)

    assert [updatedDesriptor] == getDescriptors()

    # DELETE descriptor
    deletedDescriptor = api.delete(
        '/api/v3/descriptors/' + descriptor["id"]
    ).get_json()
    assert deletedDescriptor == updatedDesriptor

    assert [] == getDescriptors()


@pytest.mark.parametrize("type", descriptorTypeValues)
def testDescriptorValidation(api, type):
    assert 400 == api.post(
        "/api/v3/descriptors",
        json={"type": type, "descriptor": {}}
    ).status_code

    assert 400 == api.post(
        "/api/v3/descriptors",
        json={"type": type, "descriptor": {"name": "my-descriptor"}}
    ).status_code


def testDuplicateNames(api, exampleCsd, exampleVnfd):
    exampleCsd, exampleVnfd = copy.deepcopy((exampleCsd, exampleVnfd))

    def addDescriptor(type, descriptor: dict):
        return api.post(
            "/api/v3/descriptors",
            json={"type": type, "descriptor": descriptor}
        ).status_code

    assert 201 == addDescriptor("service", exampleCsd)

    # Adding another descriptor with the same vendor, version, and name should not work
    assert 400 == addDescriptor("service", exampleCsd)

    # Whereas with a different version...
    exampleCsd["version"] = "0.0.0"
    assert 201 == addDescriptor("service", exampleCsd)

    # (vendor, version, name) should be unique across descriptor types
    exampleVnfd["vendor"] = exampleCsd["vendor"]
    exampleVnfd["name"] = exampleCsd["name"]
    exampleVnfd["version"] = exampleCsd["version"]
    for type in ("vm", "cn", "fpga"):
        assert 400 == addDescriptor(type, exampleVnfd)
