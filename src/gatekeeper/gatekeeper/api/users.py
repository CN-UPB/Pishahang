from .auth import adminOnly
from ..models.users import (User, AddUser)
from mongoengine.errors import DoesNotExist
from ..util import makeMessageResponse
NO_User_FOUND_MESSAGE = "No User matching the given username was found."


@adminOnly
def getUsers():
    return User.objects


def addUser(body):
    user = AddUser(**body)
    user.save()
    return user


@adminOnly
def deleteUser(username):
    """
    Delete A VIM by giving its uuid.
    """
    try:
        user = User.objects(username=username).get()
        user.delete()
        return user
    except DoesNotExist:
        return makeMessageResponse(404, NO_User_FOUND_MESSAGE)


@adminOnly
def retrieveUsers(username):
    try:
        return User.objects(username=username)
    except DoesNotExist:
        return makeMessageResponse(404, NO_User_FOUND_MESSAGE)
