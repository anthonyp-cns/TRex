import os
import time
import csv
import getpass
import threading
from datetime import datetime
import paramiko
import psutil
import sys

sys.path.append('/scratch/trex-core/scripts/automation/trex_control_plane/interactive')
from trex.stl.api import STLClient, STLProfile
from Stateless.create_v4_stream import STLSv4
from Stateless.create_v6_stream import STLSv6
from Stateless.create_imix import IMIXStream

#### SETUP ####
test_folder = 'Stateless' # folder containing all Trex Test profiles
devices = [
    ['Netelastic01.boca.acore.network', '192.168.1.58', 'root', '12345678'],
    ['Netelastic02.boca.acore.network', '192.168.1.61', 'root', '12345678']
]

v4_tests =[
    # {"name": "1101_tcp_64b","src_range": "198.18.104.","dst_range": "203.0.113.","packet_size": 64, "num_flows":240,
    #  "pg_id":10, "vlan_id": 1101, 'protocol': "tcp"},
    # {"name": "1101_tcp_512b", "src_range": "198.18.104.", "dst_range": "203.0.113.", "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
    # {"name": "1101_tcp_1500b", "src_range": "198.18.104.", "dst_range": "203.0.113.", "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1101, 'protocol': "tcp"},
    # {"name": "1101_udp_64b", "src_range": "198.18.104.", "dst_range": "203.0.113.", "packet_size": 64, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    # {"name": "1101_udp_512b", "src_range": "198.18.104.", "dst_range": "203.0.113.", "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    # {"name": "1101_udp_1500b", "src_range": "198.18.104.", "dst_range": "203.0.113.", "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1101, 'protocol': "udp"},
    # {"name": "1201_tcp_64b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 64, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_tcp_512b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_tcp_1500b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "tcp"},
    # {"name": "1201_udp_64b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 64, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
    # {"name": "1201_udp_512b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 512, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"},
    # {"name": "1201_udp_1500b", "src_range": "100.65.0.", "dst_range": "203.0.113.", "packet_size": 1500, "num_flows": 240,
    #  "pg_id": 10, "vlan_id": 1201, 'protocol': "udp"}
]
v4_imix_tests = [
    {"name": "1101_v4_imix","src_range": "198.18.104.0/24","dst_range": "203.0.113.0/24", "num_flows":240,
     "pg_id":10, "vlan_id": 1101, 'protocol': "tcp"},
    {"name": "1201_v4_imix", "src_range": "100.65.0.0/24", "dst_range": "203.0.113.0/24", "num_flows": 240,
     "pg_id": 10, "vlan_id": 1301, 'protocol': "udp"}
]
test_duration = 30 # Test duration in seconds
stats_start_delay = 0


# Function to collect system stats from a remote machine
def collect_remote_stats(device, duration, interval, output_file):
    name, hostname, username, password = device
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'cpu_percent', 'memory_percent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(duration):
            stdin, stdout, stderr = client.exec_command(
                "python3 -c \"import psutil; print(psutil.cpu_percent()), print(psutil.virtual_memory().percent)\""
            )
            output = stdout.read().decode().splitlines()
            if len(output) >= 2:
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': output[0],
                    'memory_percent': output[1]
                })
            time.sleep(interval)

    client.close()

