# RAK7268CV2 Gateway — Connect to Local ChirpStack

This points your RAK7268CV2 (WisGate Edge Lite 2) at the ChirpStack server running on your laptop.

## ⚠️ Before powering on

**Attach the LoRa antenna first.** Powering up without the antenna can damage the PA stage on the SX1303 concentrator. The antenna goes on the SMA connector labeled `LORA` (the longer of the two black antennas).

## 🔌 Physical setup

1. Screw on **LoRa antenna** (SMA, finger-tight) ← do this first
2. Screw on **WiFi antenna** (small one)
3. Connect **Ethernet cable** to the LAN/WAN port → same router/switch your laptop is on
4. Plug in **12V power adapter** (use the official one; underpowered PSUs cause packet loss)
5. Wait ~90 seconds for boot. LEDs settle: `PWR` solid, `LoRa` blinking, `ETH` solid

## 🌐 First login

Two ways to reach the gateway:

**Via Ethernet (recommended):**
1. Find its IP in your router's DHCP client list
2. Or scan: `nmap -sn 192.168.1.0/24` (replace with your subnet)
3. Look for hostname `RAK7268` or vendor `RAKwireless`

**Via WiFi AP mode (fallback):**
1. On laptop, connect to WiFi `RAK7268CV2_XXXX` (XXXX = last 4 of MAC)
2. Password is on the sticker on the bottom of the unit (default: `rakwireless`)
3. Browse to `http://192.168.230.1`

Default web login:
- Username: `root`
- Password: `root`

⚠️ **Change this password immediately:** `System → Administration → Router Password`

## 🔄 Upgrade firmware first

Before configuring anything, get the latest stable firmware:

1. Visit https://downloads.rakwireless.com/LoRa/WisGateEdgeLite2/Firmware/
2. Download the latest `.bin` for **RAK7268CV2** (not RAK7268C — different unit)
3. In the web UI: `System → Backup / Flash Firmware → Flash new firmware image`
4. ✅ Tick "Keep settings"
5. Upload, wait ~5 minutes, gateway reboots
6. Log in again, confirm version under `Status`

## ⚙️ The 8 settings that matter

### 1. System → System → General Settings
- **Hostname:** `gw-kigali-home-01` (use a naming scheme — location + number)
- **Timezone:** Africa/Kigali
- **NTP server:** `pool.ntp.org` (LoRaWAN downlink timing depends on accurate clock — this is not optional)

### 2. Network → Interfaces → WAN
- **Protocol:** DHCP client (your home router will assign an IP)
- ✅ **Pro tip:** in your router's admin, set a DHCP reservation for the gateway's MAC so its IP never changes

### 3. LoRa Network → LoRa Network Settings → Region
- **Region:** EU868
- **Channel Plan:** EU_863_870
- Keep all 8 default channels enabled

### 4. LoRa Network → LoRa Network Settings → Mode (THE IMPORTANT ONE)

Choose **Semtech UDP GWMP / Packet Forwarder** for first setup:

| Field | Value |
|---|---|
| Mode | `Packet Forwarder` (or `Semtech UDP GWMP`) |
| Server Address | `192.168.1.42` ← your laptop's IP |
| Server Port Up | `1700` |
| Server Port Down | `1700` |
| Keepalive interval | `10` |
| Stat interval | `30` |
| Push timeout | `100` ms |

**Copy down the Gateway EUI** shown on this page — you need it on the ChirpStack side. It looks like `AC1F09FFFE012345`.

Save → Apply → gateway restarts the packet forwarder.

### 5. LoRa Network → LoRa Packet Logger
- ✅ **Enable** temporarily. Lets you watch live LoRa packets — crucial for debugging.

### 6. Status → Overview (verification page)
After all the above, you should see:
- LoRa Service: **Running**
- Packet forwarder uptime: counting up
- Last received packet: timestamp (will be `--` until a device is in range)

### 7. Optional: System → Administration → SSH Access
- Enable SSH on port 22 for advanced troubleshooting (`ssh root@gateway-ip`)
- Useful command on the gateway: `logread -f` to tail system logs

### 8. Optional: Services → DDNS (skip for now)

## ➕ Register this gateway on ChirpStack

1. Open ChirpStack web UI: `http://192.168.1.42:8080`
2. **Tenants** → your tenant (or create "Internal" tenant)
3. **Gateways** → **Add Gateway**
4. Fill in:
   - **Name:** `gw-kigali-home-01` (match the gateway hostname)
   - **Gateway ID:** the 16-hex-char EUI you copied from the RAK
   - **Tenant:** Internal
   - **Stats interval:** `30` seconds
   - **Location:** drop the pin where the gateway physically sits
5. Save

Within 30–60 seconds, the gateway status should flip from "Never seen" to **Online** (green).

## ✅ Verify end-to-end

In ChirpStack, click the gateway → **Live LoRaWAN frames** tab. Even with no devices in range, you'll see periodic stat messages every 30 seconds.

Then power on any LoRaWAN end device near the gateway. You should see `JoinRequest` frames appearing in the live view within 30 seconds (even if you haven't registered the device yet — gateways forward everything they hear).

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Gateway shows "Never seen" | UDP 1700 blocked | Check laptop firewall, ping laptop from gateway |
| Status flickers Online/Offline | NTP not syncing | Check `pool.ntp.org` reachable from gateway |
| No JoinRequests appearing | No device in range / wrong region | Move device closer, confirm device is EU868 |
| JoinRequest seen but no JoinAccept | Downlink RX1 timing | NTP again, or device too close (saturation) |
| Random reboots every 5 minutes | Packet forwarder crashing | Upgrade firmware, check power supply |

## 📍 SSH into the gateway (advanced)

```bash
ssh root@192.168.1.50  # gateway's IP

# Tail packet forwarder logs
logread -f | grep -i lora

# Restart packet forwarder
/etc/init.d/lora_pkt_fwd restart

# Show packet forwarder config
cat /etc/lora/local_conf.json
```

## ➡️ Next step

→ Go to `../gateway-sensecap-m1/README.md` to convert your SenseCAP M1 into a second gateway.
→ Or jump to `../test-devices/README.md` to register your first end device.
