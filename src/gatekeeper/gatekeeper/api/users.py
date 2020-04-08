from mongoengine.errors import DoesNotExist

from connexion.exceptions import ProblemException
from gatekeeper.api.auth import adminOnly
from gatekeeper.models.users import User

NO_User_FOUND_MESSAGE = "No User matching the given username was found."


@adminOnly
def getUsers():
    return User.objects


@adminOnly
def addUser(body):
    user = User(**body)
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
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)


@adminOnly
def retrieveUsers(username):
    try:
        user = User.objects(username=username).get()
        return user
    except DoesNotExist:
        raise ProblemException(404, NO_User_FOUND_MESSAGE)


def getCurrentUser(user):
    try:
        return User.objects(username=user).get()
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)


@adminOnly
def updateUsers(username, body):
    try:
        user: User = User.objects(username=username).get()
        user.username = body["username"]
        user.isAdmin = body["isAdmin"]

        if body["password"] != "":
            user.setPassword(body["password"])

        user.save()
        return user
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)


def updateCurrentUser(user, body):
    try:
        user: User = User.objects(username=user).get()
        user.username = body["username"]
        user.isAdmin = body["isAdmin"]

        if body["password"] != "":
            user.setPassword(body["password"])

        user.save()
        return user
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)
