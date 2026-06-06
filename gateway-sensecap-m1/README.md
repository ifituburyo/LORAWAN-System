# SenseCAP M1 → ChirpStack Gateway Conversion

This guide replaces the Helium firmware on a SenseCAP M1 (Seeed Studio) with **ChirpStack Gateway OS**, turning it into a standard LoRaWAN gateway that talks to your ChirpStack server.

## ⚠️ Read this before starting

- This **permanently wipes the Helium miner firmware**. Withdraw any pending HNT first.
- Conversion takes 2–4 hours the first time.
- If you brick the eMMC, recovery needs Raspberry Pi USB Boot mode skills.
- Your M1 **must be the EU868 variant** for Rwanda. US915 hardware will NOT work on EU868 — the SX1302's RF filters are tuned at the factory.
- After conversion, you **lose any CE/FCC certification** that covered the original Helium configuration. Fine for your own internal/pilot use; **do not deploy converted M1 units at paying customers' sites**. Use proper RAK7268CV2 or Kerlink for those.

## 🔍 Step 1 — Identify your hardware

Open the case (4 Phillips screws on the bottom plate). You'll find:

- **Raspberry Pi CM4** module (with eMMC, no WiFi/BT usually disabled — confirm by reading the CM4 label, e.g. `CM4002000` = 2GB RAM, no WiFi, no eMMC; `CM4102032` = 1GB RAM, WiFi+BT, 32GB eMMC)
- **LoRa concentrator card** — usually a RAK2287 (mini-PCIe form factor with SX1302)
- Region sticker on the concentrator card — confirm "EU868"

Common SenseCAP M1 variants:
| Variant | CM4 | LoRa | Notes |
|---|---|---|---|
| M1 v1.0 | CM4 1GB / eMMC 8GB | RAK2287 EU868 | Most common |
| M1 v1.1 | CM4 2GB / eMMC 32GB | RAK2287 EU868 | Newer batches |

## 💾 Step 2 — Download what you need

On your laptop:

```bash
cd /home/izera/LORAWAN/gateway-sensecap-m1

# Create a downloads folder
mkdir -p downloads
cd downloads

# Get ChirpStack Gateway OS (Raspberry Pi 4 / CM4 image — works for SenseCAP M1)
# Check latest version at: https://www.chirpstack.io/docs/chirpstack-gateway-os/
wget https://artifacts.chirpstack.io/downloads/chirpstack-gateway-os/raspberrypi4-64/chirpstack-gateway-os-base-raspberrypi4-64-latest.wic.gz

# Verify the download
ls -lh *.wic.gz
```

Also install Raspberry Pi tools on your laptop:

```bash
sudo apt update
sudo apt install -y rpiboot pv xz-utils
# Or download Raspberry Pi Imager from rpi.org/imager
```

## 🔧 Step 3 — Put the CM4 into USB Boot mode

The CM4 needs to be told to boot from USB instead of eMMC so you can flash it.

1. **Power off** the SenseCAP M1 completely (unplug everything)
2. Locate the **BOOT** jumper or switch on the CM4 carrier board inside the M1
   - On most SenseCAP M1 boards there are two pins labeled `BOOT` near the USB-C port
   - Short these two pins with a jumper, tweezers, or a piece of wire
3. Connect a **USB-C cable** from your laptop to the M1's USB-C port (some units have a dedicated "USB OTG" port — read the label)
4. **Do NOT power-plug the M1 yet.** The CM4 will draw power from the USB cable

## 💻 Step 4 — Flash the eMMC

On your laptop:

```bash
# Start rpiboot — this exposes the eMMC as a USB mass storage device
sudo rpiboot

# Wait ~10 seconds. You should see output like:
# "Loading: bootcode4.bin ... Sending bootcode4.bin ..."
# Then a new block device appears
```

In another terminal, find the new device:

```bash
lsblk
# Look for a new device that just appeared — usually /dev/sda or /dev/sdb
# It should be ~8GB or ~32GB depending on your CM4
# ⚠️ TRIPLE CHECK THIS — wrong device = wiping your laptop's disk
```

Flash the image (replace `/dev/sdX` with the actual device):

```bash
cd /home/izera/LORAWAN/gateway-sensecap-m1/downloads

# Decompress and write in one pipe (with progress)
gunzip -c chirpstack-gateway-os-base-raspberrypi4-64-latest.wic.gz | \
  pv | \
  sudo dd of=/dev/sdX bs=4M conv=fsync status=progress

# This takes 3-10 minutes depending on USB speed
```

When done:

```bash
sudo sync
sudo eject /dev/sdX  # safely disconnect
```

## 🔌 Step 5 — Reassemble and first boot

1. **Unplug** the USB-C cable
2. **Remove** the BOOT jumper (very important — otherwise it will keep waiting for USB boot)
3. Make sure the **LoRa antenna** is attached
4. Connect **Ethernet** cable to your home/office router (same network as laptop)
5. Power on with the original power adapter
6. Wait ~60 seconds

Find the gateway on your network:

```bash
# Look for hostname "chirpstack-gateway" in your router's DHCP table
# Or scan:
nmap -sn 192.168.1.0/24 | grep -B 2 -i "chirpstack\|raspberry"
```

SSH in:

```bash
ssh root@192.168.1.55  # use the IP you found
# Default password: chirpstack
```

