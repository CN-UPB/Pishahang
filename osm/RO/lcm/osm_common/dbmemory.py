import logging
from dbbase import DbException, DbBase
from http import HTTPStatus
from uuid import uuid4
from copy import deepcopy

__author__ = "Alfonso Tierno <alfonso.tiernosepulveda@telefonica.com>"


class DbMemory(DbBase):

    def __init__(self, logger_name='db'):
        self.logger = logging.getLogger(logger_name)
        self.db = {}

    def db_connect(self, config):
        if "logger_name" in config:
            self.logger = logging.getLogger(config["logger_name"])

    @staticmethod
    def _format_filter(filter):
        return filter    # TODO

    def _find(self, table, filter):
        for i, row in enumerate(self.db.get(table, ())):
            match = True
            if filter:
                for k, v in filter.items():
                    if k not in row or v != row[k]:
                        match = False
            if match:
                yield i, row

    def get_list(self, table, filter={}):
        try:
            l = []
            for _, row in self._find(table, self._format_filter(filter)):
                l.append(deepcopy(row))
            return l
        except DbException:
            raise
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def get_one(self, table, filter={}, fail_on_empty=True, fail_on_more=True):
        try:
            l = None
            for _, row in self._find(table, self._format_filter(filter)):
                if not fail_on_more:
                    return deepcopy(row)
                if l:
                    raise DbException("Found more than one entry with filter='{}'".format(filter),
                                      HTTPStatus.CONFLICT.value)
                l = row
            if not l and fail_on_empty:
                raise DbException("Not found entry with filter='{}'".format(filter), HTTPStatus.NOT_FOUND)
            return deepcopy(l)
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def del_list(self, table, filter={}):
        try:
            id_list = []
            for i, _ in self._find(table, self._format_filter(filter)):
                id_list.append(i)
            deleted = len(id_list)
            for i in id_list:
                del self.db[table][i]
            return {"deleted": deleted}
        except DbException:
            raise
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def del_one(self, table, filter={}, fail_on_empty=True):
        try:
            for i, _ in self._find(table, self._format_filter(filter)):
                break
            else:
                if fail_on_empty:
                    raise DbException("Not found entry with filter='{}'".format(filter), HTTPStatus.NOT_FOUND)
                return None
            del self.db[table][i]
            return {"deleted": 1}
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def replace(self, table, filter, indata, fail_on_empty=True):
        try:
            for i, _ in self._find(table, self._format_filter(filter)):
                break
            else:
                if fail_on_empty:
                    raise DbException("Not found entry with filter='{}'".format(filter), HTTPStatus.NOT_FOUND)
                return None
            self.db[table][i] = deepcopy(indata)
            return {"upadted": 1}
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def create(self, table, indata):
        try:
            id = indata.get("_id")
            if not id:
                id = str(uuid4())
                indata["_id"] = id
            if table not in self.db:
                self.db[table] = []
            self.db[table].append(deepcopy(indata))
            return id
        except Exception as e:  # TODO refine
            raise DbException(str(e))


if __name__ == '__main__':
    # some test code
    db = dbmemory()
    db.create("test", {"_id": 1, "data": 1})
    db.create("test", {"_id": 2, "data": 2})
    db.create("test", {"_id": 3, "data": 3})
    print("must be 3 items:", db.get_list("test"))
    print("must return item 2:", db.get_list("test", {"_id": 2}))
    db.del_one("test", {"_id": 2})
    print("must be emtpy:", db.get_list("test", {"_id": 2}))
