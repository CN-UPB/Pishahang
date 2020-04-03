from mongoengine.errors import DoesNotExist

from connexion.exceptions import ProblemException
from gatekeeper.api.auth import adminOnly
from gatekeeper.models.users import AddUser, User

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
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)


@adminOnly
def retrieveUsers(username):
    try:
        return User.objects(username=username)
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_User_FOUND_MESSAGE)
