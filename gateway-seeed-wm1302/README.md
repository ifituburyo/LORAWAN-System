# Gateway — Seeed WM1302 SPI US915 on Raspberry Pi 4

This is the deployed gateway. **US915 for bench testing only** — for Rwanda production, an EU868 module is required (see Section 6).

## At a glance

| Field | Value |
|---|---|
| Hardware | Raspberry Pi 4 + Seeed LoRaWAN Gateway Hat + WM1302-SPI-US915 module |
| LoRa chip | Semtech SX1302 |
| RF interface | SPI (not USB) |
| Frequency band | US915 (902-928 MHz) |
| Sub-band | `us915_0` (channels 0-7) |
| Gateway EUI | `0016c001f11368ba` (chip-burned, read from SX1302 OTP) |
| IP address | `192.168.1.123` (DHCP from home router) |
| OS | ChirpStack Gateway OS 4.11.0 (OpenWrt-based) |
| SSH | `ssh root@192.168.1.123` |
| Hostname | `chirpstack-93745d` (default) |

## 1. Initial flash & boot (one-time)

```bash
# On the laptop, download the image
cd ~/LORAWAN/gateway-seeed-wm1302/downloads
wget https://artifacts.chirpstack.io/downloads/chirpstack-gateway-os/4.11.0/raspberrypi/bcm27xx/bcm2709/chirpstack-gateway-os-4.11.0-base-bcm27xx-bcm2709-rpi-2-squashfs-factory.img.gz

# Flash with Raspberry Pi Imager
# - Custom OS → select the .img.gz
# - DO NOT apply OS customization (this is OpenWrt, not Raspberry Pi OS)
# - Verify writes complete
```

Physical assembly order (the LoRa antenna must be attached before power):

1. WM1302 module seated in the mini-PCIe slot on the Seeed Hat
2. u.FL pigtail from WM1302's `RFI0` connector → SMA on case → external 915 MHz dipole antenna
3. Seeed Hat seated on all 40 GPIO pins of the Pi 4
4. Flashed microSD card inserted
5. HDMI + USB keyboard attached (needed for first boot — no remote default)
6. Ethernet connected to home router
7. Power last — official Pi 4 12V supply

First boot: `gw login:` appears. User `root`, no password. Set one with `passwd`.

## 2. First login & network check

```bash
# Find IP (it's on the bridge, not directly on eth0)
ip addr show br-lan | grep "inet "
# Output: inet 192.168.1.123/24 brd 192.168.1.255 scope global br-lan

# Optional: disable the gateway's own WiFi AP
uci set wireless.@wifi-iface[0].disabled='1'
uci commit wireless
wifi
```

From the laptop, SSH in:
```bash
ssh root@192.168.1.123
```

## 3. Configure for WM1302 SPI + US915 (the manual approach that works)

The UCI helper for chirpstack-concentratord has a bug — it doesn't generate runtime configs for the SX1302 block. We bypass it.

### 3.1 Write the hand-crafted concentratord.toml

```bash
mkdir -p /var/etc/chirpstack-concentratord

cat > /var/etc/chirpstack-concentratord/concentratord.toml << 'EOF'
[concentratord]
  log_level = "INFO"
  log_to_syslog = true
  stats_interval = "30s"
  disable_crc_filter = false

  [concentratord.api]
    event_bind = "ipc:///tmp/concentratord_event"
    command_bind = "ipc:///tmp/concentratord_command"

[gateway]
  antenna_gain = 3
  lorawan_public = true
  region = "US915"
  model = "seeed_wm1302"
  model_flags = []
  time_fallback_enabled = false

  [gateway.location]
    latitude = -1.9536
    longitude = 30.0606
    altitude = 1567
EOF
```

**Critical: `model = "seeed_wm1302"`**, not `semtech_sx1302css915gw1`. The `css` variant is USB; we have SPI. Wrong model → binary tries to open `/dev/ttyACM0` and crashes.

