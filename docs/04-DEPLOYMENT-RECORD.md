# Deployment Record — LoRaWAN Bench Network

**Date deployed:** June 2026
**Operator:** izera
**Location:** Kigali, Rwanda
**Status:** ✅ Operational

This is the as-built documentation of a working private LoRaWAN network. It records every configuration choice we made, why we made it, and how to reproduce it.

---

## 1. Final architecture (what we built)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   END DEVICES              GATEWAY                NETWORK SERVER    │
│   (US915 sensors)          (Seeed WM1302)         (ChirpStack v4)   │
│                                                                     │
│  ┌─────────────┐ ──LoRa──► ┌──────────────┐ ──MQTT──► ┌───────────┐ │
│  │ Future:     │  US915    │ Raspberry Pi │  1883     │ Laptop    │ │
│  │ Dragino     │  902-928  │ + Seeed Hat  │   TCP     │ Ubuntu    │ │
│  │ LHT65 US915 │  MHz      │ + WM1302 SPI │           │ Docker    │ │
│  └─────────────┘           └──────────────┘           └───────────┘ │
│                                  ↑                          ↑       │
│                            192.168.1.123                192.168.1.23│
│                            ChirpStack                   ChirpStack  │
│                            Gateway OS                   Server v4   │
│                            (OpenWrt)                    8080/web    │
│                                                         1883/MQTT   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.1 Hardware inventory

| Component | Model | Notes |
|---|---|---|
| Gateway compute | Raspberry Pi 4 (standard, with microSD) | Visible in original photo, not CM4 with eMMC |
| Gateway carrier | Seeed Studio LoRaWAN Gateway Hat for Raspberry Pi | 40-pin GPIO connector + mini-PCIe slot |
| LoRa concentrator | Seeed WM1302-SPI-US915 | SX1302-based, **SPI** interface, **US915** band (FCC ID Z4T-WM1302-C) |
| Storage | Fresh microSD card (8 GB or larger, Class 10) | Flashed with ChirpStack Gateway OS Base 4.11.0 |
| Antenna | 915 MHz LoRa SMA dipole + u.FL pigtail | Connected to RFI0 on WM1302 |
| Power | Official Raspberry Pi 4 USB-C 3 A | Required — phone chargers cause packet loss |
| Server compute | Ubuntu 24.04 laptop, WiFi-connected | 192.168.1.23 (dynamic DHCP, should be locked) |

### 1.2 Software inventory

| Layer | Software | Version |
|---|---|---|
| Gateway OS | ChirpStack Gateway OS Base (OpenWrt) | 4.11.0, bcm27xx/bcm2709 |
| Gateway: LoRa daemon | chirpstack-concentratord-sx1302 | from Gateway OS 4.11.0 |
| Gateway: forwarder | chirpstack-mqtt-forwarder | 4.5.1 |
| Server: NS | chirpstack/chirpstack | 4 (Docker image) |
| Server: gateway-bridge | chirpstack/chirpstack-gateway-bridge | 4 (Docker image, only Semtech UDP enabled) |
| Server: REST API | chirpstack/chirpstack-rest-api | 4 |
| Server: MQTT broker | eclipse-mosquitto | 2 |
| Server: database | postgres | 14-alpine |
| Server: cache | redis | 7-alpine |
| Host OS firewall | UFW | Active, LAN-only allow rules |
| Orchestration | Docker Compose v2 | 2.40.3 |

### 1.3 Network parameters

| Parameter | Value | Where it's set |
|---|---|---|
| Region | `us915_0` (sub-band 1) | Both server and gateway |
| LoRa channels | 902.3, 902.5, 902.7, 902.9, 903.1, 903.3, 903.5, 903.7 (uplink, 8 of 64) + 904.6 (LoRa-Std uplink) | `channels.toml` |
| Downlink channels | 923.3, 923.9, 924.5, 925.1, 925.7, 926.3, 926.9, 927.5 MHz | `region.toml` |
| RX2 | 923.3 MHz @ DR8 (SF12 BW500) | ChirpStack region |
| Max TX power | +30 dBm EIRP (US FCC max) | We use lower for bench |
| MQTT topic prefix | `us915_0` | Mosquitto, both sides |
| Gateway EUI (chip-burned) | `0016c001f11368ba` | From SX1302 OTP, can't be changed |
| Laptop IP | `192.168.1.23` | DHCP — **must be locked to a reserved IP** |
| Gateway IP | `192.168.1.123` | DHCP from home router |

