"""
FlightBridge Drone Agent - Configuration
Reads state written by install-drone.sh
"""

import os
import sys

# State file written by install-drone.sh
STATE_FILE = "/etc/flightbridge/state.conf"

# Flight Controller serial candidates
FC_SERIAL_CANDIDATES = [
    "/dev/ttyAMA0",
    "/dev/ttyUSB0",
    "/dev/ttyUSB1",
    "/dev/serial0"
]
FC_BAUD_RATE = 57600

# Telemetry
MAVPROXY_OUT_PORT = 14550

# Video
VIDEO_LISTEN_PORT = 5600

# Logging
LOG_FILE = "/var/log/flightbridge-agent.log"

# Reconnect
RECONNECT_DELAY = 5


def load_state():
    """Read drone state file, return dict of key=value pairs."""
    if not os.path.exists(STATE_FILE):
        print(f"[ERROR] State file not found: {STATE_FILE}")
        print("        Run install-drone.sh first.")
        sys.exit(1)

    state = {}
    with open(STATE_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                state[k.strip()] = v.strip()
    return state
