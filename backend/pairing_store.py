import time
import random
import string
from typing import Optional

# In-memory store for PoC
# In production this would be a database
_store = {}

ADJECTIVES = ["FALCON", "RAVEN", "EAGLE", "HAWK", "SWIFT", "VIPER", "GHOST", "STORM"]
NOUNS = ["ALPHA", "BRAVO", "DELTA", "ECHO", "FOXTROT", "KILO", "OSCAR", "TANGO"]

def generate_pairing_code() -> str:
    """Generate a human readable pairing code e.g. FALCON-7842"""
    word = random.choice(ADJECTIVES)
    number = random.randint(1000, 9999)
    return f"{word}-{number}"

def store_pairing_code(code: str, drone_ip: str, device_id: str, expiry: int):
    """Store a pairing code with drone details and expiry timestamp"""
    _store[code] = {
        "drone_ip": drone_ip,
        "device_id": device_id,
        "created_at": time.time(),
        "expires_at": time.time() + expiry,
        "claimed": False
    }

def resolve_pairing_code(code: str) -> Optional[dict]:
    """
    Resolve a pairing code to drone details.
    Returns None if code not found, expired, or already claimed.
    """
    entry = _store.get(code)

    if not entry:
        return None

    if time.time() > entry["expires_at"]:
        del _store[code]
        return None

    if entry["claimed"]:
        return None

    # Mark as claimed so it cant be reused
    _store[code]["claimed"] = True

    return {
        "drone_ip": entry["drone_ip"],
        "device_id": entry["device_id"]
    }

def cleanup_expired():
    """Remove expired codes from store"""
    now = time.time()
    expired = [k for k, v in _store.items() if now > v["expires_at"]]
    for k in expired:
        del _store[k]
