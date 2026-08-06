import time
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from config import PROVISIONING_SECRET, PAIRING_CODE_EXPIRY
from tailscale_api import mint_auth_key, get_drone_ip
from pairing_store import (
    generate_pairing_code,
    store_pairing_code,
    resolve_pairing_code,
    cleanup_expired
)

app = FastAPI(
    title="FlightBridge Provisioning Backend",
    description="Zero-touch VPN provisioning and pairing for UAV ground links.",
    version="0.1.0"
)


# -------------------------------------------------------------------
# Request / Response models
# -------------------------------------------------------------------

class ProvisionRequest(BaseModel):
    device_id: str          # Unique ID derived from Pi serial number
    secret: str             # Must match PROVISIONING_SECRET in .env

class ProvisionResponse(BaseModel):
    auth_key: str           # Single-use Tailscale auth key
    pairing_code: str       # Human readable pairing code e.g. FALCON-7842

class PairRequest(BaseModel):
    pairing_code: str       # Code entered by GCS operator
    secret: str             # Must match PROVISIONING_SECRET in .env

class PairResponse(BaseModel):
    drone_ip: str           # Tailscale IP of the paired drone
    device_id: str          # Device ID of the paired drone


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@app.get("/health")
def health():
    """Basic health check — confirms backend is reachable."""
    return {"status": "ok", "service": "flightbridge-provisioning"}


@app.post("/provision", response_model=ProvisionResponse)
def provision(req: ProvisionRequest):
    """
    Called by the drone installer at first boot.
    Authenticates the request, mints a Tailscale auth key,
    generates a pairing code, and returns both to the drone.

    FR-01: Zero-touch VPN provisioning
    FR-02: Pairing code generation
    FR-19: Single-use, short-lived auth keys
    FR-20: Provisioning request authentication
    """

    # Authenticate the request
    if req.secret != PROVISIONING_SECRET:
        raise HTTPException(status_code=403, detail="Invalid provisioning secret")

    # Mint a single-use Tailscale auth key
    try:
        auth_key = mint_auth_key()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mint auth key: {str(e)}")

    # Generate a pairing code
    pairing_code = generate_pairing_code()

    # Store pairing code with device_id
    # drone_ip is not yet known (drone hasn't enrolled yet)
    # GCS will poll /pair/{code} after drone enrolls
    store_pairing_code(
        code=pairing_code,
        drone_ip="pending",
        device_id=req.device_id,
        expiry=PAIRING_CODE_EXPIRY
    )

    return ProvisionResponse(
        auth_key=auth_key,
        pairing_code=pairing_code
    )


@app.post("/register", )
def register(device_id: str, drone_ip: str, secret: str):
    """
    Called by the drone agent after successful Tailscale enrollment.
    Updates the pairing store with the drone's actual Tailscale IP.

    This is the second call the drone makes — after it has enrolled
    with Tailscale and knows its own VPN IP address.
    """
    if secret != PROVISIONING_SECRET:
        raise HTTPException(status_code=403, detail="Invalid provisioning secret")

    # Find and update the pairing code entry for this device
    from pairing_store import _store
    for code, entry in _store.items():
        if entry["device_id"] == device_id and entry["drone_ip"] == "pending":
            _store[code]["drone_ip"] = drone_ip
            return {"status": "registered", "pairing_code": code}

    raise HTTPException(status_code=404, detail="No pending pairing entry for this device")


@app.get("/pair/{code}", response_model=PairResponse)
def pair(code: str, x_secret: Optional[str] = Header(None)):
    """
    Called by the GCS installer when the operator enters a pairing code.
    Returns the drone's Tailscale IP so the GCS can connect.

    FR-03: Pairing code resolves to drone details
    FR-04: Pairing code is the only operator input required
    FR-05: GCS enrollment without VPN dashboard interaction
    """

    if x_secret != PROVISIONING_SECRET:
        raise HTTPException(status_code=403, detail="Invalid provisioning secret")

    # Clean up any expired codes first
    cleanup_expired()

    result = resolve_pairing_code(code.upper())

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Pairing code not found, expired, or already used"
        )

    if result["drone_ip"] == "pending":
        raise HTTPException(
            status_code=202,
            detail="Drone is still enrolling, please retry in a few seconds"
        )

    return PairResponse(
        drone_ip=result["drone_ip"],
        device_id=result["device_id"]
    )
