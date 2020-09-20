"""
Utilities for pishahang-internal messaging
"""

from connexion import ProblemException
from manobase.messaging import ManoBrokerRequestResponseConnection


class ConnexionBrokerConnection(ManoBrokerRequestResponseConnection):
    """
    A subclass of `ManoBrokerRequestResponseConnection` that adds convenient methods for
    synchronous calls within Connexion endpoint handler functions.
    """

    def __init__(self, app_id, **kwargs):
        super().__init__(app_id, **kwargs)

    def call_sync(self, *args, **kwargs):
        """
        Wrapper around `ManoBrokerRequestResponseConnection.call_sync()` that raises a
        Connexion `ProblemException` in case of a timeout.
        """
        result = super().call_sync(*args, **kwargs)
        if result is None:
            raise ProblemException(
                status=500,
                title="Internal Server Error",
                detail="A microservice did not respond in time.",
            )
        return result
