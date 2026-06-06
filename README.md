# LORAWAN — Private LoRaWAN Network for Rwanda

A self-hosted private LoRaWAN network built on **ChirpStack v4**, running on a laptop for development. Currently operational on **US915** for bench testing; **migrating to EU868** for Rwanda production deployment.

## Status (as deployed June 2026)

- ✅ ChirpStack v4 NS running on laptop (`192.168.1.23:8080`)
- ✅ Mosquitto MQTT broker accessible on `192.168.1.23:1883`
- ✅ Seeed WM1302 SPI US915 gateway online (`192.168.1.123`, EUI `0016c001f11368ba`)
- ✅ MQTT data path confirmed end-to-end
- 🚧 No end devices joined yet (waiting for US915 sensor procurement)
- ⏭️ Production migration to EU868 + VPS pending

## What this project contains

```
LORAWAN/
├── chirpstack-server/         → ChirpStack NS, Docker Compose (laptop)
├── gateway-seeed-wm1302/      → Deployed gateway (Seeed WM1302 SPI on Pi 4)  ← us
├── gateway-rak7268/           → Alternative gateway docs (for future RAK7268)
├── gateway-sensecap-m1/       → Earlier work for SenseCAP M1 (superseded)
├── test-devices/              → Codecs + helpers for end devices
├── docs/                      → Architecture + ops + deployment record
│   ├── 01-ARCHITECTURE.md
│   ├── 02-OPERATIONS.md
│   ├── 03-TROUBLESHOOTING.md
│   ├── 04-DEPLOYMENT-RECORD.md  ← read this after the README
│   └── runbook/
│       ├── operator-runbook.md
│       └── validation-checklist.md
├── scripts/                   → start/stop/backup/diagnostics
└── .vscode/                   → VS Code workspace
```

## Where to start

**If you're picking this up fresh:**
1. Read `docs/04-DEPLOYMENT-RECORD.md` — the complete as-built record of what works and why
2. Read `docs/01-ARCHITECTURE.md` — conceptual overview
3. Run through `docs/runbook/validation-checklist.md` to confirm the deployment is healthy

**If you're operating it day-to-day:**
- `docs/runbook/operator-runbook.md` — common procedures
- `docs/runbook/validation-checklist.md` — post-reboot smoke test
- `docs/03-TROUBLESHOOTING.md` — when something breaks

**If you're rebuilding from scratch:**
- Phase-by-phase in `docs/04-DEPLOYMENT-RECORD.md`

## Quick start (laptop)

```bash
cd ~/LORAWAN
./scripts/start.sh                  # Start ChirpStack stack
./scripts/check-network.sh          # Verify everything green
```

## Quick start (gateway)

```bash
ssh root@192.168.1.123
ps w | grep -E "concentratord|mqtt-forwarder" | grep -v grep
logread | grep -iE "concentr|mqtt" | tail -10
```

## Architecture summary

```
End devices  ──LoRa US915──►  Seeed WM1302 gateway  ──MQTT──►  Laptop ChirpStack
   (TBD)                       (192.168.1.123)     (1883)      (192.168.1.23:8080)
```

Full diagrams in `docs/01-ARCHITECTURE.md` and `docs/04-DEPLOYMENT-RECORD.md`.

## Critical reminders

- **US915 is a bench-only configuration.** Rwanda regulatory band is EU868. Don't deploy this outdoors or for production until EU868 hardware is in place. Migration steps in `gateway-seeed-wm1302/README.md` Section 6.
- **Gateway EUI is the chip-burned one**: `0016c001f11368ba`. Not the MAC-derived one.
- **Concentratord model must be `seeed_wm1302`**, not `semtech_sx1302css915gw1`. Wrong model = USB instead of SPI = crash.
- **Default `chirpstack-concentratord` init script is broken** for SX1302 hardware. Use the `-fixed` replacement init script.
- **Laptop IP is dynamic DHCP** (`192.168.1.23`). Lock it down — when it changes, the gateway loses contact.

## License

Project files: MIT. ChirpStack itself: Apache 2.0. Seeed/Semtech firmware: vendor EULA.
