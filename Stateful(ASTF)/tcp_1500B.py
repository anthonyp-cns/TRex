from trex.astf.api import *

class Prof1():
    def __init__(self):
        pass

    def get_profile(self, **kwargs):
        # IP generator for clients and servers
        ip_gen_c = ASTFIPGenDist(ip_range=["198.18.102.1", "198.18.102.254"], distribution="seq")
        ip_gen_s = ASTFIPGenDist(ip_range=["203.0.113.1", "203.0.113.254"], distribution="seq")
        ip_gen = ASTFIPGen(dist_client=ip_gen_c, dist_server=ip_gen_s)

        # TCP client program
        prog_c = ASTFProgram()
        prog_c.connect()
        prog_c.send(b"x" * 1500)
        prog_c.recv(1500)
        prog_c.close()

        # TCP server program
        prog_s = ASTFProgram()
        prog_s.accept()
        prog_s.recv(1500)
        prog_s.send(b"x" * 1500)
        prog_s.close()

        # Create a TCP template with Packet Group ID
        temp_tcp = ASTFTemplate(
            client_template=prog_c,
            server_template=prog_s,
            pg_id=3
        )

        # Create a profile
        profile = ASTFProfile(default_ip_gen=ip_gen, templates=temp_tcp)
        return profile

def register():
    return Prof1()
