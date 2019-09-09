import socket
from datetime import datetime
from rtmp_sniffer.helpers.general import *
from rtmp_sniffer.helpers import messaging
from rtmp_sniffer.helpers.ethernet import Ethernet
from rtmp_sniffer.helpers.ipv4 import IPv4
from rtmp_sniffer.helpers.icmp import ICMP
from rtmp_sniffer.helpers.tcp import TCP
from rtmp_sniffer.helpers.udp import UDP
from rtmp_sniffer.helpers.http import HTTP
import logging
import yaml
import os


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("rtmp-sniffer")
LOG.setLevel(logging.INFO)
logging.getLogger("mac-ip-recorder:messaging").setLevel(logging.INFO)


class RTMPSniffer(object):

    def __init__(self):

        self.name = "sniffer"
        self.start_running=True
        self.topic = "rtmp.mac.ip.recorder"

        if 'nic_id' in os.environ:
            self.port = os.environ['nic_id']
        else:
            self.port = 'eth0'

        while True:
            try:
                self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)
                break
            except:
                time.sleep(5)

        if self.start_running:
            self.sniffer()

    def response(self, ch, method, props, response):

        response = yaml.load(str(response))
        if type(response) == dict:
            LOG.info(response)

    def sniffer(self):
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        conn.bind((self.port,3))
        LOG.info ("Packet capturing has been started!")
        while True:
            raw_data, addr = conn.recvfrom(65535)
            eth = Ethernet(raw_data)
            LOG.info('Destination: {}, Source: {}, Protocol: {}'.format(eth.dest_mac, eth.src_mac, eth.proto))

            # IPv4
            if eth.proto == 8:
                ipv4 = IPv4(eth.data)
                LOG.info('IPv4 Packet => Version: {}, Header Length: {}, TTL: {}, Protocol: {}, Source: {}, Target: {}'.format(ipv4.version,
                ipv4.header_length, ipv4.ttl, ipv4.proto, ipv4.src, ipv4.target))

                # ICMP
                if ipv4.proto == 1:
                    icmp = ICMP(ipv4.data)
                    LOG.info('ICMP Packet => Type: {}, Code: {}, Checksum: {},'.format(icmp.type, icmp.code, icmp.checksum))

                # TCP
                elif ipv4.proto == 6:
                    tcp = TCP(ipv4.data)
                    LOG.info('TCP Segment => Source Port: {}, Destination Port: {} Sequence: {}, Acknowledgment: {}'.format(tcp.src_port,
                    tcp.dest_port, tcp.sequence, tcp.acknowledgment))
                    LOG.info('Flags => URG: {}, ACK: {}, PSH: {} RST: {}, SYN: {}, FIN:{}'.format(tcp.flag_urg, tcp.flag_ack,
                    tcp.flag_psh, tcp.flag_rst, tcp.flag_syn, tcp.flag_fin))

                    #RTMP
                    # to ask - which MAC-IP pair shoudl be recorded? SRC or DST?
                    if tcp.src_port == 1935:
                        dateTimeObj = datetime.now()
                        LOG.info("RTMP packet found!!")
                        LOG.info("RTMP packet source MAC = '{0}' and source IP = '{1}'".format(eth.src_mac, ipv4.src))
                        LOG.info("RTMP packet destination MAC = '{0}' and destination IP = '{1}'".format(eth.dest_mac, ipv4.target))
                        message = {"mac":eth.src_mac, "ip":ipv4.src, "time":str(dateTimeObj)}
                        self.manoconn.call_async(self.response, self.topic, yaml.dump(message))

                    if tcp.dest_port ==1935:
                        dateTimeObj = datetime.now()
                        LOG.info("RTMP packet found!!")
                        LOG.info("RTMP packet source MAC = '{0}' and source IP = '{1}'".format(eth.src_mac, ipv4.src))
                        LOG.info("RTMP packet destination MAC = '{0}' and destination IP = '{1}'".format(eth.dest_mac, ipv4.target))
                        message = {"mac":eth.dest_mac, "ip":ipv4.target, "time":str(dateTimeObj)}
                        self.manoconn.call_async(self.response, self.topic, yaml.dump(message))

                    if len(tcp.data) > 0:

                        # HTTP
                        if tcp.src_port == 80 or tcp.dest_port == 80:
                            try:
                                http = HTTP(tcp.data)
                                http_info = str(http.data).split('\n')
                                for line in http_info:
                                    LOG.info(str(line))
                            except:
                                LOG.info('...')

                # UDP
                elif ipv4.proto == 17:
                    udp = UDP(ipv4.data)
                    LOG.info('UDP Segment => Source Port: {}, Destination Port: {}, Length: {}'.format(udp.src_port, udp.dest_port, udp.size))


def main():
    RTMPSniffer()

if __name__ == '__main__':
    main()
