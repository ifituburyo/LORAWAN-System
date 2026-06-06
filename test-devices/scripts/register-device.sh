#!/usr/bin/env bash
# Bulk-register devices on ChirpStack via REST API
# Reads from devices.csv and creates each entry
#
# devices.csv format (no header):
#   name,devEui,appKey,deviceProfileId,applicationId
#
# Usage:
#   1. Edit CHIRPSTACK_URL and API_TOKEN below
#   2. Get API_TOKEN from web UI: Network Server → API Keys → Create
#   3. ./register-device.sh devices.csv

set -e

CHIRPSTACK_URL="${CHIRPSTACK_URL:-http://localhost:8090}"
API_TOKEN="${CHIRPSTACK_API_TOKEN:?Set CHIRPSTACK_API_TOKEN env var}"
CSV_FILE="${1:-devices.csv}"

if [ ! -f "$CSV_FILE" ]; then
    echo "CSV file not found: $CSV_FILE"
    echo ""
    echo "Create a devices.csv with lines like:"
    echo "  lht65-test-01,A84041B2C0000123,0F8B0F6E3D8A4B2C1D5E6F708192A3B4,<DEVICE_PROFILE_ID>,<APP_ID>"
    exit 1
fi

while IFS=',' read -r name devEui appKey deviceProfileId applicationId; do
    # Skip blank lines / comments
    [[ -z "$name" || "$name" =~ ^# ]] && continue

    echo "Registering: $name ($devEui)"

    # Create the device
    curl -sS -X POST \
        -H "Grpc-Metadata-Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"device\": {
                \"devEui\": \"$devEui\",
                \"name\": \"$name\",
                \"applicationId\": \"$applicationId\",
                \"deviceProfileId\": \"$deviceProfileId\",
                \"skipFcntCheck\": false,
                \"isDisabled\": false
            }
        }" \
        "$CHIRPSTACK_URL/api/devices" \
        | jq -r '.id // .message // "OK"'

    # Set the OTAA AppKey
    curl -sS -X PUT \
        -H "Grpc-Metadata-Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"deviceKeys\": {
                \"devEui\": \"$devEui\",
                \"nwkKey\": \"$appKey\",
                \"appKey\": \"$appKey\"
            }
        }" \
        "$CHIRPSTACK_URL/api/devices/$devEui/keys" \
        > /dev/null

    echo "  ✓ $name registered"
done < "$CSV_FILE"

echo ""
echo "Done. Devices registered: $(grep -cv '^\s*#\|^\s*$' "$CSV_FILE")"
