class VimNotFoundException(Exception):
    def __init__(self, vim_type: str, vim_id: str):
        super().__init__(
            'No VIM of type "{}" with id "{}" was found.'.format(vim_type, vim_id)
        )


class VimConnectionError(Exception):
    def __init__(self, message: str = None):
        super().__init__(
            "Failed to connect to VIM{}".format(
                "." if message is None else ": " + message
            )
        )


class TerraformException(Exception):
    def __init__(self, return_code: int, output: str):
        super().__init__(output)
        self.return_code = return_code
