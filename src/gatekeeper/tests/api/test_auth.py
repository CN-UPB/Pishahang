from flask_jwt_extended import decode_token


def testTokenRetrieval(unauthorizedApi, adminUser, adminPassword):
    # Login with invalid credentials
    assert (
        401
        == unauthorizedApi.post(
            "/api/v3/auth", json={"username": "user", "password": "pass"}
        ).status_code
    )

    # Login with valid username and invalid password
    assert (
        401
        == unauthorizedApi.post(
            "/api/v3/auth", json={"username": adminUser.username, "password": "pass"}
        ).status_code
    )

    # Login with valid credentials
    reply = unauthorizedApi.post(
        "/api/v3/auth", json={"username": adminUser.username, "password": adminPassword}
    )
    assert reply.status_code == 200
    token = reply.get_json()
    assert {
        "accessToken",
        "accessTokenExpiresIn",
        "refreshToken",
        "refreshTokenExpiresIn",
    } <= set(token)

    # Decode the retrieved tokens and check their types
    assert decode_token(token["accessToken"])["type"] == "access"
    assert decode_token(token["refreshToken"])["type"] == "refresh"


def testTokenRefresh(unauthorizedApi, refreshToken):
    reply = unauthorizedApi.put("/api/v3/auth", json={"refreshToken": refreshToken})

    assert reply.status_code == 200
    token = reply.get_json()
    assert {"accessToken", "tokenExpires"} <= set(token)
    assert decode_token(token["accessToken"])["type"] == "access"
