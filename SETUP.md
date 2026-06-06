# SETUP — Step by Step

The shortest path from cloning this project to seeing your first LoRaWAN packet decoded.

## Prerequisites checklist

Before you start, you should have:

- [ ] An Ubuntu/Debian/macOS/Windows-WSL2 laptop with at least 4 GB RAM
- [ ] Docker + Docker Compose v2 installed (`docker compose version`)
- [ ] Ethernet cable connecting the laptop to your home/office router
- [ ] RAK7268CV2 gateway (EU868 variant)
- [ ] Optional: SenseCAP M1 (EU868) for a second gateway
- [ ] At least one LoRaWAN end device (Dragino LHT65N recommended)
- [ ] VS Code installed
- [ ] 2-3 hours of uninterrupted time

## ⏱️ Time budget

| Step | Time |
|---|---|
| Install Docker | 15 min |
| Start ChirpStack | 10 min |
| Configure RAK7268CV2 | 30 min |
| Convert SenseCAP M1 (optional) | 2-3 hours |
| Register first device | 20 min |
| Total (without SenseCAP) | ~1.5 hours |

## 📂 Step 1 — Get the project into VS Code

```bash
# Option A: if you received this as a zip/tar
mkdir -p /home/izera
cd /home/izera
# extract the project here, then:
cd LORAWAN

# Option B: clone from your git repo (if you've set one up)
cd /home/izera
git clone <your-repo-url> LORAWAN
cd LORAWAN

# Open in VS Code
code .
```

VS Code will prompt to install recommended extensions — click "Install All".

## 🐳 Step 2 — Start the Network Server

In the VS Code terminal (Ctrl+\`):

```bash
# Make scripts executable (once)
chmod +x scripts/*.sh test-devices/scripts/*.sh

# Start everything
./scripts/start.sh
```

Expected output:
```
🚀 Starting ChirpStack stack...
[+] Running 7/7
 ✔ Container chirpstack-server-postgres-1                  Started
 ✔ Container chirpstack-server-redis-1                     Started
 ✔ Container chirpstack-server-mosquitto-1                 Started
 ✔ Container chirpstack-server-chirpstack-1                Started
 ✔ Container chirpstack-server-chirpstack-gateway-bridge-1 Started
 ...
✅ ChirpStack is running.
   Web UI:       http://192.168.1.42:8080
```

## 🔥 Step 3 — Open the firewall

```bash
# Ubuntu / Debian
sudo ufw allow from 192.168.0.0/16 to any port 1700 proto udp
sudo ufw allow from 192.168.0.0/16 to any port 8080 proto tcp
sudo ufw allow from 192.168.0.0/16 to any port 1883 proto tcp
```

Run diagnostics to confirm:
```bash
./scripts/check-network.sh
```

All four ports should show ✅.

## 🌐 Step 4 — First login

Open in your browser: `http://<your-laptop-ip>:8080`

- Username: `admin`
- Password: `admin`

**Change the password immediately.**

You'll see an empty dashboard. That's expected. There are no gateways yet.

## 📡 Step 5 — Connect the RAK7268CV2

Follow the detailed guide in `gateway-rak7268/README.md`.

Quick version:
1. Attach LoRa antenna
2. Power on, Ethernet to your router
3. Find its IP, log in (`root`/`root`), change password
4. **LoRa Network → Network Settings:**
   - Mode: Packet Forwarder
   - Server: your laptop's IP
   - Port: 1700
5. Copy the Gateway EUI
6. In ChirpStack web UI: Gateways → Add → paste EUI

Gateway should go **Online** within 60 seconds.

## 🔄 Step 6 — (Optional) Convert SenseCAP M1

Follow `gateway-sensecap-m1/README.md` carefully. This takes 2-3 hours the first time.

Skip this step on first run if you just want to get to "working" fast. The RAK7268CV2 alone is enough for testing.

## 🌡️ Step 7 — Register your first device

Power on a Dragino LHT65N (or whatever sensor you have).

In ChirpStack web UI:
1. **Tenants → Internal → Applications → Add** `test-sensors`
2. **Tenants → Internal → Device profiles → Add** `Dragino-LHT65N-EU868`
   - Paste the codec from `test-devices/codecs/dragino-lht65n.js` into the Codec tab
3. **Applications → test-sensors → Add device** with your DevEUI
4. Add the AppKey on the next page

Press the device's join button. Within 30 seconds, you should see:
- JoinRequest → JoinAccept → UnconfirmedDataUp
- Decoded payload: `{"BatV": 3.046, "TempC_SHT": 24.5, "Hum_SHT": 67.8}`

🎉 You have a working private LoRaWAN network.

## 🎧 Step 8 — Tap into the data stream

In a new terminal:
```bash
./test-devices/scripts/mqtt-listen.sh
```

Every uplink will print as JSON. This is what your customer dashboard will subscribe to.

## ➡️ What's next

- Read `docs/01-ARCHITECTURE.md` for the full picture
- Read `docs/02-OPERATIONS.md` for the day-to-day runbook
- Read `docs/03-TROUBLESHOOTING.md` when something breaks (it will)
- When you have 50+ devices and paying customers → migrate to a VPS (procedure in Operations doc)
