from trex_stl_lib.api import *

class TCPIMIX:
    def __init__(self):
        self.tcp_ports = (12345, 80)
        self.ip_base_src = "198.18.105."
        self.ip_base_dst = "203.0.114."

    def create_stream(self, pkt_size, pg_id):
        base_pkt = Ether() / IP(src=self.ip_base_src + "1", dst=self.ip_base_dst + "1") / \
                   TCP(sport=self.tcp_ports[0], dport=self.tcp_ports[1], flags="PA")

        header_len = len(base_pkt)
        payload_len = max(0, pkt_size - header_len)
        payload = 'x' * payload_len

        return STLStream(
            packet=STLPktBuilder(pkt=base_pkt / payload),
            mode=STLTXCont(percentage=100),
            flow_stats=STLFlowStats(pg_id=pg_id)
        )

    def get_streams(self, direction=0, **kwargs):
        return [
            self.create_stream(64, pg_id=11).set_rate(percentage=50),
            self.create_stream(512, pg_id=12).set_rate(percentage=30),
            self.create_stream(1500, pg_id=13).set_rate(percentage=20)
        ]

def register():
    return TCPIMIX()
