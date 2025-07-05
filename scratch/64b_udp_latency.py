from trex.stl.api import *

class BidirectionalLatency:
    def create_stream(self, src_ip, dst_ip, pg_id):
        pkt = (
            Ether() /
            IP(src=src_ip, dst=dst_ip) /
            TCP(sport=1234, dport=1234) /
            Raw(b'\x00' * 60)  # Enough for latency tracking
        )

        return STLStream(
            packet=STLPktBuilder(pkt=pkt),
            mode=STLTXCont(pps=1000),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )

    def get_streams(self, **kwargs):
        return [
            self.create_stream("198.18.104.1", "203.0.113.1", pg_id=7),  # Port 0 ➝ 1
        ]

def register():
    return BidirectionalLatency()