# FlightBridge — Document 01: Overview & Requirements

| Field | Detail |
|---|---|
| Document ID | FB-DOC-001 |
| Version | 1.0.0 |
| Status | Draft |
| Date | 2026-08-05 |

---

## 1. Purpose of This Document

This document defines what FlightBridge is, the problem it exists to solve, the functional and non-functional requirements it must satisfy, and the constraints and assumptions under which it operates.

All subsequent design, architecture, implementation, and testing documents derive from the requirements stated here. Any requirement referenced elsewhere in the documentation suite uses the identifier format defined in Section 5 (e.g. `FR-03`, `NFR-07`).

---

## 2. Background & Problem Statement

### 2.1 The Existing Approach

4G/LTE as a UAV command-and-control and video downlink medium is well established. The general architecture — a Raspberry Pi companion computer on the drone running MAVProxy for telemetry forwarding and GStreamer for video, connected back to a GCS over a VPN tunnel — is proven, reliable, and cost-effective compared to proprietary radio links at equivalent range.

The barrier is not the technology. The barrier is the configuration burden placed on the operator.

### 2.2 The Configuration Problem

Existing implementations of this architecture require an operator to:

1. Understand what a VPN is and how to create an account on a third-party platform (ZeroTier, Tailscale, etc.)
2. Manually navigate the VPN platform dashboard to create a network
3. Note and enter the Network ID or account credentials into the drone's configuration
4. Power on the drone, find it in the dashboard, and manually click "Authorize" for each new node
5. Determine the drone's VPN-assigned IP address
6. Enter that IP address into MAVProxy and GStreamer configurations on the GCS side
7. Repeat steps 3–6 for every new drone added to the fleet

This process requires technical knowledge that most end users — and many field operators — do not have. It is error-prone, non-repeatable, and does not scale. A single misconfigured APN or wrong IP address results in no telemetry and no video with no clear diagnostic path for a non-technical operator.

### 2.3 The FlightBridge Approach

FlightBridge eliminates the configuration burden entirely. The operator's interaction with the system is reduced to:

1. Running a single installer on the drone's Raspberry Pi
2. Running a single installer on the GCS machine
3. Entering a pairing code (displayed by the drone installer, entered into the GCS installer)

No VPN accounts to create. No nodes to approve. No IP addresses to copy. No config files to edit. No knowledge of the underlying network stack required.

Everything beneath this interaction — VPN provisioning, node enrollment, telemetry routing, video pipeline setup, and service management — is handled automatically by the FlightBridge software.

---

## 3. Project Scope

### 3.1 In Scope (This PoC)

- Automated Tailscale VPN provisioning for the drone node at install time
- Pairing-code-based GCS enrollment, triggered from the drone installer output
- MAVLink telemetry forwarding from Flight Controller (via serial/UART) to GCS (via MAVProxy over VPN)
- H.264 video streaming from drone camera to GCS (via GStreamer over VPN)
- Automatic serial port detection for Flight Controller connection
- Systemd service management (auto-start on boot, auto-restart on failure)
- Fleet-level network isolation (drone-to-drone communication blocked by ACL policy)
- Basic operational logging on both drone and GCS

### 3.2 Explicitly Out of Scope (This PoC)

- Multi-drone / single-GCS fan-in (one GCS receiving from multiple simultaneous drones)
- Encrypted video (transport is VPN-encrypted; payload encryption is not added)
- Over-the-air software update mechanism
- Web-based configuration UI
- Integration with specific airspace management or UTM systems
- Flight safety systems, geofencing, or return-to-home logic (handled by the Flight Controller, not FlightBridge)
- Hardware design or drone airframe
- Any payload beyond camera (sensors, IR, etc.)
- Commercial productisation, licensing, or support

---

## 4. Intended Audience

This document and the FlightBridge repository are intended for:

- Engineers evaluating the architecture as a reference design
- Developers extending or adapting the system for their own use case
- Technical reviewers assessing the author's design and implementation approach

FlightBridge is a proof of concept. It is not a finished product and is not intended for safety-of-life or regulated operational use in its current form.

---

## 5. Functional Requirements

The following requirements define what FlightBridge **must do**. Each is assigned a unique identifier for traceability.

### 5.1 Installation & Provisioning

| ID | Requirement |
|---|---|
| FR-01 | The drone installer SHALL provision a unique Tailscale identity for the drone node without requiring the operator to create or interact with any VPN account or dashboard. |
| FR-02 | The drone installer SHALL generate a human-readable pairing code upon successful VPN provisioning and display it clearly to the operator. |
| FR-03 | The pairing code SHALL be sufficient for the GCS installer to locate and connect to the correct drone node without any additional information from the operator. |
| FR-04 | The GCS installer SHALL accept the pairing code as its only required operator input. |
| FR-05 | The GCS installer SHALL enroll the GCS machine into the same Tailscale network as the drone node without operator interaction with any VPN dashboard. |
| FR-06 | Both installers SHALL configure their respective services to start automatically on system boot without further operator action after initial installation. |
| FR-07 | The drone installer SHALL detect whether a VPN identity has already been provisioned. If so, it SHALL use the existing identity and SHALL NOT provision a new one. |

