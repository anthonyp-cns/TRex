from trex.astf.api import *

class Prof1():
    def __init__(self):
        pass

    def get_profile(self, **kwargs):
        # IP generator for clients and servers
        ip_gen_c = ASTFIPGenDist(ip_range=["16.0.0.1", "16.0.0.255"], distribution="seq")
        ip_gen_s = ASTFIPGenDist(ip_range=["48.0.0.1", "48.0.0.255"], distribution="seq")
        ip_gen = ASTFIPGen(dist_client=ip_gen_c, dist_server=ip_gen_s)

        # Create a client and server program
        prog_c = ASTFProgram()
        prog_c.send(b"x" * 1454)  # 18-byte payload
        prog_c.recv(1)

        prog_s = ASTFProgram()
        prog_s.recv(1)
        prog_s.send(b"x" * 1454)

        # Create a template for the UDP traffic with Packet Group ID
        temp_udp = ASTFTemplate(
            client_template=prog_c,
            server_template=prog_s,
           _id=7  # Example Packet Group ID
        )

        # Create a profile
        profile = ASTFProfile(default_ip_gen=ip_gen, templates=temp_udp)
        return profile

def register():
    return Prof1()
