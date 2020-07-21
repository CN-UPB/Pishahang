class DeployRequestValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class InstantiationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

    def add_error(self, e: Exception):
        """
        Stringify a provided exception and add it to the error message of the
        instantiation error.
        """
        self.message += "\n" + str(e)


class TerminationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class PlacementError(IndentationError):
    def __init__(self):
        super().__init__("Unable to perform placement.")
