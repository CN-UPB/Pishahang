import stringcase


def snakecaseDictKeys(d: dict) -> dict:
    """
    Recursively snake-case the keys of a dict
    """
    return {
        stringcase.snakecase(key): value
        if not isinstance(value, dict)
        else snakecaseDictKeys(value)
        for key, value in d.items()
    }
