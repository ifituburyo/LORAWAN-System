# Operations Runbook

Day-to-day operating procedures once the network is running.

## Daily — automatic

- ChirpStack containers auto-restart on crash (set in docker-compose.yml)
- Gateway Bridge auto-reconnects to MQTT on network blips
- Gateways auto-reconnect to NS

## Daily — you should glance at

```bash
cd /home/izera/LORAWAN
docker compose -f chirpstack-server/docker-compose.yml ps     # all containers Up?
./scripts/check-network.sh                                    # ports listening?
```

In the web UI:
- Network Server → Gateways → any showing "Last seen > 10 min ago" = investigate
- Applications → device list → any device with stale "Last seen" = sensor died, battery, out of range, or de-provisioned

## Weekly — back up data

```bash
./scripts/backup.sh
# Copy the resulting .sql.gz to off-laptop storage:
rsync -av ./backups/ user@offsite-server:/path/to/backups/
```

## When you add a new gateway

1. Configure the physical gateway to point at your NS (UDP 1700 or BS 3001)
2. In ChirpStack: Gateways → Add Gateway → enter EUI + name + location
3. Wait 60s, confirm "Online" status
4. Record the new gateway in `docs/INVENTORY.md` (create this file)

## When you add a new customer

1. **Create a tenant** for them: Tenants → Add Tenant → name = customer company
2. **Create a user** for them: Users → Add User → assign to their tenant
3. **Optionally create an API key** for their own systems: Tenant → API Keys
4. Send them:
   - Web UI URL: `http://<your-ip>:8080` (or `https://ns.yourcompany.rw`)
   - Their login credentials
   - The MQTT credentials if they want server-to-server integration
   - The "Customer Onboarding" PDF (see `docs/CUSTOMER-ONBOARDING.md`)

## When a device won't join

Check in this order:

1. **Is the gateway online?** Network Server → Gateways → confirm green
2. **Is the device transmitting?** Use a SDR (RTL-SDR + gqrx) tuned to 868 MHz to listen, or look at Gateway Live Frames in ChirpStack
3. **Are credentials correct?** Re-read DevEUI/JoinEUI/AppKey from the device sticker, compare to ChirpStack
4. **Is the device in OTAA mode?** Some devices ship in ABP; consult the manual
5. **Is the device using the right region?** A device flashed for US915 will never join EU868
6. **Wait long enough?** Some devices wait up to an hour between join attempts. Press the join button or power-cycle the device.

If you see `JoinRequest` in Gateway Live Frames but no `JoinAccept`:
- NTP problem on the gateway (downlink window timing off)
- Or device is too close to gateway (RF saturation — move 5 meters apart)

If you don't see `JoinRequest` at all:
- Device isn't transmitting, OR
- No gateway in range, OR
- Device on wrong frequency band

## When a gateway goes offline

ChirpStack marks a gateway offline after 90 seconds without stats.

Diagnostic order:
1. Can you ping the gateway from your laptop?
   - No → network problem (ISP, router, cable)
   - Yes → continue
2. SSH to the gateway, check the packet forwarder:
   ```bash
   ssh root@gateway-ip
   logread -f | grep -i lora
   ps | grep pkt_fwd      # is it running?
   ```
3. From the gateway, can it reach your NS?
   ```bash
   ping 192.168.1.42       # your laptop
   nc -zvu 192.168.1.42 1700  # test UDP port
   ```
4. Restart the packet forwarder:
   ```bash
   /etc/init.d/lora_pkt_fwd restart
   ```
5. If still broken, reboot the gateway:
   ```bash
   reboot
   ```

## When ChirpStack acts up

```bash
# Tail logs of the affected component
docker compose -f chirpstack-server/docker-compose.yml logs -f chirpstack
docker compose -f chirpstack-server/docker-compose.yml logs -f chirpstack-gateway-bridge
docker compose -f chirpstack-server/docker-compose.yml logs -f postgres

# Restart a single service
docker compose restart chirpstack

# Nuclear: full restart
docker compose down && docker compose up -d
```

## Capacity warnings

Set up Grafana later, but until then watch for:

- PostgreSQL container CPU >50% sustained → time to move to a real VM
- Mosquitto MQTT broker memory growing unbounded → check for slow subscribers
- Disk space on laptop <10% free → backup and clean docker volumes

## Production migration checklist

When you're ready to leave the laptop:

- [ ] Provision a 2vCPU/4GB VPS (Hetzner CX22 ~ €5/mo recommended for East Africa)
- [ ] Buy a domain (e.g. `iot.yourcompany.rw`)
- [ ] Point DNS A record at the VPS public IP
- [ ] Install Docker + Docker Compose on the VPS
- [ ] Copy the entire `chirpstack-server/` folder to the VPS
- [ ] Run `./scripts/backup.sh` on laptop
- [ ] `scp backups/*.sql.gz vps:/tmp/`
- [ ] Restore: `gunzip -c /tmp/*.sql.gz | docker compose exec -T postgres psql -U chirpstack chirpstack`
- [ ] Add Nginx + Certbot for TLS
- [ ] Update gateway configs to point at the new domain
- [ ] Verify all gateways come back online
- [ ] Set up UptimeRobot pinging your domain
- [ ] Disable Mosquitto anonymous auth, add per-customer passwords
- [ ] Document admin credentials in a password manager
