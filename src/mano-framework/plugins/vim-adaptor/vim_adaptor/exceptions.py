class VimNotFoundException(Exception):
    def __init__(self, vim_type: str, vim_id: str):
        super().__init__(
            'No VIM of type "{}" with id "{}" was found.'.format(vim_type, vim_id)
        )


class TerraformException(Exception):
    def __init__(self, return_code, stdout, stderr):
        super().__init__(stderr)
        self.return_code = return_code
        self.stdout = return_code
