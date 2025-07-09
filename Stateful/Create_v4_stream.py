from trex.astf.api import *


class MyProfile:
    def __init__(self):
        # Tunable parameters
        self.packet_size = 64  # Default packet size in bytes
        self.client_ip = '198.18.104.'
        self.server_ip = '203.0.113.'
        self.vlan_id = 1101  # Set to an integer to enable VLAN tagging

    def create_profile(self):
        # Client and server global information
        c_glob_info = ASTFGlobalInfo()
        s_glob_info = ASTFGlobalInfo()

        # IP generator
        ip_gen = ASTFIPGen(dist_client=ASTFIPGenDist(ip_range=[f"{self.client_ip}1", f"{self.client_ip}254"]),
                           dist_server=ASTFIPGenDist(ip_range=[f"{self.server_ip}1", f"{self.server_ip}254"]))

        # Create a buffer with the desired packet size
        client_payload = 'x' * (self.packet_size - 54)  # 54 bytes for Ethernet/IP/TCP headers
        server_payload = 'y' * (self.packet_size - 54)

        # TCP client program
        prog_c = ASTFProgram()
        prog_c.send(client_payload)
        prog_c.recv(len(server_payload))

        # TCP server program
        prog_s = ASTFProgram()
        prog_s.recv(len(client_payload))
        prog_s.send(server_payload)

        # Template for TCP traffic
        # The ip_gen object must be passed to the client template
        temp_tcp = ASTFTCPClientTemplate(ip_gen=ip_gen, program=prog_c, port=80)
        temp_s_tcp = ASTFTCPServerTemplate(program=prog_s)
        template = ASTFTemplate(client_template=temp_tcp, server_template=temp_s_tcp)

        # Create the profile
        profile = ASTFProfile(default_ip_gen=ip_gen,
                              templates=template,
                              default_c_glob_info=c_glob_info,
                              default_s_glob_info=s_glob_info)

        # Add VLAN tag if specified
        if self.vlan_id is not None:
            profile.set_vlan(self.vlan_id)

        return profile

    def get_profile(self, **kwargs):
        # Allow overriding parameters from the command line
        self.packet_size = kwargs.get('packet_size', self.packet_size)
        self.client_ip = kwargs.get('client_ip', self.client_ip)
        self.server_ip = kwargs.get('server_ip', self.server_ip)
        self.vlan_id = kwargs.get('vlan_id', self.vlan_id)

        return self.create_profile()


def register():
    return MyProfile()
