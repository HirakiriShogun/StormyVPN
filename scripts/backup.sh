#!/usr/bin/env bash
set -euo pipefail


ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | grep '=' | xargs)
fi

BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
mkdir -p "$BACKUP_DIR"

PGPASSWORD="${DB_PASSWORD:-stormypass}"
export PGPASSWORD

DATE_STR="$(date +%F_%H-%M-%S)"
OUT_FILE="$BACKUP_DIR/stormyvpn_${DATE_STR}.sql"

pg_dump \
  -h "${DB_HOST:-localhost}" \
  -p "${DB_PORT:-5433}" \
  -U "${DB_USER:-stormy}" \
  -d "${DB_NAME:-stormyvpn}" \
  > "$OUT_FILE"

# Optionally prune backups older than 30 days
find "$BACKUP_DIR" -type f -name "stormyvpn_*.sql" -mtime +30 -delete

echo "Backup created: $OUT_FILE"
