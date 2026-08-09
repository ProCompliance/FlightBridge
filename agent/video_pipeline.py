"""
FlightBridge Drone Agent - Video Pipeline
Reads camera type from state file and builds appropriate GStreamer pipeline.
Supports USB webcam (x264 software encoding) and Pi Camera (hardware encoding).
Auto-restarts on failure.
"""

import subprocess
import threading
import logging
import time
from config import (
    VIDEO_LISTEN_PORT, RECONNECT_DELAY, load_state
)

logger = logging.getLogger(__name__)


class VideoPipeline:
    def __init__(self, gcs_ip: str):
        self.gcs_ip = gcs_ip
        self.running = False
        self.process = None
        self.monitor_thread = None
        state = load_state()
        self.camera_type = state.get("CAMERA_TYPE", "usb")

    def _build_pipeline(self):
        if self.camera_type == "picam":
            # Pi Camera — hardware H.264 encoding
            return (
                f"gst-launch-1.0 libcamerasrc ! videoconvert ! "
                f"v4l2h264enc ! h264parse ! mpegtsmux ! "
                f"udpsink host={self.gcs_ip} port={VIDEO_LISTEN_PORT}"
            )
        else:
            # USB Webcam — software x264 encoding (proven working pipeline)
            return (
                f"gst-launch-1.0 v4l2src device=/dev/video0 ! "
                f"image/jpeg,width=320,height=232,framerate=30/1 ! "
                f"jpegdec ! videoconvert ! "
                f"x264enc tune=zerolatency bitrate=800 speed-preset=ultrafast ! "
                f"mpegtsmux ! udpsink host={self.gcs_ip} port={VIDEO_LISTEN_PORT}"
            )

    def _monitor(self):
        while self.running:
            if self.process and self.process.poll() is not None:
                logger.warning("GStreamer pipeline exited unexpectedly, restarting...")
                self._start_process()
            time.sleep(2)

    def _start_process(self):
        pipeline = self._build_pipeline()
        logger.info(f"Starting GStreamer pipeline (camera={self.camera_type}): {pipeline}")
        self.process = subprocess.Popen(
            pipeline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def start(self):
        self.running = True
        self._start_process()
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()
        logger.info("VideoPipeline started")

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        logger.info("VideoPipeline stopped")
