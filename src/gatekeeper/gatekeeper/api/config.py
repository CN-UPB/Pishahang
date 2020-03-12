from ..app import redisClient
from ..util import makeMessageResponse


def setKeycloakClientSecret(body: bytes):
    secret = body.decode("utf-8")
    redisClient.set('keycloakClientSecret', secret)
    return makeMessageResponse(200, "Secret successfully set")
