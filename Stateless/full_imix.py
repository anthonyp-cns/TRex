from trex_stl_lib.api import *

class ComboIMIX:
    def __init__(self):
        self.ip_base_src = "198.18.106."
        self.ip_base_dst = "203.0.115."

    def build_udp(self, pkt_size, pg_id):
        pkt = Ether() / IP(src=self.ip_base_src + "1", dst=self.ip_base_dst + "1") / \
              UDP(sport=1234, dport=5678)
        payload_len = max(0, pkt_size - len(pkt))
        return STLStream(
            packet=STLPktBuilder(pkt=pkt / ('x' * payload_len)),
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )

    def build_tcp(self, pkt_size, pg_id):
        pkt = Ether() / IP(src=self.ip_base_src + "2", dst=self.ip_base_dst + "2") / \
              TCP(sport=1111, dport=80, flags="PA")
        payload_len = max(0, pkt_size - len(pkt))
        return STLStream(
            packet=STLPktBuilder(pkt=pkt / ('x' * payload_len)),
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )

    def get_streams(self, direction=0, **kwargs):
        return [
            self.build_udp(64, pg_id=21).set_rate(percentage=30),
            self.build_udp(512, pg_id=22).set_rate(percentage=15),
            self.build_tcp(64, pg_id=23).set_rate(percentage=25),
            self.build_tcp(512, pg_id=24).set_rate(percentage=20),
            self.build_tcp(1500, pg_id=25).set_rate(percentage=10)
        ]

def register():
    return ComboIMIX()
