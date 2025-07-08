import os
import time
import csv
import getpass
import threading
from datetime import datetime, timedelta
import paramiko
import psutil
import sys

sys.path.append('/scratch/trex-core/scripts/automation/trex_control_plane/interactive')
from trex.stl.api import STLClient, STLProfile
from Stateless.create_v4_stream import STLSv4
from Stateless.create_v6_stream import STLSv6
from Stateless.create_imix import IMIXStream

#### SETUP ####
test_duration = (5 * 60 + 30) # Test duration in seconds
stats_start_delay = 30
from config import *


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
            p0 = stats.get(0, {})
            p1 = stats.get(1, {})
            global_stats = stats.get('global', {})
            # Should Return
            # {'active_flows': 0.0, 'active_sockets': 0, 'bw_per_core': 0.1750040501356125, 'cpu_util': 0.009603138081729412, 'cpu_util_raw': 0.0, 'open_flows': 0.0, 'platform_factor': 1.0, 'rx_bps': 133784.34375, 'rx_core_pps': 0.9797892570495605, 'rx_cpu_util': 1.508487734724895e-08, 'rx_drop_bps': 0.0, 'rx_pps': 245.92710876464844, 'socket_util': 0.0, 'tx_expected_bps': 0.0, 'tx_expected_cps': 0.0, 'tx_expected_pps': 0.0, 'tx_pps': 245.92710876464844, 'tx_bps': 134447.046875, 'tx_cps': 0.0, 'total_servers': 0, 'total_clients': 0, 'total_alloc_error': 0, 'queue_full': 0}

            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'tx_pps': p0.get('tx_pps', 0),
                'rx_pps': p1.get('rx_pps', 0),
                'tx_bps': p0.get('tx_bps', 0),
                'rx_bps': p1.get('rx_bps', 0),
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
    # ip = input("Enter IP address of first computer: ") or None
    # username = input("Enter username(DEFAULT: root): ") or "root"
    # password = getpass.getpass("Enter password (DEFAULT: 12345678): ") or "12345678"
    # if ip:
    #     devices.append([f'libreqos.{tower_name}.acore.network', ip, username, password])

    ### Time calculations and test lengths
    num_tests = len(v4_tests) + len(v4_imix_tests) + len(v6_tests) + len(v6_imix_tests)
    total_test_duration = num_tests * test_duration
    print(f"total test duration: {total_test_duration} seconds")
    now = datetime.now()
    future = now + timedelta(seconds=total_test_duration)

    total_test_duration_units = "seconds"
    if total_test_duration > 60:
        total_test_duration = total_test_duration / 60
        total_test_duration_units = "minutes"
        if total_test_duration > 60:
            total_test_duration = total_test_duration / 60
            total_test_duration_units = "Hours"


    print(f"Running {num_tests} tests on tower_name {tower_name}.\n Tests will take approximately "
          f"{round(total_test_duration,2)} {total_test_duration_units}.  Expected completion: {future.strftime('%Y-%m-%d %H:%M')}")

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
            client.set_service_mode(ports=[0,1], enabled=True, filtered=False, mask=None)
            if test.get("vlan_id") == 1101:
                client.set_l3_mode(0, v4_1101_tx_interface.get("src"),v4_1101_tx_interface.get("dst"),
                                   vlan=v4_1101_tx_interface.get("vlan_id"))
                client.set_l3_mode(1, v4_rx_interface.get("src"),v4_rx_interface.get("dst"), vlan=v4_rx_interface.get("vlan_id"))
                client.arp(ports=[0], retries=3, verbose=True, vlan=1101)
                client.arp(ports=[1], retries=3, verbose=True)

            elif test.get("vlan_id") ==1201:
                client.set_l3_mode(0, v4_1201_tx_interface.get("src"), v4_1201_tx_interface.get("dst"),
                                   vlan=v4_1201_tx_interface.get("vlan_id"))
                client.set_l3_mode(1, v4_rx_interface.get("src"), v4_rx_interface.get("dst"),
                                   vlan=v4_rx_interface.get("vlan_id"))
                client.arp(ports=[0], retries=3, verbose=True, vlan=1201)
                client.arp(ports=[1], retries=3, verbose=True)

            client.set_service_mode(ports=[0,1], enabled=False, filtered=False, mask=None)

            client.add_streams(profile.get_streams(), ports=[0])
            multiplier = "97%"
            if "64" in test.get("name"):
                multiplier = "3.7gbps"
            client.start(ports=[0], duration=test_duration, force=True, mult=multiplier)
            now = datetime.now()
            print(f"{now.strftime('%H:%M:%S')}   Running test {test.get('name')} for {test_duration} seconds...")
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
        profile=IMIXStream(src_range=test.get("src_range"), dst_range=test.get("dst_range"),
                           vlan_id=test.get("vlan_id"))
        client = STLClient()
        client.connect()
        client.reset()
        client.set_service_mode(ports=[0, 1], enabled=True, filtered=False, mask=None)
        if test.get("vlan_id") == 1101:
            client.set_l3_mode(0, v4_1101_tx_interface.get("src"), v4_1101_tx_interface.get("dst"),
                               vlan=v4_1101_tx_interface.get("vlan_id"))
            client.set_l3_mode(1, v4_rx_interface.get("src"), v4_rx_interface.get("dst"),
                               vlan=v4_rx_interface.get("vlan_id"))
            client.arp(ports=[0], retries=3, verbose=True, vlan=1101)
            client.arp(ports=[1], retries=3, verbose=True)

        elif test.get("vlan_id") == 1201:
            client.set_l3_mode(0, v4_1201_tx_interface.get("src"), v4_1201_tx_interface.get("dst"),
                               vlan=v4_1201_tx_interface.get("vlan_id"))
            client.set_l3_mode(1, v4_rx_interface.get("src"), v4_rx_interface.get("dst"),
                               vlan=v4_rx_interface.get("vlan_id"))
            client.arp(ports=[0], retries=3, verbose=True, vlan=1201)
            client.arp(ports=[1], retries=3, verbose=True)

        client.set_service_mode(ports=[0, 1], enabled=False, filtered=False, mask=None)

        client.add_streams(profile.get_streams(), ports=[0])

        multiplier = "96%"
        if "64" in test.get("name"):
            multiplier = "50%"

        client.start(ports=[0], duration=test_duration, force=True, mult=multiplier)
        now = datetime.now()
        print(f"{ now.strftime('%H:%M:%S') }  -  Running test {test.get('name')} for {test_duration} seconds...")
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


    for test in v6_tests:
            profile=STLSv6(src_range=test.get('src_range'), dst_range=test.get('dst_range'), pkt_size=test.get('packet_size'), num_flows=test.get("num_flows"),
                          pg_id=test.get("pg_id"), vlan_id=test.get("vlan_id"), protocol=test.get("protocol"))
            client = STLClient()
            client.connect()
            client.reset()

            #### DONT SET SERVICE MODE
            # client.set_service_mode(ports=[0,1], enabled=True, filtered=False, mask=None)
            # # 1101 Int address ipv6 route vrf alliance-evpn-public 3fff:ba7a:1101::/64  3fff:da7a:1101::5
            # # 1201 Int address ipv6 route vrf alliance-evpn-cgnat 3fff:ba7a:1201::/64  3fff:da7a:1201::5
            # if test.get("vlan_id") == 1101:
            #     client.set_l3_mode(0, "198.18.101.5","198.18.101.1", vlan=1101)
            #     client.set_l3_mode(1, "100.122.100.2", "100.122.100.1")
            #     client.conf_ipv6(0, enabled, src_ipv6="3fff:da7a:1101::5")
            #     client.conf_ipv6(1, enabled, src_ipv6="3fff:aa7a:1101::2")
            #     client.arp(ports=[0], retries=3, verbose=True, vlan=1101)
            #     client.arp(ports=[1], retries=3, verbose=True)
            #
            # elif test.get("vlan_id") ==1201:
            #     client.set_l3_mode(0, "100.66.0.5","100.66.0.1", vlan=1201)
            #     client.set_l3_mode(1, "100.122.100.2", "100.122.100.1")
            #     client.conf_ipv6(0, enabled, src_ipv6="3fff:da7a:1201::5")
            #     client.conf_ipv6(1, enabled, src_ipv6="3fff:aa7a:1101::2")
            #     client.arp(ports=[0], retries=3, verbose=True, vlan=1201)
            #     client.arp(ports=[1], retries=3, verbose=True)

            # client.set_service_mode(ports=[0,1], enabled=False, filtered=False, mask=None)

            client.add_streams(profile.get_streams(), ports=[0])
            multiplier = "98%"
            if "64" in test.get("name"):
                multiplier = "50%"
            client.start(ports=[0], duration=test_duration, force=True, mult=multiplier)
            now = datetime.now()
            print(f"{now.strftime('%H:%M:%S')}   Running test {test.get('name')} for {test_duration} seconds...")
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


    # summarize_stats_by_subfolder(stats_base_dir)
    print(f"\n\n\n ### All tests complete, Test Data written to: {stats_base_dir} ###")


if __name__ == "__main__":
    main()