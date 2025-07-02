
from trex.astf.api import *

class UDPResidential():
    def __init__(self):
        pass

    def get_profile(self, **kwargs):
        ip_gen_c = ASTFIPGenDist(ip_range=["10.0.0.1", "10.0.0.254"], distribution="seq")
        ip_gen_s = ASTFIPGenDist(ip_range=["20.0.0.1", "20.0.0.254"], distribution="seq")
        ip_gen = ASTFIPGen(dist_client=ip_gen_c, dist_server=ip_gen_s)

        # DNS-like small packet
        prog_dns_c = ASTFProgram()
        prog_dns_c.send(b"x" * 32)
        prog_dns_c.recv(64)

        prog_dns_s = ASTFProgram()
        prog_dns_s.recv(32)
        prog_dns_s.send(b"x" * 64)

        temp_dns = ASTFTemplate(client_template=prog_dns_c, server_template=prog_dns_s, pg_id=1, cps=100)

        # VoIP-like medium packet
        prog_voip_c = ASTFProgram()
        prog_voip_c.send(b"x" * 160)
        prog_voip_c.recv(160)

        prog_voip_s = ASTFProgram()
        prog_voip_s.recv(160)
        prog_voip_s.send(b"x" * 160)

        temp_voip = ASTFTemplate(client_template=prog_voip_c, server_template=prog_voip_s, pg_id=2, cps=50)

        profile = ASTFProfile(default_ip_gen=ip_gen, templates=[temp_dns, temp_voip])
        return profile

def register():
    return UDPResidential()
