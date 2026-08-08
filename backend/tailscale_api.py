"""
FlightBridge - Tailscale API client
Mints short-lived, single-use, pre-authorised auth keys for drone and GCS nodes.
"""

import httpx
from config import TAILSCALE_API_KEY, TAILSCALE_TAILNET, TS_API_BASE, DRONE_TAG

GCS_TAG = "tag:gcs"

HEADERS = {
    "Authorization": f"Bearer {TAILSCALE_API_KEY}",
    "Content-Type": "application/json"
}


def _mint_key(tag: str) -> str:
    """Mint a single-use, pre-authorised, short-lived Tailscale auth key for given tag."""
    url = f"{TS_API_BASE}/tailnet/{TAILSCALE_TAILNET}/keys"
    payload = {
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": False,
                    "ephemeral": False,
                    "preauthorized": True,
                    "tags": [tag]
                }
            }
        },
        "expirySeconds": 300
    }
    response = httpx.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()["key"]


def mint_auth_key() -> str:
    """Mint a drone auth key (tag:drone)."""
    return _mint_key(DRONE_TAG)


def mint_gcs_auth_key() -> str:
    """Mint a GCS auth key (tag:gcs)."""
    return _mint_key(GCS_TAG)


def get_drone_ip(device_id: str) -> str:
    url = f"{TS_API_BASE}/tailnet/{TAILSCALE_TAILNET}/devices"
    response = httpx.get(url, headers=HEADERS)
    response.raise_for_status()
    devices = response.json().get("devices", [])
    for device in devices:
        if device_id in device.get("hostname", ""):
            addresses = device.get("addresses", [])
            for addr in addresses:
                if addr.startswith("100."):
                    return addr
    return None