### 3.2 Copy in region & channel configs

```bash
cp /etc/chirpstack-concentratord/sx1302/examples/region_us915.toml \
   /var/etc/chirpstack-concentratord/region.toml
cp /etc/chirpstack-concentratord/sx1302/examples/channels_us915_0.toml \
   /var/etc/chirpstack-concentratord/channels.toml
```

### 3.3 Verify it works before making it permanent

```bash
/usr/bin/chirpstack-concentratord-sx1302 \
  -c /var/etc/chirpstack-concentratord/concentratord.toml \
  -c /var/etc/chirpstack-concentratord/region.toml \
  -c /var/etc/chirpstack-concentratord/channels.toml
```

Expected:
```
Opening SPI communication interface           ← MUST say SPI, not USB
Note: chip version is 0x10 (v1.0)
INFO: Configuring SX1250_0 in single input mode
INFO: using legacy timestamp
INFO: LoRa Service modem: configuring preamble size to 8 symbols
ARB: dual demodulation disabled for all SF
[... runs continuously ...]
```

`Ctrl+C` to stop once you've confirmed.

### 3.4 Make it survive reboot

```bash
# Save the working configs to a non-volatile location
mkdir -p /etc/chirpstack-concentratord-manual
cp /var/etc/chirpstack-concentratord/*.toml /etc/chirpstack-concentratord-manual/

# Replacement init script that uses our manual configs
cat > /etc/init.d/chirpstack-concentratord-fixed << 'EOF'
#!/bin/sh /etc/rc.common
START=99
STOP=99
USE_PROCD=1

start_service() {
    mkdir -p /var/etc/chirpstack-concentratord
    cp -f /etc/chirpstack-concentratord-manual/*.toml /var/etc/chirpstack-concentratord/

    procd_open_instance
    procd_set_param command /usr/bin/chirpstack-concentratord-sx1302 \
        -c /var/etc/chirpstack-concentratord/concentratord.toml \
        -c /var/etc/chirpstack-concentratord/region.toml \
        -c /var/etc/chirpstack-concentratord/channels.toml
    procd_set_param respawn 3600 5 -1
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
EOF

chmod +x /etc/init.d/chirpstack-concentratord-fixed

# Disable the broken default, enable our fixed version
/etc/init.d/chirpstack-concentratord disable
/etc/init.d/chirpstack-concentratord-fixed enable
/etc/init.d/chirpstack-concentratord-fixed start
```

### 3.5 Configure the MQTT forwarder

This part of UCI works correctly:

```bash
uci set chirpstack-mqtt-forwarder.@mqtt[0].topic_prefix='us915_0'
uci set chirpstack-mqtt-forwarder.@mqtt[0].server='tcp://192.168.1.23:1883'
uci commit chirpstack-mqtt-forwarder
/etc/init.d/chirpstack-mqtt-forwarder restart
```

`192.168.1.23` is your laptop's IP. Update if it changes.

## 4. Verification

```bash
# Concentratord running
ps w | grep concentratord-sx1302 | grep -v grep
# Should show one line with the running process

# IPC sockets present (forwarder ↔ concentratord)
ls -la /tmp/concentratord_*
# Both event and command sockets

# Forwarder connected
logread | grep -i "connected to mqtt" | tail -3
# Should show "Connected to MQTT broker"

# Forwarder reading EUI
logread | grep -i "gateway id" | tail -3
# Should show "Gateway ID: 0016c001f11368ba"
```

On the **laptop**:
```bash
docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml logs mosquitto | grep 192.168.1.123 | tail -5
# Should show "New client connected from 192.168.1.123 as 0016c001f11368ba"
```

## 5. Register in ChirpStack web UI

`http://192.168.1.23:8080` → Internal tenant → Gateways → Add:

