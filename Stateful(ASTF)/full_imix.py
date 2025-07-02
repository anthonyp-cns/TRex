
from trex.astf.api import *

class FullResidentialMix():
    def __init__(self):
        pass

    def get_profile(self, **kwargs):
        ip_gen_c = ASTFIPGenDist(ip_range=["10.0.0.1", "10.0.0.254"], distribution="seq")
        ip_gen_s = ASTFIPGenDist(ip_range=["20.0.0.1", "20.0.0.254"], distribution="seq")
        ip_gen = ASTFIPGen(dist_client=ip_gen_c, dist_server=ip_gen_s)

        templates = []

        # TCP 64B
        prog_c_64 = ASTFProgram()
        prog_c_64.connect()
        prog_c_64.send(b"x" * 10)
        prog_c_64.recv(10)
        prog_c_64.close()

        prog_s_64 = ASTFProgram()
        prog_s_64.accept()
        prog_s_64.recv(10)
        prog_s_64.send(b"x" * 10)
        prog_s_64.close()

        templates.append(ASTFTemplate(client_template=prog_c_64, server_template=prog_s_64, pg_id=1, cps=100))

        # TCP 512B
        prog_c_512 = ASTFProgram()
        prog_c_512.connect()
        prog_c_512.send(b"x" * 256)
        prog_c_512.recv(256)
        prog_c_512.close()

        prog_s_512 = ASTFProgram()
        prog_s_512.accept()
        prog_s_512.recv(256)
        prog_s_512.send(b"x" * 256)
        prog_s_512.close()

        templates.append(ASTFTemplate(client_template=prog_c_512, server_template=prog_s_512, pg_id=2, cps=60))

        # TCP 1500B
        prog_c_1500 = ASTFProgram()
        prog_c_1500.connect()
        prog_c_1500.send(b"x" * 750)
        prog_c_1500.recv(750)
        prog_c_1500.close()

        prog_s_1500 = ASTFProgram()
        prog_s_1500.accept()
        prog_s_1500.recv(750)
        prog_s_1500.send(b"x" * 750)
        prog_s_1500.close()

        templates.append(ASTFTemplate(client_template=prog_c_1500, server_template=prog_s_1500, pg_id=3, cps=20))

        # UDP DNS
        prog_dns_c = ASTFProgram()
        prog_dns_c.send(b"x" * 32)
        prog_dns_c.recv(64)

        prog_dns_s = ASTFProgram()
        prog_dns_s.recv(32)
        prog_dns_s.send(b"x" * 64)

        templates.append(ASTFTemplate(client_template=prog_dns_c, server_template=prog_dns_s, pg_id=4, cps=50))

        # UDP VoIP
        prog_voip_c = ASTFProgram()
        prog_voip_c.send(b"x" * 160)
        prog_voip_c.recv(160)

        prog_voip_s = ASTFProgram()
        prog_voip_s.recv(160)
        prog_voip_s.send(b"x" * 160)

        templates.append(ASTFTemplate(client_template=prog_voip_c, server_template=prog_voip_s, pg_id=5, cps=30))

        profile = ASTFProfile(default_ip_gen=ip_gen, templates=templates)
        return profile

def register():
    return FullResidentialMix()
