
import asyncio
from http import HTTPStatus

__author__ = "Alfonso Tierno <alfonso.tiernosepulveda@telefonica.com>"


class MsgException(Exception):
    """
    Base Exception class for all msgXXXX exceptions
    """

    def __init__(self, message, http_code=HTTPStatus.INTERNAL_SERVER_ERROR):
        """
        General exception
        :param message:  descriptive text
        :param http_code: <http.HTTPStatus> type. It contains ".value" (http error code) and ".name" (http error name
        """
        self.http_code = http_code
        Exception.__init__(self, "messaging exception " + message)


class MsgBase(object):
    """
    Base class for all msgXXXX classes
    """

    def __init__(self):
        pass

    def connect(self, config):
        pass

    def disconnect(self):
        pass

    def write(self, topic, key, msg):
        pass

    def read(self, topic):
        pass

    async def aiowrite(self, topic, key, msg, loop):
        pass

    async def aioread(self, topic, loop):
        pass
