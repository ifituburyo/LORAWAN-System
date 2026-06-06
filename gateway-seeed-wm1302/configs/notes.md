# Hardware notes — Seeed WM1302 SPI US915 on Raspberry Pi 4

## The WM1302 module

- Semtech SX1302 LoRa concentrator
- Two SX1250 radio front-ends (one TX/RX, one RX-only)
- Mini-PCIe form factor (standard 52-pin)
- SPI variant: communicates over SPI bus
- USB variant exists too — different model name, different driver path

## Valid concentratord model strings

Extracted from `strings /usr/bin/chirpstack-concentratord-sx1302`:

| Model string | Hardware | Interface |
|---|---|---|
| `dragino_pg1302` | Dragino PG1302 | SPI |
| `embit_emb_lr1302_mpci` | Embit EMB-LR1302 | mPCIe SPI |
| `miromico_gwc_02_lw_868` | Miromico GWC-02-LW EU868 | SPI |
| `miromico_gwc_02_lw_915` | Miromico GWC-02-LW US915 | SPI |
| `multitech_mtac_003e00` | MultiTech MTAC EU | varies |
| `multitech_mtac_003u00` | MultiTech MTAC US | varies |
| `multitech_mtcap3_003e00` | MultiTech mCard EU | varies |
| `multitech_mtcap3_003u00` | MultiTech mCard US | varies |
| **`seeed_wm1302`** | **Seeed WM1302 (any band)** | **SPI** ← ours |
| `semtech_sx1302c490gw1` | Semtech reference 490 MHz | SPI (single `c`) |
| `semtech_sx1302c868gw1` | Semtech reference EU868 | SPI (single `c`) |
| `semtech_sx1302c915gw1` | Semtech reference US915 | SPI (single `c`) |
| `semtech_sx1302css868gw1` | Semtech CSS USB EU868 | USB (double `ss`) |
| `semtech_sx1302css915gw1` | Semtech CSS USB US915 | USB (double `ss`) — DO NOT USE WITH SPI HARDWARE |
| `semtech_sx1302css923gw1` | Semtech CSS USB AS923 | USB |
| `waveshare_sx1302_lorawan_gateway_hat` | Waveshare Pi HAT | SPI |
| `rak_2287` | RAK2287 | SPI |
| `rak_5146` | RAK5146 | SPI |

### Naming convention decoded

- `c` (single) in `sx1302c...` = **SPI** reference design
- `css` (double s) in `sx1302css...` = **USB** reference design (CSS = Concentrator Shield Sema? Anyway: USB)
- Vendor-prefixed names (`seeed_`, `rak_`, etc.) = SPI by default

## Region is set separately

The `model` field selects hardware (SPI pins, TX gain table, RF filters).
The `region` field selects frequencies (US915 / EU868 / AS923 / etc.).

These are **independent**. The Seeed WM1302 can be configured for any region — just change the `region` field and copy the matching `region.toml` and `channels.toml` from `/etc/chirpstack-concentratord/sx1302/examples/`.

## The Seeed Gateway Hat for Raspberry Pi

40-pin GPIO header → Pi 4 GPIO header. Pin assignments (BCM numbering) used by the `seeed_wm1302` profile:

| Function | BCM Pin | Physical Pin |
|---|---|---|
| SPI MOSI | GPIO 10 | 19 |
| SPI MISO | GPIO 9 | 21 |
| SPI SCLK | GPIO 11 | 23 |
| SPI CS0 | GPIO 8 | 24 |
| SX1302 Reset | GPIO 17 | 11 |
| SX1302 Power Enable | GPIO 18 | 12 |
| SX1261 Reset (LBT, optional) | GPIO 5 | 29 |

These are embedded in the `seeed_wm1302` model profile inside the concentratord binary — you don't need to specify them in `concentratord.toml`.

## SPI device path

ChirpStack Gateway OS for Pi enables SPI by default. Confirm with:

```bash
ls -la /dev/spidev*
# /dev/spidev0.0  /dev/spidev0.1
```

The `seeed_wm1302` model uses `/dev/spidev0.0` (the first SPI device, chip select 0).

If `/dev/spidev*` is missing, SPI isn't enabled. Add to `/boot/config.txt`:
```
dtparam=spi=on
```

## RF connectors on the WM1302

The module has two u.FL connectors:

- **RFI0** — main TX/RX, 50 ohm. **Connect to your LoRa antenna.**
- **RFI** (sometimes labeled differently) — secondary RX or GNSS, depends on variant

Always connect at least RFI0 before powering on. Operating without antenna can damage the PA stage.

## US915 channel plan reference

ChirpStack `us915_0` (sub-band 1) uses these uplink channels (also what TTN uses):

| # | Frequency (MHz) | DR |
|---|---|---|
| 0 | 902.3 | 0-3 |
| 1 | 902.5 | 0-3 |
| 2 | 902.7 | 0-3 |
| 3 | 902.9 | 0-3 |
| 4 | 903.1 | 0-3 |
| 5 | 903.3 | 0-3 |
| 6 | 903.5 | 0-3 |
| 7 | 903.7 | 0-3 |
| 64 | 903.0 | 4 (LoRa-Std, SF8 BW500) |

Downlink channels (also for RX2):
- RX1 maps to one of: 923.3, 923.9, 924.5, 925.1, 925.7, 926.3, 926.9, 927.5 MHz (DR8-13)
- RX2 fixed: 923.3 MHz, DR8 (SF12 BW500)

For sub-band 2 (`us915_1`), channels are 8-15 + 65, downlinks the same.

## EU868 channel plan reference (for when EU868 hardware arrives)

Mandatory (always enabled):
- 868.1 MHz
- 868.3 MHz
- 868.5 MHz

Optional (typically enabled in chirpstack):
- 867.1, 867.3, 867.5, 867.7, 867.9 MHz

RX2: 869.525 MHz @ DR0 (SF12 BW125)

Max EIRP: +14 dBm in most EU868 sub-bands (some allow +27 dBm with 10% duty cycle).
