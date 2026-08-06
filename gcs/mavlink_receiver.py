"""
FlightBridge GCS Agent - MAVLink Receiver
Listens for MAVLink UDP from drone, forwards to QGroundControl on localhost.
"""

import socket
import threading
import logging
import time
from config import MAVLINK_LISTEN_PORT, QGC_FORWARD_PORT, RECONNECT_DELAY

logger = logging.getLogger(__name__)


class MAVLinkReceiver:
    def __init__(self):
        self.running = False
        self.thread = None

    def _forward_loop(self):
        """Receive MAVLink UDP from drone, forward to QGC on localhost."""
        while self.running:
            try:
                # Listen for incoming MAVLink from drone
                recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                recv_sock.bind(("0.0.0.0", MAVLINK_LISTEN_PORT))
                recv_sock.settimeout(5.0)

                # Forward to QGC on localhost
                fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                logger.info(f"MAVLink receiver listening on UDP:{MAVLINK_LISTEN_PORT} "
                            f"-> forwarding to localhost:{QGC_FORWARD_PORT}")

                while self.running:
                    try:
                        data, addr = recv_sock.recvfrom(4096)
                        fwd_sock.sendto(data, ("127.0.0.1", QGC_FORWARD_PORT))
                    except socket.timeout:
                        continue

            except Exception as e:
                logger.error(f"MAVLink receiver error: {e}")
                if self.running:
                    logger.info(f"Restarting in {RECONNECT_DELAY}s...")
                    time.sleep(RECONNECT_DELAY)
            finally:
                try:
                    recv_sock.close()
                    fwd_sock.close()
                except:
                    pass

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._forward_loop, daemon=True)
        self.thread.start()
        logger.info("MAVLinkReceiver started")

    def stop(self):
        self.running = False
        logger.info("MAVLinkReceiver stopped")