### 5.2 Telemetry

| ID | Requirement |
|---|---|
| FR-08 | The drone-side service SHALL establish a MAVLink connection to the Flight Controller via the available serial port or UART interface. |
| FR-09 | The drone-side service SHALL automatically detect the correct serial port for the Flight Controller without operator configuration. |
| FR-10 | The drone-side service SHALL forward MAVLink telemetry from the Flight Controller to the paired GCS over the VPN tunnel using MAVProxy. |
| FR-11 | The GCS-side service SHALL receive MAVLink telemetry and present it on a local UDP port compatible with Mission Planner and QGroundControl. |
| FR-12 | Telemetry forwarding SHALL resume automatically following a VPN link interruption without operator intervention. |

### 5.3 Video

| ID | Requirement |
|---|---|
| FR-13 | The drone-side service SHALL capture video from the attached camera and encode it as H.264 using GStreamer. |
| FR-14 | The encoded video stream SHALL be transmitted to the paired GCS over the VPN tunnel. |
| FR-15 | The GCS-side service SHALL receive the video stream and present it on a local port accessible by a standard video player (e.g. VLC, Mission Planner video widget). |
| FR-16 | Video streaming SHALL resume automatically following a VPN link interruption without operator intervention. |

### 5.4 Network & Security

| ID | Requirement |
|---|---|
| FR-17 | Each drone node SHALL be assigned a unique, persistent Tailscale identity that survives reboots. |
| FR-18 | The system SHALL enforce network isolation such that drone nodes cannot communicate directly with other drone nodes. Only drone-to-GCS and GCS-to-drone communication SHALL be permitted. |
| FR-19 | VPN provisioning SHALL NOT require a long-lived, reusable API key to be stored on the drone. Auth keys used during provisioning SHALL be single-use and short-lived. |
| FR-20 | The provisioning backend SHALL authenticate drone provisioning requests before issuing a Tailscale auth key. |

### 5.5 Logging & Diagnostics

| ID | Requirement |
|---|---|
| FR-21 | Both drone-side and GCS-side services SHALL write operational logs to a known location on the local filesystem. |
| FR-22 | Logs SHALL record service start/stop events, VPN connection state changes, telemetry link state changes, and video pipeline state changes with timestamps. |

---

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | **Boot-to-ready time:** The drone-side service SHALL be in an operational state (VPN connected, telemetry forwarding, video streaming) within 60 seconds of system boot, assuming network connectivity is available. |
| NFR-02 | **Telemetry latency:** End-to-end MAVLink telemetry latency (FC to Mission Planner) SHALL be below 500ms under normal LTE conditions. |
| NFR-03 | **Video latency:** End-to-end video latency SHALL be below 1500ms under normal LTE conditions. |
| NFR-04 | **Link recovery:** Following a complete LTE link interruption, the system SHALL automatically recover telemetry and video without operator intervention within 30 seconds of link restoration. |
| NFR-05 | **Reproducibility:** The installer SHALL produce an identical, working configuration on any Raspberry Pi 4 running Raspberry Pi OS Lite (64-bit, Bookworm) without manual steps beyond running the installer script. |
| NFR-06 | **Observability:** A non-technical operator SHALL be able to determine the operational state of the system (connected / not connected / error) from the drone-side service status output alone, without reading log files. |
| NFR-07 | **Minimal dependencies:** The installer SHALL manage all software dependencies automatically. The operator SHALL NOT be required to install any packages manually prior to running the installer. |

---

## 7. Assumptions & Constraints

| # | Assumption / Constraint |
|---|---|
| A-01 | The drone's Raspberry Pi has an active 4G/LTE data connection with a valid APN at the time of installation and operation. APN configuration is considered a prerequisite and is handled outside FlightBridge scope. |
| A-02 | The GCS machine has internet connectivity at the time of GCS installer execution. |
| A-03 | The Flight Controller is running ArduPlane firmware and outputs MAVLink on a serial interface accessible to the Raspberry Pi. |
| A-04 | A Raspberry Pi Camera Module (or compatible CSI camera) is attached to the drone Raspberry Pi. |
| A-05 | A FlightBridge provisioning backend is reachable at a known HTTPS endpoint at the time of drone installer execution. For this PoC, the provisioning backend is a simple service run by the repository author. |
| A-06 | The Tailscale account used by the provisioning backend has sufficient capacity for the number of nodes being enrolled. |
| A-07 | The operating environment provides sufficient LTE signal for a stable data connection. FlightBridge does not attempt to manage LTE modem connectivity or SIM provisioning. |
| A-08 | Both the drone and GCS are operated by the same party (i.e. this PoC does not model adversarial or untrusted node scenarios beyond the network isolation requirement FR-18). |

---

## 8. Document Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0.0 | 2026-08-05 | — | Initial draft |

---

*Next: [Document 02 — System Architecture](./02-system-architecture.md)*
