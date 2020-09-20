from typing import Type, Union

import bitmath


def create_error_response(message: str):
    return {"request_status": "ERROR", "message": message}


def create_completed_response(response={}):
    response.setdefault("request_status", "COMPLETED")
    return response


def convert_size(
    size: Union[str, int, float], unit: str, to_unit: Type[bitmath.Bitmath]
) -> float:
    """
    Parses an arbitrary `size` value (str, int, float) in a specified unit (str),
    converts it to `to_unit` (a subclass of bitmath.Bitmath) and returns the resulting
    value as a float.
    """
    return to_unit.from_other(
        bitmath.parse_string_unsafe("{} {}".format(size, unit,))
    ).value
