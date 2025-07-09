import random
from trex_stl_lib.api import *
from scapy.all import Ether, IP, TCP, UDP, Dot1Q

class STLSv4:
    def __init__(self, src_range, dst_range, pkt_size, num_flows, pg_id, vlan_id=None, protocol="tcp"):
        self.pkt_size = pkt_size
        self.num_flows = num_flows
        self.pg_id = pg_id
        self.src_range = src_range
        self.dst_range = dst_range
        self.vlan_id = vlan_id
        self.protocol = protocol.lower()

    def build_base_pkt(self, src_ip, dst_ip, sport, dport):
        eth = Ether()
        if self.vlan_id is not None:
            eth /= Dot1Q(vlan=self.vlan_id)

        if self.protocol == "udp":
            l4 = UDP(sport=sport, dport=dport)
        else:
            l4 = TCP(sport=sport, dport=dport)

        ip_pkt = IP(src=src_ip, dst=dst_ip) / l4
        return eth / ip_pkt

    def create_stream(self, src_ip, dst_ip, src_port=1025, dst_port=8080):
        base_pkt = self.build_base_pkt(src_ip, dst_ip, src_port, dst_port)

        header_len = len(base_pkt)
        payload_len = max(0, self.pkt_size - header_len)
        payload = 'x' * payload_len

        pkt_builder = STLPktBuilder(pkt=base_pkt / payload)

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont()
        )

    def create_latency_stream(self, src_ip, dst_ip, pg_id=None):
        base_pkt = self.build_base_pkt(src_ip, dst_ip, 1120, 8888)

        payload = 'x' * 24
        pkt_builder = STLPktBuilder(pkt=base_pkt / payload)

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )

    def get_streams(self, direction=0, **kwargs):
        streams = []
        for i in range(1, self.num_flows + 1):
            sport = 1025
            dport = 8080
            src = f"{self.src_range}{i}"
            dst = f"{self.dst_range}{i}"
            if i > 254:
                sport = random.randint(1025, 65534)
                dport = random.randint(1025, 65534)
                src = f"{self.src_range}{random.randint(1, 254)}"
                dst = f"{self.dst_range}{random.randint(1, 254)}"
            streams.append(self.create_stream(src, dst, sport, dport))

        # Latency stream using flow #2
        src = f"{self.src_range}1"
        dst = f"{self.dst_range}1"
        streams.append(self.create_latency_stream(src, dst, self.pg_id))

        return streams

def register():
    return STLSv4()
