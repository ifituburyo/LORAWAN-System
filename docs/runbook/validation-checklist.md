# Bench Validation Checklist

Use this after every reboot or major change to confirm the stack is healthy.

## Pre-flight (on the laptop)

```bash
cd ~/LORAWAN
```

- [ ] `docker compose -f chirpstack-server/docker-compose.yml ps` shows 6 containers (chirpstack, gateway-bridge, rest-api, mosquitto, postgres, redis) all "Up"
- [ ] No container shows "Restarting"
- [ ] `ip -4 addr show | grep "inet 192"` returns the laptop's IP — note it; it should be `192.168.1.23` or whatever was locked in
- [ ] `sudo ufw status` shows rules for 1700/udp, 8080/tcp, 1883/tcp from your LAN subnet
- [ ] `sudo ss -tulpn | grep -E '1700|1883|8080'` shows all three ports listening on `0.0.0.0`

## Server health

- [ ] `docker compose logs chirpstack --tail 30` ends with no "fatal" or "Error" lines
- [ ] `docker compose logs chirpstack | grep -i "starting api server"` shows a recent start
- [ ] `docker compose logs chirpstack | grep -i "region_id=us915_0"` (or eu868 for production) confirms region was loaded
- [ ] Browser: `http://192.168.1.23:8080` loads the login page
- [ ] Logging in as `admin` with your set password works
- [ ] Internal tenant exists with the gateway entry

## Gateway health (`ssh root@192.168.1.123`)

- [ ] Power LED solid, LoRa LED blinking, Ethernet LED solid
- [ ] LoRa antenna physically connected to the WM1302's RFI0
- [ ] `ip addr show br-lan | grep "inet "` shows an IP in your home subnet
- [ ] `ping -c 3 <laptop-ip>` succeeds (if it fails but `nc <ip> 1883` works, that's OK — just UFW blocking ICMP)
- [ ] `ps w | grep concentratord-sx1302 | grep -v grep` shows a running process
- [ ] `ps w | grep mqtt-forwarder | grep -v grep` shows a running process
- [ ] `ls -la /tmp/concentratord_*` shows both `concentratord_event` and `concentratord_command` sockets
- [ ] `logread | grep -i "concentrator started"` shows a recent successful start
- [ ] `logread | grep -i "connected to mqtt"` shows a recent successful broker connection
- [ ] `logread | grep "Gateway ID:"` shows `0016c001f11368ba` (or your hardware's chip EUI)

## End-to-end packet flow

- [ ] On the laptop, `docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml logs mosquitto | grep 192.168.1.123 | tail -3` shows a recent connection from the gateway
- [ ] `mosquitto_sub -h 192.168.1.23 -t 'us915_0/gateway/+/+/+' -v` prints a stats message within 30 seconds
- [ ] ChirpStack web UI → Gateways → your gateway → status is **Online** (green)
- [ ] Same page shows "Last seen: < 30s ago" updating periodically

## Reboot test (full system resilience)

Both sides should auto-recover after power loss:

- [ ] Power off the gateway. Wait 30 seconds. Power it back on.
- [ ] Wait 90 seconds.
- [ ] On the laptop, `docker compose logs mosquitto | tail -10` shows the gateway reconnecting.
- [ ] In the ChirpStack web UI, the gateway goes "Offline" briefly then back to "Online".

- [ ] Reboot the laptop.
- [ ] After login, `docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml ps` shows all containers Up (Docker restarts them via `restart: unless-stopped`).
- [ ] If they're not Up: `./scripts/start.sh` brings them back.
- [ ] Gateway reconnects within 60 seconds.

## If a step fails

Don't proceed past a failed step. Most failures map to a specific section in:

- **Container won't start** → `docs/03-TROUBLESHOOTING.md` → ChirpStack section
- **Gateway won't connect** → `docs/03-TROUBLESHOOTING.md` → Gateway section
- **Network issues** → `docs/04-DEPLOYMENT-RECORD.md` Phase 1.10 (firewall) and Phase 3.1 (laptop IP changing)
- **Concentratord not running but says "running"** → `gateway-seeed-wm1302/README.md` Section 7 (the procd false positive)

If you fix something, redo all steps from the top of the failed section.
