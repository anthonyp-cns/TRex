# Installation
```
# Install dependencies
apt install git build-essential zlib1g-dev python3 python3-venv -y
# Create new Working Directory
mkdir /scratch
# Make it useable by everyone
chmod 777 /scratch
# Change to that directory
cd /scratch
# Clone Trex there
git clone https://github.com/cisco-system-traffic-generator/trex-core
# Move to build directory
cd trex-core/linux_dpdk
# Run configure command
./b configure
# Build it
./b build
```

# Usage

In a Screen Session run the below to bring up the "server" instance
```trex_core_count=8
./t-rex-64 -i -c $trex_core_count``` 

In another session run the below to start the control console
```./trex-console```

In the console you can run a file with:
```start -f <file name>```

Specify ```-m <speed (ex 1gpbs)>``` to set bandwidth

show statistics once
```stats```

Run the statistics dashboard
```tui```


# Files
## Advanced Stateful

Advanced Stateful will establish a full connection on both sides. these files allow for collecting the most statistics

- tcp_64b.py 
- tcp_512b.py
- tcp_1500b.py
- udp_64b.py
- udp_512b.py
- udp_1500b.py
- imix_standard.py

## Stateless
Stateless is best for pushing the most packets but does not provide as many stats
- tcp_64b_stateless.py 
- tcp_512b_stateless.py
- tcp_1500b_stateless.py
- udp_64b_stateless.py
- udp_512b_stateless.py
- udp_1500b_stateless.py
- imix_standard_stateless.py