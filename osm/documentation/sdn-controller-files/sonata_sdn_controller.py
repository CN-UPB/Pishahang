"""
An OpenFlow 1.3 controller
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import vlan
import ipaddress
from time import sleep
import zmq
import json
from datetime import datetime
from multiprocessing import Process, Queue

VLAN_GATEWAY_SWITCH =   "000070b3d56cdf8a"
SWITCH_2 =              "000070b3d56cdf87"
SWITCH_3 =              "000070b3d56cdf3c"
NUMBER_OPENFLOW_PORTS =         3

q = Queue()

def check_forwarding_graph(q):
    """
    Helper functions that runs in background and receives forwarding graphs
    from the Sonata SDN-Plugin via ZeroMQ.
    """
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:50165")
    while True:
        try:
            forwarding_graph = socket.recv_json(zmq.DONTWAIT)["forwarding_graph"]
            q.put(forwarding_graph)
            socket.send_json({"reply": "IPs OK"})
        except zmq.error.Again:
            sleep(1)

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'dpset': dpset.DPSet,
    }

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.ip_to_mac = {}
        self.forwarding_graphs = []
        self.rules = []
        self.dpset = kwargs['dpset']

        # check ZeroMQ to receive forwarding graph
        p1 = Process(target=check_forwarding_graph, args=(q,)).start()
        
    def get_datapaths(self, params):
        return self.dpset.get_all()

    def forwarding_graph_to_rules(self, forwarding_graph, datapath):
        """
        Assumes the forwarding graph has the following format (IP
        addresses are in order of the chain):
            [
                { 'vlan': 42 },
                { 'ip': 10.0.0.1 },
                { 'ip': 10.0.0.2 },
                { 'ip': 10.0.0.3 },
                { 'ip': 10.0.0.4 }
            ] 
        """

        new_rules = []

        # example chain: A->B->C->D
        # entry rule
        # change A->D to C->B
        new_rules.append({ "vlan": forwarding_graph[0][vlan],
                       "src_mac": self.ip_to_mac[datapath.id][forwarding_graph[1][ip]],
                       "new_src_mac": self.ip_to_mac[datapath.id][forwarding_graph[3][ip]],
                       "new_dst_mac": self.ip_to_mac[datapath.id][forwarding_graph[2][ip]],
                       "new_src_ip": forwarding_graph[3][ip],
                       "new_dst_ip": forwarding_graph[2][ip],
                       "out_port": self.mac_to_port[datapath.id][forwarding_graph[2]]})

        # intermediate rules
        # change B->C to D->C
        for i in range(len(forwarding_graph))[2:-2]:
            new_rules.append({ "vlan": forwarding_graph[0][vlan],
                           "src_mac": self.ip_to_mac[datapath.id][forwarding_graphs[i][ip]],
                           "new_src_mac": self.ip_to_mac[datapath.id][forwarding_graphs[i+2][ip]],
                           "new_dst_mac": self.ip_to_mac[datapath.id][forwarding_graphs[i][ip]], # unchanged
                           "new_src_ip": forwarding_graphs[i+2][ip],
                           "new_dst_ip": forwarding_graphs[i][ip], # unchanged
                           "out_port": self.mac_to_port[datapath.id][self.ip_to_mac[datapath.id][forwarding_graph[i+1][ip]]]})

        # exit rule
        # change C->D to A->D
        new_rules.append({ "vlan": forwarding_graph[0][vlan],
                       "src_mac": self.ip_to_mac[datapath.id][forwarding_graph[len(forwarding_graph)-1][ip]],
                       "new_src_mac": self.ip_to_mac[datapath.id][forwarding_graph[1][ip]],
                       "new_dst_mac": self.ip_to_mac[datapath.id][forwarding_graph[len(forwarding_graph)][ip]],
                       "new_src_ip": forwarding_graph[1][ip],
                       "new_dst_ip": forwarding_graph[len(forwarding_graph)][ip],
                       "out_port": self.mac_to_port[datapath.id][forwarding_graph[len(forwarding_graph)][ip]]})

        self.rules.append(new_rules)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        """
        Called when a switch connects. Useful for feature requests and installing up an initial flow rule.
        """
        msg = ev.msg
        print 'OFPSwitchFeatures received: \ndatapath_id={} n_buffers={} n_tables={} auxiliary_id={} capabilities={}'.format(hex(msg.datapath_id), msg.n_buffers, msg.n_tables, msg.auxiliary_id, hex(msg.capabilities))
        self.logger.debug('OFPSwitchFeatures received: '
                          'datapath_id=0x%016x n_buffers=%d '
                          'n_tables=%d auxiliary_id=%d '
                          'capabilities=0x%08x',
                          msg.datapath_id, msg.n_buffers, msg.n_tables,
                          msg.auxiliary_id, msg.capabilities)

        # install initial rule which make the switch send unmatched packets to the controller to install a flow rules
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        priority=0
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        for port in range(1, NUMBER_OPENFLOW_PORTS+1):
            match = parser.OFPMatch(in_port=port)
            self.add_flow(datapath=datapath, priority=priority, match=match, actions=actions, hard_timeout=0)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Called when the controller receives a packet from a switch.
        """
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)

        if not q.empty():
            # new forwarding graph(s) received; convert to flow rules
            forwarding_graph = q.get(block=False)
            self.forwarding_graphs.append(forwarding_graph)
            self.forwarding_graph_to_rules(forwarding_graph, datapath)
            
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]

        # identify at which switch the packet arrived
        if dpid == VLAN_GATEWAY_SWITCH:
            # switch 1: add vlan according to identified flow
            self._handle_vlan_gateway(pkt, datapath, in_port)
        elif dpid == SWITCH_2 or dpid == SWITCH_3:
            if pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:
                pkt_arp = pkt.get_protocols(arp.arp)[0]
                self._handle_arp(datapath, in_port, msg, pkt_eth, pkt_arp)
            elif pkt_eth.ethertype == ether_types.ETH_TYPE_IP:
                pkt_ip = pkt.get_protocols(ipv4.ipv4)[0]
                self._handle_ip(datapath, pkt, pkt_ip, pkt_eth, in_port)

    def _handle_vlan_gateway(self, datapath, pkt, in_port):
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # handle ARP packets
        if pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:

            # fill mac_to_port table for ARP replies
            if pkt_eth.src not in self.mac_to_port[VLAN_GATEWAY_SWITCH].keys():
                self.mac_to_port[VLAN_GATEWAY_SWITCH][pkt_eth.src] = in_port
            data = pkt.data

            # is dst already in mac_to_port table? if yes, deliver packet, else flood
            if pkt_eth.dst in self.mac_to_port[VLAN_GATEWAY_SWITCH].keys():
                out_port = self.mac_to_port[VLAN_GATEWAY_SWITCH][pkt_eth.dst]
            else:
                out_port = ofproto.OFPP_FLOOD
            actions.append(parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER))

            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=ofproto.OFPP_CONTROLLER,
                                      actions=actions,
                                      data=data)
            datapath.send_msg(out)

        # handle VLAN packets by forwarding them to the other switch as the VLAN
        # gateway switch connectes switches 2 and 3
        elif pkt_eth.ethertype == ether_types.ETH_TYPE_8021Q:
            out_port = 3 if in_port == 2 else 2

            data = pkt.data
            actions.append(parser.OFPActionOutput(ofproto.OFPP_FLOOD, ofproto.OFPCML_NO_BUFFER))
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)

            self.add_flow(datapath=datapath, priority=2, match=match, actions=actions)

            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=ofproto.OFPP_CONTROLLER,
                                      actions=actions,
                                      data=data)
            datapath.send_msg(out)

        # if the received packet is an IP packet, then add VLAN
        elif pkt_eth.ethertype == ether_types.ETH_TYPE_IP:
            # find VLAN ID by src and dst of packet
            vlan = None
            for fg in self.forwarding_graphs:
                packet_src_ip = fg[1]['ip']
                packet_dst_ip = fg[len(fg)]['ip']
                if packet_src_ip == src_ip and packet_dst_ip == dest_ip:
                    vlan = fg[0][vlan]
                    break

            # packet does not match any forwarding graph, drop it.
            if vlan == None:
                return
            
            # apply matching VLAN ID
            else:
                data = pkt.data
                actions.append(parser.OFPActionPushVlan(33024)) # 0x8100 ethertype 802.1q
                actions.append(parser.OFPActionSetField(vlan_vid=rule["vlan"]))
                actions.append(parser.OFPActionOutput(ofproto.OFPP_FLOOD, ofproto.OFPCML_NO_BUFFER))
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)

                self.add_flow(datapath=datapath, priority=2, match=match, actions=actions)

                out = parser.OFPPacketOut(datapath=datapath,
                                          buffer_id=ofproto.OFP_NO_BUFFER,
                                          in_port=ofproto.OFPP_CONTROLLER,
                                          actions=actions,
                                          data=data)
                datapath.send_msg(out)

    def _handle_arp(self, datapath, in_port, msg, pkt_eth, pkt_arp):
        """
        Constructs a 'MAC address to port'-mapping as well as an 'IP address to MAC address'-mapping.
        Both mappings are used to generate flow rules from forwarding graphs and are helpful in various other places.
        """
        dpid = datapath.id
        if pkt_arp.opcode == arp.ARP_REQUEST:
            # fill mac to port mapping to deliver arp reply
            in_port = msg.match['in_port']
            self.mac_to_port.setdefault(dpid, {})
            self.mac_to_port[dpid][pkt_eth.src] = in_port

            self.ip_to_mac.setdefault(dpid, {})
            self.ip_to_mac[dpid][pkt_arp.src_ip] = pkt_eth.src

            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # flood arp request
            actions = [parser.OFPActionOutput(port=ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=in_port, actions=actions,
                                      data=msg.data)
        elif pkt_arp.opcode == arp.ARP_REPLY:
            actions = [
                parser.OFPActionOutput(port=self.mac_to_port[dpid][pkt_eth.dst])
            ]
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=in_port, actions=actions,
                                      data=msg.data)

    def _handle_ip(self, datapath, msg, pkt, pkt_ip, pkt_eth, in_port):
        src_mac = pkt_eth.src
        vlan = msg.match['vlan_vid']

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data

        # find matching rule and apply actions
        for rule in self.rules:
            if rule["src_mac"] == src_mac and rule["vlan"]:
                actions = [
                    parser.OFPActionSetField(eth_src=rule["new_src_mac"]),
                    parser.OFPActionSetField(eth_dst=rule["new_dst_mac"]),
                    parser.OFPActionSetField(ipv4_src=rule["new_src_ip"]),
                    parser.OFPActionSetField(ipv4_dst=rule["new_dst_ip"]),
                    parser.OFPActionSetField(vlan_vid=rule["vlan"]),
                    parser.OFPActionOutput(rule["out_port"], ofproto.OFPCML_NO_BUFFER),
                    parser.OFPActionDecNwTtl()]
                break

        match = parser.OFPMatch(eth_src=rule["src_mac"], vlan_vid=vlan_vid)
            
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath=datapath, priority=2, match=match, actions=actions)

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions, hard_timeout=5):
        """
        Adds a flow rule to a switch (aka datapath).
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath,
                                match=match,
                                cookie=0,
                                command=ofproto.OFPFC_ADD,
                                hard_timeout=hard_timeout,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                priority=priority,
                                instructions=inst)
        # self.logger.info("flow-rule %s" % (mod,))
        datapath.send_msg(mod)
