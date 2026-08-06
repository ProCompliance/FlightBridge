#!/usr/bin/env python3
"""
FlightBridge Drone Agent
========================
Main entry point for the drone-side service.

Runs on boot via systemd. Reads state written by install-drone.sh,
detects the Flight Controller serial port, then starts and monitors
the MAVProxy telemetry bridge and GStreamer video pipeline.

Satisfies: FR-08 through FR-16, FR-21, FR-22
"""

import logging
import signal
import sys
import time

from config import (
    DEVICE_ID, DRONE_IP, PAIRING_CODE,
    LOG_FILE, RECONNECT_DELAY
)
from serial_detect import get_serial_port_with_retry
from mavproxy_bridge import MAVProxyBridge
from video_pipeline import VideoPipeline

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("flightbridge.agent")


# -------------------------------------------------------------------
# State validation
# -------------------------------------------------------------------

def validate_state():
    """
    Confirm installer has run and state file is populated.
    Exits cleanly with a clear message if not provisioned yet.
    """
    if not DRONE_IP:
        logger.error(
            "No Tailscale IP found in state file. "
            "Has install-drone.sh been run? "
            "Expected state at /etc/flightbridge/state.conf"
        )
        sys.exit(1)

    if not DEVICE_ID or DEVICE_ID == "unknown":
        logger.error("No device ID found in state file.")
        sys.exit(1)

    logger.info(f"Device ID:    {DEVICE_ID}")
    logger.info(f"Drone IP:     {DRONE_IP}")
    logger.info(f"Pairing code: {PAIRING_CODE}")


# -------------------------------------------------------------------
# GCS IP resolution
# -------------------------------------------------------------------

def get_gcs_ip():
    """
    Read the paired GCS IP from the GCS state file if available,
    otherwise fall back to broadcast on the Tailscale subnet.

    In a full implementation this would query the provisioning
    backend for the paired GCS IP using the pairing code.
    For this PoC we read from local state if available.
    """
    gcs_state_file = "/etc/flightbridge/gcs-state.conf"
    try:
        with open(gcs_state_file, "r") as f:
            for line in f:
                if line.startswith("GCS_IP="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass

    # Fallback — this won't work for real but signals misconfiguration
    logger.warning(
        "GCS state file not found. "
        "GCS IP unknown — telemetry and video may not reach GCS."
    )
    return None


# -------------------------------------------------------------------
# Signal handling
# -------------------------------------------------------------------

mavproxy = None
video = None

def handle_shutdown(signum, frame):
    """Handle SIGTERM and SIGINT cleanly."""
    logger.info(f"Received signal {signum} — shutting down...")
    if mavproxy:
        mavproxy.stop()
    if video:
        video.stop()
    logger.info("FlightBridge agent stopped.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


# --------------------------------------