### 1.4 Critical legal/RF note

This is a **US915 bench setup** for testing only. Rwanda's regulatory band is **EU868**. US915 frequencies (902-928 MHz) are not in the Rwanda SRD allocation. Acceptable for indoor bench testing at low duty cycle; **never deploy this configuration outdoors or for production in Rwanda**. The path to production is to procure EU868 hardware (WM1302-SPI-EU868 module or a RAK7268CV2 EU868), then re-flash the gateway and reconfigure the server with EU868 region settings.

---

## 2. Build sequence (chronological, with reasons)

This is the order things must happen in. Each step depends on the previous. Numbered for traceability.

### Phase 1 — Network Server (on the laptop)

#### 1.1 Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
docker --version          # verify
docker compose version
```

**Why:** ChirpStack ships as Docker containers. Native install on Ubuntu is painful — Docker isolates dependencies cleanly.

#### 1.2 Clone the project

```bash
mkdir -p ~/LORAWAN
cd ~/LORAWAN
# Either extract the tar.gz/zip we built, or git clone your repo
```

#### 1.3 Generate API secret

```bash
cd ~/LORAWAN
SECRET=$(openssl rand -hex 32)
sed -i "s|CHANGE_ME_TO_A_RANDOM_32_BYTE_HEX_STRING_RUN_openssl_rand_hex_32|$SECRET|" \
  chirpstack-server/configuration/chirpstack/chirpstack.toml
```

**Why:** ChirpStack refuses to start with the placeholder secret. Must be 32 bytes of hex.

#### 1.4 Fix the PostgreSQL init script extension

The bundled init script was named `001-init-chirpstack.sh` but contained SQL only. Postgres ignores files unless they end in `.sql`, `.sh`, or `.sql.gz`. The `.sh` extension caused it to be executed as a shell script with no shebang — silent failure, the `chirpstack` database+user never got created.

```bash
mv chirpstack-server/configuration/postgresql/initdb/001-init-chirpstack.sh \
   chirpstack-server/configuration/postgresql/initdb/001-init-chirpstack.sql
```

**Why:** Init scripts in `docker-entrypoint-initdb.d` are detected by extension. SQL files need `.sql`.

#### 1.5 Fix template syntax inconsistency

Two different templating languages are used in ChirpStack v4:

| Component | Language | Syntax |
|---|---|---|
| `chirpstack` server (Rust) | Handlebars | `{{gateway_id}}`, `{{event}}`, `{{command}}` |
| `chirpstack-gateway-bridge` (Go) | Go templates | `{{ .GatewayID }}`, `{{ .EventType }}`, `{{ .CommandType }}` |
| `chirpstack-mqtt-forwarder` (Rust, on gateway) | n/a — uses fixed topic structure | n/a |

Mixing them up causes immediate startup crashes. The right combo:

```bash
# Server configs (Handlebars) — chirpstack.toml and region.toml
grep -E "topic" chirpstack-server/configuration/chirpstack/region_us915.toml
# Should show {{gateway_id}}, {{command}}

