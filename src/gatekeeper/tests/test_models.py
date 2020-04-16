from gatekeeper.models.users import User


def testUser():
    User(
        username="bill",
        password="gates",
        isAdmin="true",
        email="user@example.org",
        fullName="Bill"
    ).save()

    user: User = User.objects(username="bill").get()
    assert user.validatePassword("gates") is True
    assert user.validatePassword("password") is False

    user.setPassword("other")
    assert user.validatePassword("other") is True
    assert user.validatePassword("gates") is False

    user.delete()
