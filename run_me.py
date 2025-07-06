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


#### SETUP ####
test_folder = 'Stateless' # folder containing all Trex Test profiles
devices = [
    ['Netelastic01.boca.acore.network', '192.168.1.58', 'root', '12345678'],
    ['Netelastic02.boca.acore.network', '192.168.1.61', 'root', '12345678']
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

# Function to summarize stats from CSV files
import os
import csv

import os
import csv

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

    for test_file in os.listdir(test_folder):
        if test_file.endswith('.py'):
            test_name = os.path.splitext(test_file)[0]
            test_path = os.path.join(test_folder, test_file)
            test_stats_dir = os.path.join(stats_base_dir, test_name)
            os.makedirs(test_stats_dir, exist_ok=True)

            client = STLClient()
            client.connect()
            client.reset()
            profile = STLProfile.load(test_path)
            client.add_streams(profile.get_streams(), ports=[0])
            client.start(ports=[0], duration=test_duration, force=True, mult="98%")

            print(f"Running test {test_name} for {test_duration} seconds...")
            time.sleep(stats_start_delay)

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