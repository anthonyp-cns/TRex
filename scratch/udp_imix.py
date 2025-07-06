from trex_stl_lib.api import *

class UDPIMIX:
    def __init__(self):
        self.udp_ports = (1025, 8080)
        self.ip_base_src = "198.18.104."
        self.ip_base_dst = "203.0.113."


    def create_stream(self, pkt_size, pg_id):
        base_pkt = Ether() / IP(src=self.ip_base_src + "1", dst=self.ip_base_dst + "1") / \
                   UDP(sport=self.udp_ports[0], dport=self.udp_ports[1])

        header_len = len(base_pkt)
        payload_len = max(0, pkt_size - header_len)
        payload = 'x' * payload_len

        return STLStream(
            packet=STLPktBuilder(pkt=base_pkt / payload),
            mode=STLTXCont(percentage=100),  # Will adjust weights below
            flow_stats=STLFlowStats(pg_id=pg_id)
        )


    def get_streams(self, direction=0, **kwargs):
        return [
            self.create_stream(64, pg_id=1).set_rate(percentage=10),     # 64B = 60%
            self.create_stream(512, pg_id=2).set_rate(percentage=30),    # 512B = 30%
            self.create_stream(1500, pg_id=3).set_rate(percentage=60)    # 1500B = 10%
        ]


def register():
    return UDPIMIX()
