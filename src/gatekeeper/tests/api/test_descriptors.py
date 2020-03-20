from gatekeeper.models.descriptors import DescriptorType
import pytest

descriptorKeys = {"id", "createdAt", "updatedAt", "type", "descriptor"}


@pytest.mark.parametrize("type", [t.value for t in DescriptorType])
def testDescriptorsCrud(api, type):
    # GET all descriptors
    def getDescriptors():
        return api.get('/api/v3/descriptors?type=' + type).get_json()

    assert [] == getDescriptors()

    # POST new descriptor
    descriptor = api.post(
        '/api/v3/descriptors',
        json={'type': type, 'descriptor': {'some': 'descriptor'}}
    ).get_json()
    assert descriptorKeys <= set(descriptor)

    assert [descriptor] == getDescriptors()

    # GET single descriptor
    assert descriptor == api.get('/api/v3/descriptors/' + descriptor['id']).get_json()

    # PUT descriptor
    updatedDesriptor = api.put(
        '/api/v3/descriptors/' + descriptor["id"],
        json={'descriptor': {'some': 'other descriptor'}}
    ).get_json()
    assert updatedDesriptor['id'] == descriptor['id']
    assert updatedDesriptor != descriptor
    assert updatedDesriptor['descriptor']['some'] == 'other descriptor'
    assert descriptorKeys <= set(updatedDesriptor)

    assert [updatedDesriptor] == getDescriptors()

    # DELETE descriptor
    deletedDescriptor = api.delete(
        '/api/v3/descriptors/' + descriptor["id"]
    ).get_json()
    assert deletedDescriptor == updatedDesriptor

    assert [] == getDescriptors()
