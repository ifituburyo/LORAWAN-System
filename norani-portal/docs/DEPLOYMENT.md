# Deployment Guide — Norani Portal on Ubuntu AWS

This guide assumes you have an existing Ubuntu 22.04 EC2 instance with ChirpStack v4 already running on port 8080.

## 1. Prerequisites

```bash
# Install required system packages
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
                    postgresql-client \
                    nginx certbot python3-certbot-nginx \
                    git

# Install Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # should print v20.x
```

## 2. Create the portal database

```bash
sudo -u postgres psql <<'EOF'
CREATE DATABASE norani_portal;
CREATE USER norani_portal WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE norani_portal TO norani_portal;
\c norani_portal
GRANT ALL ON SCHEMA public TO norani_portal;
EOF
```

## 3. Clone the portal repo

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone <your-repo-url> norani-portal
sudo chown -R $USER:$USER /opt/norani-portal
cd /opt/norani-portal
```

## 4. Generate secrets

```bash
# JWT signing key (64 hex chars)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# AppKey encryption key (Fernet format)
python3 -c "from cryptography.fernet import Fernet; print('APPKEY_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

Save these — they're needed in `.env` below.

## 5. Get ChirpStack API token

1. Open ChirpStack web UI (typically http://localhost:8090 via SSH tunnel)
2. Go to **Tenant → API Keys → Add API key**
3. Tick **"Is admin"** (gives full access)
4. Name it: `norani-portal`
5. Copy the generated token

## 6. Set up the backend

```bash
cd /opt/norani-portal/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env   # Fill in all the values from steps 2, 4, 5

# Run migrations
alembic upgrade head

# Bootstrap initial admin user + device type catalog
python -m app.scripts.bootstrap
# It will prompt for admin email, name, password
# Or set BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD env vars

deactivate
```

## 7. Test the backend locally

```bash
cd /opt/norani-portal/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal:
curl http://localhost:8000/api/v1/health
# Should return: {"status":"ok",...}
```

Ctrl-C to stop, then `deactivate`.

## 8. Install backend as a systemd service

```bash
sudo cp /opt/norani-portal/deploy/systemd/norani-portal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable norani-portal
sudo systemctl start norani-portal
sudo systemctl status norani-portal   # should show 'active (running)'
sudo journalctl -u norani-portal -f   # tail logs
```

## 9. Build the frontend

```bash
cd /opt/norani-portal/frontend
npm install
npm run build
# Produces /opt/norani-portal/frontend/dist
```

## 10. Configure DNS

In your DNS provider (RICTA or wherever norani.rw is managed):

```
Type: A
Name: portal
Value: <your-EC2-public-IP>
TTL: 300
```

Wait a few minutes for DNS propagation. Verify:

```bash
dig portal.norani.rw +short
# Should print your EC2 IP
```

## 11. Configure Nginx

```bash
sudo cp /opt/norani-portal/deploy/nginx/portal.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/portal.conf /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Allow Let's Encrypt webroot before getting cert
sudo mkdir -p /var/www/letsencrypt

sudo systemctl reload nginx
```

## 12. Get TLS certificate

```bash
sudo certbot --nginx -d portal.norani.rw \
  --email founder@norani.rw \
  --agree-tos \
  --redirect
```

Certbot will:
- Add the TLS cert
- Update the nginx config to use it
- Configure auto-renewal (runs twice daily via systemd timer)

## 13. Verify everything works

```bash
# HTTPS check
curl -I https://portal.norani.rw
# Should return 200 OK

# API check
curl https://portal.norani.rw/api/v1/health

# Visit in browser
# https://portal.norani.rw
# Login with the admin credentials you set in step 6
```

## 14. Post-deployment: Link device types to ChirpStack profiles

The bootstrap script seeded a catalog of device types with **placeholder** ChirpStack profile IDs. Before you can create real devices, you need to:

1. In ChirpStack web UI: **Tenant → Device Profiles → Add device profile** for each device model you support (Dragino LHT65N, Milesight EM300-TH, etc.)
2. Copy each profile's UUID
3. Update the `device_types` table:

```bash
sudo -u postgres psql norani_portal
UPDATE device_types
SET chirpstack_profile_id = '<real-uuid-from-chirpstack>'
WHERE model = 'LHT65N';
\q
```

(A future improvement: build an admin UI to do this without raw SQL.)

## Maintenance

### Updating the portal after code changes

```bash
cd /opt/norani-portal
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate
sudo systemctl restart norani-portal

# Frontend
cd ../frontend
npm install
npm run build
# Nginx serves the new dist/ immediately, no restart needed
```

### Viewing logs

```bash
# Backend logs
sudo journalctl -u norani-portal -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database backup

```bash
# Daily cron job
sudo -u postgres pg_dump norani_portal | gzip > /backup/norani_portal_$(date +%F).sql.gz
```

Add to `/etc/cron.daily/backup-norani`:

```bash
#!/bin/bash
mkdir -p /backup
sudo -u postgres pg_dump norani_portal | gzip > /backup/norani_portal_$(date +%F).sql.gz
# Keep 30 days
find /backup -name "norani_portal_*.sql.gz" -mtime +30 -delete
```

## Troubleshooting

### Backend won't start

```bash
sudo journalctl -u norani-portal -n 100
```

Common causes:
- `.env` file missing or unreadable
- DATABASE_URL incorrect
- ChirpStack not reachable on configured port
- Migrations not run

### Login returns 401 but credentials look right

- Verify the user exists: `psql norani_portal -c "SELECT email, is_active FROM users"`
- Check that the customer account is `is_active = true`

### Device creation returns 502

- ChirpStack API token may be wrong or expired
- Test it directly: `grpcurl -plaintext -H "authorization: Bearer YOUR_TOKEN" localhost:8080 api.TenantService/List`

### Sticker PDF is corrupted in the browser

- Check that ReportLab installed correctly: `python -c "from reportlab.pdfgen import canvas; print('OK')"`
- Check backend logs for ReportLab errors during sticker generation
