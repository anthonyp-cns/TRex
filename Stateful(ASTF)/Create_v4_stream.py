from trex.astf.api import *

class StatefulTCPClient:
    def __init__(self, src_range, dst_range, vlan_id=None):
        self.src_range = src_range
        self.dst_range = dst_range
        self.vlan_id = vlan_id

    def get_profile(self):
        http_get = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"

        client_prog = ASTFProgram()
        client_prog.send(http_get)
        client_prog.recv(512)

        server_prog = ASTFProgram()
        server_prog.recv(len(http_get))
        server_prog.send(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nHello")

        return ASTFProfile(
            cap_list=[ASTFCapInfo(l7_proto="http", c_prog=client_prog, s_prog=server_prog)],
            ip_gen=ASTFIPGen(
                dist_client=ASTFIPGenDist(ip_start=self.src_range + "1", ip_end=self.src_range + "254"),
                dist_server=ASTFIPGenDist(ip_start=self.dst_range + "1", ip_end=self.dst_range + "254"),
            ),
            vlan=self.vlan_id
        )

def register():
    return StatefulTCPClient("198.18.104.", "203.0.113.").get_profile()
