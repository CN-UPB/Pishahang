from appcfg import get_config
from pytest_voluptuous import S

config = get_config("gatekeeper")


def testUsers(authorizedApi):
    adminUserData = dict(config["initialUserData"])
    adminUserData.pop("password")

    # GET /users
    def getUsers():
        return authorizedApi.get("/api/v3/users").get_json()

    # Only the admin user should be present
    users = getUsers()
    assert 1 == len(users)
    adminUser = users[0]
    assert (
        S({**adminUserData, "id": str, "createdAt": str, "updatedAt": str}) == adminUser
    )

    # GET /current-user should return the admin user
    assert adminUser == authorizedApi.get("/api/v3/current-user").get_json()

    # Let's change the username of the admin user via PUT /current-user
    newAdminUserData = {**adminUserData, "username": "admin2", "password": ""}
    reply = authorizedApi.put("/api/v3/current-user", json=newAdminUserData)
    assert 200 == reply.status_code
    assert S({**adminUserData, "username": "admin2"}) <= reply.get_json()

    # Add a new user
    newUserData = {
        "email": "user@example.com",
        "fullName": "New User",
        "isAdmin": False,
        "password": "password",
        "username": "newuser",
    }
    reply = authorizedApi.post("/api/v3/users", json=newUserData)
    newUserData.pop("password")
    assert 201 == reply.status_code
    newUser = reply.get_json()
    assert S({**newUserData, "id": str, "createdAt": str, "updatedAt": str}) == newUser

    assert 2 == len(getUsers())

    # Let's get it by its id
    reply = authorizedApi.get("/api/v3/users/" + newUser["id"])
    assert 200 == reply.status_code
    assert newUser == reply.get_json()

    # Update the new user's data without providing a password
    reply = authorizedApi.put(
        "/api/v3/users/" + newUser["id"],
        json={**newUserData, "email": "newmail@example.org", "password": ""},
    )
    assert 200 == reply.status_code
    assert S({**newUserData, "email": "newmail@example.org"}) <= reply.get_json()

    # Update the new user's password
    reply = authorizedApi.put(
        "/api/v3/users/" + newUser["id"],
        json={**newUserData, "password": "new password"},
    )
    assert 200 == reply.status_code
    assert S(newUserData) <= reply.get_json()

    # Delete the new user
    assert 200 == authorizedApi.delete("/api/v3/users/" + newUser["id"]).status_code
    assert 1 == len(getUsers())
