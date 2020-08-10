"""
Helper functions to access the repository microservice
"""

from typing import Callable, List, Union

import requests
from appcfg import get_config

repository_url = get_config(__name__)["repository_url"]


TIMEOUT = 5  # seconds

Resource = Union[dict, List[dict]]


def post(endpoint: str, data: Resource):
    """
    Sends a POST request to the given repository endpoint with the provided data and
    raises a `requests.RequestException` on error.

    Args:
        endpoint: The endpoint URL relative to the repository root URL, without a leading slash
        data: The data to be sent to the repository
    """
    response = requests.post(f"{repository_url}/{endpoint}", json=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def put(endpoint: str, data: Resource):
    """
    Sends a PUT request to the given repository endpoint with the provided data and
    raises a `requests.RequestException` on error.

    Args:
        endpoint: The endpoint URL relative to the repository root URL, without a leading slash
        data: The data to be sent to the repository
    """
    response = requests.put(f"{repository_url}/{endpoint}", json=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def get(endpoint: str) -> Resource:
    """
    Returns the deserialized JSON data retrieved from the provided repository endpoint
    or raises a `requests.RequestException` on error.

    Args:
        endpoint: The endpoint URL relative to the repository root URL, without a leading slash
    """
    response = requests.get(f"{repository_url}/{endpoint}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def delete(endpoint: str):
    """
    Sends a DELETE request to the given repository endpoint and raises a
    `requests.RequestException` on error.

    Args:
        endpoint: The endpoint URL relative to the repository root URL, without a leading slash
        data: The data to be sent to the repository
    """
    response = requests.delete(f"{repository_url}/{endpoint}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def update(endpoint: str, updater: Callable[[Resource], Resource]) -> Resource:
    """
    Retrieves the resource from `endpoint`, calls the provided `updater` function and
    sends a PUT request with the return value from the `updater` function to the
    endpoint. On error, a `requests.RequestException` is raised.

    Args:
        endpoint: The endpoint URL relative to the repository root URL, without a leading slash
        updater: A callback function that will be invoked with the data retrieved from the endpoint and returns the updated data that will be sent in a PUT request

    Returns: The updated resource as returned by the `updater` function
    """
    resource = updater(get(endpoint))
    put(endpoint, resource)
    return resource
