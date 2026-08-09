#!/bin/bash
# FlightBridge Drone Installer
set -e

BACKEND_URL="http://192.168.42.8:8000"
PROVISIONING_SECRET="flightbridge_dev_secret"
STATE_FILE="/etc/flightbridge/state.conf"
LOG_FILE="/var/log/flightbridge-install.log"

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

if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash install-drone.sh"
fi

mkdir -p /etc/flightbridge
mkdir -p /var/log

if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"
    if [ "$VPN_SET" = "true" ]; then
        warn "Already provisioned. Delete $STATE_FILE to re-provision."
        exit 0
    fi
fi

log "Reading device serial number..."
DEVICE_ID=$(cat /proc/cpuinfo | grep Serial | awk '{print $3}' | tail -c 9)
if [ -z "$DEVICE_ID" ]; then
    DEVICE_ID=$(hostname)-$(date +%s)
    warn "Could not read Pi serial, using fallback ID: $DEVICE_ID"
else
    success "Device ID: $DEVICE_ID"
fi

echo ""
echo "  Camera Selection"
echo "  ----------------"
echo "  1) Raspberry Pi Camera"
echo "  2) USB Webcam"
echo ""
read -p "  Select camera type [1/2]: " CAMERA_CHOICE

case $CAMERA_CHOICE in
    1)
        CAMERA_TYPE="picam"
        success "Camera type: Raspberry Pi Camera"
        ;;
    2)
        CAMERA_TYPE="usb"
        success "Camera type: USB Webcam"
        ;;
    *)
        warn "Invalid choice, defaulting to USB Webcam"
        CAMERA_TYPE="usb"
        ;;
esac

echo ""
echo "  Network Interface Selection"
echo "  ---------------------------"
echo "  1) WiFi (wlan0)"
echo "  2) 4G/LTE (usb0)"
echo ""
read -p "  Select network interface [1/2]: " NET_CHOICE

case $NET_CHOICE in
    1)
        NET_IFACE="wlan0"
        success "Network interface: WiFi (wlan0)"
        ;;
    2)
        NET_IFACE="usb0"
        success "Network interface: 4G/LTE (usb0)"
        ;;
    *)
        warn "Invalid choice, defaulting to WiFi"
        NET_IFACE="wlan0"
        ;;
esac

log "Requesting provisioning from backend..."
RESPONSE=$(curl -sf -X POST "$BACKEND_URL/provision" \
    -H "Content-Type: application/json" \
    -d "{\"device_id\":\"$DEVICE_ID\",\"secret\":\"$PROVISIONING_SECRET\"}") || error "Backend unreachable at $BACKEND_URL"

AUTH_KEY=$(echo "$RESPONSE" | grep -o '"auth_key":"[^"]*"' | cut -d'"' -f4)
PAIRING_CODE=$(echo "$RESPONSE" | grep -o '"pairing_code":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AUTH_KEY" ]; then
    error "Failed to get auth key from backend"
fi
success "Got auth key and pairing code: $PAIRING_CODE"

log "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

log "Connecting to Tailscale..."
tailscale up --authkey="$AUTH_KEY" --hostname="uav-$DEVICE_ID" --accept-routes

log "Getting Tailscale IP..."
DRONE_IP=$(tailscale ip -4)
if [ -z "$DRONE_IP" ]; then
    error "Could not get Tailscale IP"
fi
success "Tailscale IP: $DRONE_IP"

log "Registering with backend..."
curl -sf -X POST "$BACKEND_URL/register?device_id=$DEVICE_ID&drone_ip=$DRONE_IP&secret=$PROVISIONING_SECRET" || warn "Registration failed, pairing code may not resolve"

cat > "$STATE_FILE" << STATE
VPN_SET=true
DEVICE_ID=$DEVICE_ID
DRONE_IP=$DRONE_IP
PAIRING_CODE=$PAIRING_CODE
CAMERA_TYPE=$CAMERA_TYPE
NET_IFACE=$NET_IFACE
INSTALLED_AT=$(date '+%Y-%m-%d %H:%M:%S')
STATE

echo ""
echo "================================================"
success "FlightBridge provisioning complete!"
echo ""
echo "  Pairing Code : $PAIRING_CODE"
echo "  Drone IP     : $DRONE_IP"
echo "  Device ID    : $DEVICE_ID"
echo "  Camera Type  : $CAMERA_TYPE"
echo "  Network      : $NET_IFACE"
echo ""
echo "  Give the pairing code to your GCS operator."
echo "  To change settings: sudo nano $STATE_FILE"
echo "================================================"
echo ""
