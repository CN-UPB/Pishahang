from connexion.exceptions import BadRequestProblem


class InvalidDescriptorContentsException(BadRequestProblem):
    """
    Indicates that invalid contents have been provided to `Descriptor.descriptor`
    """

    def __init__(self, detail, **kwargs):
        super(InvalidDescriptorContentsException, self).__init__(
            title="Invalid Descriptor",
            detail=detail,
            **kwargs
        )
