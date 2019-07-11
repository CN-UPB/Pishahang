# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
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


NAP_SWITCH = 123917682139018
VIM_SWITCH = 123917682138940

fg= []
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
            print("Recived a new forwarding graph! = {0}".format(forwarding_graph))
            fg = forwarding_graph
            print fg
            socket.send_json({"reply": "IPs OK"})
        except zmq.error.Again:
            sleep(1)


class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.forwarding_graphs = []
        self.mac_to_port = {}
        self.ds_ip= None
        self.mac_adds = {"DS":"fa:16:3e:43:d9:f6", "K8":"0c:c4:7a:41:fc:b1", "SRC":"0c:c4:7a:06:97:69", "DST":"00:0a:cd:1d:91:8b"}
        p1 = Process(target=check_forwarding_graph, args=(q,)).start()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = []

        if not q.empty():
            # new forwarding graph(s) received; convert to flow rules
            forwarding_graph = q.get(block=False)
            #self.forwarding_graphs.append(forwarding_graph)
            print (forwarding_graph)
            try:
                self.ds_ip = forwarding_graph[2]["ip"]
                print self.ds_ip
            except:
                self.ds_ip = "192.168.23.104"

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        dst = eth_pkt.dst
        src = eth_pkt.src
        in_port = msg.match['in_port']


        if icmp_pkt:
            print(in_port, dpid)

        if arp_pkt:
            self._handle_arp(datapath, in_port, eth_pkt, arp_pkt, arp_pkt.dst_ip)
            return

        if ip_pkt:
            dst_ip = ip_pkt.dst
            print (in_port, dpid, dst_ip)
            if dpid == NAP_SWITCH:

                if dst_ip == "192.168.25.66" and in_port == 2:
                    actions.append(parser.OFPActionSetField(eth_dst= self.mac_adds["DS"]))
                    actions.append(parser.OFPActionSetField(ipv4_dst= self.ds_ip))
                    actions.append(parser.OFPActionSetField(eth_src= self.mac_adds["K8"]))
                    actions.append(parser.OFPActionSetField(ipv4_src= "192.168.23.10"))
                    actions.append(parser.OFPActionOutput(3, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=2, ipv4_dst= "192.168.25.66")
                    self.add_flow(datapath, 100, match, actions)

                if dst_ip == "192.168.25.55" and in_port == 1:
                    actions.append(parser.OFPActionOutput(2, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=1, ipv4_dst= "192.168.25.55")
                    self.add_flow(datapath, 1, match, actions)

                if dst_ip == "192.168.25.66" and in_port == 3:
                    actions.append(parser.OFPActionSetField(icmpv4_type= 8))
                    actions.append(parser.OFPActionSetField(icmpv4_code= 0))
                    actions.append(parser.OFPActionOutput(1, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=3, ipv4_dst= "192.168.25.66")
                    self.add_flow(datapath, 1, match, actions)
            else:
                print self.ds_ip
                if dst_ip == self.ds_ip and in_port == 3:
                    print ("1-ks")
                    actions.append(parser.OFPActionOutput(1, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=3, ipv4_dst= self.ds_ip)
                    self.add_flow(datapath, 100, match, actions)
                if dst_ip == "192.168.23.10" and in_port == 3: 
                    actions.append(parser.OFPActionOutput(2, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=3, ipv4_dst= "192.168.23.10")
                    self.add_flow(datapath, 100, match, actions)

                if dst_ip == "192.168.23.10" and in_port == 1:
                    actions.append(parser.OFPActionSetField(eth_src= self.mac_adds["DST"]))
                    actions.append(parser.OFPActionSetField(ipv4_src= "192.168.25.66"))
                    actions.append(parser.OFPActionSetField(icmpv4_type= 8))
                    actions.append(parser.OFPActionSetField(icmpv4_code= 0))
                    actions.append(parser.OFPActionOutput(2, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=1, ipv4_dst= "192.168.23.10")
                    self.add_flow(datapath, 100, match, actions)

                if dst_ip == self.ds_ip and in_port == 2:
                    actions.append(parser.OFPActionSetField(eth_dst= self.mac_adds["DS"]))
                    actions.append(parser.OFPActionOutput(1, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=2, ipv4_dst= self.ds_ip)
                    self.add_flow(datapath, 100, match, actions)

                if dst_ip == "192.168.25.66" and in_port == 2:
                    actions.append(parser.OFPActionSetField(eth_dst= self.mac_adds["DST"]))
                    actions.append(parser.OFPActionSetField(ipv4_dst= "192.168.25.66"))
                    actions.append(parser.OFPActionSetField(eth_src= self.mac_adds["SRC"]))
                    actions.append(parser.OFPActionSetField(ipv4_src= "192.168.25.55"))
                    actions.append(parser.OFPActionOutput(3, ofproto.OFPCML_NO_BUFFER))
                    match = parser.OFPMatch(in_port=2, ipv4_dst= "192.168.25.66")
                    self.add_flow(datapath, 1, match, actions)

    def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp, dst):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        src_p = "0c:c4:7a:41:fc:b1"
	if dst == "192.168.23.10":
            src_p = self.mac_adds["K8"]
        elif dst =="192.168.25.55":
            src_p = self.mac_adds["SRC"]
        elif dst == "192.168.25.66":
            src_p = self.mac_adds["DST"]

        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=src_p))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=src_p,
                                 src_ip=pkt_arp.dst_ip,
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        self._send_packet(datapath, port, pkt)

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
