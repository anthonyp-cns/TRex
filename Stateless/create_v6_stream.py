from trex_stl_lib.api import *
from scapy.all import Ether, IPv6, TCP, UDP, Dot1Q
import ipaddress


class STLSv6:
    def __init__(self, src_range, dst_range, pkt_size, num_flows, pg_id, vlan_id=None, protocol="tcp"):
        """
        :param src_range: Starting IPv6 address for source (e.g., "3fff:ba7a:1201::1")
        :param dst_range: Starting IPv6 address for destination (e.g., "3fff:aa7a:1201::1")
        :param pkt_size: Total packet size in bytes
        :param num_flows: Number of unique src/dst flows
        :param pg_id: Packet group ID for flow stats
        :param vlan_id: Optional VLAN tag
        :param protocol: "tcp" or "udp"
        """
        self.pkt_size = pkt_size
        self.num_flows = num_flows
        self.pg_id = pg_id
        self.src_base = ipaddress.IPv6Address(src_range)
        self.dst_base = ipaddress.IPv6Address(dst_range)
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

        ip_pkt = IPv6(src=str(src_ip), dst=str(dst_ip)) / l4
        return eth / ip_pkt

    def create_stream(self, src_ip, dst_ip):
        base_pkt = self.build_base_pkt(src_ip, dst_ip, sport=1025, dport=8080)
        payload_len = max(0, self.pkt_size - len(base_pkt))
        payload = b'x' * payload_len
        pkt_builder = STLPktBuilder(pkt=base_pkt / Raw(payload))

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont()
        )

    def create_latency_stream(self, src_ip, dst_ip, pg_id=None):
        base_pkt = self.build_base_pkt(src_ip, dst_ip, sport=1120, dport=8888)
        payload = b'x' * 24
        pkt_builder = STLPktBuilder(pkt=base_pkt / Raw(payload))

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )

    def get_streams(self, direction=0, **kwargs):
        streams = []

        for i in range(1, self.num_flows + 1):
            src = self.src_base + i
            dst = self.dst_base + i
            streams.append(self.create_stream(src, dst))

        # Add a latency stream using flow 2's addresses
        src = self.src_base + 2
        dst = self.dst_base + 2
        streams.append(self.create_latency_stream(src, dst, self.pg_id))

        return streams


def register():
    return STLSv6(
        src_range="3fff:ba7a:1201::1",
        dst_range="3fff:aa7a:1201::1",
        pkt_size=512,
        num_flows=240,
        pg_id=10,
        vlan_id=1201,
        protocol="tcp"
    )
