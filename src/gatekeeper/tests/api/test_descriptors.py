from gatekeeper.models.descriptors import DescriptorType
import pytest

descriptorKeys = {"id", "createdAt", "updatedAt", "type", "descriptor"}

descriptorTypeValues = [t.value for t in DescriptorType]


@pytest.mark.parametrize("type", descriptorTypeValues)
def testCrud(api, type, exampleCsd, exampleVnfd):
    exampleDescriptorData = exampleCsd if type == DescriptorType.SERVICE.value else exampleVnfd

    # GET all descriptors
    def getDescriptors():
        return api.get('/api/v3/descriptors?type=' + type).get_json()

    assert [] == getDescriptors()

    # POST new descriptor
    descriptor = api.post(
        '/api/v3/descriptors',
        json={'type': type, 'descriptor': exampleDescriptorData}
    ).get_json()
    assert descriptorKeys <= set(descriptor)

    assert [descriptor] == getDescriptors()

    # GET single descriptor
    assert descriptor == api.get('/api/v3/descriptors/' + descriptor['id']).get_json()

    # PUT descriptor
    oldDescriptorName = exampleDescriptorData["name"]
    newDescriptorName = oldDescriptorName + "-new"
    exampleDescriptorData["name"] = newDescriptorName

    updatedDesriptor = api.put(
        '/api/v3/descriptors/' + descriptor["id"],
        json={'type': type, 'descriptor': exampleDescriptorData}
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
