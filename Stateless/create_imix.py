from trex_stl_lib.api import *
from scapy.all import Ether, IP, IPv6, UDP, Raw, Dot1Q
from trex_stl_lib.trex_stl_streams import STLFlowVar, STLScVmRaw, STLScVmWrFlowVar, STLScVmFixHwCs


class IMIXStream:
    def __init__(self, src_ip_range, dst_ip_range, vlan_id=None, ipv6=False):
        self.src_ip_range = src_ip_range
        self.dst_ip_range = dst_ip_range
        self.vlan_id = vlan_id
        self.use_ipv6 = ipv6

        # Define IMIX sizes and percentages
        self.imix = [
            (64, 60),
            (512, 30),
            (1500, 10)
        ]

    def _build_pkt(self, pkt_len):
        if self.use_ipv6:
            ip_hdr = IPv6(src=self.src_ip_range[0], dst=self.dst_ip_range[0])
        else:
            ip_hdr = IP(src=self.src_ip_range[0], dst=self.dst_ip_range[0])

        l3_hdr_len = len(ip_hdr / UDP(sport=1234, dport=1234))
        eth_hdr_len = 18 if self.vlan_id is not None else 14
        pad_len = max(pkt_len - (eth_hdr_len + l3_hdr_len), 0)
        payload = Raw(load='A' * pad_len)

        eth = Ether()
        if self.vlan_id is not None:
            eth /= Dot1Q(vlan=self.vlan_id)

        pkt = eth / ip_hdr / UDP(sport=1234, dport=1234) / payload
        return STLPktBuilder(pkt=pkt, vm=self._build_vm())

    def _build_vm(self):
        if self.use_ipv6:
            return self._build_vm_ipv6()
        else:
            return self._build_vm_ipv4()

    def _build_vm_ipv4(self):
        return STLScVmRaw(variables=[
            STLFlowVar("src", min_value=self._ip_to_int(self.src_ip_range[0]),
                             max_value=self._ip_to_int(self.src_ip_range[1]), size=4, op="inc"),
            STLFlowVar("dst", min_value=self._ip_to_int(self.dst_ip_range[0]),
                             max_value=self._ip_to_int(self.dst_ip_range[1]), size=4, op="inc"),
            STLScVmWrFlowVar("src", pkt_offset="IP.src"),
            STLScVmWrFlowVar("dst", pkt_offset="IP.dst"),
            STLScVmFixHwCs()
        ])

    def _build_vm_ipv6(self):
        # Expecting prefixes like '2001:db8::' and only varying the last 2 bytes
        src_prefix = self._expand_ipv6_prefix(self.src_ip_range[0])
        dst_prefix = self._expand_ipv6_prefix(self.dst_ip_range[0])

        return STLScVmRaw(variables=[
            STLFlowVar("src", min_value=1, max_value=254, size=2, op="inc"),
            STLFlowVar("dst", min_value=1, max_value=254, size=2, op="inc"),
            STLScVmWrFlowVar("src", pkt_offset="IPv6.src", add_val=self._ipv6_prefix_to_bytes(src_prefix, offset=True)),
            STLScVmWrFlowVar("dst", pkt_offset="IPv6.dst", add_val=self._ipv6_prefix_to_bytes(dst_prefix, offset=True)),
            STLScVmFixHwCs()
        ])

    def _expand_ipv6_prefix(self, addr):
        return str(IPv6(addr).compressed).split("::")[0]

    def _ipv6_prefix_to_bytes(self, prefix, offset=False):
        from ipaddress import IPv6Address
        full_addr = IPv6Address(prefix + ("0" * (32 - len(prefix.replace(":", "")))))
        return int(full_addr) >> (16 if offset else 0)

    def _ip_to_int(self, ip):
        parts = list(map(int, ip.split('.')))
        return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]

    def get_streams(self):
        streams = []
        for size, percent in self.imix:
            streams.append(
                STLStream(
                    name=f"imix_{size}B",
                    packet=self._build_pkt(size),
                    mode=STLTXCont(percentage=percent)
                )
            )
        return streams