# Gateway-bridge configs (Go templates) — both .toml files in chirpstack-gateway-bridge/
grep -E "topic_template" chirpstack-server/configuration/chirpstack-gateway-bridge/*.toml
# Should show {{ .GatewayID }}, {{ .EventType }}, etc.

# docker-compose env vars (Go templates, because they're for gateway-bridge)
grep "TEMPLATE" chirpstack-server/docker-compose.yml
# Should show {{ .GatewayID }}, etc.
```

#### 1.6 Add the missing MQTT server URL

The default gateway-bridge tries to connect to `127.0.0.1:1883` inside its container — where nothing is listening. The Docker Compose env vars set the topic templates but not the broker URL. Add it:

```yaml
# Each gateway-bridge service's environment section needs:
- INTEGRATION__MQTT__AUTH__GENERIC__SERVER=tcp://mosquitto:1883
```

`mosquitto` resolves to the Mosquitto container via Docker's internal DNS.

#### 1.7 Disable the unused Basic Station bridge

We chose the Semtech UDP / MQTT-forwarder protocol path. The Basic Station bridge is unused and was crash-looping due to a different config bug. Disable it:

```bash
# Add a "profiles" tag so docker compose ignores it by default
python3 -c "
import yaml
with open('chirpstack-server/docker-compose.yml') as f: c = yaml.safe_load(f)
c['services']['chirpstack-gateway-bridge-basicstation']['profiles'] = ['disabled']
with open('chirpstack-server/docker-compose.yml', 'w') as f: yaml.safe_dump(c, f, default_flow_style=False, sort_keys=False)
"
```

#### 1.8 Switch region from EU868 to US915

Because our gateway hardware is US915, the server must match. This step is **temporary** — when EU868 hardware arrives we reverse it.

```bash
# Rename the region file
mv chirpstack-server/configuration/chirpstack/region_eu868.toml \
   chirpstack-server/configuration/chirpstack/region_us915.toml

# Write US915 sub-band 0 region config (see appendix for full contents)

# Update main config
sed -i 's/enabled_regions = \["eu868"\]/enabled_regions = ["us915_0"]/' \
  chirpstack-server/configuration/chirpstack/chirpstack.toml

# Update all topic templates to use us915_0 prefix
for f in chirpstack-server/configuration/chirpstack-gateway-bridge/*.toml \
         chirpstack-server/docker-compose.yml; do
  sed -i 's|eu868/gateway|us915_0/gateway|g' "$f"
done
```

#### 1.9 Start the stack

```bash
cd ~/LORAWAN/chirpstack-server
docker compose up -d
docker compose ps
# All 6 containers should show "Up"
```

#### 1.10 Open the firewall

```bash
sudo ufw allow from 192.168.1.0/24 to any port 1700 proto udp
sudo ufw allow from 192.168.1.0/24 to any port 8080 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 1883 proto tcp
sudo ufw allow proto icmp from 192.168.1.0/24
sudo ufw --force enable
```

#### 1.11 Lock the laptop's IP (recommended)

DHCP lease changes broke connectivity during our build. Lock it:

```bash
nmcli connection show              # find connection name
nmcli connection modify "MyWiFi" ipv4.addresses 192.168.1.23/24
nmcli connection modify "MyWiFi" ipv4.gateway 192.168.1.1
nmcli connection modify "MyWiFi" ipv4.dns "8.8.8.8 1.1.1.1"
nmcli connection modify "MyWiFi" ipv4.method manual
nmcli connection down "MyWiFi" && nmcli connection up "MyWiFi"
```

Or set a DHCP reservation in the router admin for the laptop's MAC.

#### 1.12 First login

Browse to `http://192.168.1.23:8080`. Default `admin / admin`. Change immediately. Create an Internal tenant for development.

### Phase 2 — Gateway flash & boot

#### 2.1 Download ChirpStack Gateway OS

```bash
cd ~/LORAWAN/gateway-seeed-wm1302/downloads
wget https://artifacts.chirpstack.io/downloads/chirpstack-gateway-os/4.11.0/raspberrypi/bcm27xx/bcm2709/chirpstack-gateway-os-4.11.0-base-bcm27xx-bcm2709-rpi-2-squashfs-factory.img.gz
```

- The `bcm2709/rpi-2` target covers Pi 2/3/4 — OpenWrt naming convention, not chip-accurate.
- **Base** image (not Full) — server runs elsewhere, gateway only needs forwarder.

#### 2.2 Flash a fresh microSD

Used a separate fresh SD card (not the one already in the gateway). Imager:
- Custom OS → selected `.img.gz`
- No OS customization (Imager's settings are for Raspberry Pi OS, won't work with OpenWrt)
- Verified after write

#### 2.3 Reassemble & boot

- LoRa antenna screwed onto WM1302's u.FL → SMA pigtail → external dipole **before** power
- Ethernet from Pi to home router
- HDMI + USB keyboard attached (needed for first login since OpenWrt's image has no remote-access defaults)
- Powered with official 12V Pi 4 supply

#### 2.4 First-boot login

HDMI showed OpenWrt boot then `gw login:`. Login `root` with no password, then set password with `passwd`.

#### 2.5 Network — what surprised us

OpenWrt on Pi 4 defaults to **router mode**: `eth0` becomes part of `br-lan`, and the bridge gets a static IP. But this Gateway OS image is configured slightly differently — it actually does DHCP on `br-lan`, so the gateway picked up `192.168.1.123` from the home router. Confirmed via:

```bash
ip addr show br-lan | grep "inet "
# inet 192.168.1.123/24 brd 192.168.1.255 scope global br-lan
```

The gateway also broadcasts its own WiFi AP at 192.168.0.1. Optionally disabled to reduce attack surface:

```bash
uci set wireless.@wifi-iface[0].disabled='1'
uci commit wireless
wifi
```

### Phase 3 — Gateway software configuration

#### 3.1 The first gotcha: connectivity false alarm

Initial `ping 192.168.1.44` from gateway failed. Long diagnostic showed:
- ARP for `192.168.1.44` returned FAILED (no MAC)
- ARP for `192.168.1.23` succeeded
- **Conclusion**: laptop IP had changed from `.44` (earlier session) to `.23` (current). We were chasing a ghost.

**Lesson:** Always re-check the laptop IP at start of every session until DHCP reservation is in place.

#### 3.2 ChirpStack Gateway OS architecture

After exploring, we determined this image uses **MQTT Forwarder**, not Gateway Bridge:

```
Hardware → chirpstack-concentratord-sx1302
              ↓ ZeroMQ IPC sockets at /tmp/concentratord_*
            chirpstack-mqtt-forwarder
              ↓ MQTT over TCP
            laptop's Mosquitto:1883
              ↓ MQTT topics
            ChirpStack server
```

Other services available but unused: `chirpstack-udp-forwarder`, `chirpstack-gateway-mesh`, `chirpstack-gateway-bridge` (not installed — only forwarder is).

#### 3.3 Concentratord — UCI configuration (the broken path)

The Gateway OS provides UCI configuration intended to generate runtime TOML files. We set everything via UCI:

```bash
uci set chirpstack-concentratord.@global[0].enabled='1'
uci set chirpstack-concentratord.@sx1302[0].model='semtech_sx1302css915gw1'
uci set chirpstack-concentratord.@sx1302[0].region='US915'
uci set chirpstack-concentratord.@sx1302[0].channel_plan='us915_0'
uci set chirpstack-concentratord.@sx1302[0].usb='0'
uci set chirpstack-concentratord.@sx1302[0].antenna_gain='3'
uci commit chirpstack-concentratord
```

But:
- The init script's `start_service` function references a `$CHIPSET` variable set by sourcing `/lib/functions/chirpstack-concentratord.sh`
- That helper has a buggy/incomplete `case` block — for our `sx1302` config block, it never copied the SX1302 example templates. It fell through to the 2g4 branch at the end of the script.
- Result: `/var/etc/chirpstack-concentratord/` stayed **empty** — no `concentratord.toml`, no `region.toml`, no `channels.toml`.
- The binary started, found no config, exited immediately.
- `procd respawn` restarted it. `status` said "running" because procd had **just** started it; by the time we checked again, it was dead.

**Lesson:** Don't trust `running` from procd-managed services — verify with `ps`.

#### 3.4 Concentratord — manual TOML approach (the working path)

We bypassed UCI by hand-writing the runtime configs:

```bash
mkdir -p /var/etc/chirpstack-concentratord

# Region & channels — direct copies from built-in examples
cp /etc/chirpstack-concentratord/sx1302/examples/channels_us915_0.toml \
   /var/etc/chirpstack-concentratord/channels.toml
cp /etc/chirpstack-concentratord/sx1302/examples/region_us915.toml \
   /var/etc/chirpstack-concentratord/region.toml

# concentratord.toml — hand-written for our hardware (see appendix A.1)
```

Critical: the `model` field. We initially used `semtech_sx1302css915gw1`. That model name is for the **USB** reference design and made the binary open `/dev/ttyACM0` even though our hardware is SPI.

We dumped the binary's known model list with `strings`:

```bash
strings /usr/bin/chirpstack-concentratord-sx1302 | grep -iE "wm1302|sx1302|seeed|rak"
```

Found `seeed_wm1302` (no region suffix — region is set separately via the `region` field). Changed:

```toml
model = "seeed_wm1302"
```

After that, the foreground run showed:

```
Opening SPI communication interface
Note: chip version is 0x10 (v1.0)
INFO: Configuring SX1250_0 in single input mode
INFO: using legacy timestamp
INFO: LoRa Service modem: configuring preamble size to 8 symbols
ARB: dual demodulation disabled for all SF
```

`Opening SPI communication interface` was the breakthrough.

#### 3.5 MQTT forwarder configuration

The MQTT forwarder UCI config did need editing (this part of UCI **does** work correctly):

```bash
# Defaults pointed at localhost (no broker there) with eu868 prefix
uci set chirpstack-mqtt-forwarder.@mqtt[0].topic_prefix='us915_0'
uci set chirpstack-mqtt-forwarder.@mqtt[0].server='tcp://192.168.1.23:1883'
uci commit chirpstack-mqtt-forwarder
/etc/init.d/chirpstack-mqtt-forwarder restart
```

The forwarder gets the gateway EUI via IPC from concentratord — so concentratord must be running first. We confirmed the chain by tailing Mosquitto logs on the laptop:

```
1780688650: New connection from 192.168.1.123:42666 on port 1883
1780688650: New client connected from 192.168.1.123:42666 as 0016c001f11368ba (p5, c0, k30)
```

**Important:** the client ID `0016c001f11368ba` is the **chip-burned EUI**, not the MAC-derived `e45f01fffe93745d`. Use the chip EUI when registering in ChirpStack.

#### 3.6 Persistence — survive reboot

Hand-written configs in `/var/etc/` are wiped on reboot. We solved this by:
1. Saving the working configs to `/etc/chirpstack-concentratord-manual/`
2. Writing a replacement init script `/etc/init.d/chirpstack-concentratord-fixed` that copies them into place on start
3. Disabling the broken default `chirpstack-concentratord` service
4. Enabling our `-fixed` version

Full script in Appendix A.2.

### Phase 4 — Register the gateway in ChirpStack

In the web UI at `http://192.168.1.23:8080`:

1. Internal tenant → Gateways → Add gateway
2. Name: `gw-bench-us915-01`
3. **Gateway EUI: `0016c001f11368ba`** (chip-burned, not MAC-derived)
4. Region: `us915_0`
5. Stats interval: 30 s
6. Location: marker in Kigali

Within 60 seconds, status: **Online** (green).

---

## 3. Verification — how to confirm everything works

### 3.1 Server-side (on laptop)

```bash
# All containers up
docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml ps
# 6 services, all "Up", none "Restarting"

# Ports listening
sudo ss -tulpn | grep -E '1700|1883|8080'
# Should show 0.0.0.0:* for all three

# Mosquitto sees the gateway
docker compose -f ~/LORAWAN/chirpstack-server/docker-compose.yml logs mosquitto | grep "192.168.1.123"
# Should show "New client connected from 192.168.1.123"

# Subscribe to gateway events and watch stats arrive every 30s
mosquitto_sub -h 192.168.1.23 -t 'us915_0/gateway/+/+/+' -v
```

### 3.2 Gateway-side

```bash
ssh root@192.168.1.123

# Both critical services running
ps w | grep -E "concentratord-sx1302|mqtt-forwarder" | grep -v grep
# Two lines, two PIDs

# IPC sockets present (concentratord ↔ forwarder)
ls -la /tmp/concentratord_*
# Both event and command sockets

# Recent logs healthy
logread | grep -iE "concentrator started|connected to mqtt" | tail -5

# After reboot, both auto-start
reboot
# Wait 60s, SSH back, repeat checks
```

### 3.3 Web UI

`http://192.168.1.23:8080` → Internal → Gateways → `gw-bench-us915-01`:
- Status: green / Online
- Last seen: < 60 seconds ago
- Stats graphs filling in over 5+ minutes
- LoRaWAN frames tab: empty (no devices joined yet) — this is expected

---

## 4. What can break and how to fix it

| Symptom | Cause | Fix |
|---|---|---|
| Gateway shows "Never seen" forever | UFW closed, or laptop IP changed | `sudo ufw allow from <subnet> ...` and re-check `ip -4 addr` on laptop |
| `chirpstack-concentratord` says "running" but no `/tmp/concentratord_*` sockets | Configs in `/var/etc/chirpstack-concentratord/` are missing or invalid | Re-copy from `/etc/chirpstack-concentratord-manual/` and restart `-fixed` service |
| "Opening USB communication interface" / `/dev/ttyACM0` error | Wrong `model` — using a `css` (USB) variant | Change to `seeed_wm1302` or another SPI model |
| "unexpected gateway model: X" | Invalid model string | `strings /usr/bin/chirpstack-concentratord-sx1302 \| grep model` to list valid ones |
| MQTT forwarder stuck on "Reading gateway id" | Concentratord not actually running | Check `ps`, restart concentratord |
| Server logs "function gateway_id not defined" | Used Handlebars where Go templates needed (gateway-bridge configs) | Revert that file's template syntax |
| Server logs "connection refused 127.0.0.1:1883" | Gateway-bridge missing `INTEGRATION__MQTT__AUTH__GENERIC__SERVER` env var | Add it to docker-compose.yml |
| Postgres logs "role chirpstack does not exist" | Init script not run (wrong extension or already-initialised volume) | Rename to `.sql`, `docker compose down -v`, restart |
| Both devices on `192.168.1.x` but can't ping each other | Laptop UFW blocks ICMP | `sudo ufw allow proto icmp from 192.168.1.0/24` |

Full troubleshooting: `docs/03-TROUBLESHOOTING.md`.

---

## 5. Path to production (EU868, outdoors)

This bench setup must be reconfigured before production deployment in Rwanda. The migration steps:

1. **Procure EU868 hardware** — either a `WM1302-SPI-EU868` module to drop into the Seeed Hat (cheapest), or a fully assembled RAK7268CV2 EU868 (cleanest path with type approval).
2. **Re-flash gateway SD** (or just edit the configs) for EU868:
   - In `/etc/chirpstack-concentratord-manual/concentratord.toml`: `region = "EU868"`, keep `model = "seeed_wm1302"`
   - Replace `region.toml` and `channels.toml` with the EU868 examples
3. **Reverse the server US915 → EU868 changes** from Phase 1.8 above.
4. **Apply for RURA type approval** for the gateway (procedure in `docs/01-ARCHITECTURE.md`).
5. **Migrate from laptop to VPS** — Phase 1 reproduces identically on a Hetzner CX22 (€5/mo) with proper domain + Let's Encrypt TLS.
6. **Switch from anonymous MQTT to TLS + per-customer credentials**.
7. **Set up monitoring** — UptimeRobot ping, Grafana dashboards on gateway last-seen + uplink rate.

Time estimate: 1-2 days for steps 2-3, 2-6 weeks for RURA approval, 1 day for VPS migration.

---

## Appendix A — Key configuration files (as deployed)

### A.1 Gateway `/etc/chirpstack-concentratord-manual/concentratord.toml`

```toml
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
```

The `model = "seeed_wm1302"` value embeds the SPI pinout (reset, power-enable) so we don't need to specify them.

### A.2 Gateway `/etc/init.d/chirpstack-concentratord-fixed`

```sh
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
```

Companion commands:

```bash
chmod +x /etc/init.d/chirpstack-concentratord-fixed
/etc/init.d/chirpstack-concentratord disable
/etc/init.d/chirpstack-concentratord-fixed enable
/etc/init.d/chirpstack-concentratord-fixed start
```

### A.3 Gateway `/etc/config/chirpstack-mqtt-forwarder` (UCI)

```
config global
    option enabled '1'

config mqtt
    option topic_prefix 'us915_0'
    option server 'tcp://192.168.1.23:1883'
    option qos '0'

config filters
```

### A.4 Server `chirpstack-server/configuration/chirpstack/chirpstack.toml` — key sections

```toml
[postgresql]
  dsn = "postgres://chirpstack:chirpstack@postgres/chirpstack?sslmode=disable"

[redis]
  servers = ["redis://redis:6379/"]

[network]
  net_id = "000000"
  enabled_regions = ["us915_0"]

[api]
  bind = "0.0.0.0:8080"
  secret = "<32 bytes of openssl rand -hex 32>"

[integration]
  enabled = ["mqtt"]

[integration.mqtt]
  server = "tcp://mosquitto:1883/"
  json = true
```

### A.5 Server `chirpstack-server/docker-compose.yml` — key changes from default

The relevant gateway-bridge service block now includes:

```yaml
chirpstack-gateway-bridge:
  image: chirpstack/chirpstack-gateway-bridge:4
  restart: unless-stopped
  ports:
    - "1700:1700/udp"
  environment:
    - INTEGRATION__MQTT__EVENT_TOPIC_TEMPLATE=us915_0/gateway/{{ .GatewayID }}/event/{{ .EventType }}
    - INTEGRATION__MQTT__STATE_TOPIC_TEMPLATE=us915_0/gateway/{{ .GatewayID }}/state/{{ .StateType }}
    - INTEGRATION__MQTT__COMMAND_TOPIC_TEMPLATE=us915_0/gateway/{{ .GatewayID }}/command/#
    - INTEGRATION__MQTT__AUTH__GENERIC__SERVER=tcp://mosquitto:1883
  volumes:
    - ./configuration/chirpstack-gateway-bridge:/etc/chirpstack-gateway-bridge
  depends_on:
    - mosquitto

chirpstack-gateway-bridge-basicstation:
  # ... existing config ...
  profiles:
    - disabled    # Won't auto-start. Re-enable with `--profile disabled` if needed.
```

---

## Appendix B — Useful commands cheat sheet

### Laptop

```bash
# Start/stop the whole stack
cd ~/LORAWAN && ./scripts/start.sh
cd ~/LORAWAN && ./scripts/stop.sh

# Check status
cd ~/LORAWAN && ./scripts/check-network.sh
docker compose -f chirpstack-server/docker-compose.yml ps

# Tail logs
docker compose -f chirpstack-server/docker-compose.yml logs -f chirpstack
docker compose -f chirpstack-server/docker-compose.yml logs -f mosquitto

# Subscribe to all gateway events
mosquitto_sub -h 192.168.1.23 -t 'us915_0/#' -v

# Backup the database
cd ~/LORAWAN && ./scripts/backup.sh

# Find current laptop IP
ip -4 addr show | grep "inet 192"
```

### Gateway

```bash
# SSH in
ssh root@192.168.1.123

# Service status
ps w | grep -E "concentratord-sx1302|mqtt-forwarder" | grep -v grep
/etc/init.d/chirpstack-concentratord-fixed status
/etc/init.d/chirpstack-mqtt-forwarder status

# Restart services
/etc/init.d/chirpstack-concentratord-fixed restart
/etc/init.d/chirpstack-mqtt-forwarder restart

# Tail logs
logread -f | grep -iE "chirp|concentr|mqtt"

# Re-read configs (after editing)
cp -f /etc/chirpstack-concentratord-manual/*.toml /var/etc/chirpstack-concentratord/
/etc/init.d/chirpstack-concentratord-fixed restart

# Show the chip-burned gateway EUI
logread | grep -i "gateway_id" | tail -3

# Show concentratord boot sequence
logread | grep -i "concentrator" | tail -20
```

---

## Appendix C — Glossary

- **NS** — Network Server. The ChirpStack process that authenticates devices, manages session keys, deduplicates uplinks from multiple gateways.
- **Gateway** — The radio that converts LoRa RF frames to IP packets. Has no awareness of which device owns which frame; just forwards.
- **Concentratord** — ChirpStack daemon that talks to the LoRa concentrator chip (SX1302 here) over SPI or USB. Publishes received frames on ZeroMQ IPC sockets.
- **MQTT Forwarder** — ChirpStack daemon that subscribes to the concentratord's IPC and republishes via MQTT. Replaces the older Gateway Bridge in some Gateway OS builds.
- **Gateway Bridge** — Alternative to MQTT Forwarder. Used when gateway speaks Semtech UDP or Basic Station; not used in our setup.
- **EUI** — Extended Unique Identifier. 64-bit MAC-address-like ID. Gateway EUI is burned into the SX1302 chip at the factory.
- **OTAA** — Over-The-Air Activation. The join procedure where a device exchanges Join-Request / Join-Accept with the NS to derive session keys.
- **ADR** — Adaptive Data Rate. NS-driven optimisation of each device's spreading factor and TX power based on link quality.
- **Sub-band** — A subset of US915's 64 channels. `us915_0` = channels 0-7. Devices and gateways must agree on the sub-band.
- **UCI** — Unified Configuration Interface. OpenWrt's config system, persisted across reboots in `/etc/config/`.
- **procd** — OpenWrt's init/service manager. Drop-in replacement for systemd-style init scripts.

---

**End of deployment record.**

For ongoing operations, see:
- `docs/02-OPERATIONS.md` — daily runbook
- `docs/03-TROUBLESHOOTING.md` — symptom-driven debugging
- `docs/runbook/` — incident-specific recovery procedures
