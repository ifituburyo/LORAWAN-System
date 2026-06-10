# Norani Portal

The customer-facing portal for Norani's LoRaWAN network.

## Quick Start

### Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your secrets
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173

## Architecture

See `docs/ARCHITECTURE.md` and the companion design spec PDF.

## Repository structure

```
backend/   FastAPI + SQLAlchemy + Alembic
frontend/  React 18 + Vite + Tailwind + TypeScript
deploy/    Nginx config, systemd units
```
