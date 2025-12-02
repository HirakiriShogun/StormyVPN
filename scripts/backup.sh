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

if command -v pg_dump >/dev/null 2>&1; then
  pg_dump \
    -h "${DB_HOST:-localhost}" \
    -p "${DB_PORT:-5433}" \
    -U "${DB_USER:-stormy}" \
    -d "${DB_NAME:-stormyvpn}" \
    > "$OUT_FILE"
else
  # fallback: run pg_dump inside the running Postgres container
  CONTAINER_NAME="${DB_CONTAINER:-stormyvpn-db}"
  docker exec -i "$CONTAINER_NAME" env PGPASSWORD="$PGPASSWORD" \
    pg_dump -U "${DB_USER:-stormy}" -d "${DB_NAME:-stormyvpn}" > "$OUT_FILE"
fi

# Optionally prune backups older than 30 days
find "$BACKUP_DIR" -type f -name "stormyvpn_*.sql" -mtime +30 -delete

echo "Backup created: $OUT_FILE"
