from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib import mac
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

class FatTreeController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FatTreeController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.arp_table = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Avoid broadcast from LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn the mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.handle_arp(datapath, pkt, in_port)
            return

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            self.handle_ip(datapath, pkt, in_port)

        # If destination mac address is known, route the packet
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

    def handle_arp(self, datapath, pkt, in_port):
        arp_pkt = pkt.get_protocol(arp.arp)
        src_ip = arp_pkt.src_ip
        dst_ip = arp_pkt.dst_ip
        src_mac = arp_pkt.src_mac

        self.arp_table[src_ip] = src_mac

        if dst_ip in self.arp_table:
            dst_mac = self.arp_table[dst_ip]
            self.send_arp_reply(datapath, dst_mac, src_mac, dst_ip, src_ip, in_port)
        else:
            self.flood_packet(datapath, pkt, in_port)

    def handle_ip(self, datapath, pkt, in_port):
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        src_ip = ipv4_pkt.src
        dst_ip = ipv4_pkt.dst

        if dst_ip in self.arp_table:
            dst_mac = self.arp_table[dst_ip]
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=dst_ip)
            actions = [parser.OFPActionOutput(self.mac_to_port[datapath.id][dst_mac])]
            self.add_flow(datapath, 1, match, actions)

    def send_arp_reply(self, datapath, dst_mac, src_mac, dst_ip, src_ip, in_port):
        e = ethernet.ethernet(dst=src_mac, src=dst_mac, ethertype=ether_types.ETH_TYPE_ARP)
        a = arp.arp(opcode=arp.ARP_REPLY, src_mac=dst_mac, src_ip=dst_ip,
                    dst_mac=src_mac, dst_ip=src_ip)
        pkt = packet.Packet()
        pkt.add_protocol(e)
        pkt.add_protocol(a)
        self.send_packet(datapath, pkt, in_port)

    def flood_packet(self, datapath, pkt, in_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=pkt.data)
        datapath.send_msg(out)

    def send_packet(self, datapath, pkt, port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER, actions=actions,
                                  data=data)
        datapath.send_msg(out)