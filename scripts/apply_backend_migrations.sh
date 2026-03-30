#!/usr/bin/env bash
# Apply SQL migrations in src/backend/db/migrations using SUPABASE_DB_URL from src/.env
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src"
ENV_FILE="$SRC/.env"
MIG_DIR="$SRC/backend/db/migrations"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy src/.env.example to src/.env and set SUPABASE_DB_URL."
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

if [[ -z "${SUPABASE_DB_URL:-}" ]]; then
  echo "SUPABASE_DB_URL is empty in src/.env"
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Install Postgres client (e.g. brew install libpq && brew link --force libpq)"
  echo "or run each file in Supabase SQL Editor: $MIG_DIR/*.sql"
  exit 1
fi

for f in "$MIG_DIR"/001_*.sql "$MIG_DIR"/002_*.sql "$MIG_DIR"/003_*.sql "$MIG_DIR"/004_*.sql; do
  [[ -f "$f" ]] || continue
  echo "Applying $(basename "$f")..."
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f "$f"
done

echo "Done. Optional demo seed: psql \"\$SUPABASE_DB_URL\" -f src/backend/db/seeds/demo_critical_sms.sql"
