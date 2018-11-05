"""
An OpenFlow 1.3 router
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
import ipaddress

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.ip_to_mac = {}
        self.mac_to_ip = {}

        # MAC addresses of switch ports
        self.port_to_router_mac = {
            1: '00:50:56:b8:90:fb',
            2: '00:50:56:b8:1d:47',
            3: '00:50:56:b8:b1:ef',
            4: '00:50:56:b8:8a:d2',
            5: '00:50:56:b8:b8:1a',
            6: '00:50:56:b8:eb:95',
            8: '00:50:56:b8:c9:91',
            9: '00:50:56:b8:0b:14'
        }

        # IP addresses of switch ports
        self.port_to_router_ip = {
            1: '172.16.21.1',
            2: '172.16.22.1',
            3: '172.16.23.1',
            4: '172.16.24.1',
            5: '172.16.25.1',
            6: '172.16.26.1',
            8: '172.16.27.1',
            9: '172.16.28.1'
        }

        # Access rules can be defined here
        self.routing = {}
        #                 src               dst        next_hop, out_port
        self.routing['172.16.21.2'] = {'172.16.22.2': ('172.16.22.2', 2),
                                       '172.24.5.2' : ('172.16.22.2', 2),
                                       '172.16.24.2': ('172.16.24.2', 4),
                                       '10.0.2.80'  : ('172.16.24.2', 4)}
        self.routing['172.16.22.2'] = {'172.16.21.2': ('172.16.21.2', 1),
                                       '172.24.4.3' : ('172.16.21.2', 1)}
        self.routing['172.24.5.2'] = {'172.16.21.2' : ('172.16.21.2', 1)}
        self.routing['172.24.4.3'] = {'172.16.22.2' : ('172.16.22.2', 2)}

        self.routing['172.16.23.2'] = {'172.16.24.2': ('172.16.24.2', 4),
                                       '10.0.2.80'  : ('172.16.24.2', 4)}
        self.routing['172.16.24.2'] = {'172.16.23.2': ('172.16.23.2', 3),
                                       '10.0.1.80'  : ('172.16.23.2', 3),
                                       '172.16.21.2': ('172.16.21.2', 1)}
        self.routing['10.0.2.80'] = {'172.16.23.2'  : ('172.16.23.2', 3),
                                     '172.16.21.2'  : ('172.16.21.2', 1)}
        self.routing['10.0.1.80'] = {'172.16.24.2'  : ('172.16.24.2', 4)}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        if pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:
            pkt_arp = pkt.get_protocols(arp.arp)[0]
            self._handle_arp(datapath, in_port, pkt_eth, pkt_arp)
        elif pkt_eth.ethertype == ether_types.ETH_TYPE_IP:
            pkt_ip = pkt.get_protocols(ipv4.ipv4)[0]
            self._handle_ip(datapath, pkt, pkt_ip, pkt_eth, in_port)

    def _handle_arp(self, datapath, in_port, pkt_eth, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return

        # Take note of MAC and IP to use for IPv4 packet handling
        dpid = datapath.id
        self.ip_to_mac.setdefault(dpid, {})
        self.ip_to_mac[dpid][pkt_arp.src_ip] = pkt_eth.src
        self.mac_to_ip.setdefault(dpid, {})
        self.mac_to_ip[dpid][pkt_eth.src] = pkt_arp.src_ip

        # Construct ARP reply
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,
                                           dst=pkt_eth.src,
                                           src=self.port_to_router_mac[in_port]))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=self.port_to_router_mac[in_port],
                                 src_ip=self.port_to_router_ip[in_port],
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=in_port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def _handle_ip(self, datapath, pkt, pkt_ip, pkt_eth, in_port):
        src_ip = pkt_ip.src
        dest_ip = pkt_ip.dst

        # Check access rules (for tenant isolation)
        try:
            next_hop = self.routing[src_ip][dest_ip][0]
            out_port = self.routing[src_ip][dest_ip][1]
            if next_hop is None:
                return
        except KeyError:
            return

        try:
            dst_mac = self.ip_to_mac[datapath.id][next_hop]
        except KeyError:
            return

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data

        # Modify MAC addresses
        actions = [parser.OFPActionSetField(eth_src=self.port_to_router_mac[out_port]),
                   parser.OFPActionSetField(eth_dst=dst_mac),
                   parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER),
                   parser.OFPActionDecNwTtl()]

        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dest_ip)
        
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath=datapath, priority=2, match=match, actions=actions)

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct and install flow rule
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath,
                                match=match,
                                cookie=0,
                                command=ofproto.OFPFC_ADD,
                                hard_timeout=5,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                priority=priority,
                                instructions=inst)
        self.logger.info("flow-rule %s" % (mod,))
        datapath.send_msg(mod)