⚠️ Change password immediately: `passwd`

## ⚙️ Step 6 — Configure for SX1302 + EU868

ChirpStack Gateway OS uses three services:
- `chirpstack-concentratord` → talks to the SX1302 hardware
- `chirpstack-gateway-bridge` → translates concentratord events to MQTT/UDP
- (Optional) `chirpstack-gateway-mesh` → for mesh deployments

### Pick the right concentratord profile

```bash
# On the gateway, via SSH:

# List available SX1302 profiles
ls /opt/chirpstack-concentratord/

# For SenseCAP M1 with RAK2287 EU868:
cd /opt/chirpstack-concentratord/sx1302/
ls
# You'll see folders like: rak_2287_eu868/  multitech_mtcap_eu868/  etc.
```

Configure the concentratord to use the RAK2287 EU868 profile:

```bash
# Edit the symlink to point at the right profile
ln -sf /opt/chirpstack-concentratord/sx1302/rak_2287_eu868/concentratord.toml \
       /etc/chirpstack-concentratord/concentratord.toml
ln -sf /opt/chirpstack-concentratord/sx1302/rak_2287_eu868/channels.toml \
       /etc/chirpstack-concentratord/channels.toml
```

### Point the gateway-bridge at your laptop

Edit `/etc/chirpstack-gateway-bridge/chirpstack-gateway-bridge.toml`:

```toml
[backend]
  type = "concentratord"

  [backend.concentratord]
    event_url = "ipc:///tmp/concentratord_event"
    command_url = "ipc:///tmp/concentratord_command"

[integration]
  marshaler = "protobuf"

  [integration.mqtt]
    event_topic_template = "eu868/gateway/{{ .GatewayID }}/event/{{ .EventType }}"
    state_topic_template = "eu868/gateway/{{ .GatewayID }}/state/{{ .StateType }}"
    command_topic_template = "eu868/gateway/{{ .GatewayID }}/command/#"
    server = "tcp://192.168.1.42:1883"   # ← your laptop's IP
    json = false
```

Restart services:

```bash
systemctl restart chirpstack-concentratord
systemctl restart chirpstack-gateway-bridge

# Check status
systemctl status chirpstack-concentratord
systemctl status chirpstack-gateway-bridge

# Tail logs
journalctl -u chirpstack-concentratord -f
journalctl -u chirpstack-gateway-bridge -f
```

You should see in the gateway-bridge logs:
```
INFO Connected to MQTT broker
INFO Subscribing to topic ... eu868/gateway/.../command/#
```

## 🆔 Step 7 — Find the Gateway EUI

```bash
# The gateway EUI is derived from eth0 MAC by inserting FFFE in the middle
ip link show eth0 | grep ether
# Example output: link/ether dc:a6:32:01:23:45 brd ff:ff:ff:ff:ff:ff

# Convert MAC dc:a6:32:01:23:45 → EUI dca632fffe012345
# (Insert "fffe" between the 3rd and 4th byte)
```

Or get it from the concentratord:

```bash
grep -i 'gateway_id' /var/log/messages
journalctl -u chirpstack-concentratord | grep -i 'gateway id'
```

## ➕ Step 8 — Register on ChirpStack

Same procedure as the RAK7268:

1. Open ChirpStack web UI on your laptop
2. **Gateways → Add Gateway**
3. Name: `gw-sensecap-m1-01`
4. Gateway ID: the EUI from Step 7
5. Region: EU868
6. Save

Within a minute, status flips to **Online**.

## ✅ Verify both gateways work

Now you have two gateways. With one device in range of both, ChirpStack will:
- Receive the same uplink twice (once via each gateway)
- Deduplicate and keep the version with the best RSSI
- Use the better-positioned gateway for downlinks

In ChirpStack → your device → **LoRaWAN frames** → click an uplink → look at `RxInfo` → you'll see both gateways listed with their RSSI/SNR.

## 🔧 SenseCAP M1 specific gotchas

| Issue | Fix |
|---|---|
| Gateway boots but no LoRa packets | Wrong concentratord profile — try `rak_2287_eu868` vs `generic_eu868` |
| LED stays red | Power supply issue — must be 12V/2A, USB-C PD won't work for the LoRa side |
| Random reboots | SenseCAP enclosure has poor airflow; check CPU temp with `vcgencmd measure_temp` |
| Can't find gateway on network | Check the M1's status LED — green = booted, blue = network up |
| eMMC flash fails | The CM4 might have the bootloader's eMMC write disabled — check with `vcgencmd otp_dump` |

## 🆘 Recovery — if you brick it

If the gateway won't boot after flashing:

1. Put it back in BOOT mode (jumper)
2. Connect USB-C to laptop
3. `sudo rpiboot` again
4. Reflash with the original Helium image (download from Seeed's GitHub) OR reflash ChirpStack Gateway OS

You cannot brick the CM4 itself this way — the bootloader is in ROM. The eMMC is always recoverable via USB Boot mode.

## 📁 Files in this folder

```
README.md                    → this file
downloads/                   → put the .wic.gz image here (gitignored)
configs/
  ├── gateway-bridge.toml    → reference gateway-bridge config
  └── concentratord-eu868.toml → reference concentratord config
```

## ➡️ Next step

You now have two gateways feeding the same ChirpStack server. Time to add a device:
→ `../test-devices/README.md`
