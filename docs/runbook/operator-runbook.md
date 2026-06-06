# Operator Runbook — common procedures

Quick reference for day-to-day work on the deployed bench. Each procedure is a self-contained recipe.

## Starting the network from scratch (e.g. after laptop reboot)

```bash
# On the laptop
cd ~/LORAWAN
./scripts/start.sh
./scripts/check-network.sh
# Verify all ports green, all containers Up
```

The gateway auto-starts on power up (assuming the `chirpstack-concentratord-fixed` init script is in place). If the laptop's IP changed, the MQTT forwarder on the gateway will retry connections in the background — it will recover within ~30 seconds of the broker being reachable.

## Confirming the gateway is online

```bash
# Quick check from the laptop
docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml logs mosquitto | grep 192.168.1.123 | tail -3
# Should show a recent "New client connected from 192.168.1.123 as 0016c001f11368ba"
```

Or visit `http://192.168.1.23:8080` → Internal tenant → Gateways → look for green dot.

## Watching live LoRa traffic

```bash
# From the laptop, subscribe to all gateway events
mosquitto_sub -h 192.168.1.23 -t 'us915_0/gateway/+/+/+' -v
```

You'll see:
- Stats messages every 30 seconds
- Uplink packets (`event/up`) whenever a device transmits
- Downlink confirmations (`event/ack`)

## SSH into the gateway

```bash
ssh root@192.168.1.123
# Password: whatever you set during first boot
```

If you forget the password: boot in fail-safe mode (hold a key during boot via HDMI), reset password from `mount_root`, reboot. See OpenWrt docs.

## Restarting gateway services

```bash
# On the gateway
/etc/init.d/chirpstack-concentratord-fixed restart
/etc/init.d/chirpstack-mqtt-forwarder restart

# Watch the logs
logread -f | grep -iE "chirp|concentr|mqtt"
# Ctrl+C to stop
```

## Updating the laptop IP in the gateway config

If your laptop's IP changes (DHCP renewal, network switch, etc.):

```bash
# On the gateway
NEW_IP=192.168.1.50
uci set chirpstack-mqtt-forwarder.@mqtt[0].server="tcp://$NEW_IP:1883"
uci commit chirpstack-mqtt-forwarder
/etc/init.d/chirpstack-mqtt-forwarder restart

# Verify
logread | grep "Connected to MQTT broker" | tail -1
```

## Changing the LoRa region

E.g. swap from US915 to EU868 after a hardware swap.

**On the gateway:**
```bash
# Replace region/channels with EU868 examples
cp /etc/chirpstack-concentratord/sx1302/examples/region_eu868.toml \
   /etc/chirpstack-concentratord-manual/region.toml
cp /etc/chirpstack-concentratord/sx1302/examples/channels_eu868.toml \
   /etc/chirpstack-concentratord-manual/channels.toml

# Edit the region in concentratord.toml
sed -i 's/region = "US915"/region = "EU868"/' \
   /etc/chirpstack-concentratord-manual/concentratord.toml

# Update MQTT topic prefix
uci set chirpstack-mqtt-forwarder.@mqtt[0].topic_prefix='eu868'
uci commit chirpstack-mqtt-forwarder

# Restart both
/etc/init.d/chirpstack-concentratord-fixed restart
/etc/init.d/chirpstack-mqtt-forwarder restart
```

**On the laptop:**
```bash
cd ~/LORAWAN

# Rename region file
mv chirpstack-server/configuration/chirpstack/region_us915.toml \
   chirpstack-server/configuration/chirpstack/region_eu868.toml

# Edit its contents for EU868 (see /home/claude/LORAWAN/chirpstack-server/configuration/chirpstack/region_eu868.toml.eu868-template — original)

# Update enabled_regions
sed -i 's/enabled_regions = \["us915_0"\]/enabled_regions = ["eu868"]/' \
   chirpstack-server/configuration/chirpstack/chirpstack.toml

# Update topic templates
for f in chirpstack-server/configuration/chirpstack-gateway-bridge/*.toml \
         chirpstack-server/docker-compose.yml; do
  sed -i 's|us915_0/gateway|eu868/gateway|g' "$f"
done

# Restart server
docker compose -f chirpstack-server/docker-compose.yml restart chirpstack chirpstack-gateway-bridge
```

In the ChirpStack web UI, edit the existing gateway entry → change Region to `eu868`. The gateway EUI stays the same.

## Adding a new gateway to this network

For example a second WM1302 unit, or a RAK7268 once you get one:

1. Set up its OS (`gateway-seeed-wm1302/README.md` for WM1302, or `gateway-rak7268/README.md` for RAK)
2. Configure its concentratord/MQTT-forwarder to point at `192.168.1.23:1883` (same broker)
3. Get its gateway EUI from logs
4. In ChirpStack web UI → Add Gateway → enter its EUI

Same NS, multiple gateways. ChirpStack automatically deduplicates packets received by both, keeping the version with the better RSSI.

## Backing up

```bash
# From the laptop
cd ~/LORAWAN
./scripts/backup.sh
# Creates a timestamped .sql.gz in backups/

# Sync off-laptop (recommended)
rsync -av backups/ user@offsite:/path/to/backups/
```

The gateway's state (UCI configs, init scripts) is mostly stateless once configured. To back up just in case:

```bash
# On the gateway
tar -czf /tmp/gateway-config-backup.tar.gz \
    /etc/config/chirpstack-* \
    /etc/chirpstack-concentratord-manual/ \
    /etc/init.d/chirpstack-concentratord-fixed

# Copy to laptop
scp root@192.168.1.123:/tmp/gateway-config-backup.tar.gz ~/LORAWAN/backups/
```

## Registering a test device (when you have one)

Buy a US915 LoRaWAN device (Dragino LHT65N-US915 ~ $35 from Aliexpress is the cheapest reliable option).

1. In ChirpStack web UI → Internal → Applications → Add → name it `test-sensors`
2. Internal → Device profiles → Add:
   - Name: `Dragino-LHT65N-US915`
   - Region: `us915_0`
   - MAC version: 1.0.3
   - Codec tab: paste contents of `test-devices/codecs/dragino-lht65n.js`
3. Applications → test-sensors → Add device:
   - DevEUI, AppKey from the sticker on the device
   - Device profile: the one you just made
4. Press the device's join button — within 30 s you should see JoinRequest → JoinAccept → first uplink in the device's "LoRaWAN frames" tab

## Stopping everything

```bash
# Laptop
cd ~/LORAWAN
./scripts/stop.sh

# Gateway
ssh root@192.168.1.123 'poweroff'
# Wait for shutdown, then unplug power
```

## Forgetting/redoing a step

The build is documented step-by-step in `docs/04-DEPLOYMENT-RECORD.md`. Each phase is numbered and idempotent — you can re-run any phase without breaking subsequent ones.

If you completely break the laptop side, wipe and restart:

```bash
cd ~/LORAWAN
docker compose -f chirpstack-server/docker-compose.yml down -v
# Re-run phase 1 from the deployment record
```

The gateway side: re-flash the SD card and start over from Phase 2.
