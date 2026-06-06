# Architecture

## What this network is

A private **LoRaWAN 1.0.3** network, operating on **EU868** (the band used in Rwanda and most of Africa), running entirely on your own infrastructure. No reliance on TTN public servers, no per-device fees, no licensing pitfalls.

## Components

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│   END DEVICES              GATEWAYS              NETWORK SERVER    │
│   (LoRaWAN sensors)        (RAK/SenseCAP)        (ChirpStack v4)   │
│                                                                    │
│  ┌─────────────┐  LoRa    ┌─────────────┐  UDP/  ┌──────────────┐  │
│  │ Dragino     │  ──RF──► │ RAK7268CV2  │  MQTT  │ Your laptop  │  │
│  │ LHT65N      │          │             │  ────► │ or VPS       │  │
│  └─────────────┘          └─────────────┘        │              │  │
│                                                  │ ┌──────────┐ │  │
│  ┌─────────────┐  LoRa    ┌─────────────┐  UDP/  │ │ NS+AS    │ │  │
│  │ Milesight   │  ──RF──► │ SenseCAP M1 │  MQTT  │ │ PostgreSQL│ │  │
│  │ EM300       │          │ (converted) │  ────► │ │ Redis    │ │  │
│  └─────────────┘          └─────────────┘        │ │ Mosquitto│ │  │
│                                                  │ └──────────┘ │  │
│                                                  └──────┬───────┘  │
│                                                         │          │
│                                                  MQTT / HTTP /     │
│                                                  InfluxDB          │
│                                                         │          │
│                                                  ┌──────▼───────┐  │
│                                                  │ Customer app │  │
│                                                  │ / dashboard  │  │
│                                                  └──────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Why ChirpStack and not TTS/TTN

| Aspect | ChirpStack | The Things Stack (TTS) |
|---|---|---|
| License | Apache 2.0 — fully free, commercial OK | Source-available, **commercial self-host needs paid license** |
| Cost at scale | $0 in software fees | Per-device or per-tenant fees on cloud, license fee for self-host |
| Maintained by | Semtech | The Things Industries |
| Community | Growing, active forum | Larger, more docs |
| TTN compatibility | Speaks LoRaWAN — devices and gateways work the same | Same |
| For your business model | ✅ Better | Possible but commercial restrictions |

## The 4 LoRaWAN entities (in ChirpStack terminology)

These are the building blocks you'll create for every customer:

1. **Tenant** — a customer or business unit. Each tenant is isolated.
2. **Application** — a logical grouping of devices within a tenant (e.g. "Farm-North-Moisture", "Office-Doors").
3. **Device Profile** — describes a model of device (e.g. "Dragino-LHT65N-EU868"). Reusable across many devices.
4. **Device** — the actual sensor, identified by DevEUI + AppKey.

## Data flow for one uplink

```
1. Sensor wakes up, samples temperature
2. Builds LoRaWAN MAC frame, encrypts payload with AppSKey
3. Transmits on 868.3 MHz (or one of 8 channels), SF12 default
4. Both gateways (in range) receive the same packet
5. Each gateway forwards via UDP 1700 → Gateway Bridge → MQTT → ChirpStack
6. ChirpStack deduplicates (keeps the version with best RSSI)
7. Decrypts payload, applies JavaScript codec → JSON
8. Publishes to MQTT topic: application/<APP_ID>/device/<DEV_EUI>/event/up
9. Customer app subscribes to that topic and gets the JSON
```

End-to-end latency: 100–500 ms typically, depending on spreading factor.

## Frequency plan (EU868) for Rwanda

LoRaWAN mandatory channels (always enabled):
- 868.1 MHz
- 868.3 MHz
- 868.5 MHz

Optional channels (enabled in our config):
- 867.1, 867.3, 867.5, 867.7, 867.9 MHz

RX2 window (downlink): 869.525 MHz @ SF12

Power: 14 dBm EIRP (legal max for EU868; Rwanda RURA SRD regulations align with this)

Duty cycle: 1% on 868.0–868.6 MHz, 0.1% on 867.x band — devices and gateways must respect this in firmware.

## Capacity planning

Single gateway capacity:
- ~10,000 devices at SF7, 1 uplink/hour, small payloads
- ~1,500 devices at SF12 (worst case spreading factor)
- ~100,000+ devices possible with mostly Class C and good RF planning

Server capacity (ChirpStack on a 2 vCPU / 4 GB VM):
- ~50 gateways
- ~50,000 devices
- ~10 uplinks/sec sustained

When you outgrow these numbers, scale horizontally: separate Gateway Bridge from NS, add a load balancer, use PostgreSQL replicas.

## Development → Production migration path

**Phase 1 (now):** Everything on your laptop. Gateways on your LAN.
**Phase 2 (~50 devices):** Migrate to a Hetzner / DigitalOcean VM. Same Docker Compose. Add domain + Let's Encrypt TLS.
**Phase 3 (~1000 devices):** Add monitoring (Grafana), automated backups, status page, on-call procedure.
**Phase 4 (~10,000 devices):** Split into separate VMs for Postgres, MQTT, NS. Add a CDN-fronted load balancer. Multi-region replication.

## Security model

For the development phase (this project):
- Plain HTTP web UI (laptop only)
- Anonymous MQTT (LAN only)
- Default passwords changed but no TLS
- No per-customer isolation

For production (add after pilot):
- Nginx reverse proxy with Let's Encrypt
- MQTT over TLS (port 8883)
- Per-customer tenants with collaborator-only roles
- API tokens with limited scope (no superuser tokens to customers)
- Daily PostgreSQL backups to off-site storage
- Fail2ban on SSH
- RURA-compliant data residency considerations (Rwanda Law N° 058/2021)