| Field | Value |
|---|---|
| Name | `gw-bench-us915-01` |
| Description | `Seeed WM1302 SPI US915 — bench test gateway` |
| **Gateway EUI** | **`0016c001f11368ba`** (the chip EUI, NOT the MAC-derived one) |
| Tenant | Internal |
| Stats interval | 30 |
| Region | `us915_0` |
| Location | Kigali pin |

Within 60 seconds, status flips to **Online** (green).

## 6. Migrating to EU868 (when proper hardware arrives)

Two paths:

### Path A — Swap the WM1302 module

1. Order a `WM1302-SPI-EU868` module (~$80 from Seeed)
2. Power off the gateway
3. Swap the WM1302 module (4 screws, slide in/out of mini-PCIe)
4. Swap the antenna for an 868 MHz dipole
5. Edit `/etc/chirpstack-concentratord-manual/concentratord.toml`:
   ```toml
   region = "EU868"
   # model stays "seeed_wm1302" — same firmware handles both bands
   ```
6. Replace region/channels:
   ```bash
   cp /etc/chirpstack-concentratord/sx1302/examples/region_eu868.toml \
      /etc/chirpstack-concentratord-manual/region.toml
   cp /etc/chirpstack-concentratord/sx1302/examples/channels_eu868.toml \
      /etc/chirpstack-concentratord-manual/channels.toml
   ```
7. Update MQTT forwarder topic prefix:
   ```bash
   uci set chirpstack-mqtt-forwarder.@mqtt[0].topic_prefix='eu868'
   uci commit chirpstack-mqtt-forwarder
   ```
8. Restart:
   ```bash
   /etc/init.d/chirpstack-concentratord-fixed restart
   /etc/init.d/chirpstack-mqtt-forwarder restart
   ```
9. On the laptop, reverse the US915 changes in the server (re-rename region file, update enabled_regions, update topic templates).
10. Update the gateway entry in ChirpStack to region `eu868`.

### Path B — Buy a RAK7268CV2 EU868

Easier for production: factory-built, RURA-approvable, has CE marking. Configuration follows `gateway-rak7268/README.md` instead.

## 7. Troubleshooting specific to this hardware

| Symptom | Fix |
|---|---|
| `ERROR: failed to open COM port /dev/ttyACM0` | Wrong model — change to `seeed_wm1302` (you tried the USB variant) |
| `unexpected gateway model: X` | Run `strings /usr/bin/chirpstack-concentratord-sx1302 \| grep -E "wm1302\|sx1302\|seeed\|rak"` to list valid models |
| `Opening SPI communication interface` then segfaults | LoRa antenna not connected — power down, attach antenna, retry |
| Boot succeeds but `ip addr show br-lan` shows no IP | DHCP not getting response from router — check Ethernet cable, router DHCP pool |
| MQTT forwarder logs "Reading gateway id" forever | Concentratord not actually running. `ps w \| grep concentratord` will confirm. Look at concentratord logs. |
| After reboot, configs gone | The UCI helper overwrote our `/var/etc/` files. Confirm `chirpstack-concentratord` is **disabled** and `chirpstack-concentratord-fixed` is **enabled** |
| `Permission denied` opening `/dev/spidev0.0` | SPI device exists but wrong owner. `chmod 666 /dev/spidev0.0`, then fix permanently via udev rule |
| Stats stop arriving in ChirpStack | Laptop IP changed (DHCP). Update `uci set chirpstack-mqtt-forwarder.@mqtt[0].server=...` and restart |

## 8. Files this folder should contain

```
gateway-seeed-wm1302/
├── README.md                          ← this file
├── configs/
│   ├── concentratord.toml             ← the hand-crafted file (Section 3.1)
│   ├── chirpstack-concentratord-fixed ← the replacement init script (Section 3.4)
│   └── notes.md                       ← model name reference, pin diagrams
└── downloads/
    └── *.img.gz                       ← Gateway OS images (gitignored)
```
