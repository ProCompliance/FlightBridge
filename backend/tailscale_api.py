import requests
from config import TAILSCALE_API_KEY, TAILSCALE_TAILNET, TS_API_BASE, DRONE_TAG

def get_headers():
    return {
        "Authorization": f"Bearer {TAILSCALE_API_KEY}",
        "Content-Type": "application/json"
    }

def mint_auth_key() -> str:
    """
    Mint a single-use, pre-authorised, short-lived Tailscale auth key
    tagged as a drone node. This key is handed to the drone at enrollment
    and consumed immediately. It cannot be reused.
    """
    url = f"{TS_API_BASE}/tailnet/{TAILSCALE_TAILNET}/keys"

    payload = {
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": False,
                    "ephemeral": False,
                    "preauthorized": True,
                    "tags": [DRONE_TAG]
                }
            }
        },
        "expirySeconds": 300  # Key expires in 5 minutes if not used
    }

    response = requests.post(url, json=payload, headers=get_headers())

    if response.status_code != 200:
        raise Exception(
            f"Tailscale API error: {response.status_code} — {response.text}"
        )

    return response.json()["key"]


def get_drone_ip(device_id: str) -> str:
    """
    Look up the Tailscale IP address of a drone node by its device ID.
    Called after enrollment to get the IP for pairing code storage.
    """
    url = f"{TS_API_BASE}/tailnet/{TAILSCALE_TAILNET}/devices"

    response = requests.get(url, headers=get_headers())

    if response.status_code != 200:
        raise Exception(
            f"Tailscale API error: {response.status_code} — {response.text}"
        )

    devices = response.json().get("devices", [])

    for device in devices:
        if device_id in device.get("hostname", "") or \
           device_id in device.get("name", ""):
            addresses = device.get("addresses", [])
            if addresses:
                return addresses[0]

    raise Exception(f"Device {device_id} not found in tailnet")


def apply_acl_policy():
    """
    Apply the fleet ACL policy:
    - Drones can reach GCS
    - GCS can reach drones
    - Drones cannot reach other drones
    """
    url = f"{TS_API_BASE}/tailnet/{TAILSCALE_TAILNET}/acl"

    policy = {
        "acls": [
            {
                "action": "accept",
                "src": ["tag:drone"],
                "dst": ["tag:gcs:*"]
            },
            {
                "action": "accept",
                "src": ["tag:gcs"],
                "dst": ["tag:drone:*"]
            }
        ],
        "tagOwners": {
            "tag:drone": [],
            "tag:gcs": []
        }
    }

    response = requests.post(
        url,
        json=policy,
        headers={**get_headers(), "Accept": "application/json"}
    )

    if response.status_code != 200:
        raise Exception(
            f"ACL policy error: {response.status_code} — {response.text}"
        )

    return True
