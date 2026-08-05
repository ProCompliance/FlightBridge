# FlightBridge

> **Zero-configuration telemetry and video bridging for ArduPlane-based UAVs over 4G/LTE.**

FlightBridge is an open-source proof-of-concept that demonstrates how a drone and a Ground Control Station (GCS) can be paired, connected, and streaming telemetry and video — with **no user configuration, no IP addresses, no VPN dashboards, and no manual node approvals.**

Two installers. One pairing code. That's it.

---

## The Problem It Solves

Traditional 4G/LTE UAV ground links require operators to:

- Manually configure APN settings
- Register and approve nodes on a VPN dashboard (ZeroTier, Tailscale, etc.)
- Know the drone's IP address or hostname
- Configure MAVProxy routing by hand
- Set up video pipeline parameters

This is a significant barrier for field deployment and completely unacceptable for any operator who isn't also the developer.

FlightBridge eliminates every one of these steps.

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                      DRONE SIDE                         │
│                                                         │
│  Flight Controller (ArduPlane)                          │
│        │ UART/Serial (MAVLink)                          │
│        ▼                                                │
│  Raspberry Pi (FlightBridge Agent)                      │
│        │ MAVProxy → Tailscale VPN tunnel                │
│        │ GStreamer → Tailscale VPN tunnel                │
│        ▼                                                │
│  4G/LTE Modem ──────────────────────────────────────►  │
└─────────────────────────────────────────────────────────┘
                          │ Internet (LTE)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      GCS SIDE                           │
│                                                         │
│  GCS Machine (FlightBridge GCS)                         │
│        │ Tailscale VPN tunnel                           │
│        ▼                                                │
│  Mission Planner / QGroundControl  ◄── MAVLink stream  │
│  Video Player / Overlay            ◄── GStreamer stream │
└─────────────────────────────────────────────────────────┘
```

FlightBridge handles the entire network layer invisibly. The operator sees only the pairing code workflow.

---

## Pairing Flow (End User Experience)

**Step 1 — Run the drone installer on the Raspberry Pi:**
```bash
curl -sSL https://raw.githubusercontent.com/yourhandle/flightbridge/main/install-drone.sh | bash
```
The installer completes and displays:
```
FlightBridge ready.
Pairing code: FALCON-7842
```

**Step 2 — Run the GCS installer on the ground station:**
```bash
curl -sSL https://raw.githubusercontent.com/yourhandle/flightbridge/main/install-gcs.sh | bash
```
The installer prompts:
```
Enter pairing code:
```
Operator types `FALCON-7842` and presses Enter.

**Step 3 — Done.**

Mission Planner opens. Telemetry is live. Video is streaming. The operator never touched a config file, IP address, or VPN dashboard.

---

## What This Repo Demonstrates

| Capability | Status |
|---|---|
| Zero-touch Tailscale provisioning (drone side) | ✅ Implemented |
| Pairing-code GCS enrollment | ✅ Implemented |
| MAVProxy telemetry forwarding over VPN | ✅ Implemented |
| GStreamer H.264 video over VPN | ✅ Implemented |
| Automatic serial port detection (Flight Controller) | ✅ Implemented |
| Boot-time service startup (systemd) | ✅ Implemented |
| Fleet isolation (ACL-based, drone ↔ drone blocked) | ✅ Implemented |
| Web-based pairing UI (optional) | 🔄 Planned |
| Multi-drone / single GCS | 🔄 Planned |
| Onboard health telemetry (Pi CPU, link quality) | 🔄 Planned |

---

## Repository Structure

```
flightbridge/
├── README.md                        # This file
├── install-drone.sh                 # Drone-side installer
├── install-gcs.sh                   # GCS-side installer
│
├── agent/                           # Drone-side Python service
│   ├── flightbridge-agent.py
│   ├── vpn_provision.py
│   ├── mavproxy_bridge.py
│   ├── video_pipeline.py
│   └── config.py
│
├── gcs/                             # GCS-side Python service
│   ├── flightbridge-gcs.py
│   ├── pair.py
│   └── config.py
│
├── provisioning/                    # Backend provisioning service
│   ├── server.py
│   ├── tailscale_api.py
│   └── pairing_store.py
│
├── systemd/                         # Service unit files
│   ├── flightbridge-agent.service
│   └── flightbridge-gcs.service
│
└── docs/                            # Full documentation
    ├── 01-overview-and-requirements.md
    ├── 02-system-architecture.md
    ├── 03-design-decisions.md
    ├── 04-vpn-provisioning.md
    ├── 05-telemetry-bridge.md
    ├── 06-video-pipeline.md
    ├── 07-build-and-bringup.md
    ├── 08-testing-and-validation.md
    └── 09-runbook.md
```

---

## Hardware Used in This PoC

| Component | Details |
|---|---|
| Drone compute | Raspberry Pi 4 (4GB) |
| OS | Raspberry Pi OS Lite (64-bit, Bookworm) |
| LTE modem | Waveshare SIM7600G-H 4G HAT |
| Flight Controller | Pixhawk / ArduPlane |
| FC ↔ Pi connection | UART via GPIO or USB-Serial |
| Camera | Raspberry Pi Camera Module 3 |
| GCS machine | Any Linux/Windows laptop |

---

## Documentation

All design documentation lives in [`/docs`](./docs/). Start with:

- [`01-overview-and-requirements.md`](./docs/01-overview-and-requirements.md) — What this system is, what it must do, and the constraints it operates under.
- [`02-system-architecture.md`](./docs/02-system-architecture.md) — Full system block diagram and component breakdown.
- [`03-design-decisions.md`](./docs/03-design-decisions.md) — Why these components were chosen over alternatives.

---

## Status

This is a **proof of concept**. It is not production hardened. It is not flight-safety-certified. It is intended to demonstrate a viable architecture and implementation approach for zero-configuration UAV ground link provisioning.

---

## License

MIT License — see [`LICENSE`](./LICENSE)
