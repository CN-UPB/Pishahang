import pytest


@pytest.mark.skip
def testAddingVim(api):
    assert 400 == api.post('/api/v3/vims').status_code
    vimData = {"type": "aws", "city": "pb", "country": "de",
               "vimName": "44", "accessKey": "22",
               "secretKey": "11"}
    reply = api.post('/api/v3/vims', json=vimData)
    assert 200 == reply.status_code
    vim = reply.get_json()
    for t in ['id', 'createdAt', 'updatedAt']:
        vim.pop(t)
    assert vim == vimData

    assert 400 == api.post('/api/v3/vims').status_code
    vimData = {"type": "kubernetes", "city": "pb", "country": "de", "vimName": "newVim",
               "serviceToken": "1234", "vimAddress": "1111", "ccc": "2222"}
    reply = api.post('/api/v3/vims', json=vimData)
    assert 200 == reply.status_code
    vim = reply.get_json()
    for t in ['id', 'createdAt', 'updatedAt']:
        vim.pop(t)
    assert vim == vimData

    assert 400 == api.post('/api/v3/vims').status_code
    vimData = {"type": "openStack", "city": "pb", "country": "de", "vimName": "1111",
               "vimAddress": "2222", "tenantId": "3333", "tenantExternalNetworkId": "4444",
               "tenantExternalRouterId": "55", "username": "66", "password": "77"}
    reply = api.post('/api/v3/vims', json=vimData)
    assert 200 == reply.status_code
    vim = reply.get_json()
    for t in ['id', 'createdAt', 'updatedAt']:
        vim.pop(t)
    assert vim == vimData


# DELETE Vims by ID

@pytest.mark.skip
def testDeleteVim(api):
    vimData = {"type": "openStack", "city": "pb", "country": "de", "vimName": "1111",
               "vimAddress": "2222", "tenantId": "3333", "tenantExternalNetworkId": "4444",
               "tenantExternalRouterId": "55", "username": "66", "password": "77"}
    newVim = api.post('/api/v3/vims', json=vimData)
    newVimData = newVim.get_json()
    getId = newVimData['id']

    assert 200 == api.delete('/api/v3/vims/' + getId).status_code


# GET all Vims

@pytest.mark.skip
def testGetVims(api):
    assert 200 == api.get('/api/v3/vims').status_code