# Function to collect TRex stats
def collect_trex_stats(client, duration, interval, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'tx_pps', 'rx_pps', 'tx_bps', 'rx_bps', 'latency_min', 'latency_avg', 'latency_max', 'out_of_order', 'packet_drop_rate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(duration):
            stats = client.get_stats()
            latency = stats.get("latency").get(10).get("latency")
            # Should return
            # {'jitter': 191, 'average': 370.0, 'total_max': 567, 'total_min': 47, 'last_max': 493, 'histogram': {100: 21, 200: 15, 300: 15, 40: 2, 400: 47, 500: 11, 80: 1, 90: 2}}

            global_stats = stats.get('global', {})
            # Should Return
            # {'active_flows': 0.0, 'active_sockets': 0, 'bw_per_core': 0.1750040501356125, 'cpu_util': 0.009603138081729412, 'cpu_util_raw': 0.0, 'open_flows': 0.0, 'platform_factor': 1.0, 'rx_bps': 133784.34375, 'rx_core_pps': 0.9797892570495605, 'rx_cpu_util': 1.508487734724895e-08, 'rx_drop_bps': 0.0, 'rx_pps': 245.92710876464844, 'socket_util': 0.0, 'tx_expected_bps': 0.0, 'tx_expected_cps': 0.0, 'tx_expected_pps': 0.0, 'tx_pps': 245.92710876464844, 'tx_bps': 134447.046875, 'tx_cps': 0.0, 'total_servers': 0, 'total_clients': 0, 'total_alloc_error': 0, 'queue_full': 0}

            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'tx_pps': global_stats.get('tx_pps', 0),
                'rx_pps': global_stats.get('rx_pps', 0),
                'tx_bps': global_stats.get('tx_bps', 0),
                'rx_bps': global_stats.get('rx_bps', 0),
                'latency_avg': latency.get('average', 0),
                'latency_min': latency.get('total_min', 0),
                'latency_max': latency.get('total_max', 0),
                'out_of_order': latency.get('out_of_order', 0),
                'packet_drop_rate': global_stats.get('rx_drop_bps', 0)
            })
            time.sleep(interval)

def summarize_stats_by_subfolder(stats_dir):
    # Go through each subfolder
    for subfolder in next(os.walk(stats_dir))[1]:  # immediate subdirectories only
        subfolder_path = os.path.join(stats_dir, subfolder)
        summary_data = []
        all_keys = set()

        # Iterate over all CSV files in this subfolder
        for file in os.listdir(subfolder_path):
            if file.endswith('.csv') and not file.endswith('_summary.csv'):
                path = os.path.join(subfolder_path, file)
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    metrics = {}
                    for row in reader:
                        for key in row:
                            if key != 'timestamp':
                                try:
                                    metrics.setdefault(key, []).append(float(row[key]))
                                    all_keys.add(key)
                                except ValueError:
                                    continue  # Skip non-numeric values

                    if metrics:
                        summary = {'file': file}
                        for key, values in metrics.items():
                            summary[f'min_{key}'] = min(values)
                            summary[f'max_{key}'] = max(values)
                        summary_data.append(summary)

        # If we collected data, write a summary file in the same subfolder
        if summary_data:
            summary_file_path = os.path.join(subfolder_path, f"{subfolder}_summary.csv")
            all_fieldnames = ['file']
            for key in sorted(all_keys):
                all_fieldnames.extend([f'min_{key}', f'max_{key}'])

            with open(summary_file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_fieldnames)
                writer.writeheader()
                for row in summary_data:
                    complete_row = {field: row.get(field, '') for field in all_fieldnames}
                    writer.writerow(complete_row)


# Main script
def main():
    tower_name = input("Enter Tower name: ")
    ip = input("Enter IP address of first computer: ")
    username = input("Enter username(DEFAULT: root): ") or "root"
    password = getpass.getpass("Enter password (DEFAULT: 12345678): ") or "12345678"

    devices.append([f'libreqos.{tower_name}.acore.network', ip, username, password])


    stats_base_dir = os.path.join('stats', tower_name)
    os.makedirs(stats_base_dir, exist_ok=True)


    stats_duration = test_duration - stats_start_delay
    interval = 1
