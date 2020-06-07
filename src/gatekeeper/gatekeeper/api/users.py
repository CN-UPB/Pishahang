from mongoengine.errors import DoesNotExist, NotUniqueError
from gatekeeper.api.auth import adminOnly

from gatekeeper.exceptions import UserDataNotUniqueError, UserNotFoundError
from gatekeeper.models.users import User


@adminOnly
def getUsers():
    return User.objects


@adminOnly
def addUser(body):
    try:
        return User(**body).save(), 201
    except NotUniqueError as e:
        raise UserDataNotUniqueError(e)


@adminOnly
def deleteUser(id):
    try:
        user = User.objects(id=id).get()
        user.delete()
        return user
    except DoesNotExist:
        raise UserNotFoundError(id)


@adminOnly
def getUser(id):
    try:
        return User.objects(id=id).get()
    except DoesNotExist:
        raise UserNotFoundError(id)


@adminOnly
def updateUser(id, body):
    try:
        user: User = User.objects(id=id).get()
        user.username = body["username"]
        user.isAdmin = body["isAdmin"]
        user.email = body["email"]
        user.fullName = body["fullName"]

        if body["password"] != "":
            user.setPassword(body["password"])

        user.save()
        return user
    except DoesNotExist:
        raise UserNotFoundError(id)
    except NotUniqueError as e:
        raise UserDataNotUniqueError(e)


def getCurrentUser(user):
    # A user with username `user` is guaranteed to exist (authorization would have
    # failed otherwise)
    return User.objects(username=user).get()


def updateCurrentUser(user, body):

    # A user with username `user` is guaranteed to exist (authorization would have
    # failed otherwise)

    user: User = User.objects(username=user).get()
    user.username = body["username"]
    user.email = body["email"]
    user.fullName = body["fullName"]

    if body["password"] != "":
        user.setPassword(body["password"])

    try:
        user.save()
        return user
    except NotUniqueError as e:
        raise UserDataNotUniqueError(e)
