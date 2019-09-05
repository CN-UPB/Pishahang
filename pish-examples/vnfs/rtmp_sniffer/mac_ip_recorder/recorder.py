import logging
import json
import datetime
import yaml
import uuid
import os
import time
from mongoengine import DoesNotExist

from mac_ip_recorder import messaging
from mac_ip_recorder import model
from mac_ip_recorder import interface

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("mac-ip-recorder")
LOG.setLevel(logging.INFO)
logging.getLogger("mac-ip-recorder:messaging").setLevel(logging.INFO)


class MACandIPrecorder(object):

    def __init__(self):
        # initialize plugin DB model
        model.initialize()

        # start up management interface
        interface.start(self)
        self.name = "recorder"
        self.start_running=True

        while True:
            try:
                self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)
                break
            except:
                time.sleep(5)

        self.declare_subscriptions()

        if self.start_running:
            self.run()

    def run(self):
        # go into infinity loop 
        while True:
            time.sleep(1)

    def declare_subscriptions(self):
        """
        Declare topics to which we want to listen and define callback methods.
        """
        self.manoconn.subscribe(self._on_register, "rtmp.mac.ip.recorder")

    def _on_register(self, ch, method, properties, message):
        """
        Event method that is called when a registration request is received.
        Registers the new MAC and IP pair in the internal data model and returns
        a fresh UUID that is used to identify it.
        :param properties: request properties
        :param message: request body
        :return: response message
        """

        if properties.app_id == self.name:
            return

        message = yaml.load(str(message))
        print (message)
        pid = str(uuid.uuid4())

        # create a entry in our plugin database
        record = model.mac_ip_pair(
            id=pid,
            mac=message.get("mac"),
            ip=message.get("ip"),
            time=message.get("time"),
        )

        try:
            record.save()
            LOG.info("MAC and IP pair recorded: %r" % record)
            # return result
            response = {
                "status": "OK",
                "id": pid,
                "mac": record.mac,
                "ip": record.ip,
                "time": record.time,
                "error": None
            }
            self.manoconn.notify(
                'rtmp.mac.ip.recorder', json.dumps(response), correlation_id=properties.correlation_id)
        except BaseException as err:
            LOG.info("MAC and IP recroding failed: %r" % str(err))
            # return result
            response = {
                "status": "Failed",
                "id": pid,
                "mac": record.mac,
                "ip": record.ip,
                "time": record.time,
                "error": str(err)
            }
            self.manoconn.notify(
                'rtmp.mac.ip.recorder', json.dumps(response), correlation_id=properties.correlation_id)


def main():
    MACandIPrecorder()

if __name__ == '__main__':
    main()
