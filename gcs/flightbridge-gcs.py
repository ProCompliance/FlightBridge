"""
FlightBridge GCS Agent - Main Entry Point
Starts MAVLink receiver and video receiver, runs until interrupted.
"""

import logging
import signal
import sys
import time
from config import load_state, LOG_FILE
from mavlink_receiver import MAVLinkReceiver
from video_receiver import VideoReceiver

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

mavlink = None
video = None


def shutdown(signum, frame):
    logger.info("Shutdown signal received")
    if mavlink:
        mavlink.stop()
    if video:
        video.stop()
    sys.exit(0)


def main():
    global mavlink, video

    logger.info("=== FlightBridge GCS Agent starting ===")

    state = load_state()
    drone_ip = state.get("DRONE_IP")
    gcs_ip = state.get("GCS_IP")

    if not drone_ip:
        logger.error("DRONE_IP not found in state file, cannot continue")
        sys.exit(1)

    logger.info(f"Drone IP : {drone_ip}")
    logger.info(f"GCS IP   : {gcs_ip}")
    logger.info("Waiting for telemetry and video from drone...")

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    mavlink = MAVLinkReceiver()
    mavlink.start()

    video = VideoReceiver()
    video.start()

    while True:
        logger.info(f"GCS agent running | drone={drone_ip} | "
                    f"telemetry=UDP:{14550} | video=UDP:{5600}")
        time.sleep(30)


if __name__ == "__main__":
    main()
