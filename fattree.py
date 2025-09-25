#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

def create_fattree_topology():
    net = Mininet(controller=Controller, link=TCLink)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding switches\n')
    core_switches = [net.addSwitch(f's{i}') for i in range(9, 11)]  # s9, s10
    agg_switches = [net.addSwitch(f's{i}') for i in range(5, 9)]    # s5, s6, s7, s8
    edge_switches = [net.addSwitch(f's{i}') for i in range(1, 5)]   # s1, s2, s3, s4

    info('*** Adding hosts\n')
    hosts = [net.addHost(f'h{i}') for i in range(1, 9)]             # h1, h2, h3, h4, h5, h6, h7, h8

    info('*** Creating links\n')
    # Links between hosts and edge switches
    for i, edge_switch in enumerate(edge_switches):
        net.addLink(edge_switch, hosts[2*i], bw=10)  # Connect h1-h2 to s1, h3-h4 to s2, etc.
        net.addLink(edge_switch, hosts[2*i+1], bw=10)

    # Links between edge switches and aggregation switches
    for edge_switch in edge_switches:
        for agg_switch in agg_switches:
            net.addLink(edge_switch, agg_switch, bw=10)

    # Links between aggregation switches and core switches
    for agg_switch in agg_switches:
        for core_switch in core_switches:
            net.addLink(agg_switch, core_switch, bw=10)

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_fattree_topology()