#!/usr/bin/env bash
# Backup PostgreSQL data — use before migrating to a VPS
# Usage: ./scripts/backup.sh [output_dir]

set -e

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${OUTPUT_DIR}/chirpstack-${TIMESTAMP}.sql.gz"

mkdir -p "$OUTPUT_DIR"

echo "📦 Backing up ChirpStack database..."

docker compose -f "$(dirname "$0")/../chirpstack-server/docker-compose.yml" \
    exec -T postgres pg_dump -U chirpstack chirpstack \
    | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup created: $BACKUP_FILE ($SIZE)"
echo ""
echo "To restore later (e.g. on production VPS):"
echo "  gunzip -c $BACKUP_FILE | docker compose exec -T postgres psql -U chirpstack chirpstack"