# {"name": "udp_64b","src_range": "198.18.104.","dst_range": "203.0.113.","packet_size": 64, "num_flows":240, "pg_id":10, "vlan_id": 1101, 'protocol': "tcp"}
    for test in v4_tests:
            profile=STLSv4(src_range=test.get('src_range'), dst_range=test.get('dst_range'), pkt_size=test.get('packet_size'), num_flows=test.get("num_flows"),
                          pg_id=test.get("pg_id"), vlan_id=test.get("vlan_id"), protocol=test.get("protocol"))
            client = STLClient()
            client.connect()
            client.reset()
            print("Setting Service Mode")
            client.set_service_mode(ports=[0], enabled=True, filtered=False, mask=None)
            if test.get("vlan_id") == 1101:
                client.set_l3_mode(0, "198.18.101.5","198.18.101.1", vlan=1101)
                client.arp(ports=[0], retries=3, verbose=True, vlan=1101)
            elif test.get("vlan_id") ==1201:
                client.set_l3_mode(0, "100.66.0.5","100.66.0.1", vlan=1201)
                client.arp(ports=[0], retries=3, verbose=True, vlan=1201)
            client.set_service_mode(ports=[0], enabled=False, filtered=False, mask=None)

            client.add_streams(profile.get_streams(), ports=[0])
            client.start(ports=[0], duration=test_duration, force=True, mult="98%")

            print(f"Running test {test.get('name')} for {test_duration} seconds...")
            time.sleep(stats_start_delay)
            test_stats_dir = os.path.join(stats_base_dir,test.get("name"))
            os.makedirs(test_stats_dir, exist_ok=True)
            threads = []
            for device in devices:
                output_file = os.path.join(test_stats_dir, f"{device[0]}.csv")
                t = threading.Thread(target=collect_remote_stats, args=(device, stats_duration, interval, output_file), name=f"collect_stats_{device[0]}")
                t.start()
                threads.append(t)

            trex_stats_file = os.path.join(test_stats_dir, "trex_stats.csv")
            t = threading.Thread(target=collect_trex_stats, args=(client, stats_duration, interval, trex_stats_file))
            t.start()
            threads.append(t)

            for t in threads:
                t.join()

            client.stop()
            client.disconnect()


    for test in v4_imix_tests:
        print(f"Starting test: {test.get('name')}")
        profile=IMIXStream(src_range=test.get("src_range"), dst_range=test.get("dst_range"),
                           vlan_id=test.get("vlan_id"))
        client = STLClient()
        client.connect()
        client.reset()
        client.set_service_mode(ports=[0], enabled=True, filtered=False, mask=None)

        if test.get("vlan_id") == 1101:
            client.set_l3_mode(0, "198.18.101.5","198.18.101.1", vlan=1101)
            client.arp(ports=[0], retries=3, verbose=True, vlan=1101)
        elif test.get("vlan_id") ==1201:
            client.set_l3_mode(0, "100.66.0.5","100.66.0.1", vlan=1201)
            client.arp(ports=[0], retries=3, verbose=True, vlan=1201)

        client.set_service_mode(ports=[0], enabled=False, filtered=False, mask=None)

        client.add_streams(profile.get_streams(), ports=[0])
        client.start(ports=[0], duration=test_duration, force=True, mult="98%")

        print(f"Running test {test.get('name')} for {test_duration} seconds...")
        time.sleep(stats_start_delay)
        test_stats_dir = os.path.join(stats_base_dir,test.get("name"))
        os.makedirs(test_stats_dir, exist_ok=True)
        threads = []
        for device in devices:
            output_file = os.path.join(test_stats_dir, f"{device[0]}.csv")
            t = threading.Thread(target=collect_remote_stats, args=(device, stats_duration, interval, output_file), name=f"collect_stats_{device[0]}")
            t.start()
            threads.append(t)

        trex_stats_file = os.path.join(test_stats_dir, "trex_stats.csv")
        t = threading.Thread(target=collect_trex_stats, args=(client, stats_duration, interval, trex_stats_file))
        t.start()
        threads.append(t)

        for t in threads:
            t.join()

        client.stop()
        client.disconnect()

    summarize_stats_by_subfolder(stats_base_dir)
    print(f"Summary written to each test folder")


if __name__ == "__main__":
    main()