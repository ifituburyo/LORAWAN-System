#!/usr/bin/env bash
# Listen to all uplinks coming through your ChirpStack MQTT broker
# Usage: ./mqtt-listen.sh [laptop_ip]

LAPTOP_IP="${1:-localhost}"
PORT=1883

# Check mosquitto-clients is installed
if ! command -v mosquitto_sub &> /dev/null; then
    echo "mosquitto_sub not found. Install with:"
    echo "  Ubuntu/Debian:  sudo apt install mosquitto-clients"
    echo "  macOS:          brew install mosquitto"
    exit 1
fi

echo "Listening to all uplinks on $LAPTOP_IP:$PORT..."
echo "Press Ctrl-C to stop."
echo ""

# -v = verbose (prints topic + payload)
# Topic pattern matches all applications, all devices, only uplink events
mosquitto_sub -h "$LAPTOP_IP" -p "$PORT" \
    -t 'application/+/device/+/event/up' \
    -v
