#import pymongo
import logging
from pymongo import MongoClient, errors
from dbbase import DbException, DbBase
from http import HTTPStatus
from time import time, sleep

__author__ = "Alfonso Tierno <alfonso.tiernosepulveda@telefonica.com>"

# TODO consider use this decorator for database access retries
# @retry_mongocall
# def retry_mongocall(call):
#     def _retry_mongocall(*args, **kwargs):
#         retry = 1
#         while True:
#             try:
#                 return call(*args, **kwargs)
#             except pymongo.AutoReconnect as e:
#                 if retry == 4:
#                     raise DbException(str(e))
#                 sleep(retry)
#     return _retry_mongocall


class DbMongo(DbBase):
    conn_initial_timout = 120
    conn_timout = 10

    def __init__(self, logger_name='db'):
        self.logger = logging.getLogger(logger_name)

    def db_connect(self, config):
        try:
            if "logger_name" in config:
                self.logger = logging.getLogger(config["logger_name"])
            self.client = MongoClient(config["host"], config["port"])
            self.db = self.client[config["name"]]
            if "loglevel" in config:
                self.logger.setLevel(getattr(logging, config['loglevel']))
            # get data to try a connection
            now = time()
            while True:
                try:
                    self.db.users.find_one({"username": "admin"})
                    return
                except errors.ConnectionFailure as e:
                    if time() - now >= self.conn_initial_timout:
                        raise
                    self.logger.info("Waiting to database up {}".format(e))
                    sleep(2)
        except errors.PyMongoError as e:
            raise DbException(str(e))

    def db_disconnect(self):
        pass  # TODO

    @staticmethod
    def _format_filter(filter):
        try:
            db_filter = {}
            for query_k, query_v in filter.items():
                dot_index = query_k.rfind(".")
                if dot_index > 1 and query_k[dot_index+1:] in ("eq", "ne", "gt", "gte", "lt", "lte", "cont",
                                                               "ncont", "neq"):
                    operator = "$" + query_k[dot_index+1:]
                    if operator == "$neq":
                        operator = "$ne"
                    k = query_k[:dot_index]
                else:
                    operator = "$eq"
                    k = query_k

                v = query_v
                if isinstance(v, list):
                    if operator in ("$eq", "$cont"):
                        operator = "$in"
                        v = query_v
                    elif operator in ("$ne", "$ncont"):
                        operator = "$nin"
                        v = query_v
                    else:
                        v = query_v.join(",")

                if operator in ("$eq", "$cont"):
                    # v cannot be a comma separated list, because operator would have been changed to $in
                    db_filter[k] = v
                elif operator == "$ncount":
                    # v cannot be a comma separated list, because operator would have been changed to $nin
                    db_filter[k] = {"$ne": v}
                else:
                    # maybe db_filter[k] exist. e.g. in the query string for values between 5 and 8: "a.gt=5&a.lt=8"
                    if k not in db_filter:
                        db_filter[k] = {}
                    db_filter[k][operator] = v

            return db_filter
        except Exception as e:
            raise DbException("Invalid query string filter at {}:{}. Error: {}".format(query_k, v, e),
                              http_code=HTTPStatus.BAD_REQUEST)

    def get_list(self, table, filter={}):
        try:
            l = []
            collection = self.db[table]
            rows = collection.find(self._format_filter(filter))
            for row in rows:
                l.append(row)
            return l
        except DbException:
            raise
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def get_one(self, table, filter={}, fail_on_empty=True, fail_on_more=True):
        try:
            if filter:
                filter = self._format_filter(filter)
            collection = self.db[table]
            if not (fail_on_empty and fail_on_more):
                return collection.find_one(filter)
            rows = collection.find(filter)
            if rows.count() == 0:
                if fail_on_empty:
                    raise DbException("Not found any {} with filter='{}'".format(table[:-1], filter),
                                      HTTPStatus.NOT_FOUND)
                return None
            elif rows.count() > 1:
                if fail_on_more:
                    raise DbException("Found more than one {} with filter='{}'".format(table[:-1], filter),
                                      HTTPStatus.CONFLICT)
            return rows[0]
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def del_list(self, table, filter={}):
        try:
            collection = self.db[table]
            rows = collection.delete_many(self._format_filter(filter))
            return {"deleted": rows.deleted_count}
        except DbException:
            raise
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def del_one(self, table, filter={}, fail_on_empty=True):
        try:
            collection = self.db[table]
            rows = collection.delete_one(self._format_filter(filter))
            if rows.deleted_count == 0:
                if fail_on_empty:
                    raise DbException("Not found any {} with filter='{}'".format(table[:-1], filter),
                                      HTTPStatus.NOT_FOUND)
                return None
            return {"deleted": rows.deleted_count}
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def create(self, table, indata):
        try:
            collection = self.db[table]
            data = collection.insert_one(indata)
            return data.inserted_id
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def set_one(self, table, filter, update_dict, fail_on_empty=True):
        try:
            collection = self.db[table]
            rows = collection.update_one(self._format_filter(filter), {"$set": update_dict})
            if rows.matched_count == 0:
                if fail_on_empty:
                    raise DbException("Not found any {} with filter='{}'".format(table[:-1], filter),
                                      HTTPStatus.NOT_FOUND)
                return None
            return {"modified": rows.modified_count}
        except Exception as e:  # TODO refine
            raise DbException(str(e))

    def replace(self, table, id, indata, fail_on_empty=True):
        try:
            _filter = {"_id": id}
            collection = self.db[table]
            rows = collection.replace_one(_filter, indata)
            if rows.matched_count == 0:
                if fail_on_empty:
                    raise DbException("Not found any {} with filter='{}'".format(table[:-1], _filter),
                                      HTTPStatus.NOT_FOUND)
                return None
            return {"replaced": rows.modified_count}
        except Exception as e:  # TODO refine
            raise DbException(str(e))
