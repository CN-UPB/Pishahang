import logging
import sys
from functools import wraps
from inspect import Parameter, signature

import connexion
from flask_jwt_extended import create_access_token, decode_token
from mongoengine import DoesNotExist

from ..app import jwt
from ..models.users import User
from ..util import hashPassword

logger = logging.getLogger("gatekeeper.api.auth")


@jwt.user_claims_loader
def getClaimsByUsername(username):
    user: User = User.objects(username=username).get()
    return {
        'isAdmin': user.isAdmin,
    }


def createTokenFromCredentials(body):
    """
    Given a request body with a username and a password, generates a new JWT token or returns an
    error response.
    """
    username = body["username"]
    password = body["password"]

    valid = False
    try:
        user: User = User.objects(username=username).get()
        valid = hashPassword(password, user.passwordSalt) == user.passwordHash
    except DoesNotExist:
        pass

    if not valid:
        return connexion.problem(400, "Bad Request", "Invalid username or password")

    return {"accessToken": create_access_token(identity=username)}


def getTokenInfo(token) -> dict:
    """
    Used internally by connexion to validate bearer access tokens
    """

    try:
        return decode_token(token)
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
