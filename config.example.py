
v4_1101_src_range = "198.18.104."
v4_1101_dst_range = "203.0.113."
v4_1201_src_range = "100.65.0."
v4_1201_dst_range = "203.0.113."

v6_1101_src_range = "3fff:ba7a:1101::1"
v6_1101_dst_range = "3fff:aa7a:1401::1"
v6_1201_src_range = "3fff:ba7a:1201::1"
v6_1201_dst_range = "3fff:aa7a:1401::1"

devices = [
    ['Netelastic01.boca.acore.network', '192.168.1.58', 'root', '12345678'],
    ['Netelastic02.boca.acore.network', '192.168.1.61', 'root', '12345678']
]

v4_tests =[
    {"name": "1101_tcp_64b","src_range": v4_1101_src_range,"dst_range": v4_1101_dst_range,"packet_size": 64, "num_flows":240,
     "pg_id":10, "vlan_id": 1101, 'protocol': "tcp"},
    {"name": "1101_tcp_512b", "src_range": v4_1101_src_range, "dst_range": v4_1101_dst_range, "packet_size": 512, "num_flows": 240,
     "pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
    {"name": "1101_tcp_1500b", "src_range": v4_1101_src_range, "dst_range": v4_1101_dst_range, "packet_size": 1500, "num_flows": 240,
     "pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
    {"name": "1101_udp_64b", "src_range": v4_1101_src_range, "dst_range": v4_1101_dst_range, "packet_size": 64, "num_flows": 240,
     "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    {"name": "1101_udp_512b", "src_range": v4_1101_src_range, "dst_range": v4_1101_dst_range, "packet_size": 512, "num_flows": 240,
     "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    {"name": "1101_udp_1500b", "src_range": v4_1101_src_range, "dst_range": v4_1101_dst_range, "packet_size": 1500, "num_flows": 240,
     "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    # {"name": "1201_tcp_64b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 64, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_tcp_512b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_tcp_1500b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_udp_64b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 64, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
    # {"name": "1201_udp_512b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
    # {"name": "1201_udp_1500b", "src_range": v4_1201_src_range, "dst_range": v4_1201_dst_range, "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"}
]
v4_imix_tests = [
    {"name": "1101_v4_imix","src_range": "198.18.104.0/24","dst_range": f"{v4_1101_dst_range}0/24", "num_flows":240,
     "pg_id":10, "vlan_id": 1101, 'protocol': "tcp"},
   # {"name": "1201_v4_imix", "src_range": "100.65.0.0/24", "dst_range": f"{v4_1101_dst_range}0/24", "num_flows": 240,
   #  "pg_id": 10, "vlan_id": 1301, 'protocol': "udp"}
]

v6_tests = [
{"name": "1101_udp_64b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 64,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
{"name": "1101_udp_512b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 512,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
{"name": "1101_udp_1500b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 1500,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
{"name": "1101_tcp_64b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 64,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
{"name": "1101_tcp_512b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 512,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
{"name": "1101_tcp_1500b_v6", "src_range": v6_1101_src_range, "dst_range": v6_1101_dst_range, "packet_size": 1500,
 "num_flows": 240,"pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
# {"name": "1201_udp_64b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 64,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
# {"name": "1201_udp_512b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 512,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
# {"name": "1201_udp_1500b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 1500,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
# {"name": "1201_tcp_64b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 64,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
# {"name": "1201_tcp_512b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 512,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
# {"name": "1201_tcp_1500b_v6", "src_range": v6_1201_src_range, "dst_range": v6_1201_dst_range, "packet_size": 1500,
#  "num_flows": 240,"pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"}
]

v6_imix_tests = []