from trex_stl_lib.api import *
from scapy.all import Ether, IP, UDP, Raw, Dot1Q
import ipaddress


class IMIXStream:
    def __init__(self, src_range, dst_range, vlan_id=None, pg_id=10):
        self.src_range = list(ipaddress.IPv4Network(src_range).hosts())
        self.dst_range = list(ipaddress.IPv4Network(dst_range).hosts())
        self.vlan_id = vlan_id
        self.pg_id = pg_id
        self.imix = [
            (64, 10),
            (512, 60),
            (1500, 30)
        ]
    def build_base_pkt(self, src_ip, dst_ip, sport, dport):
        eth = Ether()
        if self.vlan_id is not None:
            eth /= Dot1Q(vlan=self.vlan_id)
            l4 = TCP(sport=sport, dport=dport)
        ip_pkt = IP(src=src_ip, dst=dst_ip) / l4
        return eth / ip_pkt

    def _build_packet(self, src_ip, dst_ip, size):
        l3 = IP(src=str(src_ip), dst=str(dst_ip)) / UDP(sport=1234, dport=1234)
        payload_len = size - len(Ether() / l3)

        if self.vlan_id is not None:
            eth = Ether() / Dot1Q(vlan=self.vlan_id)
        else:
            eth = Ether()

        pkt = eth / l3 / Raw(b"A" * max(payload_len, 0))
        return STLPktBuilder(pkt=pkt)


    def create_latency_stream(self, src_ip, dst_ip, pg_id=None):
        base_pkt = self.build_base_pkt(src_ip, dst_ip, 1120, 8888)

        payload = 'x' * 24
        pkt_builder = STLPktBuilder(pkt=base_pkt / payload)

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )


    def get_streams(self):
        streams = []
        src_cycle = len(self.src_range)
        dst_cycle = len(self.dst_range)
        stream_id = 0

        for pkt_size, percent in self.imix:
            for i in range(percent):  # Use percent as # of streams to distribute
                src_ip = self.src_range[i % src_cycle]
                dst_ip = self.dst_range[i % dst_cycle]
                pkt_builder = self._build_packet(src_ip, dst_ip, pkt_size)
                stream = STLStream(
                    name=f"imix_{pkt_size}_{i}",
                    packet=pkt_builder,
                    mode=STLTXCont(percentage=1)  # Each stream is 1%, total equals percent
                )
                streams.append(stream)
                stream_id += 1
        src_ip = self.src_range[2]
        dst_ip = self.dst_range[2]
        streams.append(self.create_latency_stream(src_ip, dst_ip, self.pg_id))

        return streams
