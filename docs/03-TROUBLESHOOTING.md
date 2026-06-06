# Troubleshooting Reference

A symptom-driven guide. Look up your symptom; follow the diagnostic.

## Network Server (ChirpStack)

### "Cannot reach http://192.168.x.x:8080"
- `docker compose ps` — is `chirpstack` container running?
- `docker compose logs chirpstack` — startup errors?
- Firewall on laptop blocking port 8080 to LAN?
- Wrong IP — `ip addr` to confirm

### "Login fails with admin/admin"
- You changed the password (good) — use the new one
- Or the database wasn't initialized — `docker compose down -v && docker compose up -d`

### "Containers keep restarting"
- Check `docker compose logs <service>`
- Common cause: `chirpstack` starts before `postgres` is ready. Solution: wait 30s on first start
- Check disk space: `df -h`

### "Postgres won't start"
- Permissions on volume: `sudo chown -R 999:999 ./postgres_data` (Postgres image UID)
- Corrupted volume: `docker compose down -v` (DELETES DATA)

## Gateway

### "Gateway never goes online in ChirpStack"
- From gateway, can it reach the NS? `ping <laptop_ip>` and `nc -uvz <laptop_ip> 1700`
- On the gateway web UI, does Packet Forwarder show "Running"?
- Did you save the config? Some firmware needs Save → Apply → reboot
- EUI mismatch — the EUI you registered in ChirpStack must EXACTLY match the one on the gateway (case-insensitive, no separators)

### "Gateway online but no LoRa packets visible"
- Antenna actually attached and pointing up?
- Is there any LoRaWAN traffic in your area? Power on a known-good end device near the gateway
- Check the LoRa Packet Logger page on the gateway directly — does the gateway itself see RF?
- Wrong region — gateway set to US915 but devices are EU868

### "Gateway loses time, downlinks fail"
- NTP not working. From gateway: `ntpd -d` or check `/var/log/messages`
- Check the gateway can reach `pool.ntp.org` on UDP 123
- Confirm timezone is set correctly

### "Gateway reboots every few minutes"
- Underpowered PSU — use the official 12V/1A adapter, not a phone charger
- Overheating — measure CPU temp, add ventilation
- Watchdog killing packet forwarder repeatedly — upgrade firmware

## Devices

### "Device sticker shows DevEUI but join fails"
- AppKey wrong — double-check every hex character
- Wrong LoRaWAN version selected in Device Profile
- Wrong region — device may be locked to a different band
- Device using ABP not OTAA — different config path in ChirpStack

### "Device joins but no uplinks arrive"
- Look at "Live LoRaWAN frames" — are uplinks visible at the gateway level but not at the device level?
- This usually means MIC failure — wrong AppSKey/NwkSKey, meaning the keys were entered wrong
- Or DevAddr collision — extremely rare

### "Uplinks arrive but payload is garbage"
- Payload codec missing or wrong — paste the right JS codec in the Device Profile
- fPort doesn't match — some sensors use port 2 not 85, codec should handle both

## MQTT

### "Can't subscribe to MQTT from another machine"
- `mosquitto_sub -h <laptop_ip> -t '#' -v` should show everything
- If timeout: firewall blocking 1883
- If "Connection refused": Mosquitto not running

### "Don't see uplink events on MQTT"
- Correct topic pattern? `application/+/device/+/event/up`
- Device actually sending uplinks? Check the ChirpStack web UI first
- Wrong tenant/app? Topics include the app ID

## SenseCAP M1 specific

### "rpiboot doesn't see the device"
- BOOT jumper / pins not properly shorted
- Wrong USB port — must be USB OTG, not the data USB
- USB cable is power-only — use a proper data cable

### "Flash succeeds but device won't boot"
- Did you remove the BOOT jumper before powering up? It must be removed.
- Wrong image — make sure you used the 64-bit Pi 4 / CM4 image
- Image corrupted — re-download and verify SHA256

### "Concentratord won't start after flash"
- Wrong profile — try different profiles in `/opt/chirpstack-concentratord/sx1302/`
- SPI not enabled — `raspi-config` → Interfaces → SPI → Enable
- Hardware fault on the concentrator card — try moving it to a known-good carrier board

## Performance issues

### "Web UI feels slow"
- Postgres needs more RAM at scale — increase Docker memory limit
- Browser cache — try incognito
- Network latency to laptop — use Ethernet not WiFi

### "Uplinks delayed by minutes"
- Check Mosquitto isn't dropping messages: `docker compose logs mosquitto`
- Check Redis isn't out of memory: `docker compose exec redis redis-cli info memory`
- Check the gateway's packet forwarder isn't lagging: gateway-side logs

## When all else fails

1. Read the ChirpStack forum: https://forum.chirpstack.io/
2. ChirpStack docs: https://www.chirpstack.io/docs/
3. RAKwireless forum: https://forum.rakwireless.com/
4. The Things Network forum (still useful for LoRaWAN questions in general): https://www.thethingsnetwork.org/forum/
