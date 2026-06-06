# Test Devices — Register Your First End Device

Once your ChirpStack server is up and at least one gateway is online, this is where you join your first sensor.

## 🛒 Recommended starter devices

| Device | Price | What it measures | Why |
|---|---|---|---|
| **Dragino LHT65N** | ~$35 | Temperature + humidity + external probe | Cheapest reliable LoRaWAN test device |
| **Dragino LDS01** | ~$25 | Door open/close | Simplest possible payload — great for first test |
| **Milesight EM300-TH** | ~$40 | Temperature + humidity | More polished, has nice payload codec |
| **Browan TBHV110** | ~$30 | Temperature + humidity, robust enclosure | Office-ready |

All four are **LoRaWAN 1.0.3**, **EU868**, and have published payload codecs.

## 🔑 Step 1 — Get the device credentials

Every LoRaWAN end device ships with three values printed on a sticker or in a QR code:

- **DevEUI** — 16 hex chars (e.g. `A84041B2C0000123`)
- **JoinEUI / AppEUI** — 16 hex chars (e.g. `A000000000000101`)
- **AppKey** — 32 hex chars (e.g. `0F8B0F6E3D8A4B... 32 chars`)

⚠️ Some manufacturers also print a `NwkKey` — only used for LoRaWAN 1.1. For 1.0.x devices, only AppKey matters.

## 📝 Step 2 — Create the structure in ChirpStack

In the ChirpStack web UI, create things in this order:

```
Tenant (e.g. "Internal" — you already have this)
  └── Application (e.g. "test-sensors")
        └── Device Profile (e.g. "Dragino-LHT65N-EU868")
        └── Device (the actual sensor)
```

### Create an Application
1. Tenants → Internal → Applications → **Add application**
2. Name: `test-sensors`
3. Description: `Testing devices for the LoRaWAN network`
4. Save

### Create a Device Profile (once per device model)
1. Tenants → Internal → Device profiles → **Add device profile**
2. Name: `Dragino-LHT65N-EU868`
3. Region: `EU868`
4. MAC version: `LoRaWAN 1.0.3`
5. Regional parameters revision: `A`
6. ADR algorithm: `Default ADR algorithm (LoRa only)`
7. Expected uplink interval: `3600` (1 hour — match your device's setting)
8. **Codec** tab: paste the JavaScript codec for the LHT65N (see `codecs/dragino-lht65n.js` in this folder)
9. **Join (OTAA/ABP)** tab: ✅ Device supports OTAA
10. **Class B / Class C** tabs: leave defaults (Class A)
11. Save

### Register the Device
1. Applications → test-sensors → **Add device**
2. **Name:** `lht65-test-01`
3. **DevEUI:** paste from device sticker
4. **Device profile:** `Dragino-LHT65N-EU868`
5. Save
6. On next page, paste the **AppKey** under "OTAA keys" → Save

## 🔋 Step 3 — Activate the device

Most sensors join the network when:
- You insert/connect the battery, OR
- You press a button (often labeled `ACT` or `RST`)

For the Dragino LHT65N: press the button for 5 seconds until the LED flashes — it sends a Join Request.

## 👀 Step 4 — Watch it join

In ChirpStack, click your device → **LoRaWAN frames** tab.

Expected sequence (within ~30 seconds):

```
1. JoinRequest         (device → network)
2. JoinAccept          (network → device)
3. UnconfirmedDataUp   (first uplink — usually battery status)
```

Then under the **Events** tab, you'll see the decoded payload as JSON:

```json
{
  "BatV": 3.046,
  "TempC_SHT": 24.5,
  "Hum_SHT": 67.8,
  "Ext_sensor": "Temperature Sensor"
}
```

## 🎉 You now have a working private LoRaWAN network.

Sensor → your gateway → your NS → decoded JSON. Everything else is scaling.

## 📤 Step 5 — Get data out (to customer apps)

In ChirpStack → Applications → test-sensors → **Integrations** tab:

- **MQTT** — already running. Subscribe to:
  ```
  application/<APP_ID>/device/<DEV_EUI>/event/up
  ```
  with `mosquitto_sub -h 192.168.1.42 -t 'application/+/device/+/event/up' -v`

- **HTTP Webhook** — POSTs each uplink to a URL you provide. Good for testing with `webhook.site`

- **InfluxDB** — store time-series data, query with Grafana

## 📂 Files in this folder

```
README.md                    → this file
codecs/
  ├── dragino-lht65n.js      → JS payload decoder for LHT65N
  ├── dragino-lds01.js       → JS payload decoder for door sensor
  └── milesight-em300.js     → JS payload decoder for EM300-TH
scripts/
  ├── register-device.sh     → Bulk-register devices via REST API
  └── mqtt-listen.sh         → Subscribe to all uplinks via MQTT
```

## ➡️ Next step

Once devices are joining and you see decoded data:
→ Read `../docs/02-OPERATIONS.md` for the production migration plan.
