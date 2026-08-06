
import subprocess
import logging
import time
import threading
from config import FC_BAUD_RATE, MAVPROXY_OUT_PORT, RECONNECT_DELAY

logger = logging.getLogger(__name__)

class MAVProxyBridge:
    """
    Manages a MAVProxy subprocess that forwards MAVLink telemetry
    from the Flight Controller serial port to the GCS over the
    Tailscale VPN tunnel.

    Satisfies FR-08, FR-10, FR-12.
    """

    def __init__(self, serial_port, gcs_ip):
        self.serial_port = serial_port
        self.gcs_ip = gcs_ip
        self.process = None
        self.running = False
        self._monitor_thread = None

    def _build_command(self):
        """Build the MAVProxy command."""
        return [
            "mavproxy.py",
            f"--master={self.serial_port}",
            f"--baudrate={FC_BAUD_RATE}",
            f"--out=udp:{self.gcs_ip}:{MAVPROXY_OUT_PORT}",
            "--daemon",          # Run without interactive console
            "--non-interactive", # No prompts
            "--logfile=/var/log/mavproxy.log"
        ]

    def start(self):
        """Start the MAVProxy subprocess."""
        if self.process and self.process.poll() is None:
            logger.warning("MAVProxy already running")
            return

        cmd = self._build_command()
        logger.info(f"Starting MAVProxy: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.running = True
            logger.info(f"MAVProxy started (PID {self.process.pid})")
            logger.info(f"Forwarding telemetry to {self.gcs_ip}:{MAVPROXY_OUT_PORT}")

            # Start monitor thread for auto-restart
            self._monitor_thread = threading.Thread(
                target=self._monitor,
                daemon=True
            )
            self._monitor_thread.start()

        except FileNotFoundError:
            raise RuntimeError(
                "mavproxy.py not found. "
                "Install with: pip install mavproxy"
            )

    def _monitor(self):
        """
        Monitor the MAVProxy process and restart if it dies.
        Satisfies FR-12: automatic recovery after link interruption.
        """
        while self.running:
            if self.process and self.process.poll() is not None:
                returncode = self.process.returncode
                logger.warning(
                    f"MAVProxy exited with code {returncode}. "
                    f"Restarting in {RECONNECT_DELAY}s..."
                )
                time.sleep(RECONNECT_DELAY)
                try:
                    self.start()
                except Exception as e:
                    logger.error(f"Failed to restart MAVProxy: {e}")
            time.sleep(2)

    def stop(self):
        """Stop the MAVProxy subprocess cleanly."""
        self.running = False
        if self.process and self.process.poll() is None:
            logger.info("Stopping MAVProxy...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("MAVProxy stopped")

    @property
    def is_running(self):
        return (
            self.process is not None and
            self.process.poll() is None
        )
