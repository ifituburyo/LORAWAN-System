# ChirpStack Network Server — Laptop Setup

This runs ChirpStack v4 on your laptop, exposing UDP 1700 (gateway uplink) and TCP 8080 (web UI) on your local network so your RAK7268CV2 and SenseCAP M1 can connect.

## ✅ Prerequisites

```bash
# Verify Docker is installed
docker --version
docker compose version

# If missing on Ubuntu:
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
```

## 🚀 Start it up

```bash
cd /home/izera/LORAWAN/chirpstack-server

# Generate a real API secret (don't ship with the placeholder)
SECRET=$(openssl rand -hex 32)
sed -i "s/CHANGE_ME_TO_A_RANDOM_32_BYTE_HEX_STRING_RUN_openssl_rand_hex_32/$SECRET/" configuration/chirpstack/chirpstack.toml

# Pull images and start
docker compose pull
docker compose up -d

# Watch the logs until ChirpStack reports "Starting API server"
docker compose logs -f chirpstack
# Ctrl-C to stop watching (containers keep running)
```

## 🌐 Open the web UI

Find your laptop's local IP:

```bash
# Linux
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127
# Should print something like 192.168.1.42
```

Then open in your browser: **http://192.168.1.42:8080**

Default login:
- Email: `admin`
- Password: `admin`

⚠️ **Change this immediately.** Network Server → Users → admin → Change password.

## 🔥 Open the firewall for gateways

The gateway connects on UDP 1700. Your laptop firewall must allow it:

### Ubuntu / Debian
```bash
sudo ufw allow from 192.168.0.0/16 to any port 1700 proto udp
sudo ufw allow from 192.168.0.0/16 to any port 8080 proto tcp
sudo ufw allow from 192.168.0.0/16 to any port 1883 proto tcp
sudo ufw status
```

### Fedora / RHEL
```bash
sudo firewall-cmd --add-port=1700/udp --permanent
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --add-port=1883/tcp --permanent
sudo firewall-cmd --reload
```

### macOS
System Settings → Network → Firewall → either disable temporarily for testing, or add Docker to the allowed apps.

### Windows (WSL2)
```powershell
# Run in PowerShell as Administrator
New-NetFirewallRule -DisplayName "ChirpStack UDP 1700" -Direction Inbound -Protocol UDP -LocalPort 1700 -Action Allow
New-NetFirewallRule -DisplayName "ChirpStack Web 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## ✅ Verify it's listening

```bash
# Should show 0.0.0.0:1700 (UDP) and 0.0.0.0:8080 (TCP)
sudo ss -tulpn | grep -E '1700|8080|1883'

# From another device on your LAN, ping the laptop
ping 192.168.1.42

# From another device, test the web UI is reachable
curl -I http://192.168.1.42:8080
```

## 🛑 Stop / restart / wipe

```bash
# Stop (keeps data)
docker compose stop

# Start again
docker compose start

# Stop and remove containers (keeps Postgres volume)
docker compose down

# 💣 Nuke everything including the database
docker compose down -v
```

## 🔧 Common issues

| Symptom | Fix |
|---|---|
| `docker: permission denied` | `sudo usermod -aG docker $USER` then log out/in |
| Web UI shows "Failed to fetch" | Check `docker compose logs chirpstack` — usually DB connection |
| Gateway never goes online | Firewall on laptop is blocking UDP 1700 |
| Port 1700 already in use | Another LoRa packet forwarder running locally — `sudo lsof -i :1700` |
| Laptop changes IP overnight | Set a DHCP reservation in your router for the laptop's MAC |

## 📂 What goes where

```
configuration/chirpstack/             → main NS config (region, API secret)
configuration/chirpstack-gateway-bridge/  → UDP & Basic Station listener configs
configuration/mosquitto/config/       → MQTT broker config
configuration/postgresql/initdb/      → Database initialization (runs once)
lorawan-devices/                      → Drop device codecs here (see test-devices/)
```

## ➡️ Next step

Once the web UI opens and you can log in:
→ Go to `../gateway-rak7268/README.md` to connect your first gateway.
