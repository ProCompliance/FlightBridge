"""
FlightBridge GCS Agent - Configuration
Reads state written by install-gcs.sh
"""

import os
import sys

# State file written by install-gcs.sh
GCS_STATE_FILE = "/etc/flightbridge/gcs-state.conf"
DRONE_STATE_FILE = "/etc/flightbridge/state.conf"  # if GCS and drone on same machine (dev/test)

# Telemetry
MAVLINK_LISTEN_PORT = 14550       # UDP port we receive MAVLink on
QGC_FORWARD_PORT = 14551          # Forward to QGC on this port (localhost)

# Video
VIDEO_LISTEN_PORT = 5600          # UDP port we receive RTP H.264 on
VIDEO_DISPLAY = True              # Set False to receive-only (no display)

# Logging
LOG_FILE = "/var/log/flightbridge-gcs.log"

# Reconnect
RECONNECT_DELAY = 5               # seconds between restart attempts


def load_state():
    """Read GCS state file, return dict of key=value pairs."""
    if not os.path.exists(GCS_STATE_FILE):
        print(f"[ERROR] State file not found: {GCS_STATE_FILE}")
        print("        Run install-gcs.sh first.")
        sys.exit(1)

    state = {}
    with open(GCS_STATE_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                state[k.strip()] = v.strip()
    return state
