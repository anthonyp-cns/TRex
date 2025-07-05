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
test_folder = 'test_profiles' # folder containing all Trex Test profiles
devices = [
    ['Netelastic01.boca.acore.network', '192.168.1.58', 'root', '12345678'],
    ['Netelastic02.boca.acore.network', '192.168.1.61', 'root', '12345678']
]

test_duration = 120 # Test duration in seconds
stats_start_delay = 60


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
        fieldnames = ['timestamp', 'tx_pps', 'rx_pps', 'tx_bps', 'rx_bps', 'latency_avg', 'latency_max', 'out_of_order', 'packet_drops']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(duration):
            stats = client.get_stats()
            latency = stats.get('latency', {})
            global_stats = stats.get('global', {})
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'tx_pps': global_stats.get('tx_pps', 0),
                'rx_pps': global_stats.get('rx_pps', 0),
                'tx_bps': global_stats.get('tx_bps', 0),
                'rx_bps': global_stats.get('rx_bps', 0),
                'latency_avg': latency.get('average', 0),
                'latency_max': latency.get('max', 0),
                'out_of_order': global_stats.get('oo_packets', 0),
                'packet_drops': global_stats.get('tx_drop', 0)
            })
            time.sleep(interval)

# Function to summarize stats from CSV files
def summarize_stats(stats_dir, summary_file):
    summary_data = []

    for root, _, files in os.walk(stats_dir):
        for file in files:
            if file.endswith('.csv') and file != 'summary.csv':
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    metrics = {}
                    for row in reader:
                        for key in row:
                            if key != 'timestamp':
                                metrics.setdefault(key, []).append(float(row[key]))
                    if metrics:
                        summary = {'file': file}
                        for key, values in metrics.items():
                            summary[f'min_{key}'] = min(values)
                            summary[f'max_{key}'] = max(values)
                        summary_data.append(summary)

    with open(summary_file, 'w', newline='') as f:
        if summary_data:
            fieldnames = summary_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in summary_data:
                writer.writerow(row)

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
            client.add_streams(profile.get_streams())
            client.start(ports=[0], duration=test_duration, force=True)

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

    summary_file = os.path.join(stats_base_dir, 'summary.csv')
    summarize_stats(stats_base_dir, summary_file)
    print(f"Summary written to {summary_file}")

if __name__ == "__main__":
    main()