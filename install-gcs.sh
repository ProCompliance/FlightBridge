#!/bin/bash
# FlightBridge GCS Installer
# Pairs the ground station with a provisioned drone using a pairing code.
# No IP addresses, no VPN dashboards, no manual configuration required.

set -e

BACKEND_URL="http://localhost:8000"
PROVISIONING_SECRET="flightbridge_dev_secret"
STATE_FILE="/etc/flightbridge/gcs-state.conf"
LOG_FILE="/var/log/flightbridge-gcs-install.log"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}✓ $1${NC}"; log "SUCCESS: $1"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; log "WARNING: $1"; }
error() { echo -e "${RED}✗ $1${NC}"; log "ERROR: $1"; exit 1; }

echo ""
echo "================================================"
echo "  FlightBridge GCS Installer"
echo "================================================"
echo ""

# Must run as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash install-gcs.sh"
fi

# Create directories
mkdir -p /etc/flightbridge
mkdir -p /var/log

# --- Step 1: Check if already paired ---
if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"
    if [ "$GCS_PAIRED" = "true" ]; then
        warn "FlightBridge GCS already paired with drone: $DRONE_ID"
        warn "To re-pair, delete $STATE_FILE and re-run."
        exit 0
    fi
fi

# --- Step 2: Get pairing code from operator ---
echo -e "  Enter the pairing code displayed by the drone installer."
echo -e "  Example: ${CYAN}EAGLE-5481${NC}"
echo ""
read -p "  Pairing code: " PAIRING_CODE
PAIRING_CODE=$(echo "$PAIRING_CODE" | tr '[:lower:]' '[:upper:]' | xargs)

if [ -z "$PAIRING_CODE" ]; then
    error "No pairing code entered."
fi

log "Pairing code entered: $PAIRING_CODE"

# --- Step 3: Resolve pairing code to drone IP ---
echo ""
log "Contacting FlightBridge provisioning server..."

# Retry up to 5 times in case drone is still enrolling
MAX_RETRIES=5
RETRY=0
DRONE_IP=""

while [ $RETRY -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s -X GET "$BACKEND_URL/pair/$PAIRING_CODE" \
        -H "x-secret: $PROVISIONING_SECRET")

    DRONE_IP=$(echo $RESPONSE | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('drone_ip',''))" 2>/dev/null)
    DRONE_ID=$(echo $RESPONSE | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('device_id',''))" 2>/dev/null)

    if [ -n "$DRONE_IP" ] && [ "$DRONE_IP" != "pending" ]; then
        break
    fi

    RETRY=$((RETRY + 1))
    warn "Drone still enrolling, retrying in 5 seconds... ($RETRY/$MAX_RETRIES)"
    sleep 5
done

if [ -z "$DRONE_IP" ] || [ "$DRONE_IP" = "pending" ]; then
    error "Could not resolve pairing code. Check the code is correct and the drone is powered on."
fi

success "Drone found — IP: $DRONE_IP"
success "Device ID: $DRONE_ID"

# --- Step 4: Install Tailscale on GCS ---
if ! command -v tailscale &> /dev/null; then
    log "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    success "Tailscale installed"
else
    success "Tailscale already installed"
fi

# --- Step 5: Enroll GCS into tailnet ---
log "Enrolling GCS into FlightBridge network..."

# Get a GCS auth key from provisioning backend
GCS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/provision" \
    -H "Content-Type: application/json" \
    -d "{\"device_id\": \"gcs-$(hostname)\", \"secret\": \"$PROVISIONING_SECRET\"}")

GCS_AUTH_KEY=$(echo $GCS_RESPONSE | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d['auth_key'])" 2>/dev/null)

if [ -z "$GCS_AUTH_KEY" ]; then
    error "Failed to get GCS auth key from provisioning server."
fi

tailscale up --authkey="$GCS_AUTH_KEY" --hostname="gcs-$(hostname)" --accept-routes
success "GCS enrolled in FlightBridge network"

# Get our own Tailscale IP
sleep 3
GCS_IP=$(tailscale ip -4 2>/dev/null)
success "GCS Tailscale IP: $GCS_IP"

# --- Step 6: Save state ---
cat > "$STATE_FILE" << EOF
GCS_PAIRED=true
DRONE_IP=$DRONE_IP
DRONE_ID=$DRONE_ID
GCS_IP=$GCS_IP
PAIRED_AT=$(date '+%Y-%m-%d %H:%M:%S')
EOF
success "State saved to $STATE_FILE"

# --- Step 7: Done ---
echo ""
echo "================================================"
echo -e "  ${GREEN}FlightBridge GCS Pairing Complete${NC}"
echo "================================================"
echo ""
echo -e "  Drone IP:  ${GREEN}$DRONE_IP${NC}"
echo -e "  GCS IP:    ${GREEN}$GCS_IP${NC}"
echo ""
echo "  Telemetry will be available at:"
echo -e "  ${CYAN}udp://localhost:14550${NC}"
echo ""
echo "  Video stream will be available at:"
echo -e "  ${CYAN}udp://localhost:5600${NC}"
echo ""
echo "  Open Mission Planner or QGroundControl"
echo "  and connect to UDP port 14550."
echo ""
echo "================================================"
echo ""
