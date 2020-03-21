from connexion.exceptions import BadRequestProblem, ProblemException


class NotFoundProblem(ProblemException):
    def __init__(self, title='Not Found', detail=None):
        super(NotFoundProblem, self).__init__(status=404, title=title, detail=detail)


class InvalidDescriptorContentError(BadRequestProblem):
    """
    Indicates that invalid contents have been provided to `Descriptor.descriptor`
    """

    def __init__(self, detail, **kwargs):
        super(InvalidDescriptorContentError, self).__init__(
            title="Invalid Descriptor",
            detail=detail,
            **kwargs
        )


class DuplicateDescriptorNameError(BadRequestProblem):
    def __init__(self, **kwargs):
        super(DuplicateDescriptorNameError, self).__init__(
            title="Duplicate Descriptor Name",
            detail="A descriptor with the given name does already exist in the database. " +
            "Please change the descriptor name.",
            **kwargs
        )


class DescriptorNotFoundError(NotFoundProblem):
    def __init__(self, detail="No descriptor matching the given id was found.", **kwargs):
        super(DescriptorNotFoundError, self).__init__(
            title="Descriptor Not Found",
            detail=detail,
            **kwargs
        )
