"""
FlightBridge GCS Agent - Video Receiver
Receives RTP H.264 stream from drone via GStreamer, displays on screen.
"""

import subprocess
import threading
import logging
import time
from config import VIDEO_LISTEN_PORT, VIDEO_DISPLAY, RECONNECT_DELAY

logger = logging.getLogger(__name__)


class VideoReceiver:
    def __init__(self):
        self.running = False
        self.process = None
        self.monitor_thread = None

    def _build_pipeline(self):
        if VIDEO_DISPLAY:
            # Receive RTP H.264, decode, display
            return (
                f"gst-launch-1.0 udpsrc port={VIDEO_LISTEN_PORT} caps=\"application/x-rtp,media=video,"
                f"clock-rate=90000,encoding-name=H264,payload=96\" "
                f"! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink sync=false"
            )
        else:
            # Receive only, no display (useful for headless logging)
            return (
                f"gst-launch-1.0 udpsrc port={VIDEO_LISTEN_PORT} caps=\"application/x-rtp,media=video,"
                f"clock-rate=90000,encoding-name=H264,payload=96\" "
                f"! rtph264depay ! h264parse ! fakesink"
            )

    def _monitor(self):
        while self.running:
            if self.process and self.process.poll() is not None:
                logger.warning("GStreamer video receiver exited unexpectedly, restarting...")
                self._start_process()
            time.sleep(2)

    def _start_process(self):
        pipeline = self._build_pipeline()
        logger.info(f"Starting GStreamer: {pipeline}")
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
        logger.info("VideoReceiver started")

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        logger.info("VideoReceiver stopped")
