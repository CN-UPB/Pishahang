import logging
import yaml
import time
from mac_ip_recorder import messaging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("son-mano-fakeslm")

LOG.setLevel(logging.DEBUG)
logging.getLogger("mac-ip-recorder:messaging").setLevel(logging.INFO)


class fakeslm_onboarding(object):
    def __init__(self):

        self.name = 'fake-slm'
        self.version = '0.1-dev'
        self.description = 'description'

        LOG.info("Starting SLM1:...")

        # create and initialize broker connection
        self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)

        self.end = False

        self.publish_nsd()

        self.run()

    def run(self):

        # go into infinity loop

        while self.end == False:
            time.sleep(1)

    def publish_nsd(self):

        LOG.info("Sending onboard request")
        nsd = open('test_msg.yml', 'r')
        message = yaml.load(nsd)

        self.manoconn.call_async(self._on_publish_nsd_response,
                                 'rtmp.mac.ip.recorder',
                                 yaml.dump(message))
        print ("adsa")
        nsd.close()

    def _on_publish_nsd_response(self, ch, method, props, response):

        response = yaml.load(str(response))
        print ("asad")
        if type(response) == dict:
            print(response)


def main():
    fakeslm_onboarding()


if __name__ == '__main__':
    main()
