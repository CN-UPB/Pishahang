import asyncio
from time import time
from typing import Callable, Type, Union


def create_status_message(
    status: str = None, error: Union[str, Exception] = None, payload={}
):
    if status is None:
        if error is not None:
            status = "ERROR"
        else:
            status = "SUCCESS"

    if isinstance(error, Exception):
        error = str(error)

    return {
        **payload,
        "status": status,
        "error": error,
        "timestamp": time(),
    }


def get_vm_image_id(vnfd: dict, vdu: dict):
    return "{}_{}_{}_{}".format(
        vnfd["vendor"], vnfd["name"], vnfd["version"], vdu["id"]
    )


def raise_on_error_response(
    response: dict, exception_class: Type[Exception], logger=None, *log_args
):
    """
    Given a response message payload, raises an exception of the specified exception
    class if the response indicates an error (i.e. `request_status` is "ERROR" or, if
    `request_status` is not present, `status` is "Error"). The error message of the IA
    is provided as the only argument to the constructor of the exception class. If
    `logger` is provided, its `info` method will be invoked with `log_args` if
    `ia_response` indicates an error.

    Args:
        response: A response payload
        exception_class: The exception class to be used in case of an error
        logger: An optional logger instance to log the error
        *log_args: The arguments that will be provided to the `info` method of `logger`
    """
    status = response.get("request_status", None) or response.get("status", None)
    if status == "ERROR":
        message = response["message"] if "message" in response else response["error"]
        if logger is not None:
            logger.info(*log_args)
            logger.debug("Error: %s", message)
        raise exception_class(message)


async def run_sync(function: Callable, *args, **kwargs):
    """
    Async method to run a synchronous function in an executor thread
    """
    return await asyncio.get_running_loop().run_in_executor(
        None, function, *args, **kwargs
    )
