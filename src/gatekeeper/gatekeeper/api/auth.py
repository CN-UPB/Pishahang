import connexion
from config2.config import config
from connexion import request
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError

from ..app import redisClient
from ..util import makeMessageResponse

KEYCLOAK_CONNECTION_FAILED_MESSAGE = "Unable to connect to Keycloak. Please try again in a moment."


def createKeycloakOpenIdClient():
    clientSecret = redisClient.get('keycloakClientSecret')
    if clientSecret is None:
        return None

    return KeycloakOpenID(
        server_url=config.keycloak.url,
        client_id=config.keycloak.clientId,
        realm_name=config.keycloak.realmName,
        client_secret_key=clientSecret,
        verify=True
    )


def createTokenFromCredentials(body):
    """
    Given a request body with a username and a password, uses the Keycloak API to return a new
    token.
    """
    keycloak = createKeycloakOpenIdClient()
    if keycloak is None:
        return makeMessageResponse(500, KEYCLOAK_CONNECTION_FAILED_MESSAGE)

    try:
        token = keycloak.token(body['username'], body['password'])
        return {
            'accessToken': token['access_token'],
            'expiresIn': token['expires_in'],
            'refreshExpiresIn': token['refresh_expires_in'],
            'refreshToken': token['refresh_token']
        }
    except KeycloakAuthenticationError:
        return makeMessageResponse(400, "Invalid username or password")


def getTokenInfo(token) -> dict:
    """
    Used internally by connexion to validate bearer access tokens
    """
    keycloak = createKeycloakOpenIdClient()
    if keycloak is None:
        return

    tokenInfo = keycloak.introspect(token)
    if not tokenInfo['active']:
        return

    return {'uid': tokenInfo['username'], 'roles': ['admin']}
