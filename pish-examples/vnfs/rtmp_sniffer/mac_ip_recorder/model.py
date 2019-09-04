import logging
import os
from datetime import datetime
from mongoengine import Document, connect, StringField, DateTimeField, BooleanField, signals

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("mac-ip-recorder:model")
LOG.setLevel(logging.INFO)


class mac_ip_pair(Document):
    """
    This model represents pair of MAC and IP addresses in RTMP packets.
    We use mongoengine as ORM to interact with MongoDB.
    """
    id = StringField(primary_key=True, required=True)
    mac = StringField(required=True)
    ip = StringField(required=True)
    time = StringField(required=False)

    def __repr__(self):
        return "Record(id=%r, mac=%r, ip=%r, time=%r)" % (self.id, self.mac, self.ip, self.time)

    def __str__(self):
        return self.__repr__()

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)

    def to_dict(self):
        """
        Convert to dict.
        :return:
        """
        res = dict()
        res["id"] = self.id
        res["mac"] = self.mac
        res["ip"] = self.ip
        res["time"] = self.time
        return res


def initialize(db="mac-ip-pair",
               host=os.environ.get("mongo_host", "127.0.0.1"),
               port=int(os.environ.get("mongo_port", 27017)),
               clear_db=True):
    db_conn = connect(db, host=host, port=port)
    LOG.info("Connected to MongoDB %r@%s:%d" % (db, host, port))
    if clear_db:
        # remove all old data from DB
        db_conn.drop_database(db)
        LOG.info("Cleared DB %r" % db)
