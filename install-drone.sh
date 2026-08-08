#!/bin/bash
# FlightBridge Drone Installer
# Provisions a unique Tailscale identity and displays a pairing code.
# No user configuration required beyond running this script.

set -e

BACKEND_URL="http://172.29.114.77:8000"
PROVISIONING_SECRET="flightbridge_dev_secret"
STATE_FILE="/etc/flightbridge/state.conf"
LOG_FILE="/var/log/flightbridge-install.log"

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}✓ $1${NC}"; log "SUCCESS: $1"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; log "WARNING: $1"; }
error() { echo -e "${RED}✗ $1${NC}"; log "ERROR: $1"; exit 1; }

echo ""
echo "================================================"
echo "  FlightBridge Drone Installer"
echo "================================================"
echo ""

# Must run as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash install-drone.sh"
fi

# Create directories
mkdir -p /etc/flightbridge
mkdir -p /var/log

# --- Step 1: Check if already provisioned ---
if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"
    if [ "$VPN_SET" = "true" ]; then
        warn "FlightBridge already provisioned on this device."
        warn "Device ID: $DEVICE_ID"
        warn "To re-provision, delete $STATE_FILE and re-run."
        exit 0
    fi
fi

# --- Step 2: Get unique device ID from Pi serial ---
log "Reading device serial number..."
DEVICE_ID=$(cat /proc/cpuinfo | grep Serial | awk '{print $3}' | tail -c 9)
if [ -z "$DEVICE_ID" ]; then
    # Fallback for non-Pi hardware (dev/testing)
    DEVICE_ID=$(hostname)-$(date +%s)
    warn "Could not read Pi serial, using fallback ID: $DEVICE_ID"
else
    success "Device ID: $DEVICE_ID"
fi

# --- Step 3: Call

