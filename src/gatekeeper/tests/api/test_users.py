

def testUsers(authorizedApi):
    # GET all users
    def getUsers():
        return authorizedApi.get('/api/v3/users').get_json()

    assert 1 == len(getUsers())
