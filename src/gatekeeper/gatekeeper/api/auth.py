import logging
import sys
from functools import wraps
from inspect import Parameter, signature

import connexion
from config2.config import config
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                decode_token)
from mongoengine import DoesNotExist

from gatekeeper.app import jwt
from gatekeeper.models.users import User

logger = logging.getLogger("gatekeeper.api.auth")


@jwt.user_claims_loader
def __getClaimsByUser(user: User):
    return {
        'isAdmin': user.isAdmin,
    }


@jwt.user_identity_loader
def getIdentityByUser(user: User):
    return user.username


def createTokenFromCredentials(body):
    """
    Given a request body with a username and a password, generates a JWT access token or returns an
    error response.
    """
    valid = False
    try:
        user: User = User.objects(username=body["username"]).get()
        valid = user.validatePassword(body["password"])
    except DoesNotExist:
        pass

    if not valid:
        return connexion.problem(401, "Unauthorized", "Invalid username or password")

    return {
        "accessToken": create_access_token(identity=user),
        "refreshToken": create_refresh_token(identity=user),
        "accessTokenExpiresIn": config.jwt.accessTokenLifetime,
        "refreshTokenExpiresIn": config.jwt.refreshTokenLifetime
    }


def refreshToken(body):
    """
    Given a request body with a refresh token, generates a new JWT access token or returns an error
    response.
    """
    try:
        token = decode_token(body["refreshToken"])
        if token["type"] != "refresh":
            return connexion.problem(
                401,
                'Unauthorized',
                'The provided token is not valid as a refresh token.'
            )
        user = User.objects(username=token["identity"]).get()
        return {
            "accessToken": create_access_token(identity=user),
            "tokenExpires": config.jwt.accessTokenLifetime,
        }
    except Exception:
        return connexion.problem(
            401,
            'Unauthorized',
            'The provided token is invalid.'
        )


def getTokenInfo(token) -> dict:
    """
    Used internally by connexion to validate bearer access tokens
    """

    try:
        tokenInfo = decode_token(token)
        tokenInfo["sub"] = tokenInfo.pop("identity")
        return tokenInfo
    except Exception:
        _, message, _ = sys.exc_info()
        logger.info("Bearer authentication failed: {}".format(message))
        return


def __makeAuthDecorator(tokenInfoHandler):
    """
    Decorator factory for decorators that process connexion's `token_info` keyword argument

    Accepts an `tokenInfoHandler` function which is executed right before the wrapped function and
    provided with `token_info`. If `tokenInfoHandler` returns a value, the wrapper function will
    also return that value and the decorated function won't be executed.
    """

    def decorator(fn):
        sig = signature(fn)  # Get the wrapped function's signature

        @wraps(fn)
        def wrapper(*args, **kwargs):
            tokenInfoHandlerResult = tokenInfoHandler(kwargs['token_info'])
            if tokenInfoHandlerResult is not None:
                return tokenInfoHandlerResult

            if 'token_info' not in sig.parameters:
                # Remove `token_info` because the wrapped function does not take it
                kwargs.pop('token_info')
            if 'user' not in sig.parameters:
                # Remove `user` because the wrapped function does not take it (why does connexion
                # pass it at all?)
                kwargs.pop('user')
            return fn(*args, **kwargs)

        # Add a `token_info` keyword argument to the parameter list if it does not yet exist
        # (required for connexion to pass `token_info`).
        if 'token_info' not in sig.parameters:
            tokenInfoParam = Parameter(name='token_info', kind=Parameter.VAR_KEYWORD)
            newParameters = tuple(sig.parameters.values()) + (tokenInfoParam,)
            wrapper.__signature__ = sig.replace(parameters=newParameters)
        return wrapper

    return decorator


def __ensureAdminRights(token_info):
    if not token_info['user_claims']['isAdmin']:
        return connexion.problem(
            403,
            'Forbidden',
            'Only administrators are allowed to take this action'
        )


adminOnly = __makeAuthDecorator(__ensureAdminRights)
"""
A decorator for connexion endpoint handlers that makes sure the user is authenticated as an
administrator and replies with an error response otherwise.
"""
