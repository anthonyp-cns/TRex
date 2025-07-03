import sys
import time
from pprint import pprint
sys.path.append('/scratch/trex-core/scripts/automation/trex_control_plane/interactive')
from trex.stl.api import STLClient
profile_path = "/scratch/trex-core/scripts/stateless_udp_64b.py"

TEST_DURATION = 90
TEST_MULT = "1gbps"
client = STLClient()
client.connect()
client.reset()
client.add_profile(profile_path)
client.clear_stats()
client.start(duration=TEST_DURATION, mult=TEST_MULT)
time.sleep(10)
pprint(client.get_stats([0,1]))
