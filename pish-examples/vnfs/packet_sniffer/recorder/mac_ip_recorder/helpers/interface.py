import logging
import threading
import json
from flask import Flask, request
import flask_restful as fr
from mongoengine import DoesNotExist
from mac_ip_recorder.helpers import model

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("mac-ip-recorder:interface")
LOG.setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)


class RecordersEndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET list of all records")
        return [p.to_dict() for p in model.mac_ip_pair.objects], 200


class RecorderIDEndpoint(fr.Resource):

    def get(self, mac_ip_pair_id=None):
        LOG.debug("GET record info for: %r" % mac_ip_pair_id)
        try:
            p = model.mac_ip_pair.objects.get(id=mac_ip_pair_id)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % mac_ip_pair_id)
            return {}, 404

class RecorderMACEndpoint(fr.Resource):

    def get(self, mac_ip_pair_ip=None):
        LOG.debug("GET record info for: %r" % mac_ip_pair_ip)
        try:
            p = model.mac_ip_pair.objects.get(ip=mac_ip_pair_ip)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % mac_ip_pair_ip)
            return {}, 404

class RecorderIPEndpoint(fr.Resource):

    def get(self, mac_ip_pair_mac=None):
        LOG.debug("GET record info for: %r" % mac_ip_pair_mac)
        try:
            p = model.mac_ip_pair.objects.get(mac=mac_ip_pair_mac)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % mac_ip_pair_mac)
            return {}, 404

class ClearDBEndpoint(fr.Resource):

    def get(self):
        LOG.debug("Clearing DB!")
        try:
            model.initialize()
            return {"DB_restart":"succeeded"}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % mac_ip_pair_mac)
            return {"DB_restart":"failed"}, 404

# reference to plugin manager
PM = None
# setup Flask
app = Flask(__name__)
api = fr.Api(app)
# register endpoints
api.add_resource(RecordersEndpoint, "/api/records")
api.add_resource(ClearDBEndpoint, "/api/clear/db")
api.add_resource(RecorderIDEndpoint, "/api/records/id/<string:mac_ip_pair_id>")
api.add_resource(RecorderMACEndpoint, "/api/records/mac/<string:mac_ip_pair_ip>")
api.add_resource(RecorderIPEndpoint, "/api/records/ip/<string:mac_ip_pair_mac>")


def _start_flask(host, port):
    # start the Flask server
    app.run(host=host,
            port=port,
            debug=True,
            use_reloader=False  # this is needed to run Flask in a non-main thread
            )


def start(pm, host="0.0.0.0", port=8001):
    global PM
    PM = pm
    thread = threading.Thread(target=_start_flask, args=(host, port))
    thread.daemon = True
    thread.start()
    LOG.info("Started management REST interface @ http://%s:%d" % (host, port))
