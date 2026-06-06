#!/usr/bin/env bash
# Diagnose connectivity issues between laptop / gateway / ChirpStack
# Usage: ./scripts/check-network.sh [gateway_ip]

GATEWAY_IP="${1:-}"

echo "🔍 LoRaWAN network diagnostics"
echo "=============================="
echo ""

# 1. Detect laptop's LAN IP
LAPTOP_IP=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127 | head -1)
echo "Laptop IP:           ${LAPTOP_IP:-NOT DETECTED}"

# 2. Check Docker
if command -v docker &>/dev/null; then
    echo "Docker:              $(docker --version)"
else
    echo "Docker:              ❌ NOT INSTALLED"
    exit 1
fi

# 3. Check ChirpStack containers
echo ""
echo "🐳 Container status:"
docker compose -f "$(dirname "$0")/../chirpstack-server/docker-compose.yml" ps 2>/dev/null \
    || echo "  (run from project root or check docker-compose.yml exists)"

# 4. Check ports are listening
echo ""
echo "🔌 Ports listening on laptop:"
for port_proto in "1700/udp" "8080/tcp" "1883/tcp" "3001/tcp"; do
    PORT=${port_proto%/*}
    PROTO=${port_proto#*/}
    if [ "$PROTO" = "udp" ]; then
        if ss -ulpn 2>/dev/null | grep -q ":$PORT "; then
            echo "  ✅ UDP $PORT (Semtech UDP packet forwarder)"
        else
            echo "  ❌ UDP $PORT — gateway can't connect via packet forwarder mode"
        fi
    else
        if ss -tlpn 2>/dev/null | grep -q ":$PORT "; then
            case $PORT in
                8080) echo "  ✅ TCP $PORT (ChirpStack web UI)" ;;
                1883) echo "  ✅ TCP $PORT (Mosquitto MQTT broker)" ;;
                3001) echo "  ✅ TCP $PORT (Basic Station LNS)" ;;
            esac
        else
            echo "  ⚠️  TCP $PORT not listening"
        fi
    fi
done

# 5. Firewall check
echo ""
echo "🔥 Firewall:"
if command -v ufw &>/dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
    echo "  UFW: $UFW_STATUS"
    if [[ "$UFW_STATUS" == *"active"* ]]; then
        sudo ufw status 2>/dev/null | grep -E "1700|8080|1883" || echo "  ⚠️  No rules for 1700/8080/1883 — gateway may be blocked"
    fi
elif command -v firewall-cmd &>/dev/null; then
    echo "  firewalld: $(sudo firewall-cmd --state 2>/dev/null)"
    sudo firewall-cmd --list-ports 2>/dev/null
else
    echo "  No firewall tool detected (good for testing, bad for production)"
fi

# 6. If a gateway IP was provided, test connectivity to it
if [ -n "$GATEWAY_IP" ]; then
    echo ""
    echo "🌐 Gateway connectivity test to $GATEWAY_IP:"
    if ping -c 2 -W 2 "$GATEWAY_IP" &>/dev/null; then
        echo "  ✅ ping responds"
    else
        echo "  ❌ ping fails — gateway not reachable on this network"
    fi
fi

echo ""
echo "Next: open http://${LAPTOP_IP}:8080 in your browser"
