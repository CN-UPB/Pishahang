import socket
from datetime import datetime
from general import *
from helpers import messaging
from networking.ethernet import Ethernet
from networking.ipv4 import IPv4
from networking.icmp import ICMP
from networking.tcp import TCP
from networking.udp import UDP
from networking.pcap import Pcap
from networking.http import HTTP
import logging
import yaml


TAB_1 = '\t - '
TAB_2 = '\t\t - '
TAB_3 = '\t\t\t - '
TAB_4 = '\t\t\t\t - '

DATA_TAB_1 = '\t   '
DATA_TAB_2 = '\t\t   '
DATA_TAB_3 = '\t\t\t   '
DATA_TAB_4 = '\t\t\t\t   '

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("rtmp-sniffer")
LOG.setLevel(logging.INFO)
logging.getLogger("mac-ip-recorder:messaging").setLevel(logging.INFO)


class RTMPSniffer(object):

    def __init__(self):

        self.name = "sniffer"
        self.start_running=True
        self.topic = "rtmp.mac.ip.recorder"

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
        conn.bind(("ens32",3))
        while True:
            raw_data, addr = conn.recvfrom(65535)
            eth = Ethernet(raw_data)
            print(TAB_1 + 'Destination: {}, Source: {}, Protocol: {}'.format(eth.dest_mac, eth.src_mac, eth.proto))

            # IPv4
            if eth.proto == 8:
                ipv4 = IPv4(eth.data)
                print(TAB_1 + 'IPv4 Packet:')
                print(TAB_2 + 'Version: {}, Header Length: {}, TTL: {},'.format(ipv4.version, ipv4.header_length, ipv4.ttl))
                print(TAB_2 + 'Protocol: {}, Source: {}, Target: {}'.format(ipv4.proto, ipv4.src, ipv4.target))

                # ICMP
                if ipv4.proto == 1:
                    icmp = ICMP(ipv4.data)
                    print(TAB_1 + 'ICMP Packet:')
                    print(TAB_2 + 'Type: {}, Code: {}, Checksum: {},'.format(icmp.type, icmp.code, icmp.checksum))
                    print(TAB_2 + 'ICMP Data:')
                    print(format_multi_line(DATA_TAB_3, icmp.data))

                # TCP
                elif ipv4.proto == 6:
                    tcp = TCP(ipv4.data)
                    print(TAB_1 + 'TCP Segment:')
                    print(TAB_2 + 'Source Port: {}, Destination Port: {}'.format(tcp.src_port, tcp.dest_port))
                    print(TAB_2 + 'Sequence: {}, Acknowledgment: {}'.format(tcp.sequence, tcp.acknowledgment))
                    print(TAB_2 + 'Flags:')
                    print(TAB_3 + 'URG: {}, ACK: {}, PSH: {}'.format(tcp.flag_urg, tcp.flag_ack, tcp.flag_psh))
                    print(TAB_3 + 'RST: {}, SYN: {}, FIN:{}'.format(tcp.flag_rst, tcp.flag_syn, tcp.flag_fin))

                    #RTMP
                    # to ask - which MAC-IP pair shoudl be recorded? SRC or DST?
                    if tcp.src_port == 1935 or tcp.dest_port ==1935:
                        dateTimeObj = datetime.now()
                        LOG.info("RTMP packet found!!")
                        LOG.info("RTMP packet source MAC = '{0}' and source IP = '{1}'".format(eth.src_mac, ipv4.src))
                        LOG.info("RTMP packet destination MAC = '{0}' and destination IP = '{1}'".format(eth.dest_mac, ipv4.target))
                        message = {"mac":eth.dest_mac, "ip":ipv4.target, "time":str(dateTimeObj)}
                        self.manoconn.call_async(self.response, self.topic, yaml.dump(message))

                    if len(tcp.data) > 0:

                        # HTTP
                        if tcp.src_port == 80 or tcp.dest_port == 80:
                            print(TAB_2 + 'HTTP Data:')
                            try:
                                http = HTTP(tcp.data)
                                http_info = str(http.data).split('\n')
                                for line in http_info:
                                    print(DATA_TAB_3 + str(line))
                            except:
                                print(format_multi_line(DATA_TAB_3, tcp.data))
                        else:
                            print(TAB_2 + 'TCP Data:')
                            print(format_multi_line(DATA_TAB_3, tcp.data))

                # UDP
                elif ipv4.proto == 17:
                    udp = UDP(ipv4.data)
                    print(TAB_1 + 'UDP Segment:')
                    print(TAB_2 + 'Source Port: {}, Destination Port: {}, Length: {}'.format(udp.src_port, udp.dest_port, udp.size))

                # Other IPv4
                else:
                    print(TAB_1 + 'Other IPv4 Data:')
                    print(format_multi_line(DATA_TAB_2, ipv4.data))

            else:
                print('Ethernet Data:')
                print(format_multi_line(DATA_TAB_1, eth.data))



def main():
    RTMPSniffer()

if __name__ == '__main__':
    main()
