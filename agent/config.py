import os

# Load state written by the installer
STATE_FILE = "/etc/flightbridge/state.conf"

def load_state():
    """Read the state file written by install-drone.sh"""
    state = {}
    try:
        with open(STATE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    state[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return state

# Load state at import time
_state = load_state()

# VPN / network
DRONE_IP        = _state.get("DRONE_IP", "")
DEVICE_ID       = _state.get("DEVICE_ID", "unknown")
PAIRING_CODE    = _state.get("PAIRING_CODE", "")

# Serial port settings for Flight Controller
# Auto-detection will try these in order
FC_SERIAL_CANDIDATES = [
    "/dev/ttyAMA0",   # Pi GPIO UART
    "/dev/ttyUSB0",   # USB-Serial adapter
    "/dev/ttyUSB1",
    "/dev/serial0",   # Pi default serial alias
]
FC_BAUD_RATE = 57600

# MAVProxy settings
MAVPROXY_OUT_PORT = 14550   # UDP port on GCS for Mission Planner / QGC

# GStreamer video settings
VIDEO_WIDTH     = 1280
VIDEO_HEIGHT    = 720
VIDEO_FPS       = 30
VIDEO_BITRATE   = 2000      # kbps
VIDEO_PORT      = 5600      # UDP port on GCS for video

# Logging
LOG_FILE = "/var/log/flightbridge-agent.log"

# Retry / reconnection settings
RECONNECT_DELAY     = 5     # seconds between reconnect attempts
MAX_RECONNECT_TRIES = 0     # 0 = retry forever
