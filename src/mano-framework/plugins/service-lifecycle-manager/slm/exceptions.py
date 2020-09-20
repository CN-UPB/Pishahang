class DeployRequestValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class InstantiationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

    def add_error(self, e: Exception):
        """
        Add the provided exception to the args of the instantiation error.
        """
        self.args += (e,)


class TerminationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class PlacementError(InstantiationError):
    def __init__(self):
        super().__init__("Unable to perform placement.")
