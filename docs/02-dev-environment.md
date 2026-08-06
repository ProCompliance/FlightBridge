# FlightBridge — Document 02: Development Environment Setup

| Field | Detail |
|---|---|
| Document ID | FB-DOC-002 |
| Version | 1.0.0 |
| Status | Draft |
| Date | 2026-08-06 |

---

## 1. Purpose of This Document

This document describes how to set up a development environment for FlightBridge from scratch. Following these steps produces an environment identical to the one used to build and test this project, ensuring any developer can reproduce the setup without prior knowledge of the project's dependencies.

---

## 2. Development Machine Setup (Windows + WSL)

FlightBridge backend and GCS components are developed on Ubuntu running inside Windows Subsystem for Linux (WSL). The drone agent is developed in WSL and deployed to a Raspberry Pi for hardware testing.

### 2.1 WSL — Ubuntu 24.04

If WSL is not already installed, open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu-24.04
```

Restart when prompted. On first launch, create a username and password when asked.

Verify the installation:

```bash
lsb_release -a
```

Expected output:
```
Distributor ID: Ubuntu
Release:        24.04
Codename:       noble
```

### 2.2 Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Install Base Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git curl
```

Verify versions:

```bash
python3 --version   # Expected: Python 3.12.x
git --version       # Expected: git version 2.43.x
```

---

## 3. Project Structure

### 3.1 Create the Project Directory

```bash
mkdir -p ~/flightbridge/{backend,drone-agent,gcs-client,docs}
cd ~/flightbridge
```

### 3.2 Create and Activate the Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

The prompt should now show `(venv)` prefix. The virtual environment must be activated before running any FlightBridge component.

To activate the virtual environment in future sessions:

```bash
cd ~/flightbridge
source venv/bin/activate
```

### 3.3 Install Python Dependencies

```bash
pip install fastapi uvicorn requests python-dotenv
```

Verify installed packages:

```bash
pip list
```

Expected packages (versions may vary):

| Package | Purpose |
|---|---|
| fastapi | REST API framework for provisioning backend |
| uvicorn | ASGI server for running FastAPI |
| requests | HTTP client for Tailscale API calls |
| python-dotenv | Loads environment variables from .env file |
| pydantic | Data validation (installed as fastapi dependency) |

---

## 4. Tailscale Account Setup

FlightBridge uses Tailscale as its VPN layer. The provisioning backend requires a Tailscale account and API access token to mint auth keys programmatically.

### 4.1 Create a Tailscale Account

Go to [tailscale.com](https://tailscale.com) and create an account. Note your **tailnet name** — it is displayed in the top left of the admin console and typically looks like `yourname.github` or `yourname.gmail.com`.

### 4.2 Generate an API Access Token

1. Go to [tailscale.com/admin/settings/keys](https://tailscale.com/admin/settings/keys)
2. Under **API access tokens**, click **"Generate access token"**
3. Give it a description (e.g. `flightbridge-dev`)
4. Set expiry to 90 days
5. Copy the token value immediately — it is only shown once

> **Important:** The token value is shown only at generation time. The ID shown in the keys list afterwards is not the token and cannot be used in its place.

### 4.3 Configure ACL Policy

FlightBridge requires two tags (`tag:drone`, `tag:gcs`) and an ACL policy that enforces fleet isolation. Without this, Tailscale will reject auth key minting requests for tagged nodes.

1. Go to [tailscale.com/admin/acls](https://tailscale.com/admin/acls)
2. Replace the entire contents with the following policy:

```json
{
  "tagOwners": {
    "tag:drone": ["autogroup:admin"],
    "tag:gcs":   ["autogroup:admin"]
  },
  "acls": [
    {
      "action": "accept",
      "src":    ["tag:drone"],
      "dst":    ["tag:gcs:*"]
    },
    {
      "action": "accept",
      "src":    ["tag:gcs"],
      "dst":    ["tag:drone:*"]
    }
  ]
}
```

3. Click **Save**

This policy enforces the following:
- Drone nodes can communicate with GCS nodes
- GCS nodes can communicate with drone nodes
- Drone nodes cannot communicate with other drone nodes (FR-18)
- All other traffic is denied by default

---

## 5. Environment Configuration

### 5.1 Create the Backend .env File

```bash
nano ~/flightbridge/backend/.env
```

Add the following, replacing values with your own:

```
TAILSCALE_API_KEY=tskey-api-your-token-here
TAILSCALE_TAILNET=yourname.github
PROVISIONING_SECRET=flightbridge_dev_secret
```

| Variable | Description |
|---|---|
| `TAILSCALE_API_KEY` | API access token generated in step 4.2 |
| `TAILSCALE_TAILNET` | Your tailnet name from the Tailscale admin console |
| `PROVISIONING_SECRET` | Shared secret between backend and drone installer. Change this for any non-development deployment. |

> **Important:** Never commit the `.env` file to version control. It is listed in `.gitignore`.

---

## 6. Running the Provisioning Backend

```bash
cd ~/flightbridge/backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 6.1 Verify the Backend is Running

In a second terminal:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "service": "flightbridge-provisioning"}
```

### 6.2 Test Provisioning Endpoint

```bash
curl -X POST http://localhost:8000/provision \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-drone-001", "secret": "flightbridge_dev_secret"}'
```

Expected response:
```json
{
  "auth_key": "tskey-auth-...",
  "pairing_code": "EAGLE-5481"
}
```

> After testing, revoke the generated auth key from the Tailscale admin console at tailscale.com/admin/settings/keys — test keys should not be left active.

---

## 7. Raspberry Pi Setup (Drone Agent)

> This section is completed once the drone agent code is ready. Pi setup is not required for backend or GCS development.

Hardware required:

| Component | Detail |
|---|---|
| Raspberry Pi 4 | 4GB RAM recommended |
| OS | Raspberry Pi OS Lite 64-bit (Bookworm) |
| LTE Modem | Waveshare SIM7600G-H 4G HAT or equivalent |
| Camera | Raspberry Pi Camera Module 3 |
| Flight Controller | Pixhawk running ArduPlane |

Pi-specific dependencies (installed by drone installer script):

- `tailscale` — VPN client
- `mavproxy` — MAVLink telemetry forwarding
- `gstreamer1.0` — Video pipeline
- `python3` — Agent runtime

---

## 8. Recommended Development Tools

| Tool | Purpose | Install |
|---|---|---|
| VS Code | Primary editor | [code.visualstudio.com](https://code.visualstudio.com) |
| VS Code Remote - SSH | Edit files on Pi from VS Code on dev machine | VS Code extension marketplace |
| curl | API testing from terminal | Pre-installed on Ubuntu |
| git | Version control | Pre-installed (step 2.3) |

---

## 9. Common Issues

| Issue | Cause | Fix |
|---|---|---|
| `API token invalid` (401) | Wrong value in `TAILSCALE_API_KEY` | Ensure you copied the token value at generation, not the ID shown in the keys list |
| `tags are invalid or not permitted` (400) | ACL policy not configured | Complete step 4.3 |
| `venv not found` | Virtual environment not activated | Run `source ~/flightbridge/venv/bin/activate` |
| Terminal shows `/mnt/c/...` path | WSL opened in Windows directory | Run `cd ~` to return to Linux home |

---

## 10. Document Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0.0 | 2026-08-06 | — | Initial draft |

---

*Previous: [Document 01 — Overview & Requirements](./01-overview-and-requirements.md)*  
*Next: [Document 03 — System Architecture](./03-system-architecture.md)*
