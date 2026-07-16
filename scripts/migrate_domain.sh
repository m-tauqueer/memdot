#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/services/core"

URL="${MEMDOT_MIGRATION_DATABASE_URL:-${CORE_DATABASE_URL:-}}"
if [[ -z "$URL" ]]; then
  echo "MEMDOT_MIGRATION_DATABASE_URL or CORE_DATABASE_URL is required" >&2
  exit 2
fi

export MEMDOT_MIGRATION_DATABASE_URL="$URL"
uv run alembic upgrade head
echo "migration_job=ok"
echo "head=$(uv run alembic current | tail -n 1)"
