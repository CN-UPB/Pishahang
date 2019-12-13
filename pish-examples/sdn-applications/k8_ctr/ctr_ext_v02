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
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.ofproto import ofproto_v1_3 as ofp
from ryu.ofproto import ofproto_v1_3_parser as parser


# datapath id of switches
PISH_EXT_SWITCH = 198558776200496
PISH_INT_SWITCH = 227070286987073

# the MAC/IP of the k8 node
HOST_MAC = "b4:96:91:52:8d:30"
HOST_IP = "192.168.230.201"

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
            forwarding_graph = socket.recv_json(zmq.DONTWAIT) #["forwarding_graph"]
            q.put(forwarding_graph)
            print("Recived a new forwarding graph! = {0}".format(forwarding_graph))
            fg = forwarding_graph
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
        self.vlan_src_ip_mac = []
        self.vlan_dst_ip_mac = []
        #self.vlan_dst_ip_mac[10] = {"IP":"10.112.0.16", "MAC":"7a:b1:ce:3d:1a:0c"}
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
        vlan_exist = False

        if not q.empty():
            # new forwarding graph(s) received; convert to flow rules
            forwarding_graph = q.get(block=False)
            #self.forwarding_graphs.append(forwarding_graph)
            #self.logger.info("Recived a new forwarding graph++! = {0}".format(forwarding_graph))
            #print forwarding_graph["10"]
            #print (forwarding_graph)

            for i in range(len(self.vlan_dst_ip_mac)):
                if forwarding_graph["VLAN"] == self.vlan_dst_ip_mac[i]['VLAN']:
                    vlan_exist = True
                    self.logger.error("VLAN id {0} already exists!".format(forwarding_graph["VLAN"]))
                    break

            if vlan_exist == False:
                self.vlan_dst_ip_mac.append(forwarding_graph)
                self.logger.info("MAC_IP_VLAN table has been updated! = {0}".format(self.vlan_dst_ip_mac))

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)
        vlan_pkt = pkt.get_protocol(vlan.vlan)

        dst = eth_pkt.dst
        src = eth_pkt.src
        in_port = msg.match['in_port']
        vlan_id = None

        if vlan_pkt:
            vlan_id = vlan_pkt.vid
            self.logger.info("Recived a new packet with VLAN id {0}".format(vlan_id))
            if arp_pkt:
                self._handle_arp(datapath, in_port, vlan_id, eth_pkt, vlan_pkt, arp_pkt)
                return

        if ip_pkt:
            dst_ip = ip_pkt.dst
            src_ip = ip_pkt.src

        if ip_pkt:
            if dpid == PISH_EXT_SWITCH:
                if in_port == 1 and vlan_id != None:
                    try:
                        mac, ip = self.mac_ip(vlan_id)
                        self.logger.info("Retrieved MAC:{0} and IP:{1}".format(mac, ip))
                        actions.append(parser.OFPActionSetField(eth_dst= mac))
                        actions.append(parser.OFPActionSetField(ipv4_dst= ip))
                        actions.append(parser.OFPActionPopVlan())
                        actions.append(parser.OFPActionOutput(2, ofproto.OFPCML_NO_BUFFER))
                        match = parser.OFPMatch(eth_type=0x0800, in_port=1, vlan_vid= 4106)
                        self.add_flow(datapath, 100, match, actions)
                    except:
                        self.logger.info("Error in mac and ip retrieval")

                elif in_port == 2:
                    re_vlan = self._vlan_id_retrieval(dst)
                    if re_vlan != None:
                        actions.append(parser.OFPActionSetField(eth_src= HOST_MAC))
                        actions.append(parser.OFPActionSetField(ipv4_src= HOST_IP))
                        actions.append(parser.OFPActionPushVlan(ether.ETH_TYPE_8021Q))
                        actions.append(parser.OFPActionSetField(vlan_vid=self.vid_present(re_vlan)))
                        actions.append(parser.OFPActionOutput(1, ofproto.OFPCML_NO_BUFFER))
                        match = parser.OFPMatch(eth_type=0x0800, in_port=2)
                        self.add_flow(datapath, 100, match, actions)

    def vid_present(self, vid):
        return vid | ofp.OFPVID_PRESENT

    def mac_ip(self, vlan_id):
        for i in range(len(self.vlan_dst_ip_mac)):
            if str(vlan_id) == str(self.vlan_dst_ip_mac[i]['VLAN']):
                print (self.vlan_dst_ip_mac[i]['VLAN'])
                print (vlan_id)
                mac = self.vlan_dst_ip_mac[i]['MAC']
                ip = self.vlan_dst_ip_mac[i]['IP']
                return mac, ip
        self.logger.error("VLAN not found!")


    def _handle_arp(self, datapath, in_port, vlan_id, eth_pkt, vlan_pkt, arp_pkt):

        # check if it is an arp request
        if arp_pkt.opcode != arp.ARP_REQUEST: 
            return

        # variable population
        arp_dst_ip = arp_pkt.dst_ip; arp_src_mac = arp_pkt.src_mac
        arp_src_ip = arp_pkt.src_ip; vlan_exist = False
        print (in_port, vlan_id, arp_src_ip, arp_dst_ip, arp_src_mac)
        
        # save SRC IP and MAC for later use
        for i in range(len(self.vlan_src_ip_mac)):
            if vlan_id == self.vlan_src_ip_mac[i]['vlan']:
                vlan_exist = True
                break
        if vlan_exist == False:   
            self.vlan_src_ip_mac.append({"vlan": vlan_id, "MAC":arp_src_mac, "IP":arp_src_ip})           
        self.logger.info("SRC_MAC_IP_VLAN table has been updated! = {0}".format(self.vlan_src_ip_mac))  

        # create ARP Response
        if arp_dst_ip == HOST_IP:
            # create ethernet
            pkt = packet.Packet()
            pkt.add_protocol(ethernet.ethernet(ethertype=ether.ETH_TYPE_8021Q,
                                               dst = arp_src_mac,
                                               src = HOST_MAC))
            # add vlan tag
            pkt.add_protocol(vlan.vlan(vid=vlan_id, ethertype=ether.ETH_TYPE_ARP))

            #add arp header
            pkt.add_protocol(arp.arp(proto=0x0800,opcode=arp.ARP_REPLY,
                                     src_ip= arp_dst_ip,
                                     dst_ip= arp_src_ip,
                                     src_mac = HOST_MAC,
                                     dst_mac = arp_src_mac))

            self._send_packet(datapath, in_port, pkt)

        else:
            return

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

    def _vlan_id_retrieval(self, dst_mac):
        for i in range(len(self.vlan_src_ip_mac)):
            if self.vlan_src_ip_mac[i]["MAC"] == dst_mac:
                re_vlan = self.vlan_src_ip_mac[i]["vlan"]
                return re_vlan
