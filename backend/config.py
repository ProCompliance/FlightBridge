from dotenv import load_dotenv
import os

load_dotenv()

TAILSCALE_API_KEY = os.getenv("TAILSCALE_API_KEY")
TAILSCALE_TAILNET = os.getenv("TAILSCALE_TAILNET")
PROVISIONING_SECRET = os.getenv("PROVISIONING_SECRET")

# Tailscale API base URL
TS_API_BASE = "https://api.tailscale.com/api/v2"

# Tag applied to all drone nodes at enrollment
DRONE_TAG = "tag:drone"

# Pairing code expiry in seconds (10 minutes)
PAIRING_CODE_EXPIRY = 600
