from .auth import adminOnly
from ..models.users import User


@adminOnly
def getUsers():
    return User.objects
