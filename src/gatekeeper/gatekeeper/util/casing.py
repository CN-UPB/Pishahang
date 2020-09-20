import stringcase


def _convertDictKeys(conversion_function, d: dict) -> dict:
    return {
        conversion_function(key): value
        if not isinstance(value, dict)
        else _convertDictKeys(conversion_function, value)
        for key, value in d.items()
    }


def snakecaseDictKeys(d: dict) -> dict:
    """
    Recursively snake-case the keys of a dict
    """
    return _convertDictKeys(stringcase.snakecase, d)


def camelcaseDictKeys(d: dict) -> dict:
    """
    Recursively camel-case the keys of a dict
    """
    return _convertDictKeys(stringcase.camelcase, d)
