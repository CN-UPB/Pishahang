from http import HTTPStatus

__author__ = "Alfonso Tierno <alfonso.tiernosepulveda@telefonica.com>"


class DbException(Exception):

    def __init__(self, message, http_code=HTTPStatus.NOT_FOUND):
        # TODO change to http.HTTPStatus instead of int that allows .value and .name
        self.http_code = http_code
        Exception.__init__(self, "database exception " + message)


class DbBase(object):

    def __init__(self):
        pass

    def db_connect(self, config):
        pass

    def db_disconnect(self):
        pass

    def get_list(self, table, filter={}):
        pass

    def get_one(self, table, filter={}, fail_on_empty=True, fail_on_more=True):
        pass

    def create(self, table, indata):
        pass

    def del_list(self, table, filter={}):
        pass

    def del_one(self, table, filter={}, fail_on_empty=True):
        pass
