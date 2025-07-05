from trex_stl_lib.api import *
source_range = "198.18.104."
dst_range = ""
class STLS1:
    def __init__(self):
        self.pkt_size = 64  # Change to 512 or 1500 as needed
        self.num_flows = 250
        self.pg_id = 10


    def create_stream(self, src_ip, dst_ip):
        # Ethernet/IP/UDP base
        base_pkt = Ether() / IP(src=src_ip, dst=dst_ip) / UDP(sport=1025, dport=8080)

        # Calculate payload based on size (Ethernet frame is 64B including headers)
        header_len = len(base_pkt)
        payload_len = max(0, self.pkt_size - header_len)
        payload = 'x' * payload_len

        pkt_builder = STLPktBuilder(pkt=base_pkt / payload)

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont()
        )


    def create_latency_stream(self, src_ip, dst_ip, pg_id=None):
        # Ethernet/IP/UDP base
        base_pkt = Ether() / IP(src=src_ip, dst=dst_ip) / UDP(sport=1120, dport=8888)

        # Calculate payload based on size (Ethernet frame is 64B including headers)
        header_len = len(base_pkt)
        payload_len = max(0, self.pkt_size - header_len)
        payload = 'x' * payload_len

        pkt_builder = STLPktBuilder(pkt=base_pkt / payload)

        return STLStream(
            packet=pkt_builder,
            mode=STLTXCont(),
            flow_stats=STLFlowLatencyStats(pg_id=pg_id)
        )


    def get_streams(self, direction=0, **kwargs):
        streams = []
        for i in range(1, self.num_flows + 1):
            src = f"{source_range}{i}"
            dst = f"{dst_range}{i}"
            streams.append(self.create_stream(src, dst))

        # Create a separate Latency Stream
        src = f"{source_range}2"
        dst = f"{dst_range}2"
        pg_id = self.pg_id
        streams.append(self.create_latency_stream(src,dst,pg_id))
        return streams


def register():
    return STLS1()
