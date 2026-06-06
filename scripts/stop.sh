#!/usr/bin/env bash
# Stop the ChirpStack stack (data preserved)
# Usage: ./scripts/stop.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/chirpstack-server"

echo "🛑 Stopping ChirpStack..."
docker compose stop

echo ""
echo "✅ Stopped. Data is preserved in Docker volumes."
echo "   Start again: ./scripts/start.sh"
echo "   Wipe everything (including database): ./scripts/nuke.sh"
