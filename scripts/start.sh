#!/usr/bin/env bash
# Start the entire LoRaWAN stack
# Usage: ./scripts/start.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/chirpstack-server"

echo "🚀 Starting ChirpStack stack..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

echo ""
echo "📊 Service status:"
docker compose ps

LAPTOP_IP=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127 | head -1 || echo "<your-ip>")

echo ""
echo "✅ ChirpStack is running."
echo ""
echo "   Web UI:       http://${LAPTOP_IP}:8080"
echo "   Default user: admin / admin  (CHANGE IT)"
echo "   UDP for GW:   ${LAPTOP_IP}:1700"
echo "   MQTT broker:  ${LAPTOP_IP}:1883"
echo ""
echo "Tail logs:  docker compose -f chirpstack-server/docker-compose.yml logs -f chirpstack"
