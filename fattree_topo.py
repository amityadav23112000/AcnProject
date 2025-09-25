from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController

class MyTopo(Topo):
    "FatTree topology example."
    def __init__(self):
        "Create custom FatTree topology."
        # Initialize topology
        Topo.__init__(self)

        # Add hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')
        h5 = self.addHost('h5', ip='10.0.0.5/24')
        h6 = self.addHost('h6', ip='10.0.0.6/24')
        h7 = self.addHost('h7', ip='10.0.0.7/24')
        h8 = self.addHost('h8', ip='10.0.0.8/24')

        # Add edge switches with OpenFlow 1.3
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', protocols='OpenFlow13')
        
        # Add aggregate switches with OpenFlow 1.3
        s5 = self.addSwitch('s5', protocols='OpenFlow13')
        s6 = self.addSwitch('s6', protocols='OpenFlow13')
        s7 = self.addSwitch('s7', protocols='OpenFlow13')
        s8 = self.addSwitch('s8', protocols='OpenFlow13')
        
        # Add core switches with OpenFlow 1.3
        s9 = self.addSwitch('s9', protocols='OpenFlow13')
        s10 = self.addSwitch('s10', protocols='OpenFlow13')

        # Add links between hosts and edge switches
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(h5, s3)
        self.addLink(h6, s3)
        self.addLink(h7, s4)
        self.addLink(h8, s4)
        
        # Add links between edge switches and aggregate switches
        self.addLink(s1, s5)
        self.addLink(s1, s6)
        self.addLink(s2, s5)
        self.addLink(s2, s6)
        self.addLink(s3, s7)
        self.addLink(s3, s8)
        self.addLink(s4, s7)
        self.addLink(s4, s8)

        # Add links between aggregate switches and core switches
        self.addLink(s5, s9)
        self.addLink(s6, s9)
        self.addLink(s7, s10)
        self.addLink(s8, s10)

topos = {'mytopo': (lambda: MyTopo())}