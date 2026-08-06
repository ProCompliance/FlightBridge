import serial
import time
import logging
from config import FC_SERIAL_CANDIDATES, FC_BAUD_RATE

logger = logging.getLogger(__name__)

def test_serial_port(port, baud=FC_BAUD_RATE, timeout=3):
    """
    Attempt to open a serial port and read MAVLink heartbeat bytes.
    Returns True if MAVLink traffic detected, False otherwise.
    """
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        start = time.time()
        while time.time() - start < timeout:
            data = ser.read(100)
            # MAVLink v1 starts with 0xFE, MAVLink v2 starts with 0xFD
            if b'\xfe' in data or b'\xfd' in data:
                ser.close()
                logger.info(f"MAVLink detected on {port}")
                return True
        ser.close()
    except (serial.SerialException, OSError) as e:
        logger.debug(f"Port {port} not available: {e}")
    return False


def detect_flight_controller():
    """
    Scan candidate serial ports for MAVLink traffic.
    Returns the first port where MAVLink is detected.
    Raises RuntimeError if no FC found.

    Satisfies FR-09: Automatic serial port detection.
    """
    logger.info("Scanning for Flight Controller...")

    for port in FC_SERIAL_CANDIDATES:
        logger.info(f"Trying {port} at {FC_BAUD_RATE} baud...")
        if test_serial_port(port):
            logger.info(f"Flight Controller found on {port}")
            return port

    raise RuntimeError(
        f"No Flight Controller detected on any candidate port: "
        f"{FC_SERIAL_CANDIDATES}. "
        f"Check FC is powered and connected."
    )


def get_serial_port_with_retry(max_retries=0, delay=5):
    """
    Keep trying to detect FC until found.
    max_retries=0 means retry forever (correct for a boot service).

    This handles the case where the FC powers up slower than the Pi.
    """
    attempt = 0
    while True:
        try:
            port = detect_flight_controller()
            return port
        except RuntimeError as e:
            attempt += 1
            if max_retries > 0 and attempt >= max_retries:
                raise
            logger.warning(f"{e} — retrying in {delay}s (attempt {attempt})")
            time.sleep(delay)
