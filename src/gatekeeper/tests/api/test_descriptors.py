import pytest

descriptorKeys = {"id", "createdAt", "updatedAt", "type", "descriptor"}


@pytest.mark.parametrize("type", ["vm", "cn", "fpga", "service"])
def testUploadedDescriptors(api, type):
    # GET all descriptors
    def getDescriptors():
        return api.get('/api/v3/uploaded-descriptors?type=' + type).get_json()

    assert [] == getDescriptors()

    # POST new descriptor
    descriptor = api.post(
        '/api/v3/uploaded-descriptors',
        json={'type': type, 'descriptor': {'some': 'descriptor'}}
    ).get_json()
    assert descriptorKeys <= set(descriptor)

    assert [descriptor] == getDescriptors()

    # PUT descriptor
    updatedDesriptor = api.put(
        '/api/v3/uploaded-descriptors/' + descriptor["id"],
        json={'descriptor': {'some': 'other descriptor'}}
    ).get_json()
    assert updatedDesriptor['id'] == descriptor['id']
    assert updatedDesriptor != descriptor
    assert updatedDesriptor['descriptor']['some'] == 'other descriptor'
    assert descriptorKeys <= set(updatedDesriptor)

    assert [updatedDesriptor] == getDescriptors()

    # DELETE descriptor
    deletedDescriptor = api.delete(
        '/api/v3/uploaded-descriptors/' + descriptor["id"]
    ).get_json()
    assert deletedDescriptor == updatedDesriptor

    assert [] == getDescriptors()
