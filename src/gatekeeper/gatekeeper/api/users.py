from mongoengine.errors import DoesNotExist, NotUniqueError

from connexion.exceptions import BadRequestProblem, ProblemException
from gatekeeper.api.auth import adminOnly
from gatekeeper.models.users import User

NO_USER_FOUND_MESSAGE = "No User matching the given username was found."


@adminOnly
def getUsers():
    return User.objects


@adminOnly
def addUser(body):
    try:
        return User(**body).save()
    except NotUniqueError as e:
        raise BadRequestProblem(title="Invalid user data", detail=str(e))


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
        raise ProblemException(404, "Not Found", NO_USER_FOUND_MESSAGE)


@adminOnly
def retrieveUsers(username):
    try:
        user = User.objects(username=username).get()
        return user
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_USER_FOUND_MESSAGE)


def getCurrentUser(user):
    try:
        print(user)
        return User.objects(username=user).get()
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_USER_FOUND_MESSAGE)


@adminOnly
def updateUsers(username, body):
    try:
        user: User = User.objects(username=username).get()
        user.username = body["username"]
        user.isAdmin = body["isAdmin"]
        user.email = body["email"]
        user.fullName = body["fullName"]

        if body["password"] != "":
            user.setPassword(body["password"])

        user.save()
        return user
    except DoesNotExist:
        raise ProblemException(404, "Not Found", NO_USER_FOUND_MESSAGE)
    except NotUniqueError as e:
        raise BadRequestProblem(title="Invalid user data", detail=str(e))


def updateCurrentUser(user, body):
    try:
        # The user with name `user` must exists, as the authorization would have failed otherwise
        user: User = User.objects(username=user).get()
        user.username = body["username"]
        user.email = body["email"]
        user.fullName = body["fullName"]

        if body["password"] != "":
            user.setPassword(body["password"])

        return user.save()
    except NotUniqueError as e:
        raise BadRequestProblem(title="Invalid user data", detail=str(e))
