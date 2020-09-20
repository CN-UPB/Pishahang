from connexion.exceptions import BadRequestProblem, ProblemException
from mongoengine.errors import NotUniqueError


class NotFoundError(ProblemException):
    def __init__(self, title="Not Found", **kwargs):
        super(NotFoundError, self).__init__(status=404, title=title, **kwargs)


class InternalServerError(ProblemException):
    def __init__(self, title="Internal Server Error", **kwargs):
        super(InternalServerError, self).__init__(status=500, title=title, **kwargs)


class InvalidDescriptorContentError(BadRequestProblem):
    """
    Indicates that invalid content has been assigned to `Descriptor.content`
    """

    def __init__(self, detail, **kwargs):
        super(InvalidDescriptorContentError, self).__init__(
            title="Invalid Descriptor", detail=detail, **kwargs
        )


class DuplicateDescriptorError(BadRequestProblem):
    def __init__(self, **kwargs):
        super(DuplicateDescriptorError, self).__init__(
            title="Duplicate Descriptor",
            detail="A descriptor with the given type, vendor, name, and version "
            + "does already exist in the database.",
            **kwargs
        )


class DescriptorNotFoundError(NotFoundError):
    def __init__(
        self, detail="No descriptor matching the given id was found.", **kwargs
    ):
        super(DescriptorNotFoundError, self).__init__(
            title="Descriptor Not Found", detail=detail, **kwargs
        )


class ServiceNotFoundError(NotFoundError):
    def __init__(self, detail="No service matching the given id was found.", **kwargs):
        super(ServiceNotFoundError, self).__init__(
            title="Service Not Found", detail=detail, **kwargs
        )


class ServiceInstanceNotFoundError(NotFoundError):
    def __init__(
        self, detail="No service instance matching the given id was found.", **kwargs
    ):
        super(ServiceInstanceNotFoundError, self).__init__(
            title="Service Instance Not Found", detail=detail, **kwargs
        )


class PluginNotFoundError(NotFoundError):
    def __init__(self, id, **kwargs):
        super(PluginNotFoundError, self).__init__(
            title="Plugin Not Found",
            detail="No plugin with id '{}' was found.".format(id),
            **kwargs
        )


class UserNotFoundError(NotFoundError):
    def __init__(self, id, **kwargs):
        super(UserNotFoundError, self).__init__(
            title="User does not exist",
            detail="No user with id '{}' exists.".format(id),
            **kwargs
        )


class UserDataNotUniqueError(BadRequestProblem):
    def __init__(self, mongoEngineError: NotUniqueError, **kwargs):
        super(UserNotFoundError, self).__init__(
            title="User data not unique", detail=str(mongoEngineError), **kwargs
        )
